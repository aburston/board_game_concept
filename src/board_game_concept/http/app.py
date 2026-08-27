"""The Flask app that serves the read side.

Reads only. `POST` and long-poll are later steps. Each read is one request;
each request opens a `Game` for its player, calls `load()`, and returns the
JSON view - no app-level cache to disagree with the game.

The route paths carry the player number because that is what `Game(
repository, number)` takes today. When authentication lands, the identity
moves to a token and the path stops carrying it.
"""

import time

from flask import Flask, jsonify, request

from ..cli import session as session_module
from ..service import games as game_ops
from ..service import identity
from ..service.commands import as_record as _AS_RECORD, from_record
from ..service.errors import (AccountError, GameDataError, GameError,
                              NoSuchGame, NoSuchPlayer, UnreadableGame)
from ..service.turn import _awaited_players
from ..storage.lock import GameIsBusy
from ..storage.account_store import make_account_store
from .. import Game
from . import auth as auth_module
from . import registry as registry_module
from . import sessions as sessions_module
from . import seats as seats_module
from . import views as views_module
from .auth import acts_as_number, authenticated


# the long-poll wait budget: short enough to keep a proxy happy, long
# enough that a client is not making a fresh request every second.
# `POLL_INTERVAL` matches `notify.py`'s FIFO cadence so latency is the same
# across transports. Tests override `WAIT_BUDGET` down to something small
WAIT_BUDGET = 25.0
POLL_INTERVAL = 0.2


VIEW_BUILDERS = {
    'board': lambda data: views_module.board_view(data.getBoard()),
    'units': lambda data: views_module.units_view(data.getBoard()),
    'types': lambda data: views_module.types_view(data.getPlayers()),
    'players': lambda data: views_module.players_view(
        data.getPlayers(), data.getEliminated(), data.getBoard()),
    'pending': lambda data: views_module.pending_view(
        data.getPlayers(), data.getBoard()),
}

VIEWS_THAT_NEED_A_BOARD = ('board', 'units', 'pending')


def _account_store_factory(base_path, backend=None, account_store=None):
    """How this app opens the account store, and the store made once now.

    A factory rather than a store, for the reason `create_app` builds a
    repository per request: a SQLite connection belongs to the thread that
    opened it, and the app is served threaded. `ensure()` is called once
    here so the two system accounts exist before the first request; each
    request then opens its own store against the same files.

    The backend is the game's backend. One choice drives both, so a
    deployment is YAML or SQLite and never a mixture of the two.
    """
    if account_store is not None:
        account_store.ensure()
        return lambda: account_store
    resolved = backend or session_module.default_backend()
    make_account_store(resolved, base_path).ensure()
    return lambda: make_account_store(resolved, base_path)


