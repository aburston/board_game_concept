"""The think phase: every awake controller runs against the board as the
turn began, pays its meter, gives its unit's order and speaks on the radio.

These hold the board's part of `unit-program`: the snapshot discipline, the
meter on a real unit, the settled delivery of messages, and that an
eliminated player's controllers never run. The machine itself is
`test_program_executor.py`'s.
"""

from board_game_concept.domain import Board, Player, UnitType
from board_game_concept.domain.program import MAP_FRIEND


def setup(*armies, size=(8, 8)):
    """A board with each army deployed and the setup turn resolved.

    `armies` are `(player_number, [(unit_type, [(name, x, y), ...]), ...])`.
    The first unit named for each player carries the flag.
    """
    board = Board(*size)
    players = {}
    for number, specs in armies:
        players[number] = Player(number)
        first = True
        for unit_type, units in specs:
            for name, x, y in units:
                board.add(players[number], x, y, name, unit_type)
                if first:
                    board.findUnit(name, players[number]).flag = True
                    first = False
    board.commit(turn=0)
    return board, players


def unit(board, players, number, name):
    return board.findUnit(name, players[number])


class TestControllersRunFirst:

    def test_a_controller_reads_the_board_as_the_turn_began(self):
        # b stands east of a and walks away this turn; a's controller still
        # reads a friend on b's square, because every controller reads the
        # board as the turn began
        looker = UnitType('A', 'a', 1, 4, 10, 5,
                          'SET r6, 1\nSET r7, 0\nMAP r6, r7\nSTORE r0, 0')
        walker = UnitType('B', 'b', 1, 4, 10, 5, 'MOVE east')
        board, players = setup(
            (1, [(looker, [('a', 0, 0)]), (walker, [('b', 1, 0)])]),
            (2, [(walker, [('e', 7, 7)])]))
        board.commit(turn=1)
        assert unit(board, players, 1, 'a').memory[0] == MAP_FRIEND
        assert (unit(board, players, 1, 'b').x,
                unit(board, players, 1, 'b').y) == (2, 0)

    def test_the_orders_are_the_controllers(self):
        mover = UnitType('M', 'm', 1, 4, 10, 5, 'MOVE south')
        holder = UnitType('H', 'h', 1, 4, 10, 5, 'HOLD')
        board, players = setup(
            (1, [(mover, [('m1', 0, 0)]), (holder, [('h1', 3, 0)])]),
            (2, [(holder, [('h2', 7, 7)])]))
        board.commit(turn=1)
        assert (unit(board, players, 1, 'm1').y) == 1
        assert (unit(board, players, 1, 'h1').y) == 0
        # the order is consumed with the turn
        assert unit(board, players, 1, 'm1').state == UnitType.NOP

    def test_a_unit_with_no_controller_is_given_no_order(self):
        turret = UnitType('T', 't', 3, 6, 6, 0)
        hunter = UnitType('H', 'h', 1, 4, 10, 5, 'MOVE south')
        board, players = setup(
            (1, [(turret, [('t1', 0, 0)])]),
            (2, [(hunter, [('h1', 7, 7)])]))
        board.commit(turn=1)
        assert (unit(board, players, 1, 't1').x,
                unit(board, players, 1, 't1').y) == (0, 0)
        assert unit(board, players, 1, 't1').energy == 6

    def test_a_deployed_unit_thinks_only_once_it_stands(self):
        # the setup turn places the units; no controller runs on it
        marker = UnitType('M', 'm', 1, 4, 10, 5, 'SET r0, 1\nSTORE r0, 0')
        board, players = setup((1, [(marker, [('m1', 0, 0)])]),
                               (2, [(marker, [('m2', 7, 7)])]))
        assert unit(board, players, 1, 'm1').memory == {}
        board.commit(turn=1)
        assert unit(board, players, 1, 'm1').memory == {0: 1}

    def test_an_eliminated_players_controllers_do_not_run(self):
        marker = UnitType('M', 'm', 1, 4, 10, 5, 'SET r0, 1\nSTORE r0, 0')
        lance = UnitType('L', 'l', 8, 2, 10, 3, 'MOVE south')
        board, players = setup(
            (1, [(lance, [('l1', 0, 0)])]),
            (2, [(marker, [('m1', 0, 1), ('m2', 7, 7)])]))
        board.commit(turn=1)            # the lance kills m1, the carrier
        assert unit(board, players, 2, 'm1').destroyed
        assert unit(board, players, 2, 'm2').memory == {0: 1}
        unit(board, players, 2, 'm2').memory.clear()
        board.commit(turn=2)            # player 2 is out: m2 thinks nothing
        assert unit(board, players, 2, 'm2').memory == {}

    def test_what_a_controller_did_is_an_event_for_its_owner(self):
        mover = UnitType('M', 'm', 1, 4, 10, 5, 'SELF\nMOVE south')
        board, players = setup((1, [(mover, [('m1', 0, 0)])]),
                               (2, [(mover, [('m2', 7, 7)])]))
        events = board.commit(turn=1)
        thought = [e for e in events if e.kind == 'thought']
        assert len(thought) == 2
        mine = next(e for e in thought if e.detail['unit'] == 'm1')
        assert mine.detail['players'] == '1'
        assert mine.detail['ticks'] == 2
        assert mine.detail['order'] == UnitType.SOUTH
        assert mine.detail['energy'] == 0
        assert board.traces[0]['unit'] == 'm1'


