"""What a player is told about the turn the server just resolved.

Rejections used to cover only orders refused while they were being applied. A
move nobody could pay for, a move off the board, and a contest that decided
nothing were all dropped in silence, so "my unit didn't move" was
indistinguishable from "the server never got my order".
"""

from board_game_concept.domain import Player, UnitType

from game_harness import GameHarness


def a_game(tmp_path, stats=(5, 5, 50), enemy=None, size=(4, 3)):
    harness = GameHarness(tmp_path)
    harness.create(size[0], size[1], [1, 2])
    harness.deploy(1, [('X', 'X', *stats)], [('X', 'x1', 1, 0)])
    harness.deploy(2, [('O', 'O', *(enemy or stats))], [('O', 'o1', 3, 2)])
    harness.resolve()
    return harness


def reasons(harness, player_number):
    return [entry['reason'] for entry in harness.rejections(player_number)]


def test_a_move_off_the_board_is_reported(tmp_path):
    harness = a_game(tmp_path)
    harness.turn({1: [('x1', UnitType.NORTH)], 2: []})
    assert reasons(harness, 1) == ['the move would leave the board']
    assert reasons(harness, 2) == []


def test_a_move_nobody_can_pay_for_is_reported(tmp_path):
    # x2 never moves and keeps its energy: spending x1 down to nothing would
    # otherwise put player 1 out of the game (R7.1) and end it before the
    # order this test is about could be refused
    harness = GameHarness(tmp_path)
    # four rows: player 1 owns rows 0 and 1, so the reserve waits on row 1
    # rather than on row 2, which is player 2's half now
    harness.create(4, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 5, 5, 50)],
                   [('X', 'x1', 1, 0), ('X', 'x2', 0, 1)])
    harness.deploy(2, [('O', 'O', 5, 5, 50)], [('O', 'o1', 3, 3)])
    harness.resolve()

    # spend x1 down to nothing
    for _ in range(50):
        harness.turn({1: [('x1', UnitType.EAST if _ % 2 else UnitType.WEST)],
                      2: []})
    assert harness.units()['x1'].energy == 0

    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert reasons(harness, 1) == ['not enough energy to move']


def test_an_undecided_contest_is_reported_to_both_owners(tmp_path):
    # attack 5 on energy 5, against a fare of 5: each can pay to step into the
    # same square and arrives with nothing, so neither can then pay to attack
    # and the contest decides nothing
    harness = GameHarness(tmp_path)
    # they meet on (1, 2): player 1's half is rows 0 and 1, player 2's is 2
    # and 3, so the square they both step into is the first of player 2's
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [('X', 'X', 5, 5, 5)], [('X', 'x1', 1, 1)])
    harness.deploy(2, [('O', 'O', 5, 5, 5)], [('O', 'o1', 1, 3)])
    harness.resolve()

    harness.turn({1: [('x1', UnitType.SOUTH)], 2: [('o1', UnitType.NORTH)]})

    units = harness.units()
    assert (units['x1'].x, units['x1'].y) == (1, 1)
    assert (units['o1'].x, units['o1'].y) == (1, 3)
    for number in (1, 2):
        assert any('undecided' in reason for reason in reasons(harness, number)), \
            (number, reasons(harness, number))


def test_a_move_that_was_carried_out_reports_nothing(tmp_path):
    harness = a_game(tmp_path)
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert reasons(harness, 1) == []
