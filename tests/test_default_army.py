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


# --- the programs restated with subroutines give the same orders

OLD_HUNTER = '\n; hunt: walk at the nearest enemy flag, round my own units\nSELF                 ; r0 x, r1 y, r3 energy\nMOV r6, r0\nMOV r7, r1\nSUB r3, {need}       ; a step and a strike\nJIF neg r3, rest\n{target}             ; r0, r1 = where to go, or -1\nJIF neg r0, rest\nSUB r0, r6           ; dx\nSUB r1, r7           ; dy\nMOV r4, r0\nMOV r5, r1\nSIGN r4              ; which way along the row, or 0\nSIGN r5              ; which way down the column, or 0\nABS r0\nABS r1\nJIF lt r0, r1, vfirst\nMOV r2, r6           ; along the row first: what stands where I would step\nADD r2, r4\nMAP r2, r7           ; 2 is one of mine - or my own square, when dx is 0\nSUB r0, 2\nJIF zero r0, vonly\nJIF pos r4, east\nMOVE west\nHALT\neast: MOVE east\nHALT\nvfirst: MOV r2, r7   ; down the column first\nADD r2, r5\nMAP r6, r2\nSUB r0, 2\nJIF zero r0, honly\nJIF pos r5, south\nMOVE north\nHALT\nsouth: MOVE south\nHALT\nvonly: MOV r2, r7    ; the row is blocked: the column, if it is clear\nADD r2, r5\nMAP r6, r2\nSUB r0, 2\nJIF zero r0, stay\nJIF pos r5, south\nMOVE north\nHALT\nhonly: MOV r2, r6    ; the column is blocked: the row, if it is clear\nADD r2, r4\nMAP r2, r7\nSUB r0, 2\nJIF zero r0, stay\nJIF pos r4, east\nMOVE west\nHALT\nstay: SLEEP 1        ; both ways stand one of mine: rest until one moves\nrest: SLEEP 1\n'
OLD_EXPLORER = '\n; explore: walk at the nearest unknown square, round what is in the way\nSELF                 ; r0 x, r1 y, r3 energy\nMOV r6, r0\nMOV r7, r1\nSUB r3, {need}\nJIF neg r3, rest\nNEAREST unknown      ; r0, r1 = where, r2 = how far, or -1\nJIF neg r0, none\nMOV r4, r0\nMOV r5, r1\nLOAD r3, 1           ; the nearest I have been to one, or 0 at the start\nJIF zero r3, nearer\nJIF lt r2, r3, nearer\nLOAD r3, 2           ; turns without getting nearer\nADD r3, 1\nSTORE r3, 2\nSET r0, 20\nJIF lt r0, r3, none  ; too long: it is behind something I cannot pass\nJMP go\nnearer: STORE r2, 1\nSET r3, 0\nSTORE r3, 2\ngo: SUB r4, r6       ; dx\nSUB r5, r7           ; dy\nSIGN r4\nSIGN r5\nMOV r2, r7           ; first: down the column towards it\nADD r2, r5\nMAP r6, r2           ; r0 = what stands there: 0 unknown, 1 empty\nSET r3, 2\nJIF lt r0, r3, gocol\nMOV r2, r6           ; second: along the row towards it\nADD r2, r4\nMAP r2, r7\nSET r3, 2\nJIF lt r0, r3, gorow\nMOV r2, r6           ; third: a step aside, east\nADD r2, 1\nMAP r2, r7\nSET r3, 2\nJIF lt r0, r3, goeast\nMOV r2, r6           ; fourth: a step aside, west\nSUB r2, 1\nMAP r2, r7\nSET r3, 2\nJIF lt r0, r3, gowest\nJMP rest             ; nowhere to step this turn\ngocol: SET r0, 2\nADD r0, r5\nMOVE r0\nHALT\ngorow: SET r0, 3\nSUB r0, r4\nMOVE r0\nHALT\ngoeast: MOVE east\nHALT\ngowest: MOVE west\nHALT\nnone: SLEEP 100      ; nothing left to find that I can reach\nrest: SLEEP 1\n'