class TestTheMeterOnTheBoard:

    def test_a_small_program_over_several_turns(self):
        pawn = UnitType('P', 'p', 1, 4, 10, 2,
                        '\n'.join(['SELF'] * 60))               # 60 ticks
        board, players = setup((1, [(pawn, [('p1', 0, 0)])]),
                               (2, [(pawn, [('p2', 7, 7)])]))
        me = unit(board, players, 1, 'p1')
        me.energy = 1                    # below the cap, so the gain shows
        energies = []
        for turn in range(1, 6):
            board.commit(turn=turn)
            energies.append(me.energy)
        # two back every turn; the meter charges one on the fourth, when it
        # fills, so that turn nets one
        assert energies == [3, 5, 7, 8, 10]
        assert unit(board, players, 1, 'p1').meter == 100

    def test_thinking_leaves_less_for_the_fare(self):
        thinker = UnitType('T', 't', 1, 4, 10, 2, 'SELF\nMOVE south')
        board, players = setup((1, [(thinker, [('t1', 0, 0)])]),
                               (2, [(thinker, [('t2', 7, 7)])]))
        me = unit(board, players, 1, 't1')
        me.energy = 1
        me.meter = 199
        events = board.commit(turn=1)
        # the meter took its one, the move was refused for it, and the turn
        # then gave two back
        assert me.energy == 0 + UnitType.REST_GAIN
        assert (me.x, me.y) == (0, 0)
        refused = [e for e in events if e.kind == 'refused'
                   and e.detail['unit'] == 't1']
        assert refused and 'energy' in refused[0].detail['reason']

    def test_a_unit_whose_meter_charged_recovers_all_the_same(self):
        thinker = UnitType('T', 't', 1, 4, 10, 1,
                           '\n'.join(['SELF'] * 100))            # 100 ticks
        board, players = setup((1, [(thinker, [('t1', 0, 0)])]),
                               (2, [(thinker, [('t2', 7, 7)])]))
        me = unit(board, players, 1, 't1')
        me.energy = 5
        board.commit(turn=1)
        assert me.energy == 5 - 1 + 2            # paid 1, recovered 2

    def test_a_unit_that_thought_a_little_and_gave_no_order_recovers(self):
        thinker = UnitType('T', 't', 1, 4, 10, 5, 'SELF\nHOLD')
        board, players = setup((1, [(thinker, [('t1', 0, 0)])]),
                               (2, [(thinker, [('t2', 7, 7)])]))
        me = unit(board, players, 1, 't1')
        me.energy = 5
        board.commit(turn=1)
        assert me.energy == 7

    def test_a_halted_controller_holds_and_is_traced(self):
        looper = UnitType('L', 'l', 1, 4, 10, 2, 'MOVE south\nloop:\nSELF\nJMP loop')
        board, players = setup((1, [(looper, [('l1', 0, 0)])]),
                               (2, [(looper, [('l2', 7, 7)])]))
        board.commit(turn=1)
        me = unit(board, players, 1, 'l1')
        assert (me.x, me.y) == (0, 0)
        assert me.trace['halted'] is not None
        assert me.trace['ticks'] == 200 and me.trace['energy'] == 1


