"""The Flask app that serves the read side.

Reads only. `POST` and long-poll are later steps. Each read is one request;
each request opens a `Game` for its player, calls `load()`, and returns the
JSON view - no app-level cache to disagree with the game.

The route paths carry the player number because that is what `Game(
repository, number)` takes today. When authentication lands, the identity
moves to a token and the path stops carrying it.
"""

import os

from flask import Flask, jsonify, request

from ..cli import session as session_module
from ..service import games as game_ops
from ..service import identity
from ..service.commands import as_record as _AS_RECORD, from_record
from ..service.errors import (GameDataError, GameError, NoSuchGame,
                              NoSuchPlayer, UnreadableGame)
from ..service.turn import _awaited_players
from ..storage.lock import GameIsBusy
from .. import Game
from . import views as views_module


VIEW_BUILDERS = {
    'board': lambda data: views_module.board_view(data.getBoard()),
    'units': lambda data: views_module.units_view(data.getBoard()),
    'types': lambda data: views_module.types_view(data.getPlayers()),
    'players': lambda data: views_module.players_view(
        data.getPlayers(), data.getEliminated()),
    'pending': lambda data: views_module.pending_view(
        data.getPlayers(), data.getBoard()),
}

VIEWS_THAT_NEED_A_BOARD = ('board', 'units', 'pending')


def create_app(base_path=None, backend=None):
    """A Flask app configured for a games directory.

    `base_path` is what `YamlGameRepository`/`SqliteGameRepository` take:
    the directory the `games/` tree lives under. Defaults to the process
    working directory, matching the CLI binaries. `backend` overrides the
    default backend chosen by `session_module.default_backend()`.
    """
    app = Flask(__name__)
    app.config['BASE_PATH'] = base_path or os.getcwd()
    app.config['BACKEND'] = backend

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

    @app.get('/games/<gameno>/players')
    def list_players(gameno):
        return jsonify({'players': _repository(gameno).player_numbers()})

    @app.get('/games/<gameno>/players/<int:number>/state')
    def read_state(gameno, number):
        try:
            data = _load_game(gameno, number)
        except GameDataError as error:
            return _game_error_response(error)
        return jsonify(_state_payload(data))

    @app.get('/games/<gameno>/players/<int:number>/views/<subject>')
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

    @app.post('/games/<gameno>/players/<int:number>/commands')
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
                # commit that just landed rather than the state before it
                resolver = Game(_repository(gameno), int(number))
                resolved = resolver.resolveWhenReady()
                data = resolver if resolved else game
                data.load()
                payload = _commit_payload(data, resolved=bool(resolved))
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

    @app.errorhandler(GameIsBusy)
    def _busy(error):
        return jsonify({'error': str(error)}), 409

    @app.errorhandler(GameError)
    def _game_error(error):
        return _game_error_response(error)

    return app


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
