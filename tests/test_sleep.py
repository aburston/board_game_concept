"""Sleep: how a unit rests, and what wakes it."""

from board_game_concept.domain import UnitType

from test_think_phase import setup, unit


MARK = 'SET r0, 1\nSTORE r0, 0\n'


def test_a_sleeping_controller_does_not_run_and_the_unit_rests():
    sleeper = UnitType('S', 's', 1, 4, 10, 5, MARK + 'SLEEP 3')
    quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
    board, players = setup((1, [(sleeper, [('s1', 0, 0)])]),
                           (2, [(quiet, [('q1', 7, 7)])]))
    me = unit(board, players, 1, 's1')
    me.energy = 1
    board.commit(turn=1)                 # thinks, marks, sleeps
    assert me.memory == {0: 1} and me.asleep == 3
    me.memory.clear()
    for turn in (2, 3, 4):
        board.commit(turn=turn)
        assert me.memory == {}, f'the controller ran on turn {turn}'
    # two back on every turn, the one it slept on included: 1 -> 3 -> 5 ->
    # 7 -> 9
    assert me.energy == 9
    board.commit(turn=5)
    assert me.memory == {0: 1}


def test_a_sleepers_meter_is_untouched():
    sleeper = UnitType('S', 's', 1, 4, 10, 5, 'SELF\nSLEEP 3')
    quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
    board, players = setup((1, [(sleeper, [('s1', 0, 0)])]),
                           (2, [(quiet, [('q1', 7, 7)])]))
    me = unit(board, players, 1, 's1')
    board.commit(turn=1)
    meter = me.meter
    assert meter == 2
    for turn in (2, 3, 4):
        board.commit(turn=turn)
    assert me.meter == meter


def test_a_blow_wakes_a_sleeper_who_fights_back():
    sleeper = UnitType('S', 's', 2, 10, 10, 5, MARK + 'SLEEP 50')
    lance = UnitType('L', 'l', 3, 4, 10, 3, 'MOVE north')
    board, players = setup((1, [(sleeper, [('s1', 0, 0)])]),
                           (2, [(lance, [('l1', 0, 1)])]))
    me = unit(board, players, 1, 's1')
    me.energy = 6
    board.commit(turn=1)                 # s1 sleeps; l1 steps onto it
    assert me.asleep == 0
    assert me.health == 7                # struck for 3
    assert me.energy == 6 - 2 + 2        # struck back for 2, two back
    assert unit(board, players, 2, 'l1').health == 2
    assert me.trace['woken'] is True
    me.memory.clear()
    board.commit(turn=2)
    assert me.memory == {0: 1}           # the controller ran again


def test_a_message_does_not_wake_a_sleeper():
    sleeper = UnitType('S', 's', 1, 4, 10, 5, MARK + 'SLEEP 5')
    crier = UnitType('C', 'c', 1, 4, 10, 5, 'SAY s1, 1, 2, 3')
    quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
    board, players = setup((1, [(sleeper, [('s1', 0, 0)]),
                                (crier, [('c1', 1, 0)])]),
                           (2, [(quiet, [('q1', 7, 7)])]))
    me = unit(board, players, 1, 's1')
    board.commit(turn=1)
    me.memory.clear()
    board.commit(turn=2)
    board.commit(turn=3)
    assert me.memory == {}
    assert me.inbox == [(1, 2, 3)] * 3


def test_the_longest_sleep():
    sleeper = UnitType('S', 's', 1, 4, 10, 5, MARK + 'SLEEP 100')
    quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
    board, players = setup((1, [(sleeper, [('s1', 0, 0)])]),
                           (2, [(quiet, [('q1', 7, 7)])]))
    me = unit(board, players, 1, 's1')
    board.commit(turn=1)
    me.memory.clear()
    for turn in range(2, 102):
        board.commit(turn=turn)
    assert me.memory == {}
    board.commit(turn=102)
    assert me.memory == {0: 1}
    assert me.meter == 6                 # two runs of three ticks each


def test_a_struck_sleeper_that_cannot_pay_still_rests():
    sleeper = UnitType('S', 's', 5, 10, 10, 5, 'SLEEP 10')
    scout = UnitType('O', 'o', 0, 2, 12, 2, 'MOVE north')
    board, players = setup((1, [(sleeper, [('s1', 0, 0)])]),
                           (2, [(scout, [('o1', 0, 1)])]))
    me = unit(board, players, 1, 's1')
    me.energy = 2                        # below its attack: it cannot strike
    board.commit(turn=1)
    board.commit(turn=2)                 # the scout walks in; s1 is woken
    assert me.asleep == 0
    assert me.energy == 6                # two back on both turns
