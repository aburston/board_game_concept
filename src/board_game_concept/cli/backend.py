"""The seam between a role's REPL and the game it drives.

Every role holds a session and talks to it, rather than holding a `Game` and
reaching into it. That is the whole of this seam's job: to be the one thing a
role depends on, so that a later change can put an HTTP client behind the same
interface without the REPLs knowing. The REST API the game is headed for cannot
slot in where a `Game` is soldered into a role; it can slot in here.

`Session` names the surface. `LocalSession` is the one implementation there is
today: the in-process `Game`, `service.games` and turn functions the roles call
now, behind the interface instead of in front of it.

The read methods keep their `Game` names on purpose. `show.py`, `complete.py`
and `cli/session.py` already call `getBoard`, `getPlayers`, `getOutcome` and the
rest, and are held to those names by their own tests, so the session presents
the same surface and those callers do not change. The view-object reads -
`getBoard`, `getPlayers`, `getEliminated` - are the part an HTTP session cannot
answer, because a client holds no board. They are local-only, and turning them
into fetched view data is the work of the change that moves `views.py`
server-side. Until then the seam is drawn for actions, lifecycle and state, and
these three are the coupling still to cut.
"""

import requests

from .. import Game
from ..http import views as views_module
from ..service import games, identity
from ..service.commands import SetNewGame, as_record
from ..service.errors import (GameError, NoSuchGame, NoSuchPlayer,
                              UnreadableGame)
from ..storage.lock import GameIsBusy


class Session:
    """What a role's REPL asks of the game it drives.

    Subclasses implement all of it. This class says what the set is and fails
    loudly rather than silently when one is missing, the way `GameRepository`
    does for storage.
    """

    # --- lifecycle and actions, through the seam

    def load(self):
        """Read the game, or re-read it. Raises the game-data errors the
        session loop turns into an exit."""
        raise NotImplementedError

    def perform(self, command):
        """Carry out a command, recording it; raises `GameError` if refused."""
        raise NotImplementedError

    def commit(self):
        """Commit as this role commits: a player publishes, the administrator
        ends setup."""
        raise NotImplementedError

    def resolve_pending(self):
        """Resolve the turn if the barrier is met; the server's unattended
        act. `None` when it is not met, else `resolve`'s own result."""
        raise NotImplementedError

    def waitForTurn(self):
        """Wait until this player's committed orders have been resolved."""
        raise NotImplementedError

    def waitForPlayerCommit(self):
        """Wait until every player still in the game has committed."""
        raise NotImplementedError

    # --- reading the game's state

    def getOutcome(self):
        raise NotImplementedError

    def getTurnNumber(self):
        raise NotImplementedError

    def getNewGame(self):
        raise NotImplementedError

    def setNewGame(self, new_game):
        raise NotImplementedError

    def getUnprocessedMoves(self):
        raise NotImplementedError

    def getRejected(self):
        raise NotImplementedError

    def getDropped(self):
        raise NotImplementedError

    def isEliminated(self, player_number):
        raise NotImplementedError

    # --- view objects the reading half still needs (local-only; see the
    # module docstring). `show.py` and `complete.py` build views from these.

    def getBoard(self):
        raise NotImplementedError

    def getPlayers(self):
        raise NotImplementedError

    def getEliminated(self):
        raise NotImplementedError

    def getView(self, subject):
        """One `show` subject as its view value.

        `LocalSession` computes it from its live objects; `HttpSession`
        fetches it from `/views/<subject>`. Every caller of `show.py` goes
        through here rather than calling `views.<subject>_view` itself, so
        the two backends serve the same JSON.
        """
        raise NotImplementedError


