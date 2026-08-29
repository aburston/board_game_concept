"""Walls: a type with no attack and no energy.

A wall cannot move, cannot strike, and cannot be worn down - it is health
standing on a square. It costs its health and nothing else, and because it
holds no energy it does not keep its owner in the game (R7.1): an army of
walls has already lost.
"""

import pytest

from board_game_concept.domain import Player, UnitType

from game_harness import GameHarness


def a_game(tmp_path, wall=(0, 10, 0), attacker=(2, 10, 20)):
    """An attacker facing a wall across the line the two halves meet on.

    A two-player setup gives each player half the board by rows, so the wall
    cannot be stood beside its attacker in one row any more. Four rows makes
    the halves meet - player 1 owns rows 0 and 1, player 2 rows 2 and 3 - and
    `x1` at (0, 1) walks south into `w1` at (0, 2).
    """
    harness = GameHarness(tmp_path)
    harness.create(6, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', *attacker)],
                   [('X', 'x1', 0, 1), ('X', 'x2', 1, 1)])
    harness.deploy(2, [('W', 'W', *wall), ('O', 'O', 1, 10, 20)],
                   [('W', 'w1', 0, 2), ('O', 'o1', 5, 3)])
    harness.resolve()
    return harness


def test_a_wall_is_a_type_like_any_other():
    wall = UnitType('Wall', 'W', 0, 10, 0)
    assert wall.attack == 0
    assert wall.energy == 0
    assert wall.cost == 10, 'a wall costs its health and nothing else'


def test_no_energy_means_no_attack():
    """An attack a type could never pay for is a wall charged for a weapon."""
    with pytest.raises(AssertionError):
        UnitType('Half', 'H', 3, 10, 0)


def test_no_attack_with_energy_is_a_scout_and_is_allowed():
    """A unit that goes where it likes and strikes nothing.

    It used to be refused - the two zeroes had to go together - which made
    attack 1 the cheapest thing that could move. A type that will never fight
    is worth paying less for rather than being told to buy a weapon.
    """
    scout = UnitType('Scout', 'S', 0, 4, 6)
    assert scout.attack == 0
    assert scout.energy == 6
    # priced like anything else, and cheaper for having no attack
    assert scout.cost == 0 + 4 + 6


def test_a_scout_is_held_to_the_fare_like_anything_that_moves():
    # health 8 costs 2 a square, so 1 energy could never buy a move: the
    # exemption is for a type with no energy at all, not for one with no attack
    with pytest.raises(AssertionError):
        UnitType('Scout', 'S', 0, 8, 1)
    walks = UnitType('Scout', 'S', 0, 8, 2)
    assert walks.move_cost == 2


def test_a_wall_is_exempt_from_needing_energy_for_a_move():
    # every other type must hold at least its movement cost in energy, or it
    # could never move. A wall holds none against a fare of 2, which is the
    # whole point of it, so the rule that would abolish it does not reach it
    wall = UnitType('Wall', 'W', 0, 7, 0)
    assert wall.move_cost == 2
    assert wall.energy == 0


def test_an_attack_nothing_could_pay_for_says_so():
    # energy 0 with an attack above it is the one pairing still refused, and
    # the message names what it is: a wall that was charged for a weapon
    with pytest.raises(AssertionError) as refused:
        UnitType('Half', 'H', 3, 10, 0)
    assert 'wall' in str(refused.value)


def test_the_ranges_still_hold():
    for bad in ((-1, 10, 10), (11, 10, 10), (1, 0, 10), (1, 11, 10),
                (1, 10, -1), (1, 10, 101)):
        with pytest.raises(AssertionError):
            UnitType('Bad', 'B', *bad)


