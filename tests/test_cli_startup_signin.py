"""What a role does when it is pointed at a server and given no token.

Two answers, and which one depends on whether there is a person there. At a
terminal it asks, captures a forced password change, and opens the session
with the token it was issued. Anywhere else - a pipe, a script, a bot in
`matches/` - it reports that a token is needed and exits, exactly as it always
has, which is what keeps everything unattended working as it did.
"""

import os
import socket
import sys
import threading
import time

import pytest
import requests

sys.path.insert(0, os.path.dirname(__file__))

from board_game_concept.cli import accounts as accounts_module  # noqa: E402
from board_game_concept.cli import session as session_module    # noqa: E402
from board_game_concept.cli.backend import HttpSession          # noqa: E402
from board_game_concept.service.errors import (                 # noqa: E402
    GameError, NotAuthenticated, PasswordMustChange)
from game_harness import DEFAULT_BACKEND                        # noqa: E402


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


@pytest.fixture(name='served')
def _served(tmp_path):
    """A live server, and the app behind it for arranging seats."""
    from board_game_concept.http.app import create_app

    port = _free_port()
    app = create_app(base_path=str(tmp_path / 'served'),
                     backend=DEFAULT_BACKEND)
    threading.Thread(
        target=app.run,
        kwargs={'host': '127.0.0.1', 'port': port, 'threaded': True,
                'use_reloader': False},
        daemon=True).start()
    url = f'http://127.0.0.1:{port}'
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            if requests.get(f'{url}/_/health', timeout=0.5).status_code == 200:
                return url, app
        except requests.RequestException:
            time.sleep(0.05)
    raise RuntimeError('the app never answered /_/health')


@pytest.fixture(name='at_a_terminal')
def _at_a_terminal(monkeypatch):
    """Somebody is there to be asked."""
    monkeypatch.setattr(accounts_module, 'at_a_terminal', lambda: True)


def _typing(monkeypatch, username, *passwords):
    """A person typing a username and then these passwords, in order."""
    typed = iter(passwords)
    monkeypatch.setattr('builtins.input', lambda prompt='': username)
    monkeypatch.setattr(accounts_module.getpass, 'getpass',
                        lambda prompt='': next(typed))


def _no_token(monkeypatch):
    monkeypatch.delenv(session_module.TOKEN_ENV, raising=False)
    monkeypatch.delenv(session_module.SERVER_ENV, raising=False)


# --- 5.1 with a terminal, it asks


def test_a_role_with_no_token_signs_in_at_start_up(served, monkeypatch,
                                                   at_a_terminal, capsys):
    url, _app = served
    _no_token(monkeypatch)
    # `admin` is created needing a change, and the change is what the
    # start-up prompt captures before the session is opened
    _typing(monkeypatch, 'admin', 'admin', 'a-longer-secret',
            'a-longer-secret')

    session = session_module.make_session('one', 0, server=url)

    assert isinstance(session, HttpSession)
    assert session.token, 'the session was opened with no token'
    said = capsys.readouterr().out
    assert f'signing in to {url}' in said
    assert 'password changed' in said

    # the token it was issued is one the server accepts
    who = requests.get(f'{url}/accounts/current',
                       headers={'Authorization': f'Bearer {session.token}'})
    assert who.json()['username'] == 'admin'


def test_the_session_knows_who_it_signed_in_as(served, monkeypatch,
                                               at_a_terminal):
    """`whoami` answers about the token the session carries, however it came"""
    url, _app = served
    _no_token(monkeypatch)
    _typing(monkeypatch, 'admin', 'admin', 'a-longer-secret',
            'a-longer-secret')

    session = session_module.make_session('one', 0, server=url)
    accounts = session_module.make_accounts(session)

    who = accounts.whoami()

    assert who.username == 'admin'
    assert who.kind == 'admin'
    assert who.must_change is False


def test_a_token_from_the_environment_is_used_without_asking(served,
                                                             monkeypatch,
                                                             at_a_terminal):
    from conftest import make_token_for

    url, app = served
    _no_token(monkeypatch)
    monkeypatch.setattr('builtins.input', lambda prompt='': pytest.fail(
        'a role with a token asked for a username'))
    token = make_token_for(app, 'one', 0)
    monkeypatch.setenv(session_module.TOKEN_ENV, token)

    session = session_module.make_session('one', 0, server=url)

    assert session.token == token
    assert session_module.make_accounts(session).whoami().username == 'admin'


