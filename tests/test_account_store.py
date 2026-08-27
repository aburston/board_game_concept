"""What the account store keeps, and what it refuses.

Against a real SQLite file in a temporary directory. Nothing here goes near a
game: the point of this store is that it belongs to the server rather than to
any one game.
"""

import os
from datetime import timedelta

import pytest

from board_game_concept.domain import Kind
from board_game_concept.domain import account as account_rules
from board_game_concept.storage.account_store import make_account_store
from board_game_concept.storage.sqlite_account_store import (
    STORE_FILENAME, SqliteAccountStore, hash_password, new_token,
    password_matches, session_expiry, _now)
from board_game_concept.storage.yaml_account_store import STORE_DIRNAME


# both implementations of the port, held to the same behaviour. What a
# deployment may not do is mix them - that is `make_account_store`'s to
# refuse, and `test_accounts_end_to_end.py` is where it is held to.
@pytest.fixture(name='backend', params=['sqlite', 'yaml'])
def _backend(request):
    return request.param


@pytest.fixture(name='store')
def _store(tmp_path, backend):
    store = make_account_store(backend, str(tmp_path))
    store.ensure()
    return store


def _player(store, name='ada', password='secret12'):
    return store.create_account(name, hash_password(password), Kind.PLAYER)


# --- the two system accounts

def test_first_start_creates_the_two_system_accounts(store):
    administrator = store.read_account_by_name(
        account_rules.ADMINISTRATOR_NAME)
    observer = store.read_account_by_name(account_rules.OBSERVER_NAME)

    assert administrator.kind == Kind.ADMINISTRATOR
    assert observer.kind == Kind.OBSERVER
    assert administrator.must_change
    assert observer.must_change
    assert password_matches(administrator.password_hash, 'admin')
    assert password_matches(observer.password_hash, 'observer')


def test_the_store_lives_beside_the_games_rather_than_in_one(store, tmp_path,
                                                             backend):
    kept = STORE_FILENAME if backend == 'sqlite' else STORE_DIRNAME
    assert (tmp_path / kept).exists()
    assert not (tmp_path / 'games').exists()


def test_a_later_start_does_not_reset_a_changed_password(store, tmp_path,
                                                         backend):
    administrator = store.read_account_by_name('admin')
    store.set_password(administrator.account_id, hash_password('new-secret'))

    reopened = make_account_store(backend, str(tmp_path))
    reopened.ensure()
    again = reopened.read_account_by_name('admin')

    assert password_matches(again.password_hash, 'new-secret')
    assert not password_matches(again.password_hash, 'admin')
    assert not again.must_change


def test_a_later_start_does_not_clear_must_change_on_an_unchanged_one(
        store, tmp_path, backend):
    reopened = make_account_store(backend, str(tmp_path))
    reopened.ensure()
    assert reopened.read_account_by_name('observer').must_change


def test_ensuring_twice_does_not_duplicate_the_system_accounts(store):
    store.ensure()
    store.ensure()
    names = [account.key for account in store.accounts()]
    assert names.count('admin') == 1
    assert names.count('observer') == 1


# --- accounts

def test_an_account_round_trips(store):
    made = _player(store, 'Ada')
    read = store.read_account(made.account_id)

    assert read.username == 'Ada'
    assert read.key == 'ada'
    assert read.kind == Kind.PLAYER
    assert not read.must_change


def test_an_account_is_found_without_regard_to_case(store):
    _player(store, 'Ada')
    assert store.read_account_by_name('ada').username == 'Ada'
    assert store.read_account_by_name('ADA').username == 'Ada'


def test_a_name_already_taken_is_refused(store):
    _player(store, 'Ada')
    with pytest.raises(ValueError):
        _player(store, 'ada')


def test_an_unknown_account_reads_back_as_nothing(store):
    assert store.read_account_by_name('nobody') is None
    assert store.read_account(99999) is None


def test_two_accounts_with_one_password_have_different_hashes(store):
    one = _player(store, 'ada', 'the-same-one')
    two = _player(store, 'bob', 'the-same-one')
    assert one.password_hash != two.password_hash
    assert password_matches(one.password_hash, 'the-same-one')
    assert password_matches(two.password_hash, 'the-same-one')


def test_the_password_is_not_stored_readably(store, tmp_path):
    """Whatever the backend keeps, the password is not in it.

    Read off the disk rather than through the store, so this cannot pass by
    the store politely declining to hand it back.
    """
    _player(store, 'ada', 'secret12')

    found = []
    for root, _dirs, files in os.walk(str(tmp_path)):
        for name in files:
            with open(os.path.join(root, name), 'rb') as file:
                found.append(file.read())
    assert found
    assert not any(b'secret12' in blob for blob in found)


def test_setting_a_password_clears_must_change(store):
    administrator = store.read_account_by_name('admin')
    store.set_password(administrator.account_id, hash_password('new-secret'))
    again = store.read_account_by_name('admin')
    assert not again.must_change
    assert password_matches(again.password_hash, 'new-secret')


# --- tokens

