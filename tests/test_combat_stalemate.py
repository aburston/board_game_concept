"""Regression coverage for the contested-square rules.

Combat ends when a round lands no attacks, running out of energy makes a unit
inert rather than dead, and a contest nobody wins sends every unit that moved in
back to the square it came from. Deploying a brand new unit onto a square that
is already taken is illegal and refused.
"""

import threading

import pytest

from board_game_concept.storage.serialise import units_document
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
    """Two units the fare leaves too spent to attack, facing each other.

    A move costs a unit its health, so each of these arrives having spent
    everything it had on getting there and can pay for no attack at all.
    """
    red_type = UnitType('Red', 'R', 4, 7, 7)
    blue_type = UnitType('Blue', 'B', 3, 5, 5)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 3)
    board.add(p1, 0, 1, 'r1', red_type)
    board.add(p2, 2, 1, 'b1', blue_type)
    board.commit()
    return board, p1, p2


def test_contest_no_contestant_can_win_terminates():
    # two units too spent to attack move into the same empty square: resolution
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

    # nobody wins the contested square
    assert isinstance(board.getUnitByCoords(1, 1), Empty)

    # and every contestant is back where it started
    assert (red.x, red.y) == (0, 1)
    assert (blue.x, blue.y) == (2, 1)
    assert board.getUnitByCoords(0, 1) is red
    assert board.getUnitByCoords(2, 1) is blue


def test_inert_unit_holds_its_cell_and_the_attacker_falls_back():
    # a spent defender standing still is inert, not dead: it keeps its square, and
    # an attacker that cannot finish it off returns to its own
    defender_type = UnitType('Defender', 'D', 5, 6, 6)
    attacker_type = UnitType('Attacker', 'A', 6, 6, 6)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 2)
    # the attacker holds exactly the fare, so it arrives with nothing left to
    # strike with; the defender was run down to a point long ago
    board.add(p1, 0, 0, 'a1', attacker_type)
    board.add(p2, 1, 0, 'd1', defender_type, energy=1)
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
    inert_type = UnitType('Inert', 'I', 9, 2, 2)
    strong_type = UnitType('Strong', 'S', 4, 8, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 2)
    board.add(p1, 0, 0, 's1', strong_type)
    board.add(p2, 1, 0, 'i1', inert_type, energy=1)
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
    """Three units converging on one square, decided in the one exchange.

    The strong unit hits hard enough to destroy both others outright, so that
    a single exchange leaves it the sole survivor. Two units that merely
    wounded each other would both be left standing and turned back - a fight
    is one exchange a turn now, not a grind to the last unit.
    """
    strong_type = UnitType('Strong', 'S', 10, 10, 100)
    medium_type = UnitType('Medium', 'M', 1, 5, 100)
    weak_type = UnitType('Weak', 'W', 1, 5, 100)

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
    # one exchange, two casualties: the strong unit outlasts a square it
    # cleared in a single strike
    board = _three_way_board()
    board.commit()

    strong = board.getUnitByName('s1')[0]
    medium = board.getUnitByName('m1')[0]
    weak = board.getUnitByName('w1')[0]

    assert weak.destroyed is True
    assert medium.destroyed is True
    assert strong.destroyed is False
    assert board.getUnitByCoords(1, 1) is strong


def test_a_unit_destroyed_in_the_exchange_still_lands_its_blow():
    # both casualties strike in the same instant they are destroyed, so the
    # survivor takes a point from each: 10 health, less 1 and 1, is 8. All the
    # blows of an exchange land together, whoever the exchange destroys
    board = _three_way_board()
    board.commit()

    strong = board.getUnitByName('s1')[0]
    assert strong.health == 8


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


def test_deploying_onto_an_occupied_square_is_rejected():
    # issue #1: this used to raise an uncaught AssertionError out of the turn
    # and kill the session. Deployment onto a taken square is illegal, and is
    # now refused when the unit is created
    holder_type = UnitType('Holder', 'H', 2, 3, 100)
    comer_type = UnitType('Comer', 'C', 5, 6, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 3)
    board.add(p1, 1, 1, 'h1', holder_type)
    board.commit()

    with pytest.raises(AssertionError, match='occupied'):
        board.add(p2, 1, 1, 'c1', comer_type)

    # the square is untouched and the turn still resolves
    holder = board.getUnitByName('h1')[0]
    board.commit()
    assert board.getUnitByCoords(1, 1) is holder
    assert holder.destroyed is False


def test_deploying_two_of_your_own_units_onto_one_square_is_rejected():
    # issue #1 as reported: a player adding two units at the same location.
    # The second is refused before the turn is resolved, while both are still
    # waiting to be placed
    naught_type = UnitType('Naught', 'O', 1, 1, 10)

    p1 = Player(1)
    board = Board(4, 4)
    board.add(p1, 0, 0, 'o1', naught_type)

    with pytest.raises(AssertionError, match='occupied'):
        board.add(p1, 0, 0, 'o2', naught_type)

    board.commit()
    assert board.getUnitByCoords(0, 0) is board.getUnitByName('o1')[0]


def test_deployment_is_rejected_out_of_bounds_before_the_occupancy_check():
    naught_type = UnitType('Naught', 'O', 1, 1, 10)
    p1 = Player(1)
    board = Board(4, 4)

    with pytest.raises(AssertionError, match='out of bounds'):
        board.add(p1, 4, 0, 'o1', naught_type)


