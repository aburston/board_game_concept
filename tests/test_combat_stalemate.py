"""Regression coverage for the contested-cell rules.

Combat ends when a round lands no attacks, running out of energy makes a unit
inert rather than dead, and a contest nobody wins sends every unit that moved in
back to the cell it came from.
"""

import threading

from board_game_concept import UnitType, Board, Player, Empty


def commit_within(board, seconds=30):
    """Commit the turn, failing rather than hanging if it does not terminate."""
    error = []

    def run():
        try:
            board.commit()
        except BaseException as exc:  # pragma: no cover - reported below
            error.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(seconds)
    assert not worker.is_alive(), (
        f"board.commit() did not terminate within {seconds}s"
    )
    if error:
        raise error[0]


def _spent_board():
    """Two units with less energy than their attack value, facing each other."""
    red_type = UnitType('Red', 'R', 4, 7, 3)
    blue_type = UnitType('Blue', 'B', 3, 5, 2)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 3)
    board.add(p1, 0, 1, 'r1', red_type)
    board.add(p2, 2, 1, 'b1', blue_type)
    board.commit()
    return board, p1, p2


def test_contest_no_contestant_can_win_terminates():
    # two units too spent to attack move into the same empty cell: resolution
    # used to spin forever waiting for a casualty that could never happen
    board, _, _ = _spent_board()
    red = board.getUnitByName('r1')[0]
    blue = board.getUnitByName('b1')[0]

    red.move(UnitType.EAST)
    blue.move(UnitType.WEST)
    commit_within(board)

    assert red.destroyed is False
    assert blue.destroyed is False


def test_stalemate_destroys_nobody_and_leaves_units_on_the_board():
    board, _, _ = _spent_board()
    red = board.getUnitByName('r1')[0]
    blue = board.getUnitByName('b1')[0]

    red.move(UnitType.EAST)
    blue.move(UnitType.WEST)
    board.commit()

    assert red.destroyed is False
    assert blue.destroyed is False
    assert red.on_board is True
    assert blue.on_board is True


def test_stalemated_units_retreat_and_nobody_takes_the_cell():
    board, p1, p2 = _spent_board()
    red = board.getUnitByName('r1')[0]
    blue = board.getUnitByName('b1')[0]

    red.move(UnitType.EAST)
    blue.move(UnitType.WEST)
    board.commit()

    # nobody wins the contested cell
    assert isinstance(board.getUnitByCoords(1, 1), Empty)

    # and every contestant is back where it started
    assert (red.x, red.y) == (0, 1)
    assert (blue.x, blue.y) == (2, 1)
    assert board.getUnitByCoords(0, 1) is red
    assert board.getUnitByCoords(2, 1) is blue


def test_inert_unit_holds_its_cell_and_the_attacker_falls_back():
    # a spent defender standing still is inert, not dead: it keeps its cell, and
    # an attacker that cannot finish it off returns to its own
    defender_type = UnitType('Defender', 'D', 5, 6, 1)
    attacker_type = UnitType('Attacker', 'A', 6, 6, 2)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 2)
    board.add(p1, 0, 0, 'a1', attacker_type)
    board.add(p2, 1, 0, 'd1', defender_type)
    board.commit()

    attacker = board.getUnitByName('a1')[0]
    defender = board.getUnitByName('d1')[0]
    attacker.move(UnitType.EAST)
    board.commit()

    assert defender.destroyed is False
    assert defender.on_board is True
    assert board.getUnitByCoords(1, 0) is defender
    assert board.getUnitByCoords(0, 0) is attacker
    assert (attacker.x, attacker.y) == (0, 0)