def _snapshots():
    """Boards a hunter and an explorer meet: open, a friend ahead, an enemy
    ahead, both ways blocked, nothing to go at."""
    from board_game_concept.domain.army_map import ArmyMap
    from board_game_concept.domain.program import Snapshot
    me = {'x': 2, 'y': 2, 'health': 4, 'energy': 10, 'flag': False,
          'number': 0}
    flags = {1: (3, 0), 2: (3, 7)}
    cases = []
    cases.append(Snapshot(5, 8, 8, 1, {'me': (2, 2)}, flags, ArmyMap()))
    cases.append(Snapshot(5, 8, 8, 1, {'me': (2, 2), 'a': (2, 3)}, flags,
                          ArmyMap()))
    met = ArmyMap(); met.enemies[(2, 3)] = (4, 5, 10)
    cases.append(Snapshot(5, 8, 8, 1, {'me': (2, 2)}, flags, met))
    cases.append(Snapshot(5, 8, 8, 1, {'me': (2, 2), 'a': (2, 3),
                                       'b': (3, 2)}, flags, ArmyMap()))
    known = ArmyMap()
    for x in range(8):
        for y in range(8):
            known.visited[(x, y)] = 1
    cases.append(Snapshot(5, 8, 8, 1, {'me': (2, 2)}, flags, known))
    cases.append(Snapshot(5, 8, 8, 1, {'me': (2, 2)}, {1: (3, 0)},
                          ArmyMap()))
    return me, cases


def test_the_hunter_with_a_subroutine_gives_the_same_orders():
    from board_game_concept.domain.program import Program, run
    old = Program(OLD_HUNTER.format(need=3, target='FLAG enemy'))
    new = Program(army.types()['Runner']['program'])
    me, cases = _snapshots()
    for snap in cases:
        before = run(old, snap, me, None, {}, [], 5, 10, 0)
        after = run(new, snap, me, None, {}, [], 5, 10, 0)
        assert (before.order, before.sleep) == (after.order, after.sleep)
        assert after.halted is None


def test_the_explorer_with_a_subroutine_gives_the_same_orders():
    from board_game_concept.domain.program import Program, run
    old = Program(OLD_EXPLORER.format(need=1))
    new = Program(army.types()['Scout']['program'])
    me, cases = _snapshots()
    for snap in cases:
        memory_old, memory_new = {}, {}
        for _turn in range(3):
            before = run(old, snap, me, None, memory_old, [], 6, 12, 0)
            after = run(new, snap, me, None, memory_new, [], 6, 12, 0)
            assert (before.order, before.sleep) == (after.order, after.sleep)
            assert memory_old == memory_new
            assert after.halted is None


# --- the doctrine of each default program
#
# What the catalogue says each program does, held on hand-built boards. The
# programs are written for readability first and may change their shape, so
# the bar is the doctrine and not the instruction stream: these are what a
# rewrite has to pass, and they were written against the programs they
# replaced before anything was rewritten.


def think(type_name, square, *, friends=(), enemies=(), visited=(),
          flags=None, energy=None, memory=None, turn=5):
    """Run a catalogue type's program once for a unit of player 1 standing
    on `square` of an 8 by 8 board, against what its army knows."""
    from board_game_concept.domain.army_map import ArmyMap
    from board_game_concept.domain.program import Program, Snapshot, run
    record = army.types()[type_name]
    program = Program(record['program'])
    known = ArmyMap()
    for x, y in visited:
        known.visited[(x, y)] = 1
    for x, y in enemies:
        known.enemies[(x, y)] = (turn - 1, 3, 6)
    allies = {'me': square}
    allies.update({f'friend{i}': at for i, at in enumerate(friends)})
    snap = Snapshot(turn, 8, 8, 1, allies,
                    {1: (3, 0), 2: (3, 7)} if flags is None else flags,
                    known)
    me = {'x': square[0], 'y': square[1], 'health': record['health'],
          'energy': record['energy'] if energy is None else energy,
          'flag': False, 'number': 0}
    memory = {} if memory is None else memory
    result = run(program, snap, me, None, memory, [], record['compute'],
                 me['energy'], 0)
    assert result.halted is None, result.halted
    return result, memory


