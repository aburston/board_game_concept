"""Movement planned against the board as the turn began, then applied at once.

These are the scenarios `unit-movement` gained with the `fix-rules-defects`
change: nothing depends on the order units are held in, and two units ordered
into each other's squares collide instead of passing through.
"""

from board_game_concept import Board, Player, UnitType


def board_with(units, size_x=6, size_y=3):
    """`units` are `(player, name, x, y, attack, health, energy)`."""
    board = Board(size_x, size_y)
    players = {}
    for number, name, x, y, attack, health, energy in units:
        player = players.setdefault(number, Player(number))
        board.add(player, x, y, name,
                  UnitType(name, name[0].upper(), attack, health, energy))
    board.commit()
    return board


def order(board, *orders):
    for name, direction in orders:
        board.getUnitByName(name)[0].move(direction)
    return board.commit()


def at(board, name):
    unit = board.getUnitByName(name)[0]
    return (unit.x, unit.y)


# --- what a move costs


def test_a_move_costs_the_units_health_from_any_starting_energy():
    # the fare is the unit's health, and it is the same fare however much it
    # happens to be carrying. `test_movement_cost.py` is about the rule itself
    for energy in (5, 6, 50, 99, 100):
        board = board_with([(1, 'u', 0, 0, 1, 5, energy)])
        order(board, ('u', UnitType.EAST))
        assert board.getUnitByName('u')[0].energy == energy - 5


def test_a_unit_with_no_energy_does_not_move():
    board = board_with([(1, 'u', 0, 0, 1, 5, 5)])
    board.getUnitByName('u')[0].setEnergy(0)
    events = order(board, ('u', UnitType.EAST))
    assert at(board, 'u') == (0, 0)
    assert board.getUnitByName('u')[0].energy == 0
    assert any(e.kind == 'refused' for e in events)


def test_a_move_off_the_board_is_refused_and_costs_nothing():
    board = board_with([(1, 'u', 0, 0, 1, 5, 50)])
    events = order(board, ('u', UnitType.WEST))
    assert at(board, 'u') == (0, 0)
    assert board.getUnitByName('u')[0].energy == 50
    assert [e.detail['reason'] for e in events if e.kind == 'refused'] == [
        'the move would leave the board']


# --- resolution does not depend on the order units are held in


def test_a_chain_of_units_advances_together():
    board = board_with([(1, 'a', 0, 0, 1, 5, 50),
                        (1, 'b', 1, 0, 1, 5, 50),
                        (1, 'c', 2, 0, 1, 5, 50)])
    events = order(board, ('a', UnitType.EAST), ('b', UnitType.EAST),
                   ('c', UnitType.EAST))
    assert (at(board, 'a'), at(board, 'b'), at(board, 'c')) == (
        (1, 0), (2, 0), (3, 0))
    assert not any(e.kind == 'contested' for e in events)


def test_following_a_unit_that_moves_away_starts_no_contest():
    board = board_with([(1, 'lead', 1, 0, 4, 5, 5),
                        (2, 'chase', 2, 0, 3, 3, 3)])
    events = order(board, ('lead', UnitType.SOUTH), ('chase', UnitType.WEST))
    assert at(board, 'lead') == (1, 1)
    assert at(board, 'chase') == (1, 0)
    assert not any(e.kind == 'contested' for e in events)


def test_moving_into_a_cell_whose_occupant_stays_contests_it():
    board = board_with([(1, 'a', 0, 0, 1, 10, 50), (2, 'b', 1, 0, 1, 10, 50)])
    events = order(board, ('a', UnitType.EAST))
    assert any(e.kind == 'contested' for e in events)


def test_two_movers_and_a_stander_all_contest_one_cell():
    board = board_with([(1, 'a', 0, 1, 1, 10, 50),
                        (2, 'b', 2, 1, 1, 10, 50),
                        (2, 'c', 1, 1, 1, 10, 50)])
    events = order(board, ('a', UnitType.EAST), ('b', UnitType.WEST))
    contested = [e for e in events if e.kind == 'contested']
    assert len(contested) == 1
    assert contested[0].detail['units'] == 3


# --- head-on collisions


def facing(attack_a, health_a, attack_b, health_b, energy=50):
    return board_with([(1, 'a', 0, 0, attack_a, health_a, energy),
                       (2, 'b', 1, 0, attack_b, health_b, energy)])


def collide(board):
    return order(board, ('a', UnitType.EAST), ('b', UnitType.WEST))


def test_a_collision_is_fought_and_both_units_pay():
    board = facing(1, 10, 1, 10)
    events = collide(board)
    a = board.getUnitByName('a')[0]
    b = board.getUnitByName('b')[0]
    assert any(e.kind == 'collided' for e in events)
    assert a.health < 10 and b.health < 10
    assert b in a.seen_by and a in b.seen_by


def test_one_survivor_completes_its_move():
    # a kills b in a single round, and takes the square b held
    board = facing(10, 10, 1, 1)
    collide(board)
    a = board.getUnitByName('a')[0]
    b = board.getUnitByName('b')[0]
    assert b.destroyed and not b.on_board
    assert (a.x, a.y) == (1, 0)
    assert board.getUnitByCoords(1, 0) is a
    assert type(board.getUnitByCoords(0, 0)).__name__ == 'Empty'


def test_neither_survivor_leaves_both_cells_empty():
    board = facing(10, 10, 10, 10)
    collide(board)
    for x in (0, 1):
        assert type(board.getUnitByCoords(x, 0)).__name__ == 'Empty'
    assert all(unit.destroyed for unit in board.units)


def test_an_undecided_collision_leaves_both_where_they_started():
    board = facing(5, 5, 5, 5, energy=5)
    events = collide(board)
    a = board.getUnitByName('a')[0]
    b = board.getUnitByName('b')[0]
    # five health is a fare of five, which is everything either of them had:
    # both paid it, and neither could then pay to attack
    assert a.energy == 0 and b.energy == 0
    assert (a.x, a.y) == (0, 0) and (b.x, b.y) == (1, 0)
    assert not a.destroyed and not b.destroyed
    assert any(e.kind == 'undecided' for e in events)


def test_units_never_trade_squares():
    board = facing(1, 10, 1, 10)
    collide(board)
    a = board.getUnitByName('a')[0]
    b = board.getUnitByName('b')[0]
    assert not ((a.x, a.y) == (1, 0) and (b.x, b.y) == (0, 0))