def test_inert_unit_can_still_be_destroyed_by_an_opponent_with_energy():
    inert_type = UnitType('Inert', 'I', 9, 2, 1)
    strong_type = UnitType('Strong', 'S', 4, 8, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 2)
    board.add(p1, 0, 0, 's1', strong_type)
    board.add(p2, 1, 0, 'i1', inert_type)
    board.commit()

    strong = board.getUnitByName('s1')[0]
    inert = board.getUnitByName('i1')[0]
    # the inert unit cannot pay for an attack of 9 with 1 energy
    assert inert.energy < inert.attack

    strong.move(UnitType.EAST)
    board.commit()

    assert inert.destroyed is True
    assert inert.on_board is False
    assert board.getUnitByCoords(1, 0) is strong


def _three_way_board():
    """Three units converging on one cell, resolving over two attack rounds."""
    strong_type = UnitType('Strong', 'S', 5, 10, 100)
    medium_type = UnitType('Medium', 'M', 1, 10, 100)
    weak_type = UnitType('Weak', 'W', 1, 6, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(3, 3)
    board.add(p1, 1, 0, 's1', strong_type)
    board.add(p2, 0, 1, 'm1', medium_type)
    board.add(p2, 2, 1, 'w1', weak_type)
    board.commit()

    board.getUnitByName('s1')[0].move(UnitType.SOUTH)
    board.getUnitByName('m1')[0].move(UnitType.EAST)
    board.getUnitByName('w1')[0].move(UnitType.WEST)
    return board


def test_three_way_contest_leaves_the_sole_survivor_holding_the_cell():
    # the survivor count used to be decremented once per destroyed unit per
    # round, so by the second round it counted the first casualty again, reached
    # zero, and emptied the cell out from under the unit still standing
    board = _three_way_board()
    board.commit()

    strong = board.getUnitByName('s1')[0]
    medium = board.getUnitByName('m1')[0]
    weak = board.getUnitByName('w1')[0]

    assert weak.destroyed is True
    assert medium.destroyed is True
    assert strong.destroyed is False
    assert board.getUnitByCoords(1, 1) is strong


def test_a_destroyed_unit_does_not_attack_in_later_rounds():
    # the survivor holds 7 health only if the unit destroyed in the first round
    # stops attacking in the second
    board = _three_way_board()
    board.commit()

    strong = board.getUnitByName('s1')[0]
    assert strong.health == 7


def test_contest_with_no_survivors_empties_the_cell():
    a_type = UnitType('Aye', 'A', 5, 4, 100)
    b_type = UnitType('Bee', 'B', 5, 4, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 3)
    board.add(p1, 0, 1, 'a1', a_type)
    board.add(p2, 2, 1, 'b1', b_type)
    board.commit()

    a1 = board.getUnitByName('a1')[0]
    b1 = board.getUnitByName('b1')[0]
    a1.move(UnitType.EAST)
    b1.move(UnitType.WEST)
    board.commit()

    assert a1.destroyed is True
    assert b1.destroyed is True
    assert isinstance(board.getUnitByCoords(1, 1), Empty)


def test_friendly_fire_units_do_not_spare_their_own_side():
    own_type = UnitType('Own', 'O', 4, 4, 100)

    p1 = Player(1)
    board = Board(4, 3)
    board.add(p1, 0, 1, 'o1', own_type)
    board.add(p1, 2, 1, 'o2', own_type)
    board.commit()

    o1 = board.getUnitByName('o1')[0]
    o2 = board.getUnitByName('o2')[0]
    o1.move(UnitType.EAST)
    o2.move(UnitType.WEST)
    board.commit()

    # same player, but they still fight
    assert o1.destroyed is True
    assert o2.destroyed is True


def test_deploying_onto_an_occupied_cell_is_a_contest_not_a_crash():
    # issue #1: this used to raise an uncaught AssertionError
    holder_type = UnitType('Holder', 'H', 2, 3, 100)
    comer_type = UnitType('Comer', 'C', 5, 6, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 3)
    board.add(p1, 1, 1, 'h1', holder_type)
    board.commit()

    board.add(p2, 1, 1, 'c1', comer_type)
    board.commit()

    holder = board.getUnitByName('h1')[0]
    comer = board.getUnitByName('c1')[0]
    assert holder.destroyed is True
    assert board.getUnitByCoords(1, 1) is comer


def test_deploying_two_of_your_own_units_onto_one_cell_is_handled():
    # issue #1 as reported: a player adding two units at the same location
    naught_type = UnitType('Naught', 'O', 1, 1, 10)

    p1 = Player(1)
    board = Board(4, 4)
    board.add(p1, 0, 0, 'o1', naught_type)
    board.add(p1, 0, 0, 'o2', naught_type)
    board.commit()

    o1 = board.getUnitByName('o1')[0]
    o2 = board.getUnitByName('o2')[0]
    # they contest the cell rather than crashing the turn
    assert o1.destroyed or o2.destroyed
    board.print()
    board.print(p1)


def _inert_stack_board():
    """A cell two spent units share because neither can attack or fall back."""
    inert_type = UnitType('Inert', 'I', 9, 5, 1)
    other_type = UnitType('Other', 'T', 9, 5, 1)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 3)
    board.add(p1, 1, 1, 'i1', inert_type)
    board.add(p2, 1, 1, 't1', other_type)
    board.commit()
    return board, p1, p2


