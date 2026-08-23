"""Who the numbers in a game belong to.

The boundaries are what these assert - 0, 1, 999, 1000 - rather than the middle,
so that the numbers in `player-numbering` and the numbers in the code cannot be
changed apart from each other without something failing.
"""

import pytest

from board_game_concept.domain import Player
from board_game_concept.service import identity


# --- what a player's number may be


@pytest.mark.parametrize('number', [Player.FIRST, 2, 500, Player.LAST])
def test_a_player_may_have_a_number_in_range(number):
    assert Player(number).number == number
    assert identity.is_player(number)


@pytest.mark.parametrize('number', [-1, 0, 1000, 1001, 1000000])
def test_a_player_may_not_have_a_number_out_of_range(number):
    with pytest.raises(AssertionError):
        Player(number)
    assert not identity.is_player(number)


def test_the_range_is_the_one_the_spec_names():
    assert (Player.FIRST, Player.LAST) == (1, 999)


def test_a_player_number_must_still_be_a_whole_number():
    for number in ('1', 1.5, None):
        with pytest.raises(AssertionError):
            Player(number)
        assert not identity.is_player(number)


# --- the three identities


def test_the_reserved_numbers_are_the_ones_the_spec_names():
    assert identity.ADMINISTRATOR == 0
    assert identity.OBSERVER == 1000


def test_a_reserved_number_is_not_a_player():
    for number in identity.RESERVED:
        assert not identity.is_player(number)


def test_no_two_identities_are_the_same():
    assert identity.ADMINISTRATOR != identity.OBSERVER
    assert not identity.is_player(identity.ADMINISTRATOR)
    assert not identity.is_player(identity.OBSERVER)


@pytest.mark.parametrize('number', [-1, 1001, 1000000])
def test_a_number_outside_them_all_identifies_nobody(number):
    assert not identity.identifies_anyone(number)


@pytest.mark.parametrize('number', [0, 1, 999, 1000])
def test_every_number_the_game_uses_identifies_somebody(number):
    assert identity.identifies_anyone(number)


# --- what each identity is entitled to


def test_both_reserved_identities_see_the_whole_game():
    """The reason this is a question and not a comparison with zero."""
    assert identity.sees_everything(identity.ADMINISTRATOR)
    assert identity.sees_everything(identity.OBSERVER)


@pytest.mark.parametrize('number', [1, 500, 999])
def test_a_player_does_not_see_the_whole_game(number):
    assert not identity.sees_everything(number)


def test_only_the_observer_may_not_change_a_game():
    assert not identity.may_change(identity.OBSERVER)
    # the administrator sets a game up and commits it, so it may
    assert identity.may_change(identity.ADMINISTRATOR)
    for number in (1, 500, 999):
        assert identity.may_change(number)


def test_an_identity_says_what_it_is_called():
    assert identity.describe(0) == 'the administrator'
    assert identity.describe(1000) == 'the observer'
    assert identity.describe(7) == 'player 7'


def test_a_reserved_number_is_refused_as_reserved_and_not_as_out_of_range():
    """The two are different mistakes and deserve different messages."""
    assert 'reserved' in identity.out_of_range(0)
    assert 'reserved' in identity.out_of_range(1000)
    assert 'reserved' not in identity.out_of_range(1001)
    assert '999' in identity.out_of_range(1001)
