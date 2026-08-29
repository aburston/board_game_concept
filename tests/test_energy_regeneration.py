"""A unit that does nothing for a turn gets a point of energy back.

Energy used to be spent and never replenished, which is what made an
exhausted unit a permanent obstacle and every game a race to the bottom of
two pockets. Resting is the answer to that, and it is deliberately narrow: it
is doing *nothing* that pays, not surviving.
"""

from board_game_concept.domain import Player, UnitType

from game_harness import GameHarness


def a_game(tmp_path, mine=(1, 2, 10), theirs=None, my_units=None,
           their_units=None):
    # four rows, so player 1 owns rows 0 and 1 and player 2 rows 2 and 3 with
    # no neutral row between them: a two-player board is halved by rows, and
    # the two sides meet where the halves do
    harness = GameHarness(tmp_path)
    harness.create(6, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', *mine)], my_units or [('X', 'x1', 0, 1)])
    harness.deploy(2, [('O', 'O', *(theirs or mine))],
                   their_units or [('O', 'o1', 5, 3)])
    harness.resolve()
    return harness


def test_a_unit_given_no_order_recovers_a_point(tmp_path):
    harness = a_game(tmp_path)
    # four squares at one energy a square - the fare is a quarter of the
    # unit's health, rounded up - and then stand still for two turns
    for direction in (UnitType.EAST, UnitType.WEST) * 2:
        harness.turn({1: [('x1', direction)], 2: []})
    assert harness.units()['x1'].energy == 6

    harness.turn({1: [], 2: []})
    assert harness.units()['x1'].energy == 7
    harness.turn({1: [], 2: []})
    assert harness.units()['x1'].energy == 8


def test_resting_never_passes_the_energy_the_type_was_designed_with(tmp_path):
    harness = a_game(tmp_path)
    for _ in range(5):
        harness.turn({1: [], 2: []})
    assert harness.units()['x1'].energy == 10


def test_a_unit_that_was_ordered_does_not_rest(tmp_path):
    # ordered into the board's edge: the move is refused and costs nothing,
    # and it is still an order, so there is no refuelling by walking into a wall
    # deployed on row 0 - player 1's top row - so north is the board's edge
    harness = a_game(tmp_path, my_units=[('X', 'x1', 0, 0)])
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert harness.units()['x1'].energy == 9
    for _ in range(3):
        harness.turn({1: [('x1', UnitType.NORTH)], 2: []})
    assert harness.units()['x1'].energy == 9


def test_a_unit_that_fought_does_not_rest(tmp_path):
    # x1 walks into o1 and both trade a blow; neither has done nothing
    harness = a_game(tmp_path, mine=(1, 10, 20),
                     my_units=[('X', 'x1', 0, 1)],
                     their_units=[('O', 'o1', 0, 2)])
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})
    units = harness.units()
    # x1 paid three to move - a quarter of its health - and then its share of
    # the fight; o1
    # stood still and paid only for the fight, so neither is back at twenty
    assert units['x1'].energy < 20
    assert units['o1'].energy < 20


def test_a_unit_too_spent_to_strike_back_still_rests(tmp_path):
    # o1 has attack 5 and is walked down to one energy - four squares at one
    # energy each, which is what a quarter of its health costs it - so it
    # cannot pay to attack. Being hit is not an action, and doing nothing is
    # what rests. Both players keep a reserve out of the way so that nobody
    # runs out of units while this plays out
    harness = a_game(tmp_path, mine=(1, 2, 4), theirs=(5, 4, 5),
                     my_units=[('X', 'x1', 1, 1), ('X', 'x2', 0, 1)],
                     their_units=[('O', 'o1', 2, 2), ('O', 'o2', 5, 3)])
    for step in range(4):
        harness.turn({1: [], 2: [('o1', UnitType.EAST if step % 2
                                  else UnitType.WEST)]})
    assert harness.units()['o1'].energy == 1

    # x1 walks two squares to reach it and spends what is left attacking
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})
    assert harness.units()['o1'].energy == 2, 'a quiet turn is a point back'
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})

    o1 = harness.units()['o1']
    assert o1.energy == 3, 'it could not pay to fight, so it rested again'
    assert o1.health < 4, 'and it was attacked while doing it'


def test_a_unit_that_spends_its_last_point_is_spent_and_not_lost(tmp_path):
    # walking to zero is a bad afternoon rather than a death: elimination asks
    # whether a unit could ever act again (R7.1), and this one can
    harness = a_game(tmp_path, mine=(1, 10, 50), theirs=(1, 2, 2),
                     their_units=[('O', 'o1', 5, 2)])
    harness.turn({1: [], 2: [('o1', UnitType.NORTH)]})
    harness.turn({1: [], 2: [('o1', UnitType.SOUTH)]})
    assert harness.units()['o1'].energy == 0
    assert harness.session(0).getEliminated() == []

    # and the next quiet turn puts it back on its feet
    harness.turn({1: [], 2: []})
    assert harness.units()['o1'].energy == 1
