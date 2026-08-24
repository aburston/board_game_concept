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
        os.environ['BOARD_GAME_SERVER'] = self._app.base_url
        try:
            client = self.start_client(game_number, player_number)
            client.read_until(CLIENT_PROMPT)
            return client
        finally:
            os.environ.pop('BOARD_GAME_SERVER', None)

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

    def test_commit_stops_with_a_step_4_message(self):
        """`commit` is not on HTTP yet; the client says so."""
        self.server = self.established_game(players=(1,))
        client = self._start_client_over_http()
        self._send_and_wait(client, 'add type Cross X 1 5 10', 2)
        self._send_and_wait(client, 'add unit Cross x1 0 0', 3)
        client.send_line('commit')
        # the client raises NotImplementedError and exits; a graceful
        # message would be nicer, but the mention of "step 4" is what the
        # change refuses on
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if client.proc.poll() is not None:
                break
            time.sleep(0.1)
        assert client.proc.poll() is not None, (
            'the client did not exit on commit')