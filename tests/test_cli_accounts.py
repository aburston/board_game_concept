"""The account seam a command line signs in through.

Two implementations of four operations, and the point of the tests is that
they answer alike: what `LocalAccounts` does against a store on this machine
is what `HttpAccounts` does against a server, refusal for refusal. Where they
disagreed, a person's password would depend on how they happened to reach the
game - which is the thing this change exists to prevent.
"""

import os
import socket
import sys
import threading
import time

import pytest
import requests

sys.path.insert(0, os.path.dirname(__file__))

from board_game_concept.cli.accounts import (            # noqa: E402
    Accounts, HttpAccounts, LocalAccounts)
from board_game_concept.service.errors import (          # noqa: E402
    AccountError, NotAuthenticated, PasswordMustChange)
from game_harness import DEFAULT_BACKEND                 # noqa: E402


# --- the two implementations, made the same way for every test below


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _serve(base_path, backend):
    """A live app on a random port, and the URL it answers on."""
    from board_game_concept.http.app import create_app

    port = _free_port()
    app = create_app(base_path=str(base_path), backend=backend)
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
                return url
        except requests.RequestException:
            time.sleep(0.05)
    raise RuntimeError('the app never answered /_/health')


@pytest.fixture(name='local')
def _local(tmp_path):
    return LocalAccounts(backend=DEFAULT_BACKEND,
                         base_path=str(tmp_path / 'home'))


@pytest.fixture(name='served')
def _served(tmp_path):
    return HttpAccounts(_serve(tmp_path / 'served', DEFAULT_BACKEND))


@pytest.fixture(name='accounts', params=['local', 'served'])
def _accounts(request):
    """Each test below, run against both implementations."""
    return request.getfixturevalue(request.param)


# --- 1.1 the base class names the set and refuses it


@pytest.mark.parametrize('operation, arguments', [
    ('sign_in', ('ada', 'secret')),
    ('sign_out', ()),
    ('whoami', ()),
    ('change_password', ('old', 'new')),
])
def test_the_base_class_refuses_every_operation(operation, arguments):
    with pytest.raises(NotImplementedError):
        getattr(Accounts(), operation)(*arguments)


# --- 1.2 the local implementation


def test_a_local_sign_in_answers_with_the_account_and_a_token(local):
    signed_in = local.sign_in('admin', 'admin')

    assert signed_in.username == 'admin'
    assert signed_in.kind == 'admin'
    assert signed_in.token
    assert signed_in.must_change is True


def test_a_local_store_is_not_opened_until_it_is_asked_for(tmp_path):
    home = tmp_path / 'untouched'

    LocalAccounts(backend=DEFAULT_BACKEND, base_path=str(home))

    assert not home.exists(), 'constructing it created a store'


def test_a_local_store_is_created_by_the_first_sign_in(tmp_path):
    home = tmp_path / 'made-on-demand'
    accounts = LocalAccounts(backend=DEFAULT_BACKEND, base_path=str(home))

    accounts.sign_in('observer', 'observer')

    assert home.exists(), 'signing in created no store'


# --- 1.3 the two answer alike


def test_a_wrong_password_is_refused_the_same_way(accounts):
    with pytest.raises(NotAuthenticated):
        accounts.sign_in('admin', 'not-the-password')

    assert accounts.signed_in is None


def test_an_unknown_username_is_refused_the_same_way(accounts):
    with pytest.raises(NotAuthenticated) as refusal:
        accounts.sign_in('nobody', 'whatever-it-was')

    # the refusal does not say which of the two was wrong
    assert 'username and password' in str(refusal.value)


def test_a_short_new_password_is_refused_the_same_way(accounts):
    accounts.sign_in('admin', 'admin')

    with pytest.raises(AccountError) as refusal:
        accounts.change_password('admin', 'short')

    assert '8' in str(refusal.value)


