"""The catalogue and the array a game starts from.

A default that skipped the rules could hold a type no player could have
designed, and the first sign of it would be a game that could not be
committed. So the tables in `domain/army.py` are built through the ordinary
`UnitType` constructor and checked here, where a mistyped statistic fails at
once rather than reaching somebody's game.
"""

import math

from board_game_concept.domain import army, placement
from board_game_concept.domain.unit import UnitType


# name: attack, health, energy, cost, move fare
EXPECTED = {
    'Wall':   (0, 10,  0, 10, 3),
    'Scout':  (0,  2, 12, 14, 1),
    'Pawn':   (1,  4,  2,  7, 1),
    'Runner': (2,  4, 10, 16, 1),
    'Line':   (3,  6, 12, 21, 2),
    'Lance':  (8,  2, 10, 20, 1),
    'Keep':   (1, 10,  5, 16, 3),
    'Heavy':  (5, 10, 15, 30, 3),
}


def test_the_catalogue_holds_eight_types():
    assert sorted(army.types()) == sorted(EXPECTED)


def test_every_catalogue_type_is_one_the_rules_allow():
    """Built through the constructor, so its assertions are the check."""
    for name, record in army.types().items():
        assert isinstance(record['obj'], UnitType), name
        assert record['obj'].name == name


def test_the_catalogue_statistics_are_the_ones_published():
    for name, (attack, health, energy, _cost, _fare) in EXPECTED.items():
        record = army.types()[name]
        assert (record['attack'], record['health'], record['energy']) == (
            attack, health, energy), name


def test_each_type_costs_the_sum_of_its_statistics():
    for name, (_a, _h, _e, cost, _fare) in EXPECTED.items():
        assert army.types()[name]['obj'].cost == cost, name


def test_each_type_pays_the_move_fare_published_for_it():
    """A quarter of the type's health, rounded up, as for any type."""
    for name, (_a, health, _e, _cost, fare) in EXPECTED.items():
        unit_type = army.types()[name]['obj']
        assert unit_type.move_cost == fare, name
        assert fare == math.ceil(health / 4), name


def test_no_catalogue_type_is_drawn_as_an_empty_square():
    """A wall drawn as `#` is a wall its owner cannot see on their board.

    The Wall was `#` to begin with, which is the glyph `Empty` draws itself
    with, so `show board` rendered a wall and a bare square identically.
    """
    from board_game_concept.domain.square import Empty

    drawn = {record['symbol'] for record in army.types().values()}

    assert str(Empty()) not in drawn


def test_no_two_catalogue_types_share_a_symbol():
    drawn = [record['symbol'] for record in army.types().values()]
    assert sorted(drawn) == sorted(set(drawn))


def test_a_type_with_energy_can_afford_to_move():
    """The wall is the exception, and is meant to be: it cannot move at all."""
    for name, record in army.types().items():
        unit_type = record['obj']
        if unit_type.energy == 0:
            assert name == 'Wall'
            continue
        assert unit_type.energy >= unit_type.move_cost, name


# --- the array


def test_the_array_holds_sixteen_units():
    assert len(army.ARRAY) == 16


def test_the_array_costs_what_is_published():
    assert army.cost() == 242


def test_the_array_uses_only_catalogue_types():
    catalogue = army.types()
    for _depth, _x, type_name, _name in army.ARRAY:
        assert type_name in catalogue, type_name


def test_every_unit_of_the_array_is_named_once():
    names = [name for _depth, _x, _type, name in army.ARRAY]
    assert sorted(names) == sorted(set(names))


def test_no_two_units_of_the_array_share_a_square():
    squares = [(depth, x) for depth, x, _type, _name in army.ARRAY]
    assert sorted(squares) == sorted(set(squares))


def test_the_flag_stands_on_a_unit_the_array_deploys():
    names = [name for _depth, _x, _type, name in army.ARRAY]
    assert army.FLAG_UNIT in names


def test_the_array_is_symmetric_about_the_middle_of_the_board():
    """Whatever stands in column x stands in column 7 - x as well.

    A lopsided army reads as a mistake, and there is no reason for one flank
    to be stronger than the other before anybody has moved.
    """
    width = 8
    by_square = {(depth, x): type_name
                 for depth, x, type_name, _name in army.ARRAY}

    for (depth, x), type_name in by_square.items():
        mirrored = by_square.get((depth, width - 1 - x))
        assert mirrored == type_name, (depth, x, type_name, mirrored)


def test_the_array_fills_every_column_of_both_its_rows():
    """An army that leaves a column bare is not symmetric on the board."""
    for depth in (0, 1):
        columns = sorted(x for d, x, _t, _n in army.ARRAY if d == depth)
        assert columns == list(range(8)), depth


def test_the_array_shows_all_but_one_of_the_types_a_player_is_given():
    """Eight pairs of eight types cost 268, which no budget was covering.

    The Lance is the one left out: it is in the catalogue and a player may
    deploy as many as they like, but the opening array cannot hold one
    without giving up something and staying symmetric.
    """
    deployed = {type_name for _depth, _x, type_name, _name in army.ARRAY}

    assert deployed == set(army.types()) - {'Lance'}


# --- where it stands


def test_the_lower_numbered_player_starts_at_row_zero():
    assert army.rows_for(1, [1, 2], 8) == [0, 1]


def test_the_other_player_starts_at_the_last_row():
    assert army.rows_for(2, [1, 2], 8) == [7, 6]


def test_the_two_arrays_are_reflections_of_each_other():
    """Same columns, mirrored rows, as in chess."""
    mine = {(name, x, y) for _type, name, x, y
            in army.placements(1, [1, 2], 8, 8)}
    theirs = {(name, x, 7 - y) for _type, name, x, y
              in army.placements(2, [1, 2], 8, 8)}
    assert mine == theirs


def test_the_array_stands_inside_the_placement_area():
    for number in (1, 2):
        allowed = placement.rows(number, [1, 2], 8)
        for _type, name, x, y in army.placements(number, [1, 2], 8, 8):
            assert y in allowed, (number, name, y)
            assert 0 <= x < 8, (number, name, x)


def test_a_game_that_is_not_two_player_has_no_array():
    for players in ([1], [1, 2, 3], [1, 2, 3, 4]):
        assert army.placements(1, players, 8, 8) == [], players


def test_a_board_too_small_has_no_array():
    assert army.placements(1, [1, 2], 5, 5) == []
    assert army.placements(1, [1, 2], 4, 8) == [], 'too narrow'
    assert army.placements(1, [1, 2], 8, 2) == [], 'no depth to stand in'


def test_the_array_avoids_the_neutral_row():
    """An odd board leaves a middle row belonging to neither player."""
    for number in (1, 2):
        allowed = placement.rows(number, [1, 2], 9)
        middle = placement.neutral_row(9)
        for _type, name, _x, y in army.placements(number, [1, 2], 8, 9):
            assert y != middle, (number, name)
            assert y in allowed, (number, name, y)
