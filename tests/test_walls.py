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
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', *attacker)],
                   [('X', 'x1', 0, 0), ('X', 'x2', 0, 2)])
    harness.deploy(2, [('W', 'W', *wall), ('O', 'O', 1, 10, 20)],
                   [('W', 'w1', 1, 0), ('O', 'o1', 5, 2)])
    harness.resolve()
    return harness


def test_a_wall_is_a_type_like_any_other():
    wall = UnitType('Wall', 'W', 0, 10, 0)
    assert wall.attack == 0
    assert wall.energy == 0
    assert wall.cost == 10, 'a wall costs its health and nothing else'


def test_no_attack_without_no_energy():
    with pytest.raises(AssertionError):
        UnitType('Half', 'H', 0, 10, 5)
    with pytest.raises(AssertionError):
        UnitType('Half', 'H', 3, 10, 0)


def test_a_wall_is_exempt_from_needing_energy_for_a_move():
    # every other type must hold at least its health in energy, or it could
    # never move. A wall holds none against a fare of 7, which is the whole
    # point of it, so the rule that would abolish it does not reach it
    wall = UnitType('Wall', 'W', 0, 7, 0)
    assert wall.move_cost == 7
    assert wall.energy == 0


def test_a_broken_wall_is_told_it_is_a_broken_wall():
    # attack 0 with energy above 0 fails the wall rule, not the energy rule:
    # the wall check comes first so the message names the right mistake
    with pytest.raises(AssertionError) as refused:
        UnitType('Half', 'H', 0, 10, 5)
    assert 'wall' in str(refused.value)


def test_the_ranges_still_hold():
    for bad in ((-1, 10, 10), (11, 10, 10), (1, 0, 10), (1, 11, 10),
                (1, 10, -1), (1, 10, 101)):
        with pytest.raises(AssertionError):
            UnitType('Bad', 'B', *bad)


def test_a_wall_lands_no_attacks_and_the_fight_still_ends(tmp_path):
    # without the guard this is the fight that never terminates: the wall
    # pays nothing, deals nothing, and counts as having attacked
    # ten to cross the square - the fare is the attacker's health - and two
    # more, which buys it exactly one attack and no second round
    harness = a_game(tmp_path, wall=(0, 10, 0), attacker=(2, 10, 12))
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})

    units = harness.units()
    assert units['w1'].health == 10 - 2, 'attacked once, for two'
    assert units['w1'].energy == 0
    assert units['x1'].health == 10, 'a wall strikes nobody back'
    assert not units['w1'].destroyed


def test_a_wall_can_be_broken(tmp_path):
    harness = a_game(tmp_path, wall=(0, 5, 0), attacker=(5, 10, 20))
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
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
    assert (units['w1'].x, units['w1'].y) == (1, 0)
    assert [entry['reason'] for entry in harness.rejections(2)] == [
        'not enough energy to move']


def test_an_army_of_walls_is_an_army_that_has_lost(tmp_path):
    # player 2 holds a wall and one real unit. The wall keeps nobody in the
    # game, so player 2 is out the moment the real one is destroyed - but a
    # unit merely out of energy still counts, because it can rest (R7.1)
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 5, 10, 50)], [('X', 'x1', 0, 0)])
    harness.deploy(2, [('W', 'W', 0, 10, 0), ('O', 'O', 1, 1, 1)],
                   [('W', 'w1', 3, 0), ('O', 'o1', 1, 0)])
    harness.resolve()

    # o1 walks itself down to nothing, and player 2 is still in
    harness.turn({1: [], 2: [('o1', UnitType.EAST)]})
    assert harness.units()['o1'].energy == 0
    assert harness.session(0).getEliminated() == []

    # destroyed is another matter: what is left is a wall, and scenery does
    # not keep you in
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    units = harness.units()
    assert units['o1'].destroyed
    assert not units['w1'].destroyed and units['w1'].on_board
    assert harness.session(0).getEliminated() == [2]