def create_app(base_path=None, backend=None, account_store=None):
    """A Flask app configured for a games directory.

    `base_path` is what `YamlGameRepository`/`SqliteGameRepository` take:
    the directory the `games/` tree lives under. Defaults to the process
    working directory, matching the CLI binaries. `backend` overrides the
    default backend chosen by `session_module.default_backend()`.

    `account_store` is where accounts, seats and tokens are kept. It is one
    store for the whole server rather than one per game, and it is ensured
    once at startup - which is what creates `admin` and `observer` the first
    time a server is run.
    """
    # `static_folder` is the directory beside this module; Flask serves it
    # at `/static` and refuses a path that climbs out of it. Everything under
    # it is a plain file - no build step, no package manager, nothing
    # generated
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['BASE_PATH'] = base_path or session_module.default_base_path()
    app.config['BACKEND'] = backend
    app.config['ACCOUNT_STORE_FACTORY'] = _account_store_factory(
        app.config['BASE_PATH'], backend, account_store)

    def _repository(gameno):
        # each request builds its own repository - opening one is cheap and
        # sharing a connection across requests would mean holding a
        # transaction the request cannot see the boundary of
        return session_module.make_repository(
            gameno, backend=app.config['BACKEND'],
            base_path=app.config['BASE_PATH'])

    def _load_game(gameno, player_number):
        game = Game(_repository(gameno), int(player_number))
        game.load()
        return game

    @app.get('/_/health')
    def health():
        return jsonify({'ok': True})

    @app.get('/')
    def page():
        """The one page. Every screen is a route inside it.

        Served without a credential, because it is what a person signs in
        through. It holds no game state: everything it draws it fetches
        through the same contract every other client uses, and every one of
        those requests is guarded.
        """
        return app.send_static_file('index.html')

    @app.get('/games/<gameno>/players')
    @authenticated
    def list_players(gameno):
        return jsonify({'players': _repository(gameno).player_numbers()})

    @app.get('/games/<gameno>/players/<int:number>/state')
    @acts_as_number
    def read_state(gameno, number):
        try:
            data = _load_game(gameno, number)
        except GameDataError as error:
            return _game_error_response(error)
        return jsonify(_state_payload(data))

    @app.get('/games/<gameno>/players/<int:number>/views/<subject>')
    @acts_as_number
    def read_view(gameno, number, subject):
        builder = VIEW_BUILDERS.get(subject)
        if builder is None:
            return jsonify({'error': f'unknown view: {subject}'}), 404
        try:
            data = _load_game(gameno, number)
        except GameDataError as error:
            return _game_error_response(error)
        if subject in VIEWS_THAT_NEED_A_BOARD and data.getBoard() is None:
            return jsonify({'error': 'no board yet'}), 404
        return jsonify({subject: builder(data)})

    @app.get('/games/<gameno>/players/<int:number>/events')
    @acts_as_number
    def read_events(gameno, number):
        """What the turns did, as this seat was told it.

        A seat reads the feed that was written for it when each turn
        resolved; a session entitled to the whole game reads the whole log.
        Neither is filtered here: what a seat may be told was decided by what
        it could see while the turn was being fought, and there is nothing
        left at this end of the wire to decide it with.
        """
        since = request.args.get('since')
        try:
            since = None if since is None else int(since)
        except ValueError:
            return jsonify({'error': 'since is a turn number'}), 400
        repository = _repository(gameno)
        try:
            if identity.sees_everything(number):
                events = repository.read_turn_events(since=since)
            else:
                events = repository.read_events(number, since=since)
        except GameDataError as error:
            return _game_error_response(error)
        return jsonify({'events': events})

    @app.post('/games/<gameno>/players/<int:number>/commands')
    @acts_as_number
    def perform_command(gameno, number):
        record = request.get_json(silent=True)
        if not isinstance(record, dict):
            return jsonify({'error': 'a command is a JSON object'}), 400
        try:
            command = from_record(record)
        except GameError as error:
            return jsonify({'error': str(error)}), 400
        game = Game(_repository(gameno), int(number))
        try:
            # held for writing across the load + perform, because a client's
            # `perform` is what carries a mutation out and every reader has
            # to see the whole of that mutation or none of it
            with game.repository.held():
                game.load()
                game_ops.perform(game, command)
        except GameIsBusy as error:
            return jsonify({'error': str(error)}), 409
        except GameDataError as error:
            return _game_error_response(error)
        except GameError as error:
            return jsonify({'error': str(error)}), 400
        return '', 204

    @app.post('/games/<gameno>/players/<int:number>/commit')
    @acts_as_number
    def commit_turn(gameno, number):
        try:
            game = Game(_repository(gameno), int(number))
            if identity.is_player(number):
                # publish under one hold; if the barrier is met, resolve
                # under a fresh one - the two are separate for a reason
                # (design.md - Decision 2)
                game.load()
                published = game.clientSave()
                if not published:
                    return jsonify(
                        {'error': 'the board is too small to commit'}), 400
                # a fresh session for the resolve so the load reflects the
                # commit that just landed rather than the state before it -
                # and the administrator's, not the committing player's. A
                # player's session is built from that player's own published
                # view, so resolving from one applies only that player's
                # orders and republishes a board holding only the units that
                # player may see. Every other player is wiped off the record,
                # found to have nothing standing, and eliminated - which
                # handed the game to whoever committed last
                resolver = Game(_repository(gameno), identity.ADMINISTRATOR)
                resolved = resolver.resolveWhenReady()
                # the answer goes back to the player who asked, read as they
                # are entitled to read it
                game.load()
                payload = _commit_payload(game, resolved=bool(resolved))
                return jsonify(payload), (200 if resolved else 202)
            # the administrator: the setup resolution has no barrier
            game.load()
            game.serverSave()
            game.load()
            payload = _commit_payload(game, resolved=True)
            return jsonify(payload), 200
        except GameIsBusy as error:
            return jsonify({'error': str(error)}), 409
        except GameDataError as error:
            return _game_error_response(error)
        except GameError as error:
            return jsonify({'error': str(error)}), 400

    @app.get('/games/<gameno>/players/<int:number>/wait/turn')
    @acts_as_number
    def wait_for_turn(gameno, number):
        # the wait ends when the player's published orders are no longer
        # pending. `has_orders(n)` False means the server consumed them,
        # which is what `wait_for_turn` in `service/turn.py` waits on too
        budget = float(request.args.get('budget', WAIT_BUDGET))
        deadline = time.monotonic() + budget
        while True:
            try:
                repository = _repository(gameno)
                pending = repository.has_orders(int(number))
            except GameDataError as error:
                return _game_error_response(error)
            if not pending:
                # a fresh load so the turn number the client reads reflects
                # the resolution it was waiting on
                try:
                    game = Game(_repository(gameno), int(number))
                    game.load()
                    return jsonify({'resolved': True,
                                    'turn_number': game.getTurnNumber()})
                except GameDataError as error:
                    return _game_error_response(error)
            if time.monotonic() >= deadline:
                return jsonify({'resolved': False})
            time.sleep(POLL_INTERVAL)

    @app.get('/games/<gameno>/players/<int:number>/wait/commit')
    @acts_as_number
    def wait_for_commit(gameno, number):
        # the wait ends when every awaited player has committed for the
        # current turn - the same condition `wait_for_all_commits` in
        # `service/turn.py` waits on
        budget = float(request.args.get('budget', WAIT_BUDGET))
        deadline = time.monotonic() + budget
        while True:
            try:
                game = Game(_repository(gameno), int(number))
                game.load()
                awaited = _awaited_players(game)
                committed = set(game.repository.committed_players(
                    game.getTurnNumber()))
            except GameDataError as error:
                return _game_error_response(error)
            missing = sorted(awaited - committed)
            if not missing:
                return jsonify({'met': True,
                                'committed': sorted(committed)})
            if time.monotonic() >= deadline:
                return jsonify({'met': False, 'waiting_on': missing})
            time.sleep(POLL_INTERVAL)

    sessions_module.register_routes(app)
    seats_module.register_routes(app)
    registry_module.register_routes(app)
    _register_error_handlers(app)

    return app


