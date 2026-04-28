#!/usr/bin/env python3
"""
Board Game Concept - Automated Test Suite
Tests core module functionality without requiring Unix/Linux tools
"""

from BoardGameConcept import UnitType, Board, Player, Empty
from GameData import GameData


def test_imports():
    """Test that all modules can be imported"""
    print("\n[TEST 1] Module Imports")
    try:
        assert UnitType is not None
        assert Board is not None
        assert Player is not None
        assert Empty is not None
        assert GameData is not None
        print("✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_player_creation():
    """Test Player instantiation"""
    print("\n[TEST 2] Player Creation")
    try:
        p1 = Player(1)
        p2 = Player(2)
        p3 = Player(3)
        assert p1.number == 1
        assert p2.number == 2
        assert p3.number == 3
        print(f"✓ Created Player 1, Player 2, Player 3")
        return True
    except Exception as e:
        print(f"✗ Player creation failed: {e}")
        return False


def test_unit_type_creation():
    """Test UnitType instantiation with various stats"""
    print("\n[TEST 3] UnitType Creation")
    try:
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

        print(f"✓ Created Knight (A=7, H=8, E=50)")
        print(f"✓ Created Pawn (A=3, H=4, E=30)")
        print(f"✓ Created Rook (A=10, H=10, E=100)")
        return True
    except Exception as e:
        print(f"✗ UnitType creation failed: {e}")
        return False


def test_unit_type_constraints():
    """Test UnitType validation constraints"""
    print("\n[TEST 4] UnitType Validation Constraints")
    try:
        # Valid unit
        valid_unit = UnitType('Valid', 'V', 5, 5, 50)
        print(f"✓ Created valid unit with constrained values")

        # Test invalid attack (too high)
        try:
            invalid_attack = UnitType('Invalid', 'I', 11, 5, 50)
            print(f"✗ Should have rejected attack > 10")
            return False
        except AssertionError:
            print(f"✓ Correctly rejected attack value > 10")

        # Test invalid health (too high)
        try:
            invalid_health = UnitType('Invalid', 'I', 5, 11, 50)
            print(f"✗ Should have rejected health > 10")
            return False
        except AssertionError:
            print(f"✓ Correctly rejected health value > 10")

        # Test invalid energy (too high)
        try:
            invalid_energy = UnitType('Invalid', 'I', 5, 5, 101)
            print(f"✗ Should have rejected energy > 100")
            return False
        except AssertionError:
            print(f"✓ Correctly rejected energy value > 100")

        # Test invalid symbol (must be single character)
        try:
            invalid_symbol = UnitType('Invalid', 'AB', 5, 5, 50)
            print(f"✗ Should have rejected multi-character symbol")
            return False
        except AssertionError:
            print(f"✓ Correctly rejected multi-character symbol")

        return True
    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False


def test_board_creation():
    """Test Board instantiation with various sizes"""
    print("\n[TEST 5] Board Creation")
    try:
        board_4x4 = Board(4, 4)
        board_8x8 = Board(8, 8)
        board_10x10 = Board(10, 10)

        assert board_4x4.size_x == 4
        assert board_4x4.size_y == 4
        assert board_8x8.size_x == 8
        assert board_8x8.size_y == 8
        assert board_10x10.size_x == 10
        assert board_10x10.size_y == 10

        print(f"✓ Created Board 4x4")
        print(f"✓ Created Board 8x8")
        print(f"✓ Created Board 10x10")
        return True
    except Exception as e:
        print(f"✗ Board creation failed: {e}")
        return False


def test_empty_cell():
    """Test Empty cell representation"""
    print("\n[TEST 6] Empty Cell Representation")
    try:
        empty = Empty()
        assert str(empty) == "#"
        print(f"✓ Empty cell displays as: '{str(empty)}'")
        return True
    except Exception as e:
        print(f"✗ Empty cell test failed: {e}")
        return False


def test_game_data_initialization():
    """Test GameData initialization"""
    print("\n[TEST 7] GameData Initialization")
    try:
        game_data = GameData('test-game-001', 0)
        print(f"✓ GameData initialized for game 'test-game-001'")

        # Test accessing game data methods
        players = game_data.getPlayers()
        print(f"✓ getPlayers() method works")

        new_game = game_data.getNewGame()
        print(f"✓ getNewGame() method works")

        return True
    except Exception as e:
        print(f"✗ GameData initialization failed: {e}")
        return False


def test_unit_type_state_constants():
    """Test UnitType state and direction constants"""
    print("\n[TEST 8] UnitType Constants")
    try:
        # Test direction constants
        assert UnitType.NORTH == 1
        assert UnitType.EAST == 2
        assert UnitType.SOUTH == 3
        assert UnitType.WEST == 4
        assert UnitType.NONE == 0
        print(
            f"✓ Direction constants: NORTH={
                UnitType.NORTH}, EAST={
                UnitType.EAST}, SOUTH={
                UnitType.SOUTH}, WEST={
                    UnitType.WEST}")

        # Test state constants
        assert UnitType.INITIAL == 0
        assert UnitType.MOVING == 1
        assert UnitType.NOP == 2
        print(
            f"✓ State constants: INITIAL={
                UnitType.INITIAL}, MOVING={
                UnitType.MOVING}, NOP={
                UnitType.NOP}")

        return True
    except Exception as e:
        print(f"✗ Constants test failed: {e}")
        return False


def test_attack_on_entering_occupied_cell():
    """Test attack resolution when a unit moves into an occupied cell"""
    print("\n[TEST 9] Attack on Occupied Cell")
    try:
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
        assert type(square) is UnitType
        assert square.name == 'a1'
        assert square.player == p1
        assert square.health == 3
        assert defender.destroyed is True

        print('✓ Combat on entry resolved and victor occupies the target cell')
        return True
    except Exception as e:
        print(f"✗ Attack on occupied cell failed: {e}")
        return False


def test_simultaneous_move_to_same_cell_attack():
    """Test attack resolution when two units move into the same empty cell"""
    print("\n[TEST 10] Simultaneous Move into Same Cell")
    try:
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
        assert type(square) is UnitType
        assert square.name == 'r1'
        assert square.player == p1
        assert blue.destroyed is True

        print('✓ Simultaneous move combat resolved with a single victor occupying the cell')
        return True
    except Exception as e:
        print(f"✗ Simultaneous move attack failed: {e}")
        return False


def main():
    print("=" * 70)
    print("BOARD GAME CONCEPT - AUTOMATED TEST SUITE")
    print("=" * 70)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Player Creation", test_player_creation()))
    results.append(("UnitType Creation", test_unit_type_creation()))
    results.append(("UnitType Validation", test_unit_type_constraints()))
    results.append(("Board Creation", test_board_creation()))
    results.append(("Empty Cell", test_empty_cell()))
    results.append(
        ("GameData Initialization",
         test_game_data_initialization()))
    results.append(("UnitType Constants", test_unit_type_state_constants()))
    results.append(("Attack on Occupied Cell",
                    test_attack_on_entering_occupied_cell()))
    results.append(("Simultaneous Move Combat",
                    test_simultaneous_move_to_same_cell_attack()))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status:12} {test_name}")

    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit(main())
