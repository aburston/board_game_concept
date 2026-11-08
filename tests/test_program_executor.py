"""The machine that runs a program: what each instruction does and costs.

Every scenario here is one from the `unit-program` spec. The snapshot is built
by hand, so these hold the executor alone; how the board builds a snapshot is
`test_think_phase.py`'s.
"""

import pytest

from board_game_concept.domain.army_map import ArmyMap
from board_game_concept.domain.program import (
    MAP_EMPTY, MAP_ENEMY, MAP_FRIEND, MAP_OFF, MAP_UNKNOWN, Program, Result,
    Snapshot, cap, run)


def snapshot(turn=5, friends=None, flags=None, army_map=None, player=1):
    return Snapshot(turn, 8, 8, player,
                    friends if friends is not None else {'me': (3, 3)},
                    flags if flags is not None else {1: (3, 0), 2: (3, 7)},
                    army_map or ArmyMap())


ME = {'x': 3, 'y': 3, 'health': 4, 'energy': 10, 'flag': False, 'number': 2}


def go(text, snap=None, me=ME, contact=None, memory=None, inbox=None,
       compute=5, energy=10, meter=0):
    """Run a program and hand back the result and the registers it left.

    The registers are read back by appending a `STORE` of each to memory,
    which costs ticks the tests allow for.
    """
    memory = memory if memory is not None else {}
    inbox = inbox if inbox is not None else []
    program = Program(text + '\n' + '\n'.join(
        f'STORE r{n}, {100 + n}' for n in range(8)))
    result = run(program, snap or snapshot(), me, contact, memory, inbox,
                 compute, energy, meter)
    registers = [memory.get(100 + n, 0) for n in range(8)]
    return result, registers


READBACK = 8     # the ticks the eight STOREs above cost