NORTH, EAST, SOUTH, WEST = 1, 2, 3, 4


class TestTheHunter:
    """Walks at the nearest enemy flag, round its own units, fighting what it
    meets; sleeps when it cannot afford a step and a strike, or when both
    ways round stand its own."""

    def test_an_open_way_steps_towards_the_flag(self):
        for type_name in ('Runner', 'Line', 'Lance', 'Heavy'):
            result, _ = think(type_name, (2, 2))
            assert result.order == SOUTH, type_name
            assert result.sleep is None

    def test_a_friend_ahead_is_stepped_round(self):
        result, _ = think('Runner', (2, 2), friends=[(2, 3)])
        assert result.order == EAST

    def test_both_ways_blocked_sleeps_a_turn(self):
        result, _ = think('Runner', (2, 2), friends=[(2, 3), (3, 2)])
        assert result.order is None and result.sleep == 1

    def test_too_poor_for_a_step_and_a_strike_sleeps_a_turn(self):
        for type_name, need in (('Runner', 3), ('Line', 5), ('Lance', 9),
                                ('Heavy', 8)):
            result, _ = think(type_name, (2, 2), energy=need - 1)
            assert result.order is None and result.sleep == 1, type_name
            result, _ = think(type_name, (2, 2), energy=need)
            assert result.order == SOUTH, type_name

    def test_no_enemy_flag_left_sleeps(self):
        result, _ = think('Runner', (2, 2), flags={1: (3, 0)})
        assert result.order is None and result.sleep == 1

    def test_an_enemy_in_the_way_is_walked_into(self):
        """Fighting what it meets: a known enemy is not something to avoid."""
        result, _ = think('Runner', (2, 2), enemies=[(2, 3)])
        assert result.order == SOUTH


class TestTheExplorer:
    """Walks at the nearest unknown square onto unknown or empty squares
    only, a step aside when the way is blocked; sleeps when there is nothing
    left to find, or when twenty turns have not brought it nearer."""

    ROWS_0_TO_2 = [(x, y) for x in range(8) for y in range(3)]

    def test_an_unknown_square_is_walked_at(self):
        result, _ = think('Scout', (2, 2), visited=self.ROWS_0_TO_2)
        assert result.order == SOUTH

    def test_a_blocked_way_means_a_step_aside(self):
        result, _ = think('Scout', (2, 2), visited=self.ROWS_0_TO_2,
                          friends=[(2, 3)])
        assert result.order in (EAST, WEST)

    def test_it_never_steps_onto_a_known_enemy_or_its_own(self):
        result, _ = think('Scout', (2, 2), visited=self.ROWS_0_TO_2,
                          friends=[(2, 3)], enemies=[(3, 2)])
        assert result.order == WEST

    def test_nowhere_to_step_rests_a_turn(self):
        result, _ = think('Scout', (2, 2), visited=self.ROWS_0_TO_2,
                          friends=[(2, 3), (3, 2), (1, 2)])
        assert result.order is None and result.sleep == 1

    def test_nothing_left_to_find_sleeps_long(self):
        everywhere = [(x, y) for x in range(8) for y in range(8)]
        result, _ = think('Scout', (2, 2), visited=everywhere)
        assert result.order is None and result.sleep == 100

    def test_too_poor_for_a_step_sleeps_a_turn(self):
        result, _ = think('Scout', (2, 2), energy=0)
        assert result.order is None and result.sleep == 1

    def test_twenty_turns_without_getting_nearer_gives_up(self):
        memory = None
        for turn in range(22):
            result, memory = think('Scout', (2, 2), visited=self.ROWS_0_TO_2,
                                   friends=[(2, 3), (3, 2), (1, 2)],
                                   memory=memory, turn=turn + 1)
            if result.sleep == 100:
                break
        else:
            raise AssertionError('never gave up')
        assert 19 <= turn <= 21

    def test_getting_nearer_starts_the_count_again(self):
        """Nineteen turns stalled, then a turn that brings it nearer than it
        has been: it steps, and the count starts from nothing."""
        memory = {1: 3, 2: 19}
        result, memory = think('Scout', (2, 2), visited=self.ROWS_0_TO_2,
                               memory=memory)
        assert result.order == SOUTH
        assert memory[1] == 1 and memory[2] == 0