def test_units_that_cannot_fall_back_share_the_cell():
    board, _, _ = _inert_stack_board()
    cell = board.getUnitByCoords(1, 1)

    assert isinstance(cell, list)
    assert sorted(unit.name for unit in cell) == ['i1', 't1']
    assert all(unit.destroyed is False for unit in cell)
    assert all(unit.on_board is True for unit in cell)


def test_shared_cell_renders_without_failing(capsys):
    board, p1, p2 = _inert_stack_board()

    board.print()
    full = capsys.readouterr().out
    assert 'object at' not in full
    assert '[' not in full

    board.print(p1)
    for_p1 = capsys.readouterr().out
    # the player sees their own unit in the shared cell
    assert 'I' in for_p1
    assert 'T' not in for_p1

    board.print(p2)
    for_p2 = capsys.readouterr().out
    assert 'T' in for_p2
    assert 'I' not in for_p2


def test_shared_cell_survives_a_save_and_load_round_trip():
    # reload a game the way GameData does: read back the units it wrote with
    # listUnits and replay them onto a fresh board
    import yaml

    board, _, _ = _inert_stack_board()
    saved = yaml.safe_load(board.listUnits())

    players = {}
    types = {}
    reloaded = Board(board.size_x, board.size_y)
    for unit in saved['units']:
        number = unit['player']
        players.setdefault(number, Player(number))
        types.setdefault(unit['type'], UnitType(
            unit['type'], unit['symbol'], int(unit['attack']),
            int(unit['health']), int(unit['energy'])))
        reloaded.add(
            players[number], unit['x'], unit['y'], unit['name'],
            types[unit['type']], int(unit['health']), int(unit['energy']),
            bool(unit['destroyed']), bool(unit['on_board']))
    reloaded.commit()

    cell = reloaded.getUnitByCoords(1, 1)
    assert isinstance(cell, list)
    assert sorted(unit.name for unit in cell) == ['i1', 't1']


def test_a_move_order_applies_to_the_named_unit_on_a_shared_cell():
    # getUnitByCoords returns a list for a shared cell and has no move method,
    # so the server resolves an order against the unit it names
    board, p1, p2 = _inert_stack_board()
    assert isinstance(board.getUnitByCoords(1, 1), list)

    i1 = board.getUnitByName('i1', p1)[0]
    t1 = board.getUnitByName('t1', p2)[0]
    assert i1.name == 'i1' and i1.player is p1
    assert t1.name == 't1' and t1.player is p2

    # i1 has energy 1, enough to pay the cost of one move
    i1.move(UnitType.EAST)
    board.commit()

    assert (i1.x, i1.y) == (2, 1)
    assert board.getUnitByCoords(2, 1) is i1
    # the unit left behind is unaffected and now holds the cell alone
    assert board.getUnitByCoords(1, 1) is t1
    assert (t1.x, t1.y) == (1, 1)
