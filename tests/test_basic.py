import pytest

from board_game_concept import UnitType, Board, Player, Empty, GameData


def test_imports():
    assert UnitType is not None
    assert Board is not None
    assert Player is not None
    assert Empty is not None
    assert GameData is not None


def test_player_creation():
    p1 = Player(1)
    p2 = Player(2)
    p3 = Player(3)

    assert p1.number == 1
    assert p2.number == 2
    assert p3.number == 3


def test_unit_type_creation():
    knight = UnitType('Knight', 'K', 7, 8, 50)
    pawn = UnitType('Pawn', 'P', 3, 4, 30)
    rook = UnitType('Rook', 'R', 10, 10, 100)

    assert knight.name == 'Knight'
    assert knight.symbol == 'K'
    assert knight.attack == 7
    assert knight.health == 8
    assert knight.energy == 50

    assert pawn.name == 'Pawn'
    assert pawn.symbol == 'P'
    assert pawn.attack == 3

    assert rook.attack == 10
    assert rook.health == 10
    assert rook.energy == 100


def test_unit_type_constraints():
    UnitType('Valid', 'V', 5, 5, 50)

    with pytest.raises(AssertionError):
        UnitType('Invalid', 'I', 11, 5, 50)

    with pytest.raises(AssertionError):
        UnitType('Invalid', 'I', 5, 11, 50)

    with pytest.raises(AssertionError):
        UnitType('Invalid', 'I', 5, 5, 101)

    with pytest.raises(AssertionError):
        UnitType('Invalid', 'AB', 5, 5, 50)


def test_board_creation():
    board_4x4 = Board(4, 4)
    board_8x8 = Board(8, 8)
    board_10x10 = Board(10, 10)

    assert board_4x4.size_x == 4
    assert board_4x4.size_y == 4
    assert board_8x8.size_x == 8
    assert board_8x8.size_y == 8
    assert board_10x10.size_x == 10
    assert board_10x10.size_y == 10


def test_empty_cell_representation():
    empty = Empty()
    assert str(empty) == '#'


def test_game_data_initialization():
    game_data = GameData('test-game-001', 0)

    assert game_data.getPlayers() == {}
    assert game_data.getNewGame() is False


def test_unit_type_state_constants():
    assert UnitType.NORTH == 1
    assert UnitType.EAST == 2
    assert UnitType.SOUTH == 3
    assert UnitType.WEST == 4
    assert UnitType.NONE == 0

    assert UnitType.INITIAL == 0
    assert UnitType.MOVING == 1
    assert UnitType.NOP == 2


def test_attack_on_entering_occupied_cell():
    attacker_type = UnitType('Attacker', 'A', 3, 5, 100)
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

    square = board.getUnitByCoords(1, 0)
    assert isinstance(square, UnitType)
    assert square.name == 'a1'
    assert square.player == p1
    assert square.health == 1
    assert defender.destroyed is True


def test_simultaneous_move_to_same_cell_attack():
    red_type = UnitType('Red', 'R', 4, 7, 100)
    blue_type = UnitType('Blue', 'B', 3, 5, 100)

    p1 = Player(1)
    p2 = Player(2)
    board = Board(4, 3)
    board.add(p1, 0, 1, 'r1', red_type)
    board.add(p2, 2, 1, 'b1', blue_type)
    board.commit()

    red = board.getUnitByName('r1')[0]
    blue = board.getUnitByName('b1')[0]
    red.move(UnitType.EAST)
    blue.move(UnitType.WEST)
    board.commit()

    square = board.getUnitByCoords(1, 1)
    assert isinstance(square, UnitType)
    assert square.name == 'r1'
    assert square.player == p1
    assert blue.destroyed is True