# the prefixes that belong to the contract rather than to the page. A request
# under one of these that matches no route is a mistake by a client, and gets
# an answer a client can read; anything else is somebody's address bar
API_PREFIXES = ('/_/', '/games', '/accounts', '/sessions', '/tokens', '/static')


def _wants_the_page(asked):
    """Whether an unmatched request should be answered with the interface.

    Somebody who types the host and port, or follows a link to a game, or
    reloads on a screen, should land in the application - which then asks them
    to sign in. Answering that with a bare 404 makes a working server look
    broken, and it is the first thing a new player sees.

    A request under an API prefix is not that: a client asking for an endpoint
    that does not exist wants to be told so in JSON, not handed a page it
    cannot parse. Nor is anything but a GET, and nor is a caller that asked
    for JSON.
    """
    if asked.method != 'GET':
        return False
    if asked.path.startswith(API_PREFIXES):
        return False
    return not asked.accept_mimetypes.accept_json or \
        asked.accept_mimetypes.accept_html


def _register_error_handlers(app):
    """What each kind of refusal becomes on the wire.

    An `AccountError` is answered by `auth.error_response`, which knows the
    difference between not having said who you are and having said and been
    refused. Everything else is as it was.
    """

    @app.errorhandler(404)
    def _not_found(_error):
        if _wants_the_page(request):
            # 200, not a redirect: this *is* the page for that address, and
            # the application routes on it once it has loaded
            return app.send_static_file('index.html')
        return jsonify({'error': 'no such endpoint'}), 404

    @app.errorhandler(AccountError)
    def _account_error(error):
        return auth_module.error_response(error)

    @app.errorhandler(GameIsBusy)
    def _busy(error):
        return jsonify({'error': str(error)}), 409

    @app.errorhandler(GameError)
    def _game_error(error):
        return _game_error_response(error)


def _commit_payload(data, resolved):
    committed = set(
        data.repository.committed_players(data.getTurnNumber()))
    awaited = _awaited_players(data)
    return {
        'resolved': bool(resolved),
        'turn_number': data.getTurnNumber(),
        'outcome': data.getOutcome(),
        'waiting_on': sorted(awaited - committed),
    }


def _state_payload(data):
    return {
        'turn_number': data.getTurnNumber(),
        'outcome': data.getOutcome(),
        'new_game': data.getNewGame(),
        'unprocessed_moves': data.getUnprocessedMoves(),
        'rejected': data.getRejected(),
        # `getDropped` returns tuples of `(command_or_None, message)`; JSON
        # cannot carry a command object, and the client's REPL already knows
        # them as messages, so the wire is the human-readable strings
        'dropped': [
            {'message': message,
             'command': _command_repr(command)}
            for command, message in data.getDropped()],
    }


def _command_repr(command):
    """A drafted command for the wire.

    `service/commands.py` records typed dataclasses, so the wire form is
    what `as_record` gives - the same shape a draft file holds.
    """
    if command is None:
        return None
    return _AS_RECORD(command)


def _game_error_response(error):
    if isinstance(error, NoSuchGame):
        return jsonify({'error': str(error)}), 404
    if isinstance(error, NoSuchPlayer):
        return jsonify({'error': str(error)}), 404
    if isinstance(error, UnreadableGame):
        return jsonify({'error': str(error)}), 422
    if isinstance(error, GameIsBusy):
        return jsonify({'error': str(error)}), 409
    return jsonify({'error': str(error)}), 400