def test_a_token_that_was_never_issued_is_nobody(served, monkeypatch):
    url, _app = served
    session = HttpSession(url, 'one', 0, token='a-token-nobody-issued')

    assert session_module.make_accounts(session).whoami() is None


def test_a_refused_sign_in_opens_no_session(served, monkeypatch,
                                            at_a_terminal):
    url, _app = served
    _no_token(monkeypatch)
    _typing(monkeypatch, 'admin', 'not-the-password')

    with pytest.raises(NotAuthenticated):
        session_module.make_session('one', 0, server=url)


def test_declining_a_forced_change_opens_no_session(served, monkeypatch,
                                                    at_a_terminal):
    """There is no session yet for a gated account to be refused by."""
    url, _app = served
    _no_token(monkeypatch)

    def typed(prompt=''):
        if prompt.startswith('new password'):
            raise EOFError
        return 'admin'
    monkeypatch.setattr('builtins.input', lambda prompt='': 'admin')
    monkeypatch.setattr(accounts_module.getpass, 'getpass', typed)

    with pytest.raises(PasswordMustChange):
        session_module.make_session('one', 0, server=url)


# --- 5.2 without a terminal, it refuses exactly as it did


def test_a_role_with_no_token_and_no_terminal_is_refused(served, monkeypatch):
    url, _app = served
    _no_token(monkeypatch)
    monkeypatch.setattr(accounts_module, 'at_a_terminal', lambda: False)
    monkeypatch.setattr('builtins.input', lambda prompt='': pytest.fail(
        'a role with nobody at the terminal asked for a username'))

    with pytest.raises(GameError) as refused:
        session_module.make_session('one', 0, server=url)

    assert 'a token is needed' in refused.value.message
    assert session_module.TOKEN_ENV in refused.value.message


def test_a_role_started_by_a_pipe_reports_and_exits(tmp_path):
    """The refusal a script gets, from the role itself, as a subprocess."""
    from subprocess import PIPE, Popen

    from cli_harness import OBSERVER, TEST_DIR

    process = Popen(
        [str(word) for word in OBSERVER]
        + ['test-01', '--server', 'http://127.0.0.1:9'],
        cwd=str(TEST_DIR), stdin=PIPE, stdout=PIPE, stderr=PIPE,
        universal_newlines=True)
    output, errors = process.communicate('exit\n', timeout=30)

    assert process.returncode != 0
    assert 'a token is needed' in errors
    assert 'bgcobserver>' not in output, 'it opened a session anyway'


# --- 5.3 signing in as an account that may not act as this number


def test_signing_in_as_an_account_that_may_not_act_as_that_number(
        served, monkeypatch, at_a_terminal):
    """The sign-in works; the server refuses the number, and the role says so"""
    from conftest import make_player

    url, app = served
    _no_token(monkeypatch)
    make_player(app, 'ada', 'a-longer-secret')
    _typing(monkeypatch, 'ada', 'a-longer-secret')

    # the sign-in itself is answered - the account exists and its password is
    # right - and it is the game the account may not act in
    session = session_module.make_session('one', 3, server=url)

    with pytest.raises(GameError) as refused:
        session.load()

    assert 'may not act as' in str(refused.value)


def test_a_role_reports_a_refusal_about_its_account_rather_than_dying(
        served, monkeypatch):
    """`AccountError` is not a `GameDataError`, and used to reach nobody."""
    import io

    from conftest import make_player
    from board_game_concept.cli.session import load_game

    url, app = served
    make_player(app, 'ada', 'a-longer-secret')
    token = requests.post(f'{url}/sessions',
                          json={'username': 'ada',
                                'password': 'a-longer-secret'}).json()['token']
    session = HttpSession(url, 'one', 3, token=token)
    errors = io.StringIO()
    monkeypatch.setattr(sys, 'stderr', errors)

    with pytest.raises(SystemExit) as ended:
        load_game(session)

    assert ended.value.code == 1
    assert 'may not act as' in errors.getvalue()