class TestTheVanguard:
    """Steps towards the enemy's edge when it can afford a step and a strike,
    never onto one of its own; sleeps a turn otherwise."""

    def test_it_steps_at_the_enemy_edge(self):
        result, _ = think('Pawn', (1, 1))
        assert result.order == SOUTH

    def test_too_poor_sleeps_a_turn(self):
        result, _ = think('Pawn', (1, 1), energy=1)
        assert result.order is None and result.sleep == 1

    def test_one_of_its_own_in_front_means_waiting(self):
        result, _ = think('Pawn', (1, 1), friends=[(1, 2)])
        assert result.order is None and result.sleep == 1

    def test_at_the_enemy_edge_it_waits(self):
        result, _ = think('Pawn', (1, 7))
        assert result.order is None and result.sleep == 1

    def test_an_enemy_in_front_is_walked_into(self):
        result, _ = think('Pawn', (1, 1), enemies=[(1, 2)])
        assert result.order == SOUTH


class TestTheWarden:
    """Holds its square, sleeping a hundred turns at a time."""

    def test_it_sleeps_a_hundred_turns(self):
        result, _ = think('Keep', (3, 0))
        assert result.order is None and result.sleep == 100


# --- the default programs read as words

import re


def own_lines(text):
    """A program's own instruction lines: no directives, comments or blanks."""
    lines = []
    continuing = False
    for raw in text.splitlines():
        line = raw.split(';', 1)[0].rstrip()
        if continuing or line.lstrip().startswith('#'):
            continuing = line.endswith('\\')
            continue
        if line.strip():
            lines.append(line.strip())
    return lines


def test_every_default_program_reads_as_words():
    """Each includes the unit header, names its registers and constants, and
    names no direction or map answer by number."""
    for name, record in army.types().items():
        text = record['program']
        if text is None:
            continue
        assert '#include <unit.h>' in text, name
        for line in own_lines(text):
            # no raw register: every one the program keeps a value in has a
            # name, given by a #define
            assert not re.search(r'\br[0-7]\b', line), (name, line)
            # no direction by number
            assert not re.search(r'\bMOVE\s+\d', line), (name, line)
            # no map answer or direction as a bare number against what MAP
            # or SELF answered: SET, SUB and ADD with a literal are left to
            # counting, as `ADD look_x, 1` is
            assert not re.search(r'\b(SUB|SET)\s+\w+,\s*[2-4]\b', line), (
                name, line)


def test_a_player_can_copy_a_default_program_onto_their_own_type(tmp_path):
    """What a catalogue type's program reads back as can be set, as it
    stands, on a type of the player's own, and thinks as the catalogue's."""
    from board_game_concept.service import games
    from board_game_concept.service.commands import AddType, SetProgram
    from board_game_concept.service.replay import program_view
    harness = GameHarness(tmp_path)
    harness.create(army.DEFAULT_SIZE_X, army.DEFAULT_SIZE_Y, [1, 2])
    session = harness.session(1)
    shown = program_view(session.getPlayers()[1]['types']['Runner'])
    games.perform(session, AddType(name='Hound', symbol='h', attack=2,
                                   health=4, energy=10, compute=5))
    games.perform(session, SetProgram(type_name='Hound',
                                      program=shown['program']))
    mine = session.getPlayers()[1]['types']['Hound']
    assert mine['program'] == shown['program']
    assert (program_view(mine)['total'] == shown['total']
            and shown['total'] > 0)
    assert Program(mine['program']).instructions == Program(
        army.types()['Runner']['program']).instructions
