"""A command-line role proving itself to a server.

Three things: a role with a token for the seat it was started for plays; a
role with no token is refused before it opens a session; a role with a token
for some other seat reports the server's refusal rather than a prompt.

The local flow is not here, because it has none of this to do - which is the
point, and `test_cli_*_surface.py` is what holds it to that.
"""

import os
import socket
import threading
import time

import pytest
import requests

from board_game_concept import Game
from board_game_concept.cli import session as session_module
from board_game_concept.cli.backend import HttpSession, LocalSession
from board_game_concept.service import games as game_ops
from board_game_concept.service.commands import AddPlayer, SetBoard
from board_game_concept.service.errors import GameError
from board_game_concept.storage.sqlite_repository import SqliteGameRepository

pytestmark = pytest.mark.backend('sqlite')

GAME = 'one'


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class _AppThread:
    """A Flask app served on a random port in a daemon thread."""

    def __init__(self, base_path, backend='sqlite'):
        from board_game_concept.http.app import create_app
        self.port = _free_port()
        self.base_url = f'http://127.0.0.1:{self.port}'
        self._app = create_app(base_path=str(base_path), backend=backend)
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


@pytest.fixture(name='served')
def _served(tmp_path, monkeypatch):
    for name in (session_module.SERVER_ENV, session_module.TOKEN_ENV,
                 session_module.LOCAL_API_ENV,
                 session_module.NO_REDIRECT_ENV):
        monkeypatch.delenv(name, raising=False)

    admin = Game(SqliteGameRepository(GAME, base_path=str(tmp_path)), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    game_ops.perform(admin, AddPlayer(number=1))
    game_ops.perform(admin, AddPlayer(number=2))
    admin.serverSave()

    app = _AppThread(tmp_path)
    app.start()
    return app


def test_a_role_with_a_token_for_its_seat_opens_a_session(served):
    from conftest import make_token_for

    session = session_module.make_session(
        GAME, 1, server=served.base_url,
        token=make_token_for(served.app, GAME, 1))

    assert isinstance(session, HttpSession)
    session.load()
    assert session.getBoard() is not None


def test_every_request_a_role_makes_carries_the_token(served):
    from conftest import make_token_for

    token = make_token_for(served.app, GAME, 1)
    session = session_module.make_session(GAME, 1, server=served.base_url,
                                          token=token)

    assert session._session.headers['Authorization'] == f'Bearer {token}'


def test_a_role_with_no_token_is_refused_before_a_session_is_opened(served):
    with pytest.raises(GameError) as refusal:
        session_module.make_session(GAME, 1, server=served.base_url)

    assert 'token' in str(refusal.value)
    assert session_module.TOKEN_ENV in str(refusal.value)


def test_the_token_may_come_from_the_environment(served, monkeypatch):
    from conftest import make_token_for

    monkeypatch.setenv(session_module.TOKEN_ENV,
                       make_token_for(served.app, GAME, 1))

    session = session_module.make_session(GAME, 1, server=served.base_url)

    assert isinstance(session, HttpSession)
    session.load()


def test_a_named_token_beats_the_environment(served, monkeypatch):
    from conftest import make_token_for

    monkeypatch.setenv(session_module.TOKEN_ENV, 'from-the-environment')
    named = make_token_for(served.app, GAME, 1)

    session = session_module.make_session(GAME, 1, server=served.base_url,
                                          token=named)

    assert session._session.headers['Authorization'] == f'Bearer {named}'


def test_a_token_for_another_seat_is_refused_by_the_server(served):
    from conftest import make_token_for

    # a token for seat 1, used to open seat 2
    session = session_module.make_session(
        GAME, 2, server=served.base_url,
        token=make_token_for(served.app, GAME, 1))

    with pytest.raises(GameError) as refusal:
        session.load()

    assert 'may not act as' in str(refusal.value)


def test_a_made_up_token_is_refused_by_the_server(served):
    session = session_module.make_session(GAME, 1, server=served.base_url,
                                          token='never-issued')

    with pytest.raises(GameError):
        session.load()


def test_the_local_flow_needs_no_token(tmp_path, monkeypatch):
    """No server, so nothing to prove anything to."""
    for name in (session_module.SERVER_ENV, session_module.TOKEN_ENV,
                 session_module.LOCAL_API_ENV):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(session_module.NO_REDIRECT_ENV, '1')

    admin = Game(SqliteGameRepository(GAME, base_path=str(tmp_path)), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    game_ops.perform(admin, AddPlayer(number=1))
    admin.serverSave()

    session = session_module.make_session(GAME, 1, backend='sqlite',
                                          base_path=str(tmp_path))

    assert isinstance(session, LocalSession)
    session.load()
    assert session.getBoard() is not None


def test_no_account_store_is_made_for_a_local_game(tmp_path, monkeypatch):
    for name in (session_module.SERVER_ENV, session_module.TOKEN_ENV,
                 session_module.LOCAL_API_ENV):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(session_module.NO_REDIRECT_ENV, '1')

    admin = Game(SqliteGameRepository(GAME, base_path=str(tmp_path)), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    game_ops.perform(admin, AddPlayer(number=1))
    admin.serverSave()

    session_module.make_session(GAME, 1, backend='sqlite',
                                base_path=str(tmp_path)).load()

    assert not os.path.exists(os.path.join(str(tmp_path),
                                           'accounts.sqlite3'))
