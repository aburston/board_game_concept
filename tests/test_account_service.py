"""What a caller may ask about an account, and every refusal.

Against a real store and a real game directory: the seat rules are answered
partly by the game's own repository, and a fake would let this agree with
something the game does not do.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from game_harness import GameHarness                      # noqa: E402
from board_game_concept.domain import Kind                # noqa: E402
from board_game_concept.service import accounts, identity  # noqa: E402
from board_game_concept.service.errors import (            # noqa: E402
    AccountError, NotAuthenticated, NotAuthorised, PasswordMustChange)
from board_game_concept.storage.account_store import (  # noqa: E402
    make_account_store)
from board_game_concept.storage.sqlite_account_store import (  # noqa: E402
    password_matches)
from game_harness import DEFAULT_BACKEND                    # noqa: E402


@pytest.fixture(name='store')
def _store(tmp_path):
    # the same backend the games in this run use: one choice drives both
    store = make_account_store(DEFAULT_BACKEND, str(tmp_path / 'server'))
    store.ensure()
    return store


@pytest.fixture(name='harness')
def _harness(tmp_path):
    return GameHarness(tmp_path / 'games-root')


def _usable_admin(store):
    """The administrator with its password changed, so it may act."""
    administrator = store.read_account_by_name('admin')
    accounts.change_password(store, administrator, 'admin', 'new-secret')
    return store.read_account_by_name('admin')


# --- registering

def test_registering_makes_a_player(store):
    ada = accounts.register(store, 'Ada', 'secret12')
    assert ada.kind == Kind.PLAYER
    assert ada.username == 'Ada'
    assert not ada.must_change


def test_registering_a_reserved_name_is_refused(store):
    for name in ('admin', 'Admin', 'observer', 'OBSERVER'):
        with pytest.raises(AccountError, match='reserved'):
            accounts.register(store, name, 'secret12')


def test_registering_a_taken_name_is_refused_in_any_case(store):
    accounts.register(store, 'Ada', 'secret12')
    with pytest.raises(AccountError):
        accounts.register(store, 'ada', 'secret12')
    with pytest.raises(AccountError):
        accounts.register(store, 'ADA', 'secret12')


def test_a_short_password_is_refused_and_no_account_is_made(store):
    with pytest.raises(AccountError, match='8'):
        accounts.register(store, 'ada', 'short')
    assert store.read_account_by_name('ada') is None


def test_registration_never_makes_a_system_kind(store):
    ada = accounts.register(store, 'ada', 'secret12')
    assert ada.kind == Kind.PLAYER
    assert not ada.is_administrator()
    assert not ada.is_observer()


# --- authenticating

def test_authenticating_returns_a_token_that_identifies_the_account(store):
    ada = accounts.register(store, 'ada', 'secret12')
    account, token = accounts.authenticate(store, 'ada', 'secret12')

    assert account.account_id == ada.account_id
    assert accounts.account_for(store, token).account_id == ada.account_id


def test_authenticating_by_a_name_in_another_case(store):
    accounts.register(store, 'Ada', 'secret12')
    _, token = accounts.authenticate(store, 'ADA', 'secret12')
    assert accounts.account_for(store, token).username == 'Ada'


def test_a_wrong_password_and_an_unknown_name_refuse_alike(store):
    accounts.register(store, 'ada', 'secret12')

    with pytest.raises(NotAuthenticated) as wrong:
        accounts.authenticate(store, 'ada', 'not-the-one')
    with pytest.raises(NotAuthenticated) as unknown:
        accounts.authenticate(store, 'nobody', 'not-the-one')

    assert str(wrong.value) == str(unknown.value)


def test_an_unaccepted_token_is_refused(store):
    with pytest.raises(NotAuthenticated):
        accounts.account_for(store, 'never-issued')
    with pytest.raises(NotAuthenticated):
        accounts.account_for(store, None)


def test_an_ended_token_is_refused(store):
    accounts.register(store, 'ada', 'secret12')
    _, token = accounts.authenticate(store, 'ada', 'secret12')
    accounts.end_token(store, token)

    with pytest.raises(NotAuthenticated):
        accounts.account_for(store, token)


def test_a_minted_token_identifies_the_account(store):
    ada = accounts.register(store, 'ada', 'secret12')
    token = accounts.mint_token(store, ada, label='reaper-bot')
    assert accounts.account_for(store, token).account_id == ada.account_id


# --- the password gate

def test_a_system_account_must_change_its_password_first(store):
    administrator = store.read_account_by_name('admin')
    with pytest.raises(PasswordMustChange):
        accounts.require_usable(administrator)


def test_changing_the_password_lifts_the_gate(store):
    administrator = _usable_admin(store)
    accounts.require_usable(administrator)
    assert password_matches(administrator.password_hash, 'new-secret')


def test_a_registered_account_is_usable_at_once(store):
    ada = accounts.register(store, 'ada', 'secret12')
    accounts.require_usable(ada)


def test_the_observer_is_held_to_the_gate_too(store):
    with pytest.raises(PasswordMustChange):
        accounts.require_usable(store.read_account_by_name('observer'))


# --- passwords

def test_changing_with_the_wrong_current_password_is_refused(store):
    ada = accounts.register(store, 'ada', 'secret12')
    with pytest.raises(NotAuthorised):
        accounts.change_password(store, ada, 'not-the-one', 'new-secret')
    assert password_matches(
        store.read_account_by_name('ada').password_hash, 'secret12')


def test_changing_to_a_short_password_is_refused(store):
    ada = accounts.register(store, 'ada', 'secret12')
    with pytest.raises(AccountError, match='8'):
        accounts.change_password(store, ada, 'secret12', 'short')


def test_the_administrator_resets_another_account(store):
    administrator = _usable_admin(store)
    accounts.register(store, 'ada', 'secret12')

    accounts.reset_password(store, administrator, 'ada', 'reset-secret')

    assert password_matches(
        store.read_account_by_name('ada').password_hash, 'reset-secret')


def test_a_player_cannot_reset_another_account(store):
    accounts.register(store, 'ada', 'secret12')
    bob = accounts.register(store, 'bob', 'secret12')

    with pytest.raises(NotAuthorised):
        accounts.reset_password(store, bob, 'ada', 'stolen-secret')

    assert password_matches(
        store.read_account_by_name('ada').password_hash, 'secret12')


def test_resetting_an_account_that_does_not_exist(store):
    administrator = _usable_admin(store)
    with pytest.raises(AccountError):
        accounts.reset_password(store, administrator, 'nobody', 'secret12')


# --- may_act_as

def test_the_administrator_is_player_zero_of_every_game(store):
    administrator = _usable_admin(store)
    for gameno in ('1', '2', 'anything'):
        assert accounts.may_act_as(store, administrator, gameno,
                                   identity.ADMINISTRATOR)


def test_the_observer_is_one_thousand_of_every_game(store):
    observer = store.read_account_by_name('observer')
    for gameno in ('1', '2', 'anything'):
        assert accounts.may_act_as(store, observer, gameno, identity.OBSERVER)


def test_the_administrator_may_act_as_the_observer(store):
    administrator = _usable_admin(store)
    assert accounts.may_act_as(store, administrator, '1', identity.OBSERVER)


def test_the_observer_may_not_act_as_the_administrator(store):
    observer = store.read_account_by_name('observer')
    assert not accounts.may_act_as(store, observer, '1',
                                   identity.ADMINISTRATOR)


def test_the_administrator_is_not_a_player_without_a_seat(store):
    administrator = _usable_admin(store)
    assert not accounts.may_act_as(store, administrator, '1', 2)


def test_a_player_may_act_as_the_seat_it_holds(store):
    ada = accounts.register(store, 'ada', 'secret12')
    store.claim_seat('1', 2, ada.account_id)
    assert accounts.may_act_as(store, ada, '1', 2)


def test_a_player_may_not_act_as_another_seat(store):
    ada = accounts.register(store, 'ada', 'secret12')
    store.claim_seat('1', 2, ada.account_id)
    assert not accounts.may_act_as(store, ada, '1', 3)


def test_a_seat_in_another_game_is_not_a_seat_in_this_one(store):
    ada = accounts.register(store, 'ada', 'secret12')
    store.claim_seat('1', 2, ada.account_id)
    assert not accounts.may_act_as(store, ada, '2', 2)


def test_a_player_may_not_act_as_a_reserved_number(store):
    ada = accounts.register(store, 'ada', 'secret12')
    store.claim_seat('1', 2, ada.account_id)
    assert not accounts.may_act_as(store, ada, '1', identity.ADMINISTRATOR)
    assert not accounts.may_act_as(store, ada, '1', identity.OBSERVER)


def test_a_number_that_identifies_nobody_is_never_actable(store):
    administrator = _usable_admin(store)
    for number in (-1, 1001, 5000):
        assert not accounts.may_act_as(store, administrator, '1', number)


def test_requiring_it_raises_rather_than_answering(store):
    ada = accounts.register(store, 'ada', 'secret12')
    accounts.require_may_act_as.__call__  # present
    with pytest.raises(NotAuthorised):
        accounts.require_may_act_as(store, ada, '1', 2)


def test_requiring_it_applies_the_password_gate_first(store):
    administrator = store.read_account_by_name('admin')
    with pytest.raises(PasswordMustChange):
        accounts.require_may_act_as(store, administrator, '1',
                                    identity.ADMINISTRATOR)


# --- seats

def test_claiming_a_registered_unclaimed_seat(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')

    accounts.claim_seat(store, harness.repository(), ada,
                        harness.gameno, 2)

    assert store.holds_seat(harness.gameno, 2, ada.account_id)
    assert accounts.may_act_as(store, ada, harness.gameno, 2)


def test_claiming_a_number_the_game_has_not_registered(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')

    with pytest.raises(AccountError, match='no player 7'):
        accounts.claim_seat(store, harness.repository(), ada,
                            harness.gameno, 7)

    assert store.read_membership(harness.gameno, 7) is None
    assert harness.repository().player_numbers() == [1, 2]


def test_claiming_a_number_outside_the_player_range(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')

    for number in (0, 1000, -1):
        with pytest.raises(AccountError):
            accounts.claim_seat(store, harness.repository(), ada,
                                harness.gameno, number)


def test_claiming_a_seat_another_account_holds(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')
    bob = accounts.register(store, 'bob', 'secret12')
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)

    with pytest.raises(AccountError):
        accounts.claim_seat(store, harness.repository(), bob,
                            harness.gameno, 2)

    assert store.read_membership(harness.gameno, 2) == ada.account_id


def test_one_account_may_claim_several_seats_of_one_game(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')

    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 1)
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)

    assert accounts.may_act_as(store, ada, harness.gameno, 1)
    assert accounts.may_act_as(store, ada, harness.gameno, 2)


def test_a_seat_may_be_claimed_after_setup_is_committed(store, harness):
    """The window a lobby exists for: the board is set and nobody has moved."""
    harness.create(5, 5, [1, 2])
    harness.session(0).serverSave()
    ada = accounts.register(store, 'ada', 'secret12')

    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)

    assert store.holds_seat(harness.gameno, 2, ada.account_id)


def test_claiming_is_refused_once_a_turn_has_resolved(store, harness):
    harness.create(5, 5, [1, 2])
    harness.session(0).serverSave()
    _play_one_turn(harness)
    ada = accounts.register(store, 'ada', 'secret12')

    with pytest.raises(AccountError, match='started'):
        accounts.claim_seat(store, harness.repository(), ada,
                            harness.gameno, 2)


def test_claiming_does_not_register_a_player(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)

    assert harness.repository().player_numbers() == [1, 2]


def test_a_seat_is_given_up_before_the_game_starts(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')
    bob = accounts.register(store, 'bob', 'secret12')
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)

    accounts.release_seat(store, harness.repository(), ada,
                          harness.gameno, 2)

    assert store.read_membership(harness.gameno, 2) is None
    accounts.claim_seat(store, harness.repository(), bob, harness.gameno, 2)
    assert store.read_membership(harness.gameno, 2) == bob.account_id


def test_giving_up_is_refused_once_a_turn_has_resolved(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)
    harness.session(0).serverSave()
    _play_one_turn(harness)

    with pytest.raises(AccountError, match='started'):
        accounts.release_seat(store, harness.repository(), ada,
                              harness.gameno, 2)

    assert store.holds_seat(harness.gameno, 2, ada.account_id)


def test_only_the_holder_gives_up_a_seat(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')
    bob = accounts.register(store, 'bob', 'secret12')
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)

    with pytest.raises(NotAuthorised):
        accounts.release_seat(store, harness.repository(), bob,
                              harness.gameno, 2)

    assert store.read_membership(harness.gameno, 2) == ada.account_id


def test_giving_up_a_seat_nobody_holds(store, harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')

    with pytest.raises(AccountError):
        accounts.release_seat(store, harness.repository(), ada,
                              harness.gameno, 2)


def _play_one_turn(harness):
    """Deploy for both players and resolve, so the turn number reaches 1."""
    from board_game_concept.service import games
    from board_game_concept.service.commands import (AddType, AddUnit,
                                                     SetFlag)

    for number, square in ((1, (0, 0)), (2, (4, 4))):
        session = harness.session(number)
        games.perform(session, AddType(name='Cross', symbol='X', attack=1,
                                       health=1, energy=10))
        games.perform(session, AddUnit(type_name='Cross', name=f'u{number}',
                                       x=square[0], y=square[1]))
        games.perform(session, SetFlag(unit=f'u{number}'))
        session.clientSave()
    harness.session(0).resolveWhenReady()


# --- the administrator's seat is an ordinary seat
#
# The administrator can play because `claim_seat` never asks what kind of
# account is claiming and `may_act_as` grants a seat on the membership rather
# than on the kind. Both are properties of this module, so this is where they
# are held; the served contract is held to the same rule in
# `tests/test_admin_plays.py`.

def test_the_administrator_may_claim_a_seat(store, harness):
    harness.create(5, 5, [1, 2])
    administrator = _usable_admin(store)

    accounts.claim_seat(store, harness.repository(), administrator,
                        harness.gameno, 1)

    assert store.holds_seat(harness.gameno, 1, administrator.account_id)
    assert (store.read_membership(harness.gameno, 1)
            == administrator.account_id)


def test_the_administrator_may_act_as_the_seat_it_holds(store, harness):
    harness.create(5, 5, [1, 2])
    administrator = _usable_admin(store)
    accounts.claim_seat(store, harness.repository(), administrator,
                        harness.gameno, 1)

    assert accounts.may_act_as(store, administrator, harness.gameno, 1)
    # the seat it does not hold is still refused: holding one is not holding
    # them all, and being the administrator does not stand in for a membership
    assert not accounts.may_act_as(store, administrator, harness.gameno, 2)
    # and what it was already entitled to is untouched by holding a seat
    assert accounts.may_act_as(store, administrator, harness.gameno,
                               identity.ADMINISTRATOR)
    assert accounts.may_act_as(store, administrator, harness.gameno,
                               identity.OBSERVER)


def _refusal(call):
    """The message a call was refused with, so two refusals can be compared."""
    with pytest.raises(AccountError) as raised:
        call()
    return str(raised.value)


def test_the_administrator_is_refused_a_claim_exactly_as_a_player_is(store,
                                                                     harness):
    """Each claim refusal, worded as it is for a registered player.

    Compared against a player's refusal rather than against a literal, so the
    two cannot drift apart: the requirement is that they are the same message,
    not that either is any particular message.
    """
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')
    bob = accounts.register(store, 'bob', 'secret12')
    administrator = _usable_admin(store)

    # a seat somebody else holds
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)
    held_by_player = _refusal(
        lambda: accounts.claim_seat(store, harness.repository(), bob,
                                    harness.gameno, 2))
    held_by_admin = _refusal(
        lambda: accounts.claim_seat(store, harness.repository(),
                                    administrator, harness.gameno, 2))
    assert held_by_admin == held_by_player
    assert store.read_membership(harness.gameno, 2) == ada.account_id

    # a number the game never registered
    assert (_refusal(lambda: accounts.claim_seat(
                store, harness.repository(), administrator, harness.gameno, 7))
            == _refusal(lambda: accounts.claim_seat(
                store, harness.repository(), bob, harness.gameno, 7)))
    assert store.read_membership(harness.gameno, 7) is None
    assert harness.repository().player_numbers() == [1, 2]

    # a number outside the player range at all
    assert (_refusal(lambda: accounts.claim_seat(
                store, harness.repository(), administrator,
                harness.gameno, identity.OBSERVER))
            == _refusal(lambda: accounts.claim_seat(
                store, harness.repository(), bob,
                harness.gameno, identity.OBSERVER)))


def test_the_administrator_is_refused_a_claim_after_a_turn_resolves(store,
                                                                    harness):
    harness.create(5, 5, [1, 2])
    harness.session(0).serverSave()
    _play_one_turn(harness)
    bob = accounts.register(store, 'bob', 'secret12')
    administrator = _usable_admin(store)

    started = _refusal(lambda: accounts.claim_seat(
        store, harness.repository(), administrator, harness.gameno, 2))

    assert started == _refusal(lambda: accounts.claim_seat(
        store, harness.repository(), bob, harness.gameno, 2))
    assert 'has started' in started


def test_the_administrator_gives_up_a_seat_on_the_same_terms(store, harness):
    harness.create(5, 5, [1, 2])
    administrator = _usable_admin(store)
    accounts.claim_seat(store, harness.repository(), administrator,
                        harness.gameno, 1)

    accounts.release_seat(store, harness.repository(), administrator,
                          harness.gameno, 1)

    assert store.read_membership(harness.gameno, 1) is None
    # and the seat is open to anybody, as giving one up leaves it
    ada = accounts.register(store, 'ada', 'secret12')
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 1)
    assert store.read_membership(harness.gameno, 1) == ada.account_id


def test_the_administrator_may_not_give_up_a_seat_it_does_not_hold(store,
                                                                   harness):
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)
    administrator = _usable_admin(store)

    with pytest.raises(NotAuthorised):
        accounts.release_seat(store, harness.repository(), administrator,
                              harness.gameno, 2)

    assert store.read_membership(harness.gameno, 2) == ada.account_id


def test_the_administrator_is_refused_a_release_after_a_turn_resolves(
        store, harness):
    """The refusal a player is given, given to the administrator too."""
    harness.create(5, 5, [1, 2])
    ada = accounts.register(store, 'ada', 'secret12')
    administrator = _usable_admin(store)
    accounts.claim_seat(store, harness.repository(), administrator,
                        harness.gameno, 1)
    accounts.claim_seat(store, harness.repository(), ada, harness.gameno, 2)
    harness.session(0).serverSave()
    _play_one_turn(harness)

    started = _refusal(lambda: accounts.release_seat(
        store, harness.repository(), administrator, harness.gameno, 1))

    assert started == _refusal(lambda: accounts.release_seat(
        store, harness.repository(), ada, harness.gameno, 2))
    assert 'has started' in started
    assert store.holds_seat(harness.gameno, 1, administrator.account_id)


# --- the observer holds a seat in no game
#
# The account is shared and `visibility` grants it every unit of every player,
# so a seat it held would be a seat played with the whole board in view by
# whoever knows the shared password.

def test_the_observer_may_not_claim_a_seat(store, harness):
    harness.create(5, 5, [1, 2])
    observer = store.read_account_by_name('observer')
    accounts.change_password(store, observer, 'observer', 'new-secret')
    observer = store.read_account_by_name('observer')

    with pytest.raises(NotAuthorised, match='holds a seat in none'):
        accounts.claim_seat(store, harness.repository(), observer,
                            harness.gameno, 1)

    assert store.read_membership(harness.gameno, 1) is None


def test_a_seat_row_does_not_make_the_observer_a_player(store, harness):
    """Defence in depth: a row written before the claim was refused.

    `claim_seat` refuses the observer, so no new row can appear. This is about
    a store as it is found rather than as it is written - the rule holds even
    where a row already exists.
    """
    harness.create(5, 5, [1, 2])
    observer = store.read_account_by_name('observer')
    store.claim_seat(harness.gameno, 1, observer.account_id)

    assert not accounts.may_act_as(store, observer, harness.gameno, 1)
    # and what it is entitled to is untouched
    assert accounts.may_act_as(store, observer, harness.gameno,
                               identity.OBSERVER)
