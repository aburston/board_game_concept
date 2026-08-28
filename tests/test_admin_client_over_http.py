"""`bgcclient` driven by the administrator, for a seat it holds.

The served contract is held to the equivalence in `tests/test_admin_plays.py`.
This holds the other client to it: that nothing between a prompt and a request
narrows or widens a role by the account behind its token.

The role a command line takes is fixed by which executable was run, and the
server decides the rest - so `bgcclient` carrying the administrator's token is
a client, with a client's commands, and not a server.

Modelled on `test_observer_over_http.py`, which is where a role driven over
HTTP lives; the local-file surface suites carry no server.
"""

import os
import socket
import threading
import time

import pytest
import requests

from cli_harness import CliTestCase, CLIENT_PROMPT, TEST_DIR

pytestmark = pytest.mark.backend('sqlite')

GAME = 'test-01'


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
        self.app = create_app(base_path=str(base_path), backend=backend)
        self._thread = threading.Thread(
            target=self.app.run,
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


class AdminClientOverHttp(CliTestCase):
    """The client surface, run by the administrator for a seat it holds."""

    def setUp(self):
        super().setUp()
        self._app = _AppThread(TEST_DIR)
        self._app.start()

    def _client_as(self, number, holder, game_number=GAME):
        """A `bgcclient` for this seat, proving itself as `holder`."""
        from conftest import make_token_for

        os.environ['BOARD_GAME_SERVER'] = self._app.base_url
        os.environ['BOARD_GAME_TOKEN'] = make_token_for(
            self._app.app, game_number, number, holder=holder)
        try:
            return self.start_client(game_number, number)
        finally:
            os.environ.pop('BOARD_GAME_SERVER', None)
            os.environ.pop('BOARD_GAME_TOKEN', None)

    def _admin_client(self, number=1, game_number=GAME):
        client = self._client_as(number, 'admin', game_number)
        client.read_until(CLIENT_PROMPT)
        return client

    # --- 4.2 the session opens and prints what a client prints

    def test_the_administrator_opens_a_session_for_its_seat(self):
        self.server = self.established_game(GAME, players=(1, 2))
        client = self._admin_client()

        assert client.errors == '', f'client errors: {client.errors!r}'
        shown = self.shown(client, CLIENT_PROMPT, 'show board')
        assert '+' in shown or '#' in shown
        assert 'size_x' not in shown, 'the raw JSON leaked through'

        players = self.shown(client, CLIENT_PROMPT, 'show players')
        assert 'PLAYER' in players

        client.send_line('exit')
        assert client.wait_for_exit() == 0

    # --- 4.3 the role is the client's, not the server's

    def test_the_token_does_not_widen_the_role(self):
        """`add player` is the server's command, and stays the server's."""
        self.server = self.established_game(GAME, players=(1, 2))
        client = self._admin_client()

        refused = self.shown(client, CLIENT_PROMPT, 'add player 3')
        assert 'invalid command' in refused.lower(), refused

        listed = self.shown(client, CLIENT_PROMPT, 'help')
        assert 'add unit' in listed
        assert 'add player' not in listed
        assert 'set board' not in listed

    # --- 4.4 a seat it does not hold is still refused

    def test_a_seat_the_administrator_does_not_hold_is_refused(self):
        """The token is the administrator's; seat 2 is somebody else's."""
        self.server = self.established_game(GAME, players=(1, 2))
        # arrange seat 2 as a registered player's, then run for it with a
        # token minted for the administrator
        from conftest import make_token_for, make_admin, token_for

        make_token_for(self._app.app, GAME, 2)          # ada now holds seat 2
        os.environ['BOARD_GAME_SERVER'] = self._app.base_url
        os.environ['BOARD_GAME_TOKEN'] = token_for(
            self._app.app, make_admin(self._app.app))
        try:
            client = self.start_client(GAME, 2)
        finally:
            os.environ.pop('BOARD_GAME_SERVER', None)
            os.environ.pop('BOARD_GAME_TOKEN', None)

        assert client.wait_for_exit() != 0
        printed = client.output + client.errors
        assert 'may not act as' in printed, printed
