"""The test harness starts each test from nothing.

The suites that serve a role over HTTP run the app with `TEST_DIR` as its base
path, because the roles they start are subprocesses cwd'd there and the games
tree has to be the one those roles write. The account store lives beside that
tree, so those suites share one store.

Nothing cleared it. Accounts, tokens and seats survived from one test to the
next and from one run to the next, and a seat left behind made
`conftest.authorise` hand back a token for an account that did not hold the
seat - so a test failed on entitlement rather than on what it was testing, and
which test failed depended on what an earlier run had left on disk.

These hold the two halves of the fix: the store is cleared around every
`CliTestCase`, and `authorise` makes the seat the account's rather than
assuming nobody holds it.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from cli_harness import CliTestCase, TEST_DIR, remove_account_store  # noqa: E402
from conftest import authorise, make_admin, make_player              # noqa: E402
from board_game_concept.http.app import create_app                   # noqa: E402
from board_game_concept.service import accounts                      # noqa: E402
from board_game_concept.storage.sqlite_account_store import (        # noqa: E402
    STORE_FILENAME)
from board_game_concept.storage.yaml_account_store import (          # noqa: E402
    STORE_DIRNAME)

GAME = 'isolation-01'


def _served():
    """An app on the shared base path, as the over-HTTP suites build one."""
    return create_app(base_path=str(TEST_DIR), backend='sqlite')


@pytest.fixture(name='shared')
def _shared():
    """Leave the shared base path as this test found it.

    Deliberately not `autouse`: the tests below that drive `authorise` ask for
    it, and the `CliTestCase` class does not. An autouse fixture would have
    cleared the store around those methods too, which is the very thing they
    exist to check `setUp` does - and with one in place they passed whether or
    not `CliTestCase` cleared anything.
    """
    remove_account_store()
    yield
    remove_account_store()


def test_removing_the_store_takes_every_file_it_kept(shared):
    app = _served()
    make_player(app, 'ada')
    assert os.path.exists(os.path.join(str(TEST_DIR), STORE_FILENAME))

    remove_account_store()

    base = str(TEST_DIR)
    for name in (STORE_FILENAME, f'{STORE_FILENAME}-wal',
                 f'{STORE_FILENAME}-shm'):
        assert not os.path.exists(os.path.join(base, name)), name
    assert not os.path.exists(os.path.join(base, STORE_DIRNAME))


def test_an_account_does_not_survive_the_store_being_removed(shared):
    make_player(_served(), 'ada')

    remove_account_store()

    store = _served().config['ACCOUNT_STORE_FACTORY']()
    assert store.read_account_by_name('ada') is None
    # and the two system accounts are made afresh, needing a password change
    assert store.read_account_by_name('admin').must_change


def test_a_seat_does_not_survive_the_store_being_removed(shared):
    app = _served()
    authorise(app, GAME, 1)
    store = app.config['ACCOUNT_STORE_FACTORY']()
    assert store.read_membership(GAME, 1) is not None

    remove_account_store()

    assert _served().config['ACCOUNT_STORE_FACTORY']().read_membership(
        GAME, 1) is None


def test_authorise_makes_the_seat_the_accounts_own(shared):
    """A seat somebody else holds is reassigned, not silently left alone.

    Without this, `authorise` returned a token for an account that did not
    hold the seat, and the caller met a 403 about entitlement.
    """
    app = _served()
    authorise(app, GAME, 1)                       # player1 takes seat 1
    store = app.config['ACCOUNT_STORE_FACTORY']()
    first = store.read_account(store.read_membership(GAME, 1))
    assert first.username == 'player1'

    headers = authorise(app, GAME, 1, holder='admin')

    store = app.config['ACCOUNT_STORE_FACTORY']()
    now = store.read_account(store.read_membership(GAME, 1))
    assert now.username == 'admin'
    token = headers['Authorization'].split(' ', 1)[1]
    assert accounts.may_act_as(store, store.read_session(token), GAME, 1)


def test_authorise_leaves_a_seat_the_account_already_holds(shared):
    """Reassigning is not re-claiming: asking twice changes nothing."""
    app = _served()
    first = authorise(app, GAME, 2)
    again = authorise(app, GAME, 2)

    store = app.config['ACCOUNT_STORE_FACTORY']()
    assert store.read_account(store.read_membership(GAME, 2)).username \
        == 'player2'
    # two calls, two tokens, both of them the same account's
    assert first != again
    for headers in (first, again):
        token = headers['Authorization'].split(' ', 1)[1]
        assert accounts.may_act_as(store, store.read_session(token), GAME, 2)


class StoreIsClearedBetweenTests(CliTestCase):
    """`CliTestCase` clears the store, so neither test sees the other's.

    Named so the two run in this order under unittest's alphabetical
    ordering: the first leaves an account behind, the second requires it gone.
    """

    def test_a_leaves_an_account_and_a_seat_behind(self):
        app = _served()
        make_player(app, 'ghost')
        authorise(app, GAME, 1, username='ghost')
        store = app.config['ACCOUNT_STORE_FACTORY']()
        assert store.read_account_by_name('ghost') is not None
        assert store.read_membership(GAME, 1) is not None

    def test_b_finds_neither(self):
        store = _served().config['ACCOUNT_STORE_FACTORY']()
        assert store.read_account_by_name('ghost') is None
        assert store.read_membership(GAME, 1) is None
