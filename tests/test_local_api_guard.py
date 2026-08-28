"""The guard that redirects local sessions to a running `bgcapiserver`.

Two processes writing the same storage would step on each other's holds.
When a caller names neither `--server` nor `--backend`, `make_session`
probes the local API address; if a live `bgcapiserver` answers, the
session is HTTP-backed and a warning goes to stderr. Anything the caller
did name is honoured without consulting the probe.
"""

import os
import socket
import sys
import threading
import time
from io import StringIO

import pytest
import requests

from board_game_concept.cli import session as session_module
from board_game_concept.cli.backend import HttpSession, LocalSession


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


def _clean_env(monkeypatch):
    """Rip out every env var that would steer `make_session`."""
    for name in (session_module.SERVER_ENV, session_module.BACKEND_ENV,
                 session_module.LOCAL_API_ENV,
                 session_module.NO_REDIRECT_ENV,
                 session_module.TOKEN_ENV):
        monkeypatch.delenv(name, raising=False)


def test_probe_returns_none_when_no_api_server_is_running(monkeypatch,
                                                          tmp_path):
    """The probe hits a random unused port; nothing answers; None."""
    _clean_env(monkeypatch)
    port = _free_port()  # nothing is listening on this port
    monkeypatch.setenv(session_module.LOCAL_API_ENV,
                       f'http://127.0.0.1:{port}')
    assert session_module.probe_local_api() is None


def test_probe_returns_the_url_when_the_api_server_is_running(monkeypatch,
                                                              tmp_path):
    """A live Flask app answering `/_/health` is what the probe recognises."""
    _clean_env(monkeypatch)
    app = _AppThread(tmp_path)
    app.start()
    monkeypatch.setenv(session_module.LOCAL_API_ENV, app.base_url)
    assert session_module.probe_local_api() == app.base_url


def test_probe_ignores_a_stranger_on_the_port(monkeypatch, tmp_path):
    """Any HTTP server that is not `bgcapiserver` fails the JSON check."""
    _clean_env(monkeypatch)
    # a tiny server that returns 200 but not the JSON the probe expects
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'something else')

        def log_message(self, *_):
            pass

    port = _free_port()
    server = HTTPServer(('127.0.0.1', port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv(session_module.LOCAL_API_ENV,
                           f'http://127.0.0.1:{port}')
        assert session_module.probe_local_api() is None
    finally:
        server.shutdown()


def test_make_session_redirects_to_the_running_api_server(monkeypatch,
                                                          tmp_path, capsys):
    """No `--server`, no `--backend`; the guard finds the API server up and
    hands back an `HttpSession` with a warning on stderr."""
    _clean_env(monkeypatch)
    app = _AppThread(tmp_path)
    app.start()
    monkeypatch.setenv(session_module.LOCAL_API_ENV, app.base_url)
    from conftest import make_token_for
    monkeypatch.setenv(session_module.TOKEN_ENV,
                       make_token_for(app.app, 'one', 1))

    session = session_module.make_session('one', 1)
    assert isinstance(session, HttpSession)
    assert session.base_url == app.base_url

    captured = capsys.readouterr()
    assert 'bgcapiserver' in captured.err
    assert app.base_url in captured.err
    assert session_module.NO_REDIRECT_ENV in captured.err


def test_make_session_uses_local_when_no_api_server(monkeypatch, tmp_path):
    """No server, no backend, no API server up; a `LocalSession` over the
    compiled default backend."""
    _clean_env(monkeypatch)
    port = _free_port()
    monkeypatch.setenv(session_module.LOCAL_API_ENV,
                       f'http://127.0.0.1:{port}')
    session = session_module.make_session('one', 1, base_path=str(tmp_path))
    assert isinstance(session, LocalSession)


def test_explicit_backend_bypasses_the_guard(monkeypatch, tmp_path, capsys):
    """`--backend sqlite` says local, and the probe is never consulted -
    even if the API server is up."""
    _clean_env(monkeypatch)
    app = _AppThread(tmp_path)
    app.start()
    monkeypatch.setenv(session_module.LOCAL_API_ENV, app.base_url)

    session = session_module.make_session('one', 1, backend='sqlite',
                                          base_path=str(tmp_path))
    assert isinstance(session, LocalSession)
    captured = capsys.readouterr()
    assert captured.err == ''


def test_explicit_backend_env_var_bypasses_the_guard(monkeypatch, tmp_path,
                                                     capsys):
    """`BOARD_GAME_BACKEND` is the caller naming a backend too."""
    _clean_env(monkeypatch)
    app = _AppThread(tmp_path)
    app.start()
    monkeypatch.setenv(session_module.LOCAL_API_ENV, app.base_url)
    monkeypatch.setenv(session_module.BACKEND_ENV, 'sqlite')

    session = session_module.make_session('one', 1, base_path=str(tmp_path))
    assert isinstance(session, LocalSession)
    captured = capsys.readouterr()
    assert captured.err == ''


def test_explicit_server_bypasses_the_guard(monkeypatch, tmp_path, capsys):
    """`--server URL` is honoured verbatim, guard silent."""
    _clean_env(monkeypatch)
    # a URL nothing is listening on: the guard would have said local, but
    # the explicit `--server` is what wins
    port = _free_port()
    session = session_module.make_session(
        'one', 1, server=f'http://127.0.0.1:{port}', token='any-token')
    assert isinstance(session, HttpSession)
    captured = capsys.readouterr()
    assert captured.err == ''


def test_no_redirect_env_var_suppresses_the_guard(monkeypatch, tmp_path,
                                                  capsys):
    """`BOARD_GAME_NO_REDIRECT=1` is the escape hatch for a caller that
    genuinely wants local while another API server is up."""
    _clean_env(monkeypatch)
    app = _AppThread(tmp_path)
    app.start()
    monkeypatch.setenv(session_module.LOCAL_API_ENV, app.base_url)
    monkeypatch.setenv(session_module.NO_REDIRECT_ENV, '1')

    session = session_module.make_session('one', 1, base_path=str(tmp_path))
    assert isinstance(session, LocalSession)
    captured = capsys.readouterr()
    assert captured.err == ''


def test_the_health_probe_is_open_but_the_game_is_not(monkeypatch, tmp_path):
    """`/_/health` has to answer without a credential - it is what the guard
    probes for - and nothing else does."""
    _clean_env(monkeypatch)
    app = _AppThread(tmp_path)
    app.start()

    assert requests.get(f'{app.base_url}/_/health',
                        timeout=5).status_code == 200
    assert requests.get(f'{app.base_url}/games/one/players/1/state',
                        timeout=5).status_code == 401
