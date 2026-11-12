"""Every unit standing on the board gets REST_GAIN energy back each turn.

Energy used to be spent and never replenished, which is what made an
exhausted unit a permanent obstacle and every game a race to the bottom of
two pockets. Then it came back one a turn, and only on a turn the unit did
nothing, which made every programmed unit sleep to afford its next step. Now
the recovery is unconditional: whatever a unit did during the turn, it
recovers the same amount, and never past the energy its type was designed
with (R3.9).

The board is driven directly here, as `test_think_phase.py` drives it, so
that a unit's energy can be set by hand before a turn; `GameHarness` reloads
every session from storage and would not keep such a change.
"""

from board_game_concept.domain import Player, UnitType

from game_harness import GameHarness
from test_think_phase import setup, unit

PAWN = UnitType('P', 'p', 1, 2, 10)          # a fare of one a square
QUIET = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')


def rested(events, name):
    return [e for e in events if e.kind == 'rested'
            and e.detail['unit'] == name]


def a_pair(mine=PAWN, theirs=QUIET, where=(0, 0), their_square=(7, 7)):
    board, players = setup((1, [(mine, [('x1', *where)])]),
                           (2, [(theirs, [('o1', *their_square)])]))
    return board, players, unit(board, players, 1, 'x1')


def test_the_gain_is_two():
    assert UnitType.REST_GAIN == 2


def test_a_unit_given_no_order_recovers_two():
    board, players, me = a_pair()
    me.energy = 4
    board.commit(turn=1)
    assert me.energy == 6
    board.commit(turn=2)
    assert me.energy == 8


def test_resting_never_passes_the_energy_the_type_was_designed_with():
    board, players, me = a_pair()
    me.energy = 7
    for turn in range(1, 6):
        board.commit(turn=turn)
    assert me.energy == 10


def test_a_unit_at_full_energy_is_not_reported_as_rested():
    board, players, me = a_pair()
    events = board.commit(turn=1)
    assert not [e for e in events if e.kind == 'rested'], (
        'a full army at rest is not a line per unit per turn')


def test_a_unit_one_short_recovers_to_full_and_is_reported():
    board, players, me = a_pair()
    me.energy = 9
    events = board.commit(turn=1)
    assert me.energy == 10
    assert [e.detail['energy'] for e in rested(events, 'x1')] == [10]


def test_a_unit_that_moved_recovers_two_less_the_fare():
    # health 2 is a fare of one a square: each step costs one and the turn
    # gives two back, so a walking unit climbs by one a turn
    board, players, me = a_pair()
    me.energy = 4
    me.move(UnitType.EAST)
    board.commit(turn=1)
    assert (me.x, me.y) == (1, 0) and me.energy == 5
    me.move(UnitType.WEST)
    board.commit(turn=2)
    assert (me.x, me.y) == (0, 0) and me.energy == 6


def test_a_unit_ordered_off_the_board_recovers_two():
    # ordered into the board's edge: the move is refused and costs nothing,
    # and an order is no longer a reason not to recover
    board, players, me = a_pair()
    me.energy = 4
    me.move(UnitType.NORTH)
    board.commit(turn=1)
    assert (me.x, me.y) == (0, 0) and me.energy == 6


def test_a_unit_that_fought_recovers_two_less_its_strike():
    # x1 walks into o1 and both trade a blow. x1 pays three to move - a
    # quarter of its health - and one to strike, and gets two back; o1 stood
    # still and paid only for its strike, and gets two back
    heavy = UnitType('H', 'h', 1, 10, 20)
    board, players, me = a_pair(mine=heavy, theirs=heavy, where=(0, 0),
                                their_square=(0, 1))
    them = unit(board, players, 2, 'o1')
    them.energy = 10                         # below its cap, so the gain shows
    me.move(UnitType.SOUTH)
    board.commit(turn=1)
    assert me.energy == 20 - 3 - 1 + 2
    assert them.energy == 10 - 1 + 2


def test_a_unit_too_spent_to_strike_back_recovers_two():
    # o1 has attack 5 and one energy, so it cannot pay to strike back when
    # x1 walks in. Being hit is no bar to recovering
    striker = UnitType('S', 's', 1, 2, 4)
    spent = UnitType('T', 't', 5, 4, 5)
    board, players, me = a_pair(mine=striker, theirs=spent, where=(0, 0),
                                their_square=(0, 1))
    them = unit(board, players, 2, 'o1')
    them.energy = 1
    me.move(UnitType.SOUTH)
    board.commit(turn=1)
    assert them.energy == 3, 'it could not pay to fight, and recovered anyway'
    assert them.health < 4, 'and it was attacked while doing it'


def test_a_unit_whose_meter_charged_recovers_two():
    thinker = UnitType('T', 't', 1, 4, 10, 1,
                       '\n'.join(['SELF'] * 100))            # 100 ticks
    board, players, me = a_pair(mine=thinker)
    me.energy = 5
    board.commit(turn=1)
    assert me.energy == 6                    # paid 1, recovered 2


def test_a_unit_that_thought_a_little_recovers_two():
    thinker = UnitType('T', 't', 1, 4, 10, 5, 'SELF\nHOLD')
    board, players, me = a_pair(mine=thinker)
    me.energy = 5
    board.commit(turn=1)
    assert me.energy == 7


def test_a_sleeping_unit_recovers_two():
    sleeper = UnitType('S', 's', 1, 4, 10, 5, 'SLEEP 3')
    board, players, me = a_pair(mine=sleeper)
    me.energy = 2
    board.commit(turn=1)                     # thinks and sleeps
    assert me.energy == 4
    board.commit(turn=2)                     # asleep
    assert me.energy == 6


def test_a_wall_recovers_nothing():
    wall = UnitType('W', 'w', 0, 10, 0)
    board, players = setup((1, [(QUIET, [('q1', 0, 0)]), (wall, [('w1', 1, 0)])]),
                           (2, [(QUIET, [('q2', 7, 7)])]))
    events = board.commit(turn=1)
    assert unit(board, players, 1, 'w1').energy == 0
    assert not rested(events, 'w1')


def test_a_destroyed_unit_recovers_nothing():
    # o1 is walked into by something that kills it outright
    killer = UnitType('K', 'k', 10, 10, 20)
    board, players = setup((1, [(killer, [('x1', 0, 0)])]),
                           (2, [(PAWN, [('o1', 0, 1), ('o2', 7, 7)])]))
    me = unit(board, players, 1, 'x1')
    them = unit(board, players, 2, 'o1')
    me.move(UnitType.SOUTH)
    events = board.commit(turn=1)
    assert them.destroyed
    assert them.energy == 10 - 1, 'its strike, and nothing back'
    assert not rested(events, 'o1')


def test_a_unit_that_spends_its_last_point_is_spent_and_not_lost(tmp_path):
    # walking to zero is a bad afternoon rather than a death: elimination asks
    # whether a unit could ever act again (R7.1), and this one can. Through
    # the stored game, so that the service's judgement is the one asked
    harness = GameHarness(tmp_path)
    harness.create(6, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 1, 10, 50)], [('X', 'x1', 0, 1)])
    # ten health is a fare of three, and three energy is exactly one step
    harness.deploy(2, [('O', 'O', 1, 10, 3)], [('O', 'o1', 5, 2)])
    harness.resolve()
    assert harness.units()['o1'].energy == 3
    harness.turn({1: [], 2: [('o1', UnitType.NORTH)]})
    assert harness.units()['o1'].energy == 2, 'its fare to nothing, and two back'
    assert harness.session(0).getEliminated() == []
