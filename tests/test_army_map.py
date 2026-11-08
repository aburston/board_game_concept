"""The army's map: what its units have stood on and fought, shared for free."""

from board_game_concept.domain import UnitType
from board_game_concept.domain.army_map import ArmyMap
from board_game_concept.domain.program import (
    MAP_EMPTY, MAP_ENEMY, MAP_UNKNOWN)

from test_think_phase import setup, unit


def test_a_square_walked_on_is_known_empty_next_turn():
    walker = UnitType('W', 'w', 1, 4, 10, 5, 'MOVE south')
    quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
    board, players = setup((1, [(walker, [('w1', 0, 0)])]),
                           (2, [(quiet, [('q1', 7, 7)])]))
    board.commit(turn=1)
    army = board.maps[1]
    assert army.at(0, 0)[:2] == (MAP_EMPTY, 0)      # stood there after setup
    assert army.at(0, 1)[:2] == (MAP_EMPTY, 1)
    assert army.at(0, 2)[0] == MAP_UNKNOWN
    assert 2 not in board.maps or board.maps[2].at(0, 1)[0] == MAP_UNKNOWN


def test_an_enemy_met_by_one_unit_is_known_to_all():
    hunter = UnitType('H', 'h', 1, 10, 10, 5, 'MOVE south')
    reader = UnitType('R', 'r', 1, 4, 10, 5,
                      'SET r6, 0\nSET r7, 2\nMAP r6, r7\nSTORE r0, 0\n'
                      'STORE r1, 1\nSTORE r2, 2\nSTORE r3, 3')
    keep = UnitType('K', 'k', 2, 10, 5, 0)
    board, players = setup(
        (1, [(hunter, [('h1', 0, 1)]), (reader, [('r1', 7, 0)])]),
        (2, [(keep, [('k1', 0, 2)])]))
    board.commit(turn=1)                 # h1 steps onto k1: undecided, falls back
    army = board.maps[1]
    assert army.at(0, 2) == (MAP_ENEMY, 1, 2, 10)
    assert unit(board, players, 1, 'r1').memory[0] == MAP_UNKNOWN
    board.commit(turn=2)                 # read as the turn began: known now
    assert unit(board, players, 1, 'r1').memory == {0: MAP_ENEMY, 1: 1,
                                                      2: 2, 3: 10}


def test_the_map_is_not_a_sensor():
    quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
    board, players = setup((1, [(quiet, [('q1', 0, 0)])]),
                           (2, [(quiet, [('q2', 0, 1)])]))
    board.commit(turn=1)
    assert board.maps[1].at(0, 1)[0] == MAP_UNKNOWN


def test_stale_knowledge_stays_stamped():
    army = ArmyMap()
    army.enemies[(3, 3)] = (2, 5, 10)
    assert army.at(3, 3, turn=7) == (MAP_ENEMY, 2, 5, 10)


def test_a_friend_standing_on_a_square_clears_an_enemy_once_met_there():
    army = ArmyMap()
    army.enemies[(3, 3)] = (2, 5, 10)

    class Stand:
        def __init__(self, number, x, y):
            self.player = type('P', (), {'number': number})()
            self.x, self.y = x, y
            self.destroyed, self.on_board = False, True
            self.seen_by = []
    army.observe([Stand(1, 3, 3)], 1, 5)
    assert army.at(3, 3)[:2] == (MAP_EMPTY, 5)


def test_a_turret_feeds_the_map_and_reads_nothing():
    turret = UnitType('T', 't', 3, 6, 6, 0)
    hunter = UnitType('H', 'h', 1, 10, 10, 5, 'MOVE north')
    board, players = setup((1, [(turret, [('t1', 0, 0)])]),
                           (2, [(hunter, [('h1', 0, 1)])]))
    board.commit(turn=1)                 # h1 walks into the turret
    assert board.maps[1].at(0, 1) == (MAP_ENEMY, 1, 1, 10)
    assert unit(board, players, 1, 't1').trace is None


def test_the_record_round_trips():
    army = ArmyMap()
    army.visited[(1, 2)] = 3
    army.enemies[(4, 5)] = (6, 7, 8)
    again = ArmyMap.from_record(army.record())
    assert again.record() == army.record()
    assert again.record() == {'visited': [[1, 2, 3]],
                              'enemies': [[4, 5, 6, 7, 8]]}
