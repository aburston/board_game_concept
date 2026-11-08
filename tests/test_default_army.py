"""The catalogue and the array a game starts from.

A default that skipped the rules could hold a type no player could have
designed, and the first sign of it would be a game that could not be
committed. So the tables in `domain/army.py` are built through the ordinary
`UnitType` constructor and checked here, where a mistyped statistic fails at
once rather than reaching somebody's game.
"""

import math

from board_game_concept.domain import army, placement
from board_game_concept.domain.program import TICKS, Program, cap
from board_game_concept.domain.unit import UnitType

from game_harness import GameHarness


# name: attack, health, energy, compute, cost, move fare
EXPECTED = {
    'Wall':   (0, 10,  0, 0, 10, 3),
    'Scout':  (0,  2, 12, 6, 20, 1),
    'Pawn':   (1,  4,  2, 3, 10, 1),
    'Runner': (2,  4, 10, 5, 21, 1),
    'Line':   (3,  6, 12, 4, 25, 2),
    'Lance':  (8,  2, 10, 4, 24, 1),
    'Keep':   (1, 10,  5, 8, 24, 3),
    'Heavy':  (5, 10, 15, 4, 34, 3),
}


def test_the_catalogue_holds_eight_types():
    assert sorted(army.types()) == sorted(EXPECTED)


def test_every_catalogue_type_is_one_the_rules_allow():
    """Built through the constructor, so its assertions are the check."""
    for name, record in army.types().items():
        assert isinstance(record['obj'], UnitType), name
        assert record['obj'].name == name


def test_the_catalogue_statistics_are_the_ones_published():
    for name, (attack, health, energy, compute, _cost,
               _fare) in EXPECTED.items():
        record = army.types()[name]
        assert (record['attack'], record['health'], record['energy'],
                record['compute']) == (attack, health, energy, compute), name


def test_each_type_costs_the_sum_of_its_statistics():
    """All four of them: compute is bought like attack, health and energy."""
    for name, (_a, _h, _e, _c, cost, _fare) in EXPECTED.items():
        assert army.types()[name]['obj'].cost == cost, name


def test_each_type_pays_the_move_fare_published_for_it():
    """A quarter of the type's health, rounded up, as for any type."""
    for name, (_a, health, _e, _c, _cost, fare) in EXPECTED.items():
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
    assert army.cost() == 308


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


# --- the default programs


def test_every_default_program_parses():
    """A type with compute carries a program, and one without carries none."""
    for name, record in army.types().items():
        if record['compute'] == 0:
            assert record['program'] is None, name
            continue
        program = Program(record['program'])
        assert program.instructions, name


def a_stock_game(tmp_path):
    """Two unchanged stock armies, committed as seeded and played to the end."""
    harness = GameHarness(tmp_path)
    harness.create(army.DEFAULT_SIZE_X, army.DEFAULT_SIZE_Y, [1, 2])
    assert harness.session(1).clientSave()
    assert harness.session(2).clientSave()
    harness.play()
    return harness


def test_each_default_program_fits_its_cap_on_every_turn(tmp_path):
    """A controller that runs out of ticks gives no order, so a default
    program that overran its type's cap would field a unit that stands
    still on the turn it mattered. Every trace of a stock-army game is
    within the cap, and none was halted."""
    harness = a_stock_game(tmp_path)
    compute = {name: record['compute']
               for name, record in army.types().items()}
    type_of = {name: type_name for _depth, _x, type_name, name in army.ARRAY}
    repository = harness.repository()
    turns = repository.turn_numbers()
    assert turns[-1] >= 2
    seen = set()
    for turn in turns:
        for trace in repository.read_turn(turn)['traces']:
            limit = cap(compute[type_of[trace['unit']]])
            assert trace['ticks'] <= limit, (turn, trace)
            # a controller is also stopped where the meter would take energy
            # its unit no longer has, which a spent unit comes to late in a
            # game; the cap stops one only in the last few ticks before it
            if trace['halted'] is not None:
                assert trace['ticks'] <= limit - max(TICKS.values()), (
                    turn, trace)
            seen.add(type_of[trace['unit']])
    # every thinking type the array fields was seen thinking; the Lance is
    # in the catalogue and not in the array
    fielded = {type_name for _depth, _x, type_name, _name in army.ARRAY}
    assert seen == {name for name, c in compute.items()
                    if c > 0 and name in fielded}


