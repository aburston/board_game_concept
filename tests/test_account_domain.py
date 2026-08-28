"""What an account is, before anything stores one.

The rules a username and a password must satisfy, tested against the domain
directly, with no database and no server - the same way `test_point_budget.py`
tests the budget arithmetic against a board.
"""

import pytest

from board_game_concept.domain import Account, Kind
from board_game_concept.domain import account as account_rules


def test_the_three_kinds_are_distinct():
    assert len(set(Kind.ALL)) == 3
    assert Kind.ADMINISTRATOR in Kind.ALL
    assert Kind.OBSERVER in Kind.ALL
    assert Kind.PLAYER in Kind.ALL


def test_an_account_is_exactly_one_kind():
    administrator = Account('admin', 'hash', Kind.ADMINISTRATOR)
    observer = Account('observer', 'hash', Kind.OBSERVER)
    player = Account('ada', 'hash', Kind.PLAYER)

    assert administrator.is_administrator()
    assert not administrator.is_observer()
    assert observer.is_observer()
    assert not observer.is_administrator()
    assert not player.is_administrator()
    assert not player.is_observer()


def test_an_account_cannot_be_a_kind_that_is_not_one():
    with pytest.raises(AssertionError):
        Account('ada', 'hash', 'wizard')


@pytest.mark.parametrize('name', ['admin', 'Admin', 'ADMIN', 'aDmIn',
                                  'observer', 'Observer', 'OBSERVER'])
def test_reserved_names_are_refused_in_any_case(name):
    refusal = account_rules.username_refusal(name)
    assert refusal is not None
    assert 'reserved' in refusal


def test_an_ordinary_name_is_allowed():
    assert account_rules.username_refusal('ada') is None
    assert account_rules.username_refusal('reaper-bot') is None


def test_a_name_differing_only_in_case_is_the_same_name():
    assert account_rules.normalise('Ada') == account_rules.normalise('ada')
    assert account_rules.normalise('  ADA  ') == 'ada'


def test_an_empty_or_shapeless_name_is_refused():
    assert account_rules.username_refusal('') is not None
    assert account_rules.username_refusal('   ') is not None
    assert account_rules.username_refusal(None) is not None
    assert account_rules.username_refusal('a da') is not None
    assert account_rules.username_refusal(
        'a' * (account_rules.MAX_USERNAME + 1)) is not None


def test_the_stored_name_keeps_its_case_and_compares_without_it():
    account = Account('Ada', 'hash', Kind.PLAYER)
    assert account.username == 'Ada'
    assert account.key == 'ada'


def test_a_password_of_seven_is_refused_and_eight_is_not():
    seven = account_rules.password_refusal('1234567')
    assert seven is not None
    assert str(account_rules.MIN_PASSWORD) in seven
    assert account_rules.password_refusal('12345678') is None


def test_no_composition_rule_is_imposed():
    assert account_rules.password_refusal('aaaaaaaa') is None
    assert account_rules.password_refusal('        ') is None


def test_a_password_that_is_not_a_string_is_refused():
    assert account_rules.password_refusal(None) is not None
    assert account_rules.password_refusal(12345678) is not None


def test_the_domain_hashes_nothing():
    """The hash is `storage/`'s to make; this class only carries one."""
    account = Account('ada', 'already-a-hash', Kind.PLAYER)
    assert account.password_hash == 'already-a-hash'
