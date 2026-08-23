"""The coordinate system, and what a destroyed unit looks like afterwards.

Both were true of the code and written down nowhere, which is the first thing a
player needs and the first thing another front end would get wrong.
"""

from board_game_concept import Board, Empty, Player, UnitType
from board_game_concept.cli.render import render_board
from board_game_concept.storage.serialise import serialise_units

from game_harness import GameHarness


def one_unit(x, y, size=(4, 3), stats=(1, 5, 50)):
    board = Board(*size)
    board.add(Player(1), x, y, 'u', UnitType('U', 'U', *stats))
    board.commit()
    return board


# --- the coordinate system


def test_the_origin_is_the_north_west_cell():
    board = one_unit(0, 0)
    drawn = render_board(board).splitlines()
    # the first drawn row is y = 0, and the unit at (0, 0) is its first square
    assert drawn[1].startswith('|U|')


def test_the_south_east_cell_is_the_far_corner():
    board = one_unit(3, 2)
    drawn = render_board(board).splitlines()
    assert drawn[-2].endswith('|U|')


def test_x_increases_left_to_right_and_y_top_to_bottom():
    board = Board(4, 3)
    player = Player(1)
    board.add(player, 1, 0, 'a', UnitType('A', 'A', 1, 5, 50))
    board.add(player, 0, 2, 'b', UnitType('B', 'B', 1, 5, 50))
    board.commit()
    rows = [line for line in render_board(board).splitlines()
            if line.startswith('|')]
    assert rows[0] == '|#|A|#|#|'
    assert rows[2] == '|B|#|#|#|'


def test_each_direction_moves_the_axis_the_rules_say():
    for direction, (dx, dy) in ((UnitType.NORTH, (0, -1)),
                                (UnitType.SOUTH, (0, 1)),
                                (UnitType.EAST, (1, 0)),
                                (UnitType.WEST, (-1, 0))):
        board = one_unit(1, 1)
        unit = board.getUnitByName('u')[0]
        board.getUnitByName('u')[0].move(direction)
        board.commit()
        assert (unit.x, unit.y) == (1 + dx, 1 + dy), direction


# --- destroyed units are a marked casualty record


def duel_to_the_death(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 3, [1, 2])
    harness.deploy(1, [('X', 'X', 5, 5, 50)],
                   [('X', 'x1', 0, 0), ('X', 'x2', 0, 2)])
    harness.deploy(2, [('O', 'O', 5, 5, 50)],
                   [('O', 'o1', 1, 0), ('O', 'o2', 3, 2)])
    harness.resolve()
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    return harness


def test_a_player_still_sees_their_own_casualties(tmp_path):
    harness = duel_to_the_death(tmp_path)
    listed = serialise_units(harness.session(1).getBoard())
    assert 'name: "x1"' in listed
    assert 'destroyed: True' in listed
    assert 'on_board: False' in listed


def test_a_casualty_is_not_drawn_on_any_cell(tmp_path):
    harness = duel_to_the_death(tmp_path)
    board = harness.session(1).getBoard()
    assert type(board.getUnitByCoords(0, 0)) is Empty
    assert type(board.getUnitByCoords(1, 0)) is Empty
    assert 'X' not in render_board(board).replace('|', '').replace('+', '')[:8]


def test_an_enemy_casualty_is_listed_for_the_turn_contact_was_made(tmp_path):
    harness = duel_to_the_death(tmp_path)
    listed = serialise_units(harness.session(1).getBoard())
    assert 'name: "o1"' in listed


def test_an_enemy_casualty_drops_out_next_turn(tmp_path):
    harness = duel_to_the_death(tmp_path)
    harness.turn({1: [], 2: []})
    listed = serialise_units(harness.session(1).getBoard())
    assert 'name: "o1"' not in listed
    assert 'name: "x1"' in listed