def test_a_rejected_deployment_leaves_no_trace_of_the_unit():
    naught_type = UnitType('Naught', 'O', 1, 1, 10)
    p1 = Player(1)
    board = Board(4, 4)
    board.add(p1, 0, 0, 'o1', naught_type)

    with pytest.raises(AssertionError):
        board.add(p1, 0, 0, 'o2', naught_type)

    # the refused unit was never registered
    assert len(board.units) == 1
    assert 'o2' not in board.unit_dict


def test_moving_onto_an_occupied_square_is_still_allowed():
    # a move into a held square is combat, not a deployment, and stays legal.
    # The attacker strikes hard enough to clear the square in the one exchange
    # a turn now buys - a lighter attacker would leave the defender standing
    # and be turned back, which the undecided tests below cover
    attacker_type = UnitType('Attacker', 'A', 4, 5, 100)
    defender_type = UnitType('Defender', 'D', 2, 4, 100)

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

    assert defender.destroyed is True
    assert board.getUnitByCoords(1, 0) is attacker


def _shared_cell_board():
    """A square two units share because neither of them can fall back.

    Deployment onto a taken square is illegal, so the only way a square ends up
    holding more than one unit is a contest nobody won in which every survivor
    found the square it came from already taken.
    """
    # light enough to afford the fare twice over, and hitting far harder than
    # it can pay for: each arrives holding less than its attack value, so the
    # contest in the middle square is one nobody can win
    aye_type = UnitType('Aye', 'A', 5, 2, 4)
    bee_type = UnitType('Bee', 'B', 5, 2, 4)
    cee_type = UnitType('Cee', 'C', 5, 2, 2)
    dee_type = UnitType('Dee', 'D', 5, 2, 2)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(3, 3)
    board.add(p1, 0, 0, 'a1', aye_type)
    board.add(p2, 2, 0, 'b1', bee_type)
    board.add(p1, 0, 1, 'c1', cee_type)
    board.add(p2, 2, 1, 'd1', dee_type)
    board.commit()

    # a1 and b1 contest the middle of the top row and neither can attack, while
    # c1 and d1 move into the squares they came from
    board.getUnitByName('a1')[0].move(UnitType.EAST)
    board.getUnitByName('b1')[0].move(UnitType.WEST)
    board.getUnitByName('c1')[0].move(UnitType.NORTH)
    board.getUnitByName('d1')[0].move(UnitType.NORTH)
    board.commit()
    return board, p1, p2


def test_units_that_cannot_fall_back_share_the_square():
    board, _, _ = _shared_cell_board()
    square = board.getUnitByCoords(1, 0)

    assert isinstance(square, list)
    assert sorted(unit.name for unit in square) == ['a1', 'b1']
    assert all(unit.destroyed is False for unit in square)
    assert all(unit.on_board is True for unit in square)


def test_shared_square_renders_without_failing():
    from board_game_concept.cli.render import render_board

    board, p1, p2 = _shared_cell_board()

    full = render_board(board)
    assert 'object at' not in full
    assert '[' not in full

    for_p1 = render_board(board, p1)
    # the player sees their own unit in the shared square, and none of the
    # other player's units anywhere
    assert 'A' in for_p1
    assert 'C' in for_p1
    assert 'B' not in for_p1
    assert 'D' not in for_p1

    for_p2 = render_board(board, p2)
    assert 'B' in for_p2
    assert 'D' in for_p2
    assert 'A' not in for_p2
    assert 'C' not in for_p2


def test_shared_square_survives_a_save_and_load_round_trip():
    # reload a game the way GameData does: read back the units it wrote with
    # units_document and replay them onto a fresh board. Restoring is not a
    # deployment, so the occupancy rule does not refuse the shared square
    board, _, _ = _shared_cell_board()
    saved = units_document(board)

    players = {}
    types = {}
    reloaded = Board(board.size_x, board.size_y)
    for unit in saved['units']:
        # a unit dump writes the player number as text; GameData converts it
        # back on the way in, and so does this
        number = int(unit['player'])
        players.setdefault(number, Player(number))
        # GameData rebuilds types from the player's type definitions and
        # then overrides health and energy per unit, so a unit that has spent
        # all its energy still reloads
        types.setdefault(unit['type'], UnitType(
            unit['type'], unit['symbol'], int(unit['attack']), 2, 4))
        reloaded.add(
            players[number], unit['x'], unit['y'], unit['name'],
            types[unit['type']], int(unit['health']), int(unit['energy']),
            bool(unit['destroyed']), bool(unit['on_board']),
            restoring=True)
    reloaded.commit()

    square = reloaded.getUnitByCoords(1, 0)
    assert isinstance(square, list)
    assert sorted(unit.name for unit in square) == ['a1', 'b1']
    assert all(unit.destroyed is False for unit in square)


def test_a_move_order_applies_to_the_named_unit_on_a_shared_square():
    # getUnitByCoords returns a list for a shared square and has no move
    # method, so the server resolves an order against the unit it names
    board, p1, p2 = _shared_cell_board()
    assert isinstance(board.getUnitByCoords(1, 0), list)

    a1 = board.getUnitByName('a1', p1)[0]
    b1 = board.getUnitByName('b1', p2)[0]
    assert a1.name == 'a1' and a1.player is p1
    assert b1.name == 'b1' and b1.player is p2

    # a1 still has the energy to pay for one move
    a1.move(UnitType.SOUTH)
    board.commit()

    assert (a1.x, a1.y) == (1, 1)
    assert board.getUnitByCoords(1, 1) is a1
    # the unit left behind is unaffected and now holds the square alone
    assert board.getUnitByCoords(1, 0) is b1
    assert (b1.x, b1.y) == (1, 0)
    assert b1.destroyed is False
    assert b1.on_board is True
