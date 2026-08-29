"""Where a player may deploy during setup, as the rule itself answers it.

A two-player game gives each player half the board to form up in, split by
rows, and leaves the middle row neutral where the row count is odd. Every
other player count is the null case of the same rule: the whole board, reached
through the same calls, so a game that is not two-player behaves exactly as it
did before the rule existed.

These test the rule directly. `test_placement_over_http.py` holds the served
contract to it, and `test_placement_refusals.py` the two places a deployment
is refused.
"""

import pytest

from board_game_concept.domain import placement


# --- the two-player split


@pytest.mark.parametrize('size_y, top, bottom, neutral', [
    (2, [0], [1], None),
    (3, [0], [2], 1),
    (4, [0, 1], [2, 3], None),
    (5, [0, 1], [3, 4], 2),
    (8, [0, 1, 2, 3], [4, 5, 6, 7], None),
    (9, [0, 1, 2, 3], [5, 6, 7, 8], 4),
    (10, [0, 1, 2, 3, 4], [5, 6, 7, 8, 9], None),
])
def test_two_players_split_the_rows_between_them(size_y, top, bottom, neutral):
    assert placement.rows(1, [1, 2], size_y) == top
    assert placement.rows(2, [1, 2], size_y) == bottom
    assert placement.neutral_row(size_y) == neutral


def test_the_lower_number_takes_the_top_whatever_the_numbers_are():
    """Which half is whose is the order of the two numbers, not their value."""
    for lower, higher in ((1, 2), (2, 5), (3, 7), (17, 900)):
        assert placement.rows(lower, [lower, higher], 6) == [0, 1, 2]
        assert placement.rows(higher, [lower, higher], 6) == [3, 4, 5]
        # and the order they are given in makes no difference
        assert placement.rows(lower, [higher, lower], 6) == [0, 1, 2]


def test_an_odd_board_leaves_exactly_the_middle_row_to_nobody():
    top = placement.rows(1, [1, 2], 7)
    bottom = placement.rows(2, [1, 2], 7)
    assert placement.neutral_row(7) == 3
    assert 3 not in top and 3 not in bottom
    # and every other row belongs to one of them
    assert sorted(top + bottom + [3]) == list(range(7))


def test_an_even_board_has_no_neutral_row_and_the_halves_meet():
    top = placement.rows(1, [1, 2], 6)
    bottom = placement.rows(2, [1, 2], 6)
    assert placement.neutral_row(6) is None
    assert sorted(top + bottom) == list(range(6))
    assert top[-1] + 1 == bottom[0], 'the halves meet'


def test_columns_are_never_restricted():
    """A half is the full width: only the row decides."""
    for x in range(5):
        assert placement.allows(1, [1, 2], x, 0, 5, 4) is True
        assert placement.allows(1, [1, 2], x, 3, 5, 4) is False


# --- the null case: every other player count is the whole board


@pytest.mark.parametrize('numbers', [
    [1],
    [1, 2, 3],
    [1, 2, 3, 4],
    [2, 5, 9],
])
def test_a_game_that_is_not_two_player_is_unrestricted(numbers):
    for number in numbers:
        assert placement.rows(number, numbers, 5) == [0, 1, 2, 3, 4]
        for y in range(5):
            assert placement.allows(number, numbers, 0, y, 4, 5) is True
            assert placement.refusal(number, numbers, 0, y, 4, 5) is None


def test_a_game_that_is_not_two_player_has_no_neutral_row():
    """The neutral row is part of the two-player split, not a rule of its own.

    An odd board in a three-player game has every row in play, which is what
    it had before this rule existed.
    """
    for numbers in ([1], [1, 2, 3]):
        assert placement.area(1, numbers, 4, 5)['neutral_row'] is None
        assert placement.allows(1, numbers, 0, 2, 4, 5) is True


def test_a_session_that_is_not_placing_is_told_the_whole_board():
    """The observer and the administrator watch rather than place."""
    for number in (0, 1000):
        assert placement.rows(number, [1, 2], 5) == [0, 1, 2, 3, 4]
        assert placement.area(number, [1, 2], 4, 5)['restricted'] is False


# --- the published area


def test_the_area_names_the_board_and_the_rows_this_seat_may_use():
    assert placement.area(1, [1, 2], 4, 5) == {
        'size_x': 4, 'size_y': 5, 'rows': [0, 1],
        'neutral_row': 2, 'restricted': True,
    }
    assert placement.area(2, [1, 2], 4, 5) == {
        'size_x': 4, 'size_y': 5, 'rows': [3, 4],
        'neutral_row': 2, 'restricted': True,
    }


def test_an_unrestricted_area_says_so():
    area = placement.area(1, [1, 2, 3], 4, 5)
    assert area['rows'] == [0, 1, 2, 3, 4]
    assert area['restricted'] is False


def test_the_published_area_is_exactly_what_is_allowed():
    """What must never drift: what is shown and what is enforced."""
    for numbers in ([1, 2], [1], [1, 2, 3], [4, 6]):
        for size_y in range(2, 11):
            for number in numbers:
                area = placement.area(number, numbers, 4, size_y)
                allowed = set(area['rows'])
                for y in range(size_y):
                    assert (y in allowed) == placement.allows(
                        number, numbers, 0, y, 4, size_y), (
                            numbers, number, size_y, y)


def test_the_same_game_answers_the_same_every_time():
    """A pure function of the board size and the players: nothing is stored."""
    first = placement.area(1, [1, 2], 6, 7)
    again = placement.area(1, [2, 1], 6, 7)
    assert first == again


# --- what a refusal says


def test_a_square_in_the_other_half_is_refused_as_the_other_half():
    said = placement.refusal(1, [1, 2], 0, 4, 4, 5)
    assert said is not None
    assert "other player's half" in said


def test_the_neutral_row_is_refused_as_the_neutral_row():
    said = placement.refusal(1, [1, 2], 0, 2, 4, 5)
    assert said is not None
    assert 'neutral row' in said


def test_a_square_in_your_own_half_is_not_refused():
    assert placement.refusal(1, [1, 2], 0, 1, 4, 5) is None
    assert placement.refusal(2, [1, 2], 3, 4, 4, 5) is None


def test_a_square_off_the_board_is_not_allowed():
    assert placement.allows(1, [1, 2, 3], 0, 5, 4, 5) is False
    assert placement.allows(1, [1, 2, 3], -1, 0, 4, 5) is False


def test_a_square_off_the_board_is_not_this_rule_to_refuse():
    """It is out of bounds, and saying "the other half" names the wrong thing."""
    assert placement.refusal(1, [1, 2], 0, 9, 4, 4) is None
    assert placement.refusal(1, [1, 2], -1, 0, 4, 4) is None