class LocalSession(Session):
    """The in-process implementation: a `Game`, driven as the roles drive it."""

    def __init__(self, repository, player_number):
        self.player_number = player_number
        self._game = Game(repository, player_number)

    def load(self):
        return self._game.load()

    def perform(self, command):
        return games.perform(self._game, command)

    def commit(self):
        # a player's commit publishes orders and waits to be woken; the
        # administrator's ends setup. Which one is decided by identity, the
        # same fact `sees_everything` and the barrier are decided by
        if identity.is_player(self.player_number):
            return self._game.clientSave()
        return self._game.serverSave()

    def resolve_pending(self):
        return self._game.resolveWhenReady()

    def waitForTurn(self):
        return self._game.waitForTurn()

    def waitForPlayerCommit(self):
        return self._game.waitForPlayerCommit()

    def getOutcome(self):
        return self._game.getOutcome()

    def getTurnNumber(self):
        return self._game.getTurnNumber()

    def getNewGame(self):
        return self._game.getNewGame()

    def setNewGame(self, new_game):
        return self._game.setNewGame(new_game)

    def getUnprocessedMoves(self):
        return self._game.getUnprocessedMoves()

    def getRejected(self):
        return self._game.getRejected()

    def getDropped(self):
        return self._game.getDropped()

    def isEliminated(self, player_number):
        return self._game.isEliminated(player_number)

    def getBoard(self):
        return self._game.getBoard()

    def getPlayers(self):
        return self._game.getPlayers()

    def getEliminated(self):
        return self._game.getEliminated()

    def getView(self, subject):
        if subject == 'board':
            return views_module.board_view(self._game.getBoard())
        if subject == 'units':
            return views_module.units_view(self._game.getBoard())
        if subject == 'types':
            return views_module.types_view(self._game.getPlayers())
        if subject == 'players':
            return views_module.players_view(self._game.getPlayers(),
                                             self._game.getEliminated(),
                                             self._game.getBoard())
        if subject == 'pending':
            return views_module.pending_view(self._game.getPlayers(),
                                             self._game.getBoard())
        if subject == 'events':
            # a session entitled to the whole game reads the whole log; a
            # seat reads what was written for it when each turn resolved
            repository = self._game.repository
            if self._game.seesEverything():
                return repository.read_turn_events()
            return repository.read_events(self._game.player_number)
        if subject == 'designs':
            if self._game.seesEverything():
                return views_module.types_seen_view(
                    views_module.types_view(self._game.getPlayers()),
                    met=False)
            return views_module.types_seen_view(
                self._game.repository.read_known_types(
                    self._game.player_number))
        raise ValueError(f"unknown view: {subject}")