def test_a_session_is_created_read_and_deleted(store):
    ada = _player(store)
    token = new_token()
    store.create_session(ada.account_id, token, session_expiry())

    assert store.read_session(token).account_id == ada.account_id

    store.delete_session(token)
    assert store.read_session(token) is None


def test_a_token_that_was_never_issued_reads_back_as_nothing(store):
    assert store.read_session(new_token()) is None
    assert store.read_session('') is None
    assert store.read_session(None) is None


def test_an_expired_token_does_not_read_back(store):
    ada = _player(store)
    token = new_token()
    store.create_session(ada.account_id, token, _now() - timedelta(seconds=1))
    assert store.read_session(token) is None


def test_a_token_is_accepted_until_its_time(store):
    ada = _player(store)
    token = new_token()
    expiry = _now() + timedelta(hours=1)
    store.create_session(ada.account_id, token, expiry)

    assert store.read_session(token, now=_now()) is not None
    assert store.read_session(token, now=expiry + timedelta(1)) is None


def test_every_token_of_an_account_can_be_ended(store):
    ada = _player(store)
    tokens = [new_token() for _ in range(3)]
    for token in tokens:
        store.create_session(ada.account_id, token, session_expiry())
    assert len(store.sessions_of(ada.account_id)) == 3

    store.delete_sessions_of(ada.account_id)
    assert store.sessions_of(ada.account_id) == []
    for token in tokens:
        assert store.read_session(token) is None


def test_a_minted_token_is_the_same_row_with_a_label(store):
    ada = _player(store)
    token = new_token()
    store.create_session(ada.account_id, token, session_expiry(minted=True),
                         label='reaper-bot')

    held = store.sessions_of(ada.account_id)
    assert len(held) == 1
    assert held[0]['label'] == 'reaper-bot'
    assert store.read_session(token).account_id == ada.account_id


# --- seats

def test_a_seat_is_claimed_once(store):
    ada = _player(store, 'ada')
    bob = _player(store, 'bob')

    store.claim_seat('1', 2, ada.account_id)
    assert store.read_membership('1', 2) == ada.account_id
    assert store.holds_seat('1', 2, ada.account_id)
    assert not store.holds_seat('1', 2, bob.account_id)


def test_a_seat_already_held_is_refused(store):
    ada = _player(store, 'ada')
    bob = _player(store, 'bob')
    store.claim_seat('1', 2, ada.account_id)

    with pytest.raises(ValueError):
        store.claim_seat('1', 2, bob.account_id)

    assert store.read_membership('1', 2) == ada.account_id


def test_one_account_may_hold_several_seats_in_one_game(store):
    ada = _player(store)
    store.claim_seat('1', 1, ada.account_id)
    store.claim_seat('1', 2, ada.account_id)

    assert store.seats_of_account(ada.account_id) == [('1', 1), ('1', 2)]
    assert store.seats_of_game('1') == {1: ada.account_id, 2: ada.account_id}


def test_a_seat_in_one_game_is_not_a_seat_in_another(store):
    ada = _player(store)
    store.claim_seat('1', 2, ada.account_id)

    assert not store.holds_seat('2', 2, ada.account_id)
    assert store.read_membership('2', 2) is None


def test_a_released_seat_is_claimable_again(store):
    ada = _player(store, 'ada')
    bob = _player(store, 'bob')
    store.claim_seat('1', 2, ada.account_id)

    store.release_seat('1', 2)
    assert store.read_membership('1', 2) is None

    store.claim_seat('1', 2, bob.account_id)
    assert store.read_membership('1', 2) == bob.account_id


def test_an_unclaimed_seat_holds_nobody(store):
    assert store.read_membership('1', 5) is None
    assert store.seats_of_game('1') == {}


def test_two_claims_arriving_together_cannot_both_succeed(store, tmp_path,
                                                          backend):
    """The refusal comes from the primary key, not a read-then-write.

    Two stores over one file, each claiming the same seat inside its own
    transaction. One commits; the other is refused rather than overwriting.
    """
    ada = _player(store, 'ada')
    bob = _player(store, 'bob')

    other = make_account_store(backend, str(tmp_path))
    other.ensure()

    with store.held():
        store.claim_seat('1', 2, ada.account_id)

    with pytest.raises(ValueError):
        with other.held():
            other.claim_seat('1', 2, bob.account_id)

    assert other.read_membership('1', 2) == ada.account_id


def test_deleting_an_account_takes_its_seats_and_tokens(store, backend):
    """SQLite cascades; the YAML store has no rows to cascade from.

    Deleting an account is not something either store offers through the port
    - there is no `delete_account` - so this is about the SQLite schema being
    trustworthy rather than about a use case.
    """
    if backend != 'sqlite':
        pytest.skip('no cascade to test without foreign keys')

    ada = _player(store)
    token = new_token()
    store.create_session(ada.account_id, token, session_expiry())
    store.claim_seat('1', 2, ada.account_id)

    store._get('DELETE FROM accounts WHERE id=?', (ada.account_id,))

    assert store.read_membership('1', 2) is None
    assert store.read_session(token) is None