def test_a_wall_lands_no_attacks_and_the_fight_still_ends(tmp_path):
    # without the guard this is the fight that never terminates: the wall
    # pays nothing, deals nothing, and counts as having attacked
    # three to cross the square - the fare is a quarter of the attacker's
    # health - and two more, which buys it exactly one attack and no second
    # round
    harness = a_game(tmp_path, wall=(0, 10, 0), attacker=(2, 10, 5))
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})

    units = harness.units()
    assert units['w1'].health == 10 - 2, 'attacked once, for two'
    assert units['w1'].energy == 0
    assert units['x1'].health == 10, 'a wall strikes nobody back'
    assert not units['w1'].destroyed


def test_a_wall_can_be_broken(tmp_path):
    harness = a_game(tmp_path, wall=(0, 5, 0), attacker=(5, 10, 20))
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})
    assert harness.units()['w1'].destroyed


def test_a_wall_never_rests(tmp_path):
    # its type was designed with no energy, so there is nothing to recover to
    harness = a_game(tmp_path)
    for _ in range(3):
        harness.turn({1: [], 2: []})
    assert harness.units()['w1'].energy == 0


def test_a_wall_cannot_be_ordered_to_move(tmp_path):
    harness = a_game(tmp_path)
    harness.turn({1: [], 2: [('w1', UnitType.EAST)]})
    units = harness.units()
    assert (units['w1'].x, units['w1'].y) == (0, 2)
    assert [entry['reason'] for entry in harness.rejections(2)] == [
        'not enough energy to move']


def test_an_army_of_walls_is_an_army_that_has_lost(tmp_path):
    # player 2 holds a wall and one real unit. The wall keeps nobody in the
    # game, so player 2 is out the moment the real one is destroyed - but a
    # unit merely out of energy still counts, because it can rest (R7.1)
    harness = GameHarness(tmp_path)
    harness.create(6, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 5, 10, 50)], [('X', 'x1', 0, 1)])
    harness.deploy(2, [('W', 'W', 0, 10, 0), ('O', 'O', 1, 1, 1)],
                   [('W', 'w1', 3, 2), ('O', 'o1', 0, 2)])
    harness.resolve()

    # o1 walks itself down to nothing, and player 2 is still in
    harness.turn({1: [], 2: [('o1', UnitType.EAST)]})
    assert harness.units()['o1'].energy == 0
    assert harness.session(0).getEliminated() == []

    # destroyed is another matter: what is left is a wall, and scenery does
    # not keep you in
    # o1 walked east out of the square below x1, so x1 goes south and then
    # east after it
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    units = harness.units()
    assert units['o1'].destroyed
    assert not units['w1'].destroyed and units['w1'].on_board
    assert harness.session(0).getEliminated() == [2]


# --- a scout: no attack, but energy to walk on


def test_a_scout_moves_and_strikes_nothing(tmp_path):
    """It goes where it likes and lands nothing when it gets there."""
    harness = GameHarness(tmp_path)
    harness.create(6, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('S', 'S', 0, 4, 20), ('X', 'X', 2, 4, 20)],
                   [('S', 's1', 0, 1), ('X', 'x1', 5, 0)], flag='x1')
    harness.deploy(2, [('O', 'O', 2, 8, 20)], [('O', 'o1', 0, 2)])
    harness.resolve()

    # it walks into the enemy and the exchange is one-sided: the scout lands
    # nothing, and takes what the other one deals
    harness.turn({1: [('s1', UnitType.SOUTH)], 2: []})

    units = harness.units()
    assert units['o1'].health == 8, 'the scout struck nothing'
    assert units['s1'].health == 4 - 2, 'and was struck for it'
    assert not units['s1'].destroyed
    # the fare came out of its energy, and nothing was paid for an attack
    assert units['s1'].energy == 20 - units['s1'].move_cost


def test_a_scout_keeps_its_owner_in_the_game(tmp_path):
    """Unlike a wall, it has energy: it can act, so it is not nothing."""
    harness = GameHarness(tmp_path)
    harness.create(6, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('S', 'S', 0, 4, 20)], [('S', 's1', 0, 1)])
    harness.deploy(2, [('O', 'O', 1, 4, 20)], [('O', 'o1', 5, 3)])
    harness.resolve()

    assert harness.session(0).getEliminated() == []
