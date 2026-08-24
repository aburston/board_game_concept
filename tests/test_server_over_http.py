"""`bgcserver` in HTTP mode: the interactive admin session against a REST server.

Runs the admin's setup end to end, then verifies the server exits (rather
than looping as an unattended resolver). Local mode keeps the resolver
loop and is covered by `test_cli_server_surface.py`.
"""

import os
import socket
import threading
import time

import pytest
import requests

from cli_harness import CliTestCase, SERVER_PROMPT, TEST_DIR

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
        self._app = create_app(base_path=str(base_path), backend='sqlite')
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


class ServerOverHttp(CliTestCase):

    def setUp(self):
        super().setUp()
        self._app = _AppThread(TEST_DIR)
        self._app.start()

    def _start_server_over_http(self, game_number='test-01'):
        os.environ['BOARD_GAME_SERVER'] = self._app.base_url
        try:
            server = self.start_server(game_number)
            server.read_until(SERVER_PROMPT)
            return server
        finally:
            os.environ.pop('BOARD_GAME_SERVER', None)

    def test_setup_and_commit_exits_the_server(self):
        """The admin sets the board, registers a player, commits, and the
        binary exits (option (b) removes the need for an unattended
        resolver in HTTP mode)."""
        server = self._start_server_over_http()
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        server.send_line('commit')
        # the server prints `commit complete` and exits with code 0
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if server.proc.poll() is not None:
                break
            time.sleep(0.1)
        assert server.proc.poll() == 0, (
            f"server did not exit cleanly; return code: "
            f"{server.proc.poll()}, output: {server.output!r}")
        assert 'commit complete' in server.output