class TestSensors:

    def test_self(self):
        me = dict(ME, flag=True)
        result, r = go('SELF', me=me)
        assert r[:6] == [3, 3, 4, 10, 1, 2]
        assert result.ticks == 1 + READBACK

    def test_turn_and_extent(self):
        _, r = go('TURN\nMOV r5, r0\nEXTENT')
        assert r[5] == 5 and r[:2] == [8, 8]

    def test_flags(self):
        result, r = go('FLAG mine\nMOV r4, r0\nMOV r5, r1\nFLAG enemy')
        assert (r[4], r[5]) == (3, 0)
        assert r[:2] == [3, 7]
        assert result.ticks == 2 + 1 + 1 + 2 + READBACK

    def test_a_fallen_flag(self):
        _, r = go('FLAG mine', snap=snapshot(flags={2: (3, 7)}))
        assert r[:2] == [-1, -1]
        _, r = go('FLAG enemy', snap=snapshot(flags={1: (3, 0)}))
        assert r[:2] == [-1, -1]

    def test_the_nearest_enemy_flag_by_distance_then_y_then_x(self):
        # three enemy flags all two squares away: y 3 beats y 5, and of the
        # two on row 3, x 1 beats x 5
        snap = snapshot(flags={1: (0, 0), 2: (3, 5), 3: (5, 3), 4: (1, 3)})
        _, r = go('FLAG enemy', snap=snap)
        assert r[:2] == [1, 3]

    def test_map_kinds(self):
        army = ArmyMap()
        army.visited[(2, 2)] = 3
        army.enemies[(6, 6)] = (4, 8, 2)
        snap = snapshot(army_map=army, friends={'me': (3, 3), 'f': (1, 1)})
        _, r = go('SET r6, 2\nSET r7, 2\nMAP r6, r7', snap=snap)
        assert r[:2] == [MAP_EMPTY, 3]
        _, r = go('SET r6, 6\nSET r7, 6\nMAP r6, r7', snap=snap)
        assert r[:4] == [MAP_ENEMY, 4, 8, 2]
        _, r = go('SET r6, 1\nSET r7, 1\nMAP r6, r7', snap=snap)
        assert r[:2] == [MAP_FRIEND, 5]
        _, r = go('SET r6, 4\nSET r7, 4\nMAP r6, r7', snap=snap)
        assert r[:2] == [MAP_UNKNOWN, -1]
        _, r = go('SET r6, 8\nSET r7, 0\nMAP r6, r7', snap=snap)
        assert r[0] == MAP_OFF

    def test_nearest(self):
        army = ArmyMap()
        army.enemies[(6, 3)] = (4, 8, 2)
        army.enemies[(3, 6)] = (4, 8, 2)
        for x in range(8):
            for y in range(8):
                army.visited[(x, y)] = 1
        del army.visited[(0, 7)]
        snap = snapshot(army_map=army,
                        friends={'me': (3, 3), 'a': (3, 1), 'b': (5, 3)})
        _, r = go('NEAREST friend', snap=snap)
        assert r[:3] == [3, 1, 2]      # ties: lower y
        _, r = go('NEAREST enemy', snap=snap)
        assert r[:3] == [6, 3, 3]      # distance 3 both; y 3 beats y 6
        result, r = go('NEAREST unknown', snap=snap)
        assert r[:3] == [0, 7, 7]
        assert result.ticks == 4 + READBACK

    def test_nearest_of_nothing(self):
        _, r = go('NEAREST enemy')
        assert r[:3] == [-1, -1, -1]
        _, r = go('NEAREST friend')
        assert r[:3] == [-1, -1, -1]

    def test_a_sensors_cost_does_not_depend_on_its_answer(self):
        army = ArmyMap()
        for n in range(12):
            army.enemies[(n % 8, n // 8)] = (1, 1, 1)
        full, _ = go('NEAREST enemy', snap=snapshot(army_map=army))
        empty, _ = go('NEAREST enemy')
        assert full.ticks == empty.ticks == 4 + READBACK

    def test_contact(self):
        result, r = go('CONTACT', contact=(4, 3, 5, 10))
        assert r[:4] == [4, 3, 5, 10]
        assert result.ticks == 2 + READBACK
        _, r = go('CONTACT')
        assert r[0] == -1

    def test_recv_and_flush(self):
        inbox = [(1, 2, 3), (4, 5, 6)]
        result, r = go('RECV', inbox=inbox)
        assert r[:4] == [1, 1, 2, 3]
        assert inbox == [(4, 5, 6)]
        _, r = go('FLUSH\nRECV', inbox=inbox)
        assert r[0] == 0 and inbox == []


class TestArithmeticAndFlow:

    def test_arithmetic(self):
        _, r = go('SET r0, 5\nSET r1, -3\nADD r0, r1\nSUB r0, 4\n'
                  'MOV r2, r1\nABS r2\nSIGN r1\nSET r3, 0\nSIGN r3')
        assert r[:4] == [-2, -1, 3, 0]

    def test_dist(self):
        _, r = go('SET r6, 0\nSET r7, 0\nDIST r6, r7')
        assert r[0] == 6

    def test_memory(self):
        memory = {}
        _, r = go('SET r0, 9\nSTORE r0, 3\nSET r1, 3\nLOAD r2, r1\nLOAD r3, 99',
                  memory=memory)
        assert r[2] == 9 and r[3] == 0
        assert memory[3] == 9

    def test_jumps(self):
        _, r = go('SET r0, 0\nJIF zero r0, skip\nSET r1, 1\nskip:\n'
                  'SET r2, 2\nJMP end\nSET r3, 3\nend:')
        assert r[1:4] == [0, 2, 0]

    def test_every_condition(self):
        text = ('SET r0, 0\nSET r1, 5\nSET r2, -1\n'
                'JIF zero r0, a\nSET r3, 100\na:\n'
                'JIF notzero r1, b\nSET r3, 100\nb:\n'
                'JIF neg r2, c\nSET r3, 100\nc:\n'
                'JIF pos r1, d\nSET r3, 100\nd:\n'
                'JIF eq r0, r0, e\nSET r3, 100\ne:\n'
                'JIF lt r2, r1, f\nSET r3, 100\nf:\n'
                'JIF lt r1, r2, g\nSET r4, 1\ng:')
        _, r = go(text)
        assert r[3] == 0 and r[4] == 1

    def test_a_loop_costs_what_it_runs(self):
        result, _ = go('SET r0, 10\nloop:\nSUB r0, 1\nJIF pos r0, loop',
                       compute=10)
        # SET, then ten SUBs and ten JIFs
        assert result.ticks == 1 + 20 + READBACK


class TestActuators:

    def test_move_and_hold(self):
        result, _ = go('MOVE north')
        assert result.order == 1
        result, _ = go('MOVE north\nMOVE east')
        assert result.order == 2
        result, _ = go('MOVE west\nHOLD')
        assert result.order == 'hold'
        result, _ = go('SET r0, 3\nMOVE r0')
        assert result.order == 3

    def test_a_register_outside_the_directions_orders_nothing(self):
        result, _ = go('SET r0, 7\nMOVE r0')
        assert result.order is None

    def test_say(self):
        result, _ = go('SET r0, 7\nSAY all, 1, r0, 3\nSAY runner1, r0, r0, 0')
        assert result.said == [('all', 1, 7, 3), ('runner1', 7, 7, 0)]
        assert result.ticks == 1 + 5 + 5 + READBACK

    def test_sleep_ends_the_run(self):
        result, r = go('SET r0, 1\nSLEEP 3\nSET r0, 2')
        assert result.sleep == 3
        assert result.ticks == 2            # the readback never ran
        assert result.order is None

    def test_halt_ends_the_run_for_nothing(self):
        result, _ = go('MOVE north\nHALT\nMOVE south')
        assert result.order == 1
        assert result.ticks == 1


class TestTheMeterAndTheCap:

    def test_cap(self):
        assert cap(2) == 20 and cap(10) == 100

    def test_a_small_program_over_several_turns(self):
        program = Program('SELF\nSELF\nSELF\nSELF\nSELF\nSELF')   # 6 ticks
        meter, charged = 0, []
        for _ in range(5):
            result = run(program, snapshot(), ME, None, {}, [], 2, 10, meter)
            charged.append(result.charged)
            meter = result.meter
        assert charged == [0, 0, 0, 1, 0]
        assert meter == 10                  # 30 ticks, one fill of 20

    def test_thinking_within_a_turn_halts_at_the_cap(self):
        program = Program('loop:\nSELF\nJMP loop')
        result = run(program, snapshot(), ME, None, {}, [], 5, 10, 0)
        assert result.ticks == 50
        assert result.halted is not None
        assert result.charged == 1
        assert result.meter == 0

    def test_a_halted_programs_order_is_dropped(self):
        program = Program('MOVE north\nloop:\nSELF\nJMP loop')
        result = run(program, snapshot(), ME, None, {}, [], 2, 10, 0)
        assert result.order is None
        assert result.halted == 3 or result.halted == 4

    def test_thinking_when_the_energy_is_gone(self):
        program = Program('\n'.join(['SELF'] * 25))        # 25 ticks
        result = run(program, snapshot(), ME, None, {}, [], 2, 0, 15)
        # the meter holds 15; the fifth SELF would make 20 and charge 1,
        # which a unit with 0 energy has not got
        assert result.ticks == 4
        assert result.halted == 5
        assert result.charged == 0
        assert result.meter == 19

    def test_compute_buys_ticks(self):
        program = Program('\n'.join(['SELF'] * 30))
        slow = run(program, snapshot(), ME, None, {}, [], 3, 10, 0)
        fast = run(program, snapshot(), ME, None, {}, [], 6, 10, 0)
        assert slow.charged == 1 and slow.meter == 0
        assert fast.charged == 0 and fast.meter == 30

    def test_no_controller_runs_nothing(self):
        program = Program('MOVE north')
        result = run(program, snapshot(), ME, None, {}, [], 0, 10, 0)
        assert result.order is None and result.ticks == 0
        result = run(None, snapshot(), ME, None, {}, [], 5, 10, 7)
        assert result.ticks == 0 and result.meter == 7


class TestDeterminism:

    def test_the_same_snapshot_gives_the_same_result(self):
        army = ArmyMap()
        army.enemies[(6, 3)] = (4, 8, 2)
        text = ('NEAREST enemy\nSUB r0, 3\nSIGN r0\nSAY all, r0, r1, r2\n'
                'STORE r0, 1\nMOVE east\nSLEEP 2')
        runs = []
        for _ in range(2):
            snap = snapshot(army_map=army, flags={1: (3, 0), 2: (7, 7)})
            result = run(Program(text), snap, ME, (4, 3, 1, 1), {},
                         [(1, 1, 1)], 4, 10, 3)
            runs.append((result.order, result.said, result.sleep,
                         result.ticks, result.charged, result.meter))
        assert runs[0] == runs[1]
