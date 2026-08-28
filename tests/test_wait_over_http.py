"""HttpSession's wait methods, end to end against a live Flask thread.

The wait endpoints hold a request for up to a server-side budget; the
client loops until the response says the condition is met. These tests
verify the loop resolves promptly once the condition holds and does not
loop when it already does.
"""

import socket
import threading
import time

import pytest
import requests

from board_game_concept import Game
from board_game_concept.cli.backend import HttpSession
from board_game_concept.service import games as game_ops
from board_game_concept.service.commands import (AddPlayer, AddType, AddUnit,
                                                 SetBoard)
from board_game_concept.storage.sqlite_repository import SqliteGameRepository

pytestmark = pytest.mark.backend('sqlite')


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class _AppThread:
    def __init__(self, base_path):
        from board_game_concept.http.app import create_app
        self.port = _free_port()
        self.base_url = f'http://127.0.0.1:{self.port}'
        self._app = create_app(base_path=str(base_path),
                               backend='sqlite')
        # the suites mint a token from this to prove who a role is
        self.app = self._app
        self._thread = threading.Thread(
            target=self._app.run,
            kwargs={'host': '127.0.0.1', 'port': self.port,
                    'threaded': True, 'use_reloader': False},
            daemon=True)

    def start(self):
        self._thread.start()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                if requests.get(f'{self.base_url}/_/health',
                                timeout=0.5).status_code == 200:
                    return
            except requests.RequestException:
                time.sleep(0.1)
        raise RuntimeError('Flask app never responded to /_/health')


def _game_with_resolved_turn(base_path):
    """A one-player game past its setup turn - player 1 has no pending
    orders, so `waitForTurn` should return at once."""
    admin = Game(SqliteGameRepository('one', base_path=str(base_path)), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    game_ops.perform(admin, AddPlayer(number=1))
    admin.serverSave()

    player = Game(SqliteGameRepository('one', base_path=str(base_path)), 1)
    player.load()
    game_ops.perform(player, AddType(name='Cross', symbol='X',
                                     attack=1, health=5, energy=10))
    game_ops.perform(player, AddUnit(type_name='Cross', name='x1',
                                     x=0, y=0))
    player.clientSave()

    server = Game(SqliteGameRepository('one', base_path=str(base_path)), 0)
    server.load()
    server.serverSave()


def test_wait_for_turn_returns_at_once_when_the_turn_is_resolved(tmp_path):
    _game_with_resolved_turn(tmp_path)
    app = _AppThread(tmp_path)
    app.start()

    from conftest import make_token_for
    session = HttpSession(app.base_url, 'one', 1,
                          token=make_token_for(app.app, 'one', 1))
    started = time.monotonic()
    session.waitForTurn()
    elapsed = time.monotonic() - started
    # a proper wait loop would linger; a returning-at-once wait is under
    # one poll interval
    assert elapsed < 2.0, f"waitForTurn took {elapsed:.1f}s"


def test_wait_for_turn_returns_when_the_turn_is_resolved_during_the_wait(
        tmp_path):
    """Player 1 has pending orders; another thread resolves the turn a
    beat later; the wait loop returns promptly once the turn resolves."""
    admin = Game(SqliteGameRepository('two', base_path=str(tmp_path)), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    game_ops.perform(admin, AddPlayer(number=1))
    admin.serverSave()

    player = Game(SqliteGameRepository('two', base_path=str(tmp_path)), 1)
    player.load()
    game_ops.perform(player, AddType(name='Cross', symbol='X',
                                     attack=1, health=5, energy=10))
    game_ops.perform(player, AddUnit(type_name='Cross', name='x1',
                                     x=0, y=0))
    player.clientSave()
    # player 1 has published; the barrier is met (one player), so any
    # resolve_when_ready wins. Fire it in a background thread half a
    # second in the future, and watch the wait loop return promptly
    app = _AppThread(tmp_path)
    app.start()

    def resolve_soon():
        time.sleep(0.5)
        resolver = Game(SqliteGameRepository('two',
                                             base_path=str(tmp_path)), 0)
        resolver.resolveWhenReady()

    threading.Thread(target=resolve_soon, daemon=True).start()

    from conftest import make_token_for
    session = HttpSession(app.base_url, 'two', 1,
                          token=make_token_for(app.app, 'two', 1))
    started = time.monotonic()
    session.waitForTurn()
    elapsed = time.monotonic() - started
    # the wait should return within a poll interval or two of the resolve
    assert elapsed < 3.0, f"waitForTurn took {elapsed:.1f}s"


def test_the_wait_endpoints_are_guarded(tmp_path):
    """The waits above carry a token; this proves they had to."""
    app = _AppThread(tmp_path)
    app.start()

    for path in (f'{app.base_url}/games/one/players/1/wait/turn',
                 f'{app.base_url}/games/one/players/1/wait/commit'):
        response = requests.get(path, timeout=5)
        assert response.status_code == 401
        assert set(response.json()) == {'error'}
