"""Playing a game on past its first casualty.

Every test here plays turns after a unit has been destroyed. That is the ground
nothing else covered, which is how a destroyed unit came to be redeployed at
full health without a single test noticing.

Each player keeps a second unit well out of the way, so that losing the first
does not end the game and the turns can keep coming.
"""

from board_game_concept.domain import UnitType

from game_harness import GameHarness


def two_players(tmp_path, stats=(5, 5, 50), enemy=None):
    """A game with two units each: a duellist on the top row, and a reserve."""
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2])
    attack, health, energy = stats
    harness.deploy(1, [('X', 'X', attack, health, energy)],
                   [('X', 'x1', 0, 0), ('X', 'x2', 0, 2)])
    e_attack, e_health, e_energy = enemy or stats
    harness.deploy(2, [('O', 'O', e_attack, e_health, e_energy)],
                   [('O', 'o1', 2, 0), ('O', 'o2', 5, 2)])
    harness.resolve()
    return harness


def test_a_destroyed_unit_does_not_come_back(tmp_path):
    # equal units annihilate each other, leaving the cell they died on empty
    harness = two_players(tmp_path)
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    harness.turn({1: [], 2: [('o1', UnitType.WEST)]})

    units = harness.units()
    assert units['x1'].destroyed
    assert units['o1'].destroyed

    # play on. The cell they died on is empty, which is what used to bring them
    # back at full health
    for _ in range(3):
        harness.turn({1: [], 2: []})

    board = harness.session(0).getBoard()
    assert len(board.units) == 4, [u.name for u in board.units]
    dead = {unit.name for unit in board.units if unit.destroyed}
    assert dead == {'x1', 'o1'}
    for unit in board.units:
        if unit.destroyed:
            assert not unit.on_board
            assert unit.health <= 0


def test_a_destroyed_unit_is_not_reported_every_turn(tmp_path):
    harness = two_players(tmp_path)
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    harness.turn({1: [], 2: [('o1', UnitType.WEST)]})
    assert harness.units()['x1'].destroyed

    harness.turn({1: [], 2: []})
    assert harness.rejections(1) == []
    harness.turn({1: [], 2: []})
    assert harness.rejections(1) == []


def test_a_survivor_can_take_the_cell_a_unit_died_on(tmp_path):
    # x1 is strong enough to win outright, then walks off the cell and back
    harness = two_players(tmp_path, stats=(10, 10, 50), enemy=(1, 1, 50))
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert harness.units()['o1'].destroyed

    # step off the cell o1 died on, leaving it empty for a turn
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    board = harness.session(0).getBoard()
    assert len(board.units) == 4, [u.name for u in board.units]
    assert not board.getUnitByName('o1')[0].on_board

    # and step back onto it
    harness.turn({1: [('x1', UnitType.WEST)], 2: []})
    units = harness.units()
    assert (units['x1'].x, units['x1'].y) == (2, 0)
    assert units['o1'].destroyed
    assert not units['o1'].on_board
