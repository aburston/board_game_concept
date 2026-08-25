"""A unit that does nothing for a turn gets a point of energy back.

Energy used to be spent and never replenished, which is what made an
exhausted unit a permanent obstacle and every game a race to the bottom of
two pockets. Resting is the answer to that, and it is deliberately narrow: it
is doing *nothing* that pays, not surviving.
"""

from board_game_concept.domain import Player, UnitType

from game_harness import GameHarness


def a_game(tmp_path, mine=(1, 10, 10), theirs=None, my_units=None,
           their_units=None):
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', *mine)], my_units or [('X', 'x1', 0, 0)])
    harness.deploy(2, [('O', 'O', *(theirs or mine))],
                   their_units or [('O', 'o1', 5, 2)])
    harness.resolve()
    return harness


def test_a_unit_given_no_order_recovers_a_point(tmp_path):
    harness = a_game(tmp_path)
    # spend two points walking, then stand still for two turns
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    harness.turn({1: [('x1', UnitType.WEST)], 2: []})
    assert harness.units()['x1'].energy == 8

    harness.turn({1: [], 2: []})
    assert harness.units()['x1'].energy == 9
    harness.turn({1: [], 2: []})
    assert harness.units()['x1'].energy == 10


def test_resting_never_passes_the_energy_the_type_was_designed_with(tmp_path):
    harness = a_game(tmp_path)
    for _ in range(5):
        harness.turn({1: [], 2: []})
    assert harness.units()['x1'].energy == 10


def test_a_unit_that_was_ordered_does_not_rest(tmp_path):
    # ordered into the board's edge: the move is refused and costs nothing,
    # and it is still an order, so there is no refuelling by walking into a wall
    harness = a_game(tmp_path)
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert harness.units()['x1'].energy == 9
    for _ in range(3):
        harness.turn({1: [('x1', UnitType.NORTH)], 2: []})
    assert harness.units()['x1'].energy == 9


def test_a_unit_that_fought_does_not_rest(tmp_path):
    # x1 walks into o1 and both trade a blow; neither has done nothing
    harness = a_game(tmp_path, mine=(1, 10, 10),
                     my_units=[('X', 'x1', 0, 0)],
                     their_units=[('O', 'o1', 1, 0)])
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    units = harness.units()
    # x1 paid one to move and its share of the fight; o1 stood still and paid
    # only for the fight, so neither is back at ten
    assert units['x1'].energy < 10
    assert units['o1'].energy < 10


def test_a_unit_too_spent_to_strike_back_still_rests(tmp_path):
    # o1 has attack 5 and is walked down to one energy, so it cannot pay to
    # attack. Being hit is not an action, and doing nothing is what rests.
    # Both players keep a reserve out of the way so that nobody runs out of
    # units while this plays out
    harness = a_game(tmp_path, mine=(1, 10, 4), theirs=(5, 10, 5),
                     my_units=[('X', 'x1', 0, 0), ('X', 'x2', 0, 2)],
                     their_units=[('O', 'o1', 2, 0), ('O', 'o2', 5, 2)])
    for step in range(4):
        harness.turn({1: [], 2: [('o1', UnitType.EAST if step % 2
                                  else UnitType.WEST)]})
    assert harness.units()['o1'].energy == 1

    # x1 walks two squares to reach it and spends what is left attacking
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert harness.units()['o1'].energy == 2, 'a quiet turn is a point back'
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})

    o1 = harness.units()['o1']
    assert o1.energy == 3, 'it could not pay to fight, so it rested again'
    assert o1.health < 10, 'and it was attacked while doing it'


def test_a_unit_spending_its_last_point_is_out_before_it_can_rest(tmp_path):
    # resting happens at the end of the turn and elimination is judged after
    # it, so a unit that acted its way to zero does not get to recover first
    harness = a_game(tmp_path, mine=(1, 10, 50), theirs=(1, 10, 2),
                     their_units=[('O', 'o1', 5, 2)])
    harness.turn({1: [], 2: [('o1', UnitType.NORTH)]})
    harness.turn({1: [], 2: [('o1', UnitType.SOUTH)]})
    assert harness.units()['o1'].energy == 0
    assert harness.session(0).getEliminated() == [2]


def test_a_spent_unit_recovers_while_its_owner_is_still_in(tmp_path):
    # o2 keeps player 2 in the game, so o1 lives to rest off zero and comes
    # back into the count
    harness = a_game(tmp_path, mine=(1, 10, 50), theirs=(1, 10, 2),
                     their_units=[('O', 'o1', 5, 2), ('O', 'o2', 5, 0)])
    harness.turn({1: [], 2: [('o1', UnitType.NORTH)]})
    harness.turn({1: [], 2: [('o1', UnitType.WEST)]})
    assert harness.units()['o1'].energy == 0
    assert harness.session(0).getEliminated() == []

    harness.turn({1: [], 2: []})
    assert harness.units()['o1'].energy == 1
