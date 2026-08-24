"""The Flask app that serves the read side.

Reads only. `POST` and long-poll are later steps. Each read is one request;
each request opens a `Game` for its player, calls `load()`, and returns the
JSON view - no app-level cache to disagree with the game.

The route paths carry the player number because that is what `Game(
repository, number)` takes today. When authentication lands, the identity
moves to a token and the path stops carrying it.
"""

import os

from flask import Flask, jsonify

from ..cli import session as session_module
from ..service.commands import as_record as _AS_RECORD
from ..service.errors import (GameDataError, GameError, NoSuchGame,
                              NoSuchPlayer, UnreadableGame)
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

    @app.errorhandler(GameIsBusy)
    def _busy(error):
        return jsonify({'error': str(error)}), 409

    @app.errorhandler(GameError)
    def _game_error(error):
        return _game_error_response(error)

    return app


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