class TestTheRadio:

    def test_a_message_sent_this_turn_is_read_next_turn_in_order(self):
        sender_b = UnitType('B', 'b', 1, 4, 10, 5, 'SAY r1, 2, 2, 2')
        sender_a = UnitType('A', 'a', 1, 4, 10, 5, 'SAY r1, 1, 1, 1')
        reader = UnitType('R', 'r', 1, 4, 10, 5,
                          'RECV\nSTORE r1, 0\nRECV\nSTORE r1, 1')
        board, players = setup(
            (1, [(sender_b, [('b', 0, 0)]), (sender_a, [('a', 1, 0)]),
                 (reader, [('r1', 2, 0)])]),
            (2, [(reader, [('r2', 7, 7)])]))
        board.commit(turn=1)
        r1 = unit(board, players, 1, 'r1')
        assert r1.memory == {0: 0, 1: 0}          # nothing had arrived
        assert r1.inbox == [(1, 1, 1), (2, 2, 2)]  # a before b, by name
        board.commit(turn=2)
        assert r1.memory == {0: 1, 1: 2}

    def test_a_broadcast_reaches_every_friendly_controller_and_no_enemy(self):
        crier = UnitType('C', 'c', 1, 4, 10, 5, 'SAY all, 7, 0, 0')
        quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
        turret = UnitType('T', 't', 3, 6, 6, 0)
        board, players = setup(
            (1, [(crier, [('c1', 0, 0)]), (quiet, [('q1', 1, 0)]),
                 (turret, [('t1', 2, 0)])]),
            (2, [(quiet, [('q2', 7, 7)])]))
        board.commit(turn=1)
        assert unit(board, players, 1, 'q1').inbox == [(7, 0, 0)]
        assert unit(board, players, 1, 'c1').inbox == []
        assert unit(board, players, 1, 't1').inbox == []
        assert unit(board, players, 2, 'q2').inbox == []

    def test_a_message_to_an_enemy_is_dropped_into_the_trace(self):
        crier = UnitType('C', 'c', 1, 4, 10, 5, 'SAY q2, 7, 0, 0')
        quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
        board, players = setup((1, [(crier, [('c1', 0, 0)])]),
                               (2, [(quiet, [('q2', 7, 7)])]))
        board.commit(turn=1)
        assert unit(board, players, 2, 'q2').inbox == []
        assert unit(board, players, 1, 'c1').trace['dropped'] == [
            ['q2', 7, 0, 0]]

    def test_the_inbox_persists_until_read(self):
        crier = UnitType('C', 'c', 1, 4, 10, 5, 'SAY q1, 1, 2, 3')
        quiet = UnitType('Q', 'q', 1, 4, 10, 5, 'HOLD')
        board, players = setup((1, [(crier, [('c1', 0, 0)]),
                                    (quiet, [('q1', 1, 0)])]),
                               (2, [(quiet, [('q2', 7, 7)])]))
        for turn in range(1, 5):
            board.commit(turn=turn)
        assert unit(board, players, 1, 'q1').inbox == [(1, 2, 3)] * 4


class TestWhoIAm:

    def test_a_unit_knows_its_number_among_its_type(self):
        teller = UnitType('T', 't', 1, 4, 10, 5, 'SELF\nSTORE r5, 0')
        board, players = setup(
            (1, [(teller, [('t3', 0, 0), ('t1', 1, 0), ('t2', 2, 0)])]),
            (2, [(teller, [('t1', 7, 7)])]))
        board.commit(turn=1)
        assert unit(board, players, 1, 't1').memory == {0: 0}
        assert unit(board, players, 1, 't2').memory == {0: 1}
        assert unit(board, players, 1, 't3').memory == {0: 2}
        assert unit(board, players, 2, 't1').memory == {0: 0}

    def test_two_units_of_one_type_share_nothing_but_code(self):
        counter = UnitType('C', 'c', 1, 4, 10, 5,
                           'LOAD r0, 0\nADD r0, 1\nSTORE r0, 0')
        board, players = setup((1, [(counter, [('c1', 0, 0), ('c2', 1, 0)])]),
                               (2, [(counter, [('c3', 7, 7)])]))
        board.commit(turn=1)
        unit(board, players, 1, 'c1').memory[0] = 10
        board.commit(turn=2)
        assert unit(board, players, 1, 'c1').memory == {0: 11}
        assert unit(board, players, 1, 'c2').memory == {0: 2}