# --- the default plays


def test_a_hunter_blocked_both_ways_sleeps_rather_than_holds():
    """A hunter that finds one of its own on both ways round has run most of
    its program to find out; it rests the turn rather than pay to hold."""
    from board_game_concept.domain.army_map import ArmyMap
    from board_game_concept.domain.program import Program, Snapshot, run
    program = Program(army.types()['Runner']['program'])
    # me at (2, 0), the flag at (3, 7): the column is blocked by wall1 at
    # (2, 1) and the row by keep1 at (3, 0), as the old array stood
    snap = Snapshot(2, 8, 8, 1, {'me': (2, 0), 'wall1': (2, 1),
                                 'keep1': (3, 0)},
                    {1: (3, 0), 2: (3, 7)}, ArmyMap())
    me = {'x': 2, 'y': 0, 'health': 4, 'energy': 10, 'flag': False,
          'number': 0}
    result = run(program, snap, me, None, {}, [], 5, 10, 0)
    assert result.order is None
    assert result.sleep == 1


def test_the_whole_army_gets_out(tmp_path):
    """In the mirror of two unchanged arrays every unit with a controller
    but the Keeps leaves the square it was seeded on inside twenty turns of
    play: the front rank goes, and nothing behind it is boxed in."""
    harness = a_stock_game(tmp_path)
    repository = harness.repository()
    seeded = {}
    for unit in repository.read_turn(1)['units']:
        seeded[(unit['player'], unit['name'])] = (unit['x'], unit['y'])
    moved = set()
    for turn in repository.turn_numbers():
        if turn > 21:
            break
        for unit in repository.read_turn(turn)['units']:
            key = (unit['player'], unit['name'])
            if key in seeded and (unit['x'], unit['y']) != seeded[key]:
                moved.add(key)
        for entry in repository.read_turn(turn)['events']:
            if entry['kind'] == 'destroyed':
                # a unit destroyed where it was seeded is not boxed in
                moved |= {key for key in seeded
                          if key[1] == entry['detail'].get('unit')}
    expected = {(player, name) for player in (1, 2)
                for _depth, _x, type_name, name in army.ARRAY
                if type_name not in ('Wall', 'Keep')}
    assert expected <= moved, sorted(expected - moved)


def test_a_scout_goes_round_an_enemy_it_knows_of_rather_than_into_it():
    """A Scout strikes nothing, so a step onto a known enemy is a contest
    it cannot win and a fare for nothing: two Scouts facing each other
    across the frontier used to bump for fifty turns until the quiet stop
    took the game. The explorer goes round what its map shows."""
    from board_game_concept.domain.army_map import ArmyMap
    from board_game_concept.domain.program import Program, Snapshot, run
    program = Program(army.types()['Scout']['program'])
    known = ArmyMap()
    # everything round me is known but the row beyond the enemy
    for x in range(8):
        for y in range(0, 4):
            known.visited[(x, y)] = 1
    known.enemies[(1, 4)] = (60, 0, 2)
    snap = Snapshot(61, 8, 8, 1, {'me': (1, 3)}, {1: (3, 0), 2: (3, 7)},
                    known)
    me = {'x': 1, 'y': 3, 'health': 2, 'energy': 2, 'flag': False,
          'number': 0}
    result = run(program, snap, me, None, {}, [], 6, 2, 0)
    # the nearest unknown is (1, 4) itself or the square beyond; either way
    # the step is not south onto the enemy
    assert result.order != 3, result
    assert result.halted is None


def test_the_mirror_comes_out_a_mirror(tmp_path):
    """Two unchanged arrays face each other across the board, and nothing
    in the rules or the programs tells north from south: every turn of the
    record is its own reflection, unit for unit, to the end."""
    harness = a_stock_game(tmp_path)
    repository = harness.repository()
    size_y = army.DEFAULT_SIZE_Y
    for turn in repository.turn_numbers():
        units = {}
        for unit in repository.read_turn(turn)['units']:
            units[(unit['player'], unit['name'])] = unit
        for (player, name), unit in units.items():
            other = units[(3 - player, name)]
            assert unit.get('destroyed') == other.get('destroyed'), (turn, name)
            if unit.get('destroyed'):
                continue
            assert (unit['x'], unit['y']) == (other['x'], size_y - 1 - other['y']), (turn, name)
            assert (unit['health'], unit['energy']) == (other['health'], other['energy']), (turn, name)
