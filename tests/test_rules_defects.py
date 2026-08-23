"""One test per defect catalogued in `GAME_RULES.md` Part 2.

Each was red before the `fix-rules-defects` change and names the question it
answers, so a regression points straight back at what it broke.
"""

import pytest

from board_game_concept import Board, Player, UnitType
from board_game_concept.service import games
from board_game_concept.service.commands import Move

from game_harness import GameHarness


def a_board(size_x=6, size_y=3):
    return Board(size_x, size_y)


# --- Q1: a refused placement must leave nothing behind


def test_a_refused_duplicate_name_registers_nothing():
    board = a_board()
    player = Player(1)
    unit_type = UnitType('X', 'X', 1, 5, 50)
    board.add(player, 0, 0, 'scout', unit_type)
    before = list(board.units)

    with pytest.raises(AssertionError):
        board.add(player, 3, 0, 'scout', unit_type)

    assert board.units == before
    assert [u.name for u in board.unit_dict['scout']] == ['scout']


def test_a_cell_named_by_a_refused_placement_is_still_free():
    board = a_board()
    player = Player(1)
    unit_type = UnitType('X', 'X', 1, 5, 50)
    board.add(player, 0, 0, 'scout', unit_type)

    with pytest.raises(AssertionError):
        board.add(player, 3, 0, 'scout', unit_type)

    # the refused unit must not have claimed (3, 0) on its way out
    assert board.squareIsFree(3, 0)
    board.add(player, 3, 0, 'runner', unit_type)
    board.commit()
    assert board.getUnitByCoords(3, 0).name == 'runner'


# --- Q3: resolution must not depend on the order units are held in


def a_pair(first, second, size_x=6, size_y=3):
    """A board holding two units, registered in the order given.

    Each entry is `(player_number, name, x, y, stats)`.
    """
    board = a_board(size_x, size_y)
    players = {}
    for number, name, x, y, stats in (first, second):
        player = players.setdefault(number, Player(number))
        attack, health, energy = stats
        board.add(player, x, y, name,
                  UnitType(name.upper(), name[0].upper(), attack, health, energy))
    board.commit()
    return board


def resolved(order_first, order_second, first, second):
    board = a_pair(first, second)
    for name, direction in (order_first, order_second):
        board.getUnitByName(name)[0].move(direction)
    board.commit()
    return {unit.name: (unit.x, unit.y, unit.health, unit.energy, unit.destroyed)
            for unit in board.units}


def test_registration_order_does_not_change_the_outcome():
    # `chase` follows `lead` into the cell `lead` is leaving. Resolved unit by
    # unit against a live board, whether it gets there depends on whether
    # `lead` has moved yet
    lead = (1, 'lead', 1, 0, (4, 5, 4))
    chase = (2, 'chase', 2, 0, (3, 3, 1))
    orders = (('lead', UnitType.SOUTH), ('chase', UnitType.WEST))

    lead_first = resolved(*orders, lead, chase)
    chase_first = resolved(*orders, chase, lead)

    assert lead_first == chase_first


def test_two_units_ordered_into_each_other_do_not_swap():
    board = a_pair((1, 'x', 0, 0, (1, 5, 50)), (2, 'o', 1, 0, (1, 5, 50)))
    x = board.getUnitByName('x')[0]
    o = board.getUnitByName('o')[0]
    x.move(UnitType.EAST)
    o.move(UnitType.WEST)
    board.commit()

    # neither may end the turn where the other started it
    assert not ((x.x, x.y) == (1, 0) and (o.x, o.y) == (0, 0))
    # and they must have met: a collision reveals both
    assert o in x.seen_by
    assert x in o.seen_by


# --- Q5: a client must not hold what its player may not see


def a_two_player_game(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2])
    harness.deploy(1, [('Sneaky', 'X', 9, 9, 90)], [('Sneaky', 'x1', 0, 0)])
    harness.deploy(2, [('Brute', 'O', 2, 2, 20)], [('Brute', 'o1', 5, 2)])
    harness.resolve()
    return harness


def test_a_client_holds_no_record_of_an_unseen_enemy(tmp_path):
    harness = a_two_player_game(tmp_path)
    session = harness.session(1)
    names = [unit.name for unit in session.getBoard().units]
    assert names == ['x1']


def test_a_client_lists_no_enemy_type_before_contact(tmp_path):
    from board_game_concept.cli.render import type_lines

    harness = a_two_player_game(tmp_path)
    session = harness.session(1)
    listed = type_lines(session.getPlayers())
    assert all('Brute' not in line for line in listed), listed


# --- Q6: a name an opponent used first must not block your own order


def test_a_player_can_order_their_own_unit_when_a_name_is_shared(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2])
    # player 2 deploys first, so their `scout` is registered first
    harness.deploy(2, [('O', 'O', 1, 5, 50)], [('O', 'scout', 5, 2)])
    harness.deploy(1, [('X', 'X', 1, 5, 50)], [('X', 'scout', 0, 0)])
    harness.resolve()

    # the server registers players in ascending order, so player 1's `scout`
    # is always the first one holding that name. It is player 2 whose own
    # order is refused because of it
    session = harness.session(2)
    games.order_move(session, Move(unit='scout', direction=UnitType.WEST))

    ordered = session.getBoard().getUnitByName('scout', session.getPlayerObj(2))[0]
    assert ordered.player.number == 2
    assert ordered.state == UnitType.MOVING


# --- Q1: restoring is not deploying


def test_no_restored_unit_is_waiting_to_deploy(tmp_path):
    harness = a_two_player_game(tmp_path)
    harness.turn({1: [], 2: []})
    for number in (0, 1, 2):
        board = harness.session(number).getBoard()
        for unit in board.units:
            assert unit.state != UnitType.INITIAL, (number, unit.name)


def test_an_order_naming_a_destroyed_unit_is_refused(tmp_path):
    from board_game_concept.storage.serialise import serialise_units

    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2])
    # each keeps a reserve out of the way, so losing the duellist does not end
    # the game and there are further turns to play
    harness.deploy(1, [('X', 'X', 5, 5, 50)],
                   [('X', 'x1', 0, 0), ('X', 'x2', 0, 2)])
    harness.deploy(2, [('O', 'O', 5, 5, 50)],
                   [('O', 'o1', 1, 0), ('O', 'o2', 5, 2)])
    harness.resolve()
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert harness.units()['x1'].destroyed

    # publish x1 by hand, as a client that had not been fixed would
    repository = harness.repository()
    server = harness.session(0)
    repository.write_orders(1, serialise_units(server.getBoard(),
                                               server.getPlayers()[1]['obj']))
    repository.mark_committed(1)
    harness.order(2, [])
    harness.resolve()

    reasons = [r['reason'] for r in harness.rejections(1)]
    assert any('destroyed' in reason for reason in reasons), reasons
    board = harness.session(0).getBoard()
    assert len([u for u in board.units if u.name == 'x1']) == 1
    assert board.getUnitByName('x1')[0].destroyed
    assert len(board.units) == 4