def test_a_wrong_current_password_is_refused_the_same_way(accounts):
    accounts.sign_in('admin', 'admin')

    with pytest.raises(AccountError):
        accounts.change_password('not-the-password', 'long-enough-one')


def test_an_account_that_must_change_is_reported_as_one(accounts):
    signed_in = accounts.sign_in('observer', 'observer')

    assert signed_in.must_change is True
    assert accounts.whoami().must_change is True


def test_changing_the_password_lifts_the_refusal(accounts):
    accounts.sign_in('admin', 'admin')

    accounts.change_password('admin', 'a-longer-secret')

    assert accounts.whoami().must_change is False
    assert accounts.signed_in.must_change is False


def test_the_new_password_is_the_one_that_authenticates(accounts):
    accounts.sign_in('admin', 'admin')
    accounts.change_password('admin', 'a-longer-secret')
    accounts.sign_out()

    signed_in = accounts.sign_in('admin', 'a-longer-secret')

    assert signed_in.must_change is False
    with pytest.raises(NotAuthenticated):
        accounts.sign_in('admin', 'admin')


def test_signing_out_ends_the_token(accounts):
    accounts.sign_in('admin', 'admin')

    accounts.sign_out()

    assert accounts.signed_in is None
    assert accounts.whoami() is None


def test_asking_anything_of_a_session_that_is_not_signed_in(accounts):
    assert accounts.whoami() is None
    with pytest.raises(NotAuthenticated):
        accounts.sign_out()
    with pytest.raises(NotAuthenticated):
        accounts.change_password('one', 'a-longer-secret')


def test_a_password_that_must_change_still_refuses_everything_else(accounts):
    """The gate `service/accounts.py` states, seen from a command line."""
    from board_game_concept.service import accounts as account_rules

    signed_in = accounts.sign_in('observer', 'observer')

    with pytest.raises(PasswordMustChange):
        account_rules.require_usable(
            _account_behind(accounts, signed_in))


def _account_behind(accounts, signed_in):
    """The stored account this session is signed in as.

    Read through whichever store the implementation uses, so the assertion
    above is about the account and not about the transport.
    """
    if isinstance(accounts, LocalAccounts):
        return accounts.store().read_account_by_name(signed_in.username)

    class _Stub:
        username = signed_in.username
        must_change = signed_in.must_change

    return _Stub()


# --- 1.4 the game's access method decides the account's


def test_an_http_session_asks_the_server_it_reached(tmp_path):
    from board_game_concept.cli.backend import HttpSession
    from board_game_concept.cli.session import make_accounts

    session = HttpSession('http://127.0.0.1:45678/', 'one', 1, token='t')

    accounts = make_accounts(session)

    assert isinstance(accounts, HttpAccounts)
    assert accounts.base_url == 'http://127.0.0.1:45678'


def test_a_local_session_asks_the_store_beside_the_games(tmp_path):
    from board_game_concept.cli.session import make_accounts, make_repository
    from board_game_concept.cli.backend import LocalSession

    session = LocalSession(
        make_repository('one', backend=DEFAULT_BACKEND,
                        base_path=str(tmp_path)), 0)

    accounts = make_accounts(session, backend=DEFAULT_BACKEND,
                             base_path=str(tmp_path))

    assert isinstance(accounts, LocalAccounts)
    assert accounts._base_path == str(tmp_path)


def test_signing_in_replaces_the_token_the_session_carries(tmp_path):
    """A `login` at the prompt has to reach the requests the session makes."""
    from board_game_concept.cli.backend import HttpSession
    from board_game_concept.cli.session import make_accounts

    url = _serve(tmp_path / 'served', DEFAULT_BACKEND)
    session = HttpSession(url, 'one', 0, token='a-token-that-was-never-issued')
    accounts = make_accounts(session)

    signed_in = accounts.sign_in('admin', 'admin')

    assert (session._session.headers['Authorization']
            == f'Bearer {signed_in.token}')

    accounts.sign_out()

    assert 'Authorization' not in session._session.headers
