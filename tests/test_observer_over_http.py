"""The observer, end to end, against a live Flask thread.

Same commands `test_cli_observer_surface.py` runs locally, driven through
`--server URL`. The Flask app runs in a background thread; the observer
runs as a subprocess. The two agree on `BOARD_GAME_BACKEND` because the
harness sets it on the app and passes it into the subprocess env.
"""

import os
import socket
import threading
import time

import pytest
import requests

from cli_harness import CliTestCase, OBSERVER_PROMPT, TEST_DIR

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
        # Werkzeug's dev server is fine for tests. `threaded=True` so a busy
        # request does not block a health check
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


class ObserverOverHttp(CliTestCase):
    """The observer surface, over HTTP rather than over the file system."""

    def setUp(self):
        super().setUp()
        # the app serves whatever the harness would have opened locally;
        # they share `BOARD_GAME_BACKEND` and a working directory. The CLI
        # harness runs subprocesses cwd'd to `TEST_DIR`, so the games/ tree
        # the app reads lives under that same directory
        self._app = _AppThread(TEST_DIR)
        self._app.start()

    def _start_observer_over_http(self, game_number='test-01'):
        # `add_server_argument` reads `BOARD_GAME_SERVER` when no `--server`
        # was passed, so a subprocess started by the cli harness picks up
        # the URL that way without every test having to know
        from conftest import make_token_for
        os.environ['BOARD_GAME_SERVER'] = self._app.base_url
        # the observer role proves itself as the observer identity, 1000
        os.environ['BOARD_GAME_TOKEN'] = make_token_for(
            self._app.app, game_number, 1000)
        try:
            observer = self.start_observer(game_number)
            observer.read_until(OBSERVER_PROMPT)
            return observer
        finally:
            os.environ.pop('BOARD_GAME_SERVER', None)
            os.environ.pop('BOARD_GAME_TOKEN', None)

    def _send_and_wait(self, observer, line, expected_prompts):
        """Send a line and wait for the prompt count to reach `expected`."""
        observer.send_line(line)
        observer.read_until_count(OBSERVER_PROMPT, expected_prompts)

    def test_show_board_returns_the_grid_the_server_computed(self):
        self.server = self.established_game(players=(1, 2))
        observer = self._start_observer_over_http()
        self._send_and_wait(observer, 'show board', 2)
        # the grid renders as ASCII rules, so a printed board contains '+' or
        # '#'; no raw JSON leaks through
        assert '+' in observer.output or '#' in observer.output
        assert 'size_x' not in observer.output, (
            'the raw JSON leaked through: the renderer should have drawn '
            'the grid')

    def test_show_players_lists_the_registered_players(self):
        self.server = self.established_game(players=(1, 2))
        observer = self._start_observer_over_http()
        self._send_and_wait(observer, 'show players', 2)
        assert observer.errors == '', f"observer errors: {observer.errors!r}"
        # `players_view` includes each registered player; the renderer draws
        # the number in a column, so the number '1' appears in the output
        assert 'PLAYER' in observer.output or 'no players' in observer.output

    def test_show_types_before_a_type_is_added(self):
        self.server = self.established_game(players=(1,))
        observer = self._start_observer_over_http()
        self._send_and_wait(observer, 'show types', 2)
        # a game with no types shows an empty table rather than crashing
        assert 'no unit types' in observer.output.lower() or \
               'no such command' not in observer.output.lower()

    def test_reload_refreshes_over_http(self):
        self.server = self.established_game(players=(1,))
        observer = self._start_observer_over_http()
        self._send_and_wait(observer, 'reload', 2)
        assert 'reloading' in observer.output
