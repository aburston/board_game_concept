"""The client, end to end, against a live Flask thread.

Same shape as `test_observer_over_http.py`: the app runs in a background
thread and the client runs as a subprocess against `--server URL`. Covers
`add type`, `add unit`, `show units`, `remove unit`, `order`, `reload`.

`commit` still stops - it lands in step 4.
"""

import os
import socket
import threading
import time

import pytest
import requests

from cli_harness import CliTestCase, CLIENT_PROMPT, TEST_DIR

pytestmark = pytest.mark.backend('sqlite')


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


class ClientOverHttp(CliTestCase):
    """The client surface, over HTTP rather than over the file system."""

    def setUp(self):
        super().setUp()
        self._app = _AppThread(TEST_DIR)
        self._app.start()

    def _start_client_over_http(self, game_number='test-01', player_number=1):
        from conftest import make_token_for
        os.environ['BOARD_GAME_SERVER'] = self._app.base_url
        # the role proves itself as exactly the seat it was started for
        os.environ['BOARD_GAME_TOKEN'] = make_token_for(
            self._app.app, game_number, player_number)
        try:
            client = self.start_client(game_number, player_number)
            client.read_until(CLIENT_PROMPT)
            return client
        finally:
            os.environ.pop('BOARD_GAME_SERVER', None)
            os.environ.pop('BOARD_GAME_TOKEN', None)

    def _send_and_wait(self, client, line, expected_prompts):
        client.send_line(line)
        client.read_until_count(CLIENT_PROMPT, expected_prompts)

    def test_add_type_and_add_unit_go_over_http(self):
        self.server = self.established_game(players=(1,))
        client = self._start_client_over_http()
        self._send_and_wait(client, 'add type Cross X 1 5 10', 2)
        assert 'error' not in client.output.lower(), client.output
        self._send_and_wait(client, 'add unit Cross x1 0 0', 3)
        assert 'error' not in client.output.lower(), client.output
        # show units reads back through the view: the unit is there
        self._send_and_wait(client, 'show units', 4)
        assert 'x1' in client.output

    def test_a_refused_command_reports_a_reason(self):
        """A command the rules refuse comes back as the message locally."""
        self.server = self.established_game(players=(1,))
        client = self._start_client_over_http()
        self._send_and_wait(client, 'add type Cross X 1 5 10', 2)
        self._send_and_wait(client, 'add unit Cross x1 0 0', 3)
        # trying to deploy another unit at the same square is refused
        self._send_and_wait(client, 'add unit Cross x2 0 0', 4)
        assert 'exists' in client.output.lower() or \
               'refused' in client.output.lower() or \
               'occupied' in client.output.lower(), client.output

    def test_commit_closes_the_barrier_and_resolves_the_turn(self):
        """A one-player commit resolves the setup turn inline (option b)."""
        self.server = self.established_game(players=(1,))
        client = self._start_client_over_http()
        self._send_and_wait(client, 'add type Cross X 1 5 10', 2)
        self._send_and_wait(client, 'add unit Cross x1 0 0', 3)
        # commit closes the barrier for the one player - the server
        # resolves the setup turn during the request (option b) and the
        # client prints `commit complete` and returns to the prompt
        client.send_line('commit')
        client.read_until('commit complete')
        client.read_until_count(CLIENT_PROMPT, 4)
        # a subsequent `show units` reads back the deployed unit as it
        # stands after the turn resolved
        self._send_and_wait(client, 'show units', 5)
        assert 'x1' in client.output

    def test_two_players_commit_in_turn_and_neither_wins(self):
        """Two clients, the game a person plays with a friend.

        Player 1 commits and waits; player 2's commit closes the barrier and
        resolves the setup turn during the request. Nobody has given an order,
        so the game is still there to be played - which is what the turn
        resolved from the committing player's own half-sighted view was not:
        it wiped player 1 off the board and handed player 2 the game on turn 1.
        """
        self.server = self.established_game(players=(1, 2))
        one = self._start_client_over_http(player_number=1)
        two = self._start_client_over_http(player_number=2)

        self._send_and_wait(one, 'add type Cross X 1 5 10', 2)
        self._send_and_wait(one, 'add unit Cross x1 0 0', 3)
        self._send_and_wait(two, 'add type Ring O 1 5 10', 2)
        self._send_and_wait(two, 'add unit Ring o1 3 3', 3)

        # player 1 commits first and is left waiting on the barrier
        one.send_line('commit')
        one.read_until('waiting for turn to complete...')

        # player 2's commit closes it, and the turn resolves in the request
        two.send_line('commit')
        two.read_until('commit complete')
        two.read_until_count(CLIENT_PROMPT, 4, timeout=60)

        # the resolution releases player 1, who is prompted again
        one.read_until_count(CLIENT_PROMPT, 4, timeout=60)

        for client in (one, two):
            assert 'game over' not in client.output, client.output
            assert 'out of the game' not in client.output, client.output

        # and both units are standing where they were deployed
        self._send_and_wait(one, 'show units', 5)
        assert 'x1' in one.output
        self._send_and_wait(two, 'show units', 5)
        assert 'o1' in two.output


    def test_the_served_game_is_guarded(self):
        """The roles above carry a token; this proves they had to."""
        response = requests.get(
            f'{self._app.base_url}/games/test-01/players/1/state', timeout=5)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(set(response.json()), {'error'})
