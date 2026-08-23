"""Regression coverage for a unit seen more than once in a turn.

Issue #3: a fight lasting several rounds recorded the same contact once per
attack, the player's view then named the enemy unit once per contact, and the
client died restoring a unit it had already restored.
"""

import yaml

from board_game_concept.storage.serialise import serialise_units
from board_game_concept import UnitType, Board, Player


def _fighting_board():
    """Two units with enough health to trade blows over several rounds."""
    red_type = UnitType('Red', 'R', 1, 10, 100)
    blue_type = UnitType('Blue', 'B', 1, 10, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(3, 3)
    board.add(p1, 0, 1, 'r1', red_type)
    board.add(p2, 2, 1, 'b1', blue_type)
    board.commit()

    red = board.getUnitByName('r1')[0]
    blue = board.getUnitByName('b1')[0]
    red.move(UnitType.EAST)
    blue.move(UnitType.WEST)
    board.commit()
    return board, p1, p2, red, blue


def _restore(board, source, players, types):
    """Load a published view the way the client's game data loader does."""
    for unit in yaml.safe_load(source)['units']:
        board.add(
            players[unit['player']],
            unit['x'], unit['y'],
            unit['name'],
            types[unit['player']],
            int(unit['health']),
            int(unit['energy']),
            bool(unit['destroyed']),
            bool(unit['on_board']),
            restoring=True)
    board.commit()


def test_a_drawn_out_fight_records_each_unit_once():
    # the contest runs for several rounds, but each unit meets one other unit
    _, _, _, red, blue = _fighting_board()

    assert [unit.name for unit in red.seen_by] == ['b1']
    assert [unit.name for unit in blue.seen_by] == ['r1']


def test_a_view_names_a_unit_seen_repeatedly_once():
    board, p1, _, _, _ = _fighting_board()

    view = yaml.safe_load(serialise_units(board, p1))
    names = [unit['name'] for unit in view['units']]

    assert sorted(names) == ['b1', 'r1']


def test_a_view_names_an_enemy_engaged_by_several_units_once():
    # two of player 1's units converge on one enemy: the enemy is seen by both
    red_type = UnitType('Red', 'R', 1, 10, 100)
    blue_type = UnitType('Blue', 'B', 1, 10, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(3, 3)
    board.add(p1, 0, 1, 'r1', red_type)
    board.add(p1, 1, 0, 'r2', red_type)
    board.add(p2, 1, 2, 'b1', blue_type)
    board.commit()

    board.getUnitByName('r1')[0].move(UnitType.EAST)
    board.getUnitByName('r2')[0].move(UnitType.SOUTH)
    board.getUnitByName('b1')[0].move(UnitType.NORTH)
    board.commit()

    blue = board.getUnitByName('b1')[0]
    assert sorted(unit.name for unit in blue.seen_by) == ['r1', 'r2']

    names = [unit['name']
             for unit in yaml.safe_load(serialise_units(board, p1))['units']]
    assert names.count('b1') == 1


def test_find_unit_answers_rather_than_asserting():
    board, p1, p2, red, _ = _fighting_board()

    assert board.findUnit('r1', p1) is red
    assert board.findUnit('r1', p2) is None
    assert board.findUnit('nosuchunit', p1) is None


def test_restoring_a_unit_the_board_already_holds_updates_it():
    red_type = UnitType('Red', 'R', 1, 10, 100)
    p1 = Player(1)
    board = Board(3, 3)

    board.add(p1, 0, 0, 'r1', red_type, 10, 100, False, True, restoring=True)
    board.add(p1, 1, 2, 'r1', red_type, 4, 60, False, True, restoring=True)

    assert len(board.units) == 1
    assert len(board.getUnitByName('r1')) == 1
    restored = board.getUnitByName('r1', p1)[0]
    assert (restored.x, restored.y) == (1, 2)
    assert restored.health == 4
    assert restored.energy == 60

    board.commit()
    assert board.getUnitByCoords(1, 2) is restored


def test_restoring_a_view_that_names_a_unit_twice_loads():
    # a view written by an older server names a unit once per contact made
    board, p1, p2, _, _ = _fighting_board()
    published = serialise_units(board, p1)
    doubled = yaml.safe_load(published)
    doubled['units'] = doubled['units'] + [
        unit for unit in doubled['units'] if unit['player'] == 2]

    seen_board = Board(3, 3)
    _restore(
        seen_board,
        yaml.safe_dump(doubled),
        {1: p1, 2: p2},
        {1: UnitType('Red', 'R', 1, 10, 100),
         2: UnitType('Blue', 'B', 1, 10, 100)})

    assert sorted(unit.name for unit in seen_board.units) == ['b1', 'r1']


def test_placing_a_name_a_player_already_holds_still_fails():
    red_type = UnitType('Red', 'R', 1, 10, 100)
    p1 = Player(1)
    p2 = Player(2)
    board = Board(3, 3)
    board.add(p1, 0, 0, 'r1', red_type)

    # another player may reuse the name
    board.add(p2, 2, 2, 'r1', red_type)

    try:
        board.add(p1, 1, 1, 'r1', red_type)
    except AssertionError as error:
        assert str(error) == "unit r1 already exists for player 1"
    else:
        raise AssertionError("placing a name the player already holds succeeded")