class HttpSession(Session):
    """The seam's HTTP implementation, read-only for now.

    Reads a state snapshot and a view whenever the REPL asks. Writes and
    waits raise; step 3 fills them in.
    """

    def __init__(self, base_url, gameno, player_number, token=None):
        self._session = requests.Session()
        if token:
            # one header, set once, on the session every request already
            # goes through - rather than a change at each of the dozen
            # call sites that make one
            self._session.headers['Authorization'] = f'Bearer {token}'
        self.base_url = base_url.rstrip('/')
        self.gameno = gameno
        self.player_number = player_number
        self._state = None
        self._board = None
        self._players = None

    def load(self):
        # a fresh screen: throw the cached snapshot away and refetch
        self._state = None
        self._board = None
        self._players = None
        self._state = self._get(f'/players/{self.player_number}/state')

    def perform(self, command):
        # `load` reads a file on the caller's disk and hands its contents
        # over; opening that file server-side would let a client name a
        # path the server owns. Doing it right - opening on the client
        # and sequencing the effective commands - is its own change
        if command.kind in ('load_board', 'load_player'):
            raise GameError(
                f"{command.kind}: not yet supported over HTTP")
        response = self._session.post(
            f'{self.base_url}/games/{self.gameno}/players/'
            f'{self.player_number}/commands',
            json=as_record(command))
        _raise_for(response)
        self._invalidate()

    def _invalidate(self):
        # ordinary cache invalidation: the next reader fetches fresh
        self._state = None
        self._board = None
        self._players = None

    def commit(self):
        response = self._session.post(
            f'{self.base_url}/games/{self.gameno}/players/'
            f'{self.player_number}/commit')
        if response.status_code == 400:
            # a publish-side refusal: matches `LocalSession.commit` returning
            # False when `publish` refused (the board is too small)
            self._invalidate()
            return False
        _raise_for(response)
        self._invalidate()
        return True

    def resolve_pending(self):
        response = self._session.post(
            f'{self.base_url}/games/{self.gameno}/players/'
            f'{self.player_number}/commit')
        if response.status_code == 202:
            # the barrier was not met: matches `resolveWhenReady` returning
            # None when another caller had not yet committed
            self._invalidate()
            return None
        _raise_for(response)
        self._invalidate()
        return True

    def waitForTurn(self):
        # long-poll: the server holds the request for up to its wait
        # budget, either the turn resolves and it returns 'resolved:
        # true', or the budget runs out and it returns 'resolved: false'
        # and this loops. `notify.py`'s cadence is one-liner behind it
        while True:
            response = self._session.get(
                f'{self.base_url}/games/{self.gameno}/players/'
                f'{self.player_number}/wait/turn',
                timeout=self._wait_timeout())
            _raise_for(response)
            if response.json().get('resolved'):
                # fresh state so a subsequent `getOutcome` sees what the
                # server just wrote
                self._invalidate()
                return

    def waitForPlayerCommit(self):
        # the administrator's counterpart: waits until the barrier closes.
        # Only the admin calls this; a player's REPL calls `waitForTurn`
        while True:
            response = self._session.get(
                f'{self.base_url}/games/{self.gameno}/players/'
                f'{self.player_number}/wait/commit',
                timeout=self._wait_timeout())
            _raise_for(response)
            if response.json().get('met'):
                self._invalidate()
                return

    def _wait_timeout(self):
        # a socket-timeout longer than the server's wait budget: whatever
        # the server chose, the client's request outlasts it. The server
        # sets its own budget as `WAIT_BUDGET` in `http/app.py`; the
        # client does not need to know it and always uses a generous cap
        return 60.0

    def getOutcome(self):
        return self._require_state()['outcome']

    def getTurnNumber(self):
        return self._require_state()['turn_number']

    def getNewGame(self):
        return self._require_state()['new_game']

    def setNewGame(self, new_game):
        # `SetNewGame` is a command like any other on the HTTP tier so the
        # wire has one shape - `service/commands.py::SetNewGame` is the
        # node the server carries out
        self.perform(SetNewGame(new_game=bool(new_game)))

    def getUnprocessedMoves(self):
        return self._require_state()['unprocessed_moves']

    def getRejected(self):
        return self._require_state()['rejected']

    def getDropped(self):
        # the on-disk `getDropped` returns `(command, message)` tuples; the
        # wire form is `{command, message}` records, and the REPL only ever
        # reads the message
        return [(record.get('command'), record['message'])
                for record in self._require_state()['dropped']]

    def isEliminated(self, player_number):
        # the state snapshot does not carry every player's eliminated flag,
        # only this session's. The value the REPL asks for is derived from
        # the `players` view instead
        players = self.getPlayers()
        return player_number in self._eliminated_from(players)

    def getBoard(self):
        if self._board is None:
            self._board = _HttpBoard(
                self._get(f'/players/{self.player_number}/views/board')
                .get('board', {}))
        return self._board

    def getPlayers(self):
        if self._players is None:
            types_by_player = {}
            for entry in self._get(
                    f'/players/{self.player_number}/views/types'
                    ).get('types', []):
                types_by_player.setdefault(entry['player'], {})[
                    entry['name']] = {
                        'name': entry['name'], 'symbol': entry['symbol'],
                        'attack': entry['attack'],
                        'health': entry['health'],
                        'energy': entry['energy']}
            listed = self._get_list('/players').get('players', [])
            self._players = {
                number: {'number': number, 'types': types_by_player.get(
                    number, {})}
                for number in listed}
        return self._players

    def getEliminated(self):
        players = self._get(
            f'/players/{self.player_number}/views/players'
            ).get('players', [])
        return [entry['player'] for entry in players
                if entry.get('status') == 'eliminated']

    def getView(self, subject):
        response = self._get(
            f'/players/{self.player_number}/views/{subject}')
        # each endpoint returns `{<subject>: value}`; hand back the value
        return response.get(subject)

    # --- private

    def _require_state(self):
        if self._state is None:
            self._state = self._get(f'/players/{self.player_number}/state')
        return self._state

    def _get(self, path):
        return self._request(f'/games/{self.gameno}{path}')

    def _get_list(self, path):
        # for `/games/<n>/players`, which has no player number in the path
        return self._request(f'/games/{self.gameno}{path}')

    def _request(self, path):
        response = self._session.get(self.base_url + path)
        _raise_for(response)
        return response.json()

    @staticmethod
    def _eliminated_from(players):
        return {number for number, info in players.items()
                if info.get('status') == 'eliminated'}


class _HttpBoard:
    """The little of a `Board` the REPL still asks for.

    `show.py` and `complete.py` reach for `board.size_x` and `board.size_y`
    when they check whether a game has been sized yet. Everything else the
    board is used for goes through a view the server already computed, so
    this holds the two attributes and nothing more.
    """

    def __init__(self, view):
        self._view = view or {}

    @property
    def size_x(self):
        return self._view.get('size_x')

    @property
    def size_y(self):
        return self._view.get('size_y')


def _raise_for(response):
    if response.status_code // 100 == 2:
        return
    try:
        body = response.json()
        message = body.get('error', response.text)
    except ValueError:
        message = response.text
    if response.status_code in (404,):
        # the wire does not distinguish "no game" from "no player" strongly
        # enough to hand the caller different exceptions; the message names
        # which
        if 'player' in message.lower():
            raise NoSuchPlayer(message)
        raise NoSuchGame(message)
    if response.status_code == 409:
        raise GameIsBusy(message)
    if response.status_code == 422:
        raise UnreadableGame(message)
    raise GameError(message)
