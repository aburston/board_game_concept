"""The point budget: what a type costs, and what a player has left to spend.

The arithmetic on its own, against a board built by hand. What the client does
with a refusal and what the turn does with a rejection are tested where those
live; this is the rule they both ask.
"""

import pytest

from board_game_concept import Board, Player, UnitType
from board_game_concept.domain import budget
from board_game_concept.service import games
from board_game_concept.service.commands import (
    AddPlayer, AddType, AddUnit, LoadPlayer, SetBoard, SetFlag)
from board_game_concept.service.errors import GameError

from board_game_concept.storage.serialise import units_document

from game_harness import GameHarness


def a_type(name='O', attack=1, health=10, energy=10):
    return UnitType(name, name[0].upper(), attack, health, energy)


def a_board(size=10):
    return Board(size, size)


def deploy(board, player, unit_type, name, x, y):
    board.add(player, x, y, name, unit_type)
    board.commit()


# --- what a type costs


def test_a_type_costs_the_sum_of_its_statistics():
    assert a_type(attack=1, health=10, energy=10).cost == 21


def test_the_cheapest_and_the_dearest_definable_types():
    assert a_type(attack=1, health=1, energy=1).cost == 3
    assert a_type(attack=10, health=10, energy=100).cost == 120


def test_a_worn_unit_costs_what_its_type_cost():
    board, player = a_board(), Player(1)
    deploy(board, player, a_type(), 'o1', 0, 0)
    unit = board.units[0]
    unit.setHealth(2)
    unit.setEnergy(0)
    unit.setDestroyed(True)
    assert unit.cost == 21


# --- what a player has spent


def test_a_player_who_has_deployed_nothing_has_spent_nothing():
    board, player = a_board(), Player(1)
    assert budget.spent(board, player) == 0
    assert budget.remaining(board, player) == Player.DEFAULT_BUDGET


def test_spend_is_the_sum_of_what_is_deployed():
    board, player = a_board(), Player(1)
    for index in range(3):
        deploy(board, player, a_type(), f'o{index}', index, 0)
    assert budget.spent(board, player) == 63
    assert budget.remaining(board, player) == Player.DEFAULT_BUDGET - 63


def test_a_destroyed_unit_is_not_refunded():
    board, player = a_board(), Player(1)
    deploy(board, player, a_type(), 'o1', 0, 0)
    before = budget.spent(board, player)
    board.units[0].setDestroyed(True)
    board.units[0].setOnBoard(False)
    assert budget.spent(board, player) == before
    assert budget.remaining(board, player) == Player.DEFAULT_BUDGET - before


def test_one_player_does_not_spend_another_player_budget():
    board = a_board()
    one, two = Player(1), Player(2)
    deploy(board, one, a_type(), 'o1', 0, 0)
    deploy(board, two, a_type(), 'o1', 1, 0)
    assert budget.spent(board, one) == 21
    assert budget.spent(board, two) == 21


def test_budgets_are_per_player():
    board = a_board()
    one, two = Player(1, 60), Player(2, 200)
    assert budget.remaining(board, one) == 60
    assert budget.remaining(board, two) == 200


# --- affordability


def test_a_deployment_that_fits_is_not_refused():
    board, player = a_board(), Player(1)
    for index in range(3):
        deploy(board, player, a_type(), f'o{index}', index, 0)
    assert budget.refusal(board, player, a_type()) is None


def test_a_deployment_that_spends_exactly_what_is_left_is_allowed():
    board, player = a_board(), Player(1, 21)
    assert budget.refusal(board, player, a_type()) is None


def test_one_point_over_is_refused():
    board, player = a_board(), Player(1, 20)
    refusal = budget.refusal(board, player, a_type())
    assert refusal is not None
    # the cost, what is left, and the budget it is left out of
    assert '21' in refusal and '20' in refusal


def test_a_spent_budget_refuses_the_cheapest_type():
    board, player = a_board(), Player(1, 21)
    deploy(board, player, a_type(), 'o1', 0, 0)
    assert budget.remaining(board, player) == 0
    assert budget.refusal(board, player, a_type(attack=1, health=1, energy=1))


def test_an_unknown_budget_has_no_remaining():
    board, player = a_board(), Player(1, None)
    # spend is still readable from the board; what is left is not a number
    assert budget.spent(board, player) == 0
    with pytest.raises(AssertionError):
        budget.remaining(board, player)


# --- registering a player with a budget


def test_a_player_is_registered_with_the_default_budget(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    assert harness.session(1).getPlayerObj(1).budget == Player.DEFAULT_BUDGET


def test_a_player_is_registered_with_the_budget_they_were_given(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [(1, 150), (2, 60)])
    server = harness.session(0)
    assert server.getPlayers()[1]['obj'].budget == 150
    assert server.getPlayers()[2]['obj'].budget == 60


def test_a_budget_out_of_range_is_refused_and_registers_nobody(tmp_path):
    harness = GameHarness(tmp_path)
    server = harness.session(0)
    games.set_board_size(server, SetBoard(size_x=4, size_y=4))
    for bad in (0, 1001):
        with pytest.raises(GameError) as raised:
            games.add_player(server, AddPlayer(number=1, budget=bad))
        assert '1 to 1000' in str(raised.value)
    assert server.getPlayers() == {}


def test_a_budget_survives_being_saved_and_opened_again(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [(1, 150)])
    harness.deploy(1, [('Cross', 'X', 1, 5, 10)], [('Cross', 'x1', 0, 0)])
    harness.resolve()
    assert harness.session(1).getPlayerObj(1).budget == 150


def test_a_player_does_not_learn_another_players_budget(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [(1, 150), (2, 60)])
    harness.deploy(1, [('Cross', 'X', 1, 5, 10)], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [('Ring', 'O', 1, 5, 10)], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    client = harness.session(1)
    assert client.getPlayers()[1]['obj'].budget == 150
    assert client.getPlayers()[2]['obj'].budget is None
    # and the administrator, who reads every record, knows both
    server = harness.session(0)
    assert server.getPlayers()[2]['obj'].budget == 60


def test_a_loaded_player_file_takes_its_budget(tmp_path):
    written = tmp_path / 'player.yaml'
    written.write_text(
        'number: 1\nbudget: 40\ntypes: {}\nunits: []\n')
    harness = GameHarness(tmp_path)
    server = harness.session(0)
    games.set_board_size(server, SetBoard(size_x=4, size_y=4))
    games.load_player(server, LoadPlayer(path=str(written)))
    assert server.getPlayers()[1]['obj'].budget == 40


def test_a_loaded_player_file_without_a_budget_takes_the_default(tmp_path):
    written = tmp_path / 'player.yaml'
    written.write_text('number: 1\ntypes: {}\nunits: []\n')
    harness = GameHarness(tmp_path)
    server = harness.session(0)
    games.set_board_size(server, SetBoard(size_x=4, size_y=4))
    games.load_player(server, LoadPlayer(path=str(written)))
    assert server.getPlayers()[1]['obj'].budget == Player.DEFAULT_BUDGET


def test_a_loaded_player_file_with_a_budget_out_of_range_is_refused(tmp_path):
    written = tmp_path / 'player.yaml'
    written.write_text('number: 1\nbudget: 5000\ntypes: {}\nunits: []\n')
    harness = GameHarness(tmp_path)
    server = harness.session(0)
    games.set_board_size(server, SetBoard(size_x=4, size_y=4))
    with pytest.raises(GameError) as raised:
        games.load_player(server, LoadPlayer(path=str(written)))
    assert '1 to 1000' in str(raised.value)
    assert server.getPlayers() == {}


# --- what the client refuses


def a_client(tmp_path, player_budget, type_stats=(1, 10, 10)):
    """A session for player 1 with a budget and one type defined."""
    harness = GameHarness(tmp_path)
    harness.create(10, 10, [(1, player_budget)])
    client = harness.session(1)
    attack, health, energy = type_stats
    games.perform(client, AddType(name='Cross', symbol='X', attack=attack,
                                  health=health, energy=energy))
    return client


def test_a_deployment_that_fits_is_carried_out(tmp_path):
    client = a_client(tmp_path, 100)
    for index in range(3):
        games.perform(client, AddUnit(type_name='Cross', name=f'x{index}',
                                      x=index, y=0))
    player = client.getPlayerObj(1)
    assert budget.remaining(client.getBoard(), player) == 37


def test_a_deployment_that_spends_exactly_what_is_left_is_carried_out(tmp_path):
    client = a_client(tmp_path, 21)
    games.perform(client, AddUnit(type_name='Cross', name='x1', x=0, y=0))
    assert budget.remaining(client.getBoard(), client.getPlayerObj(1)) == 0


def test_a_deployment_one_point_over_is_refused(tmp_path):
    client = a_client(tmp_path, 20)
    with pytest.raises(GameError) as raised:
        games.perform(client, AddUnit(type_name='Cross', name='x1', x=0, y=0))
    message = str(raised.value)
    assert '21' in message and '20' in message

    # nothing was placed, nothing was spent, and nothing was drafted
    assert client.getBoard().units == []
    assert client.getDraft() == [AddType(name='Cross', symbol='X', attack=1,
                                         health=10, energy=10)]


def test_every_further_deployment_is_refused_once_nothing_is_left(tmp_path):
    client = a_client(tmp_path, 21)
    games.perform(client, AddUnit(type_name='Cross', name='x1', x=0, y=0))
    games.perform(client, AddType(name='Speck', symbol='.', attack=1,
                                  health=1, energy=1))
    with pytest.raises(GameError):
        games.perform(client, AddUnit(type_name='Speck', name='s1', x=1, y=0))


def test_a_unit_deployed_a_moment_ago_is_already_counted(tmp_path):
    # the client's board is its own view, so its own deployment is in it
    client = a_client(tmp_path, 42)
    games.perform(client, AddUnit(type_name='Cross', name='x1', x=0, y=0))
    assert budget.remaining(client.getBoard(), client.getPlayerObj(1)) == 21
    games.perform(client, AddUnit(type_name='Cross', name='x2', x=1, y=0))
    with pytest.raises(GameError):
        games.perform(client, AddUnit(type_name='Cross', name='x3', x=2, y=0))


def test_a_type_too_expensive_to_deploy_may_still_be_defined(tmp_path):
    client = a_client(tmp_path, 100)
    games.perform(client, AddType(name='Brute', symbol='B', attack=10,
                                  health=10, energy=100))
    assert 'Brute' in client.getPlayers()[1]['types']
    assert budget.spent(client.getBoard(), client.getPlayerObj(1)) == 0
    with pytest.raises(GameError):
        games.perform(client, AddUnit(type_name='Brute', name='b1', x=0, y=0))


# --- what the turn rejects


def _publish_deployments(harness, number, type_stats, units):
    """Publish deployment orders by hand, as an unfixed client would.

    The client refuses what the budget will not pay for, so the only way to
    put an unaffordable deployment in front of the server is to write the
    orders directly - which is what a loaded player file and a hand-written
    client both amount to.
    """
    attack, health, energy = type_stats
    client = harness.session(number)
    games.perform(client, AddType(name='Cross', symbol='X', attack=attack,
                                  health=health, energy=energy))
    board = client.getBoard()
    unit_type = client.getPlayers()[number]['types']['Cross']['obj']
    for name, x, y in units:
        board.add(client.getPlayerObj(number), x, y, name, unit_type)
    board.commit()
    # the record is written by hand, so it must carry every type the units
    # being published were made from - the catalogue this player was
    # registered with as well as the one this helper defines
    written = {name: {key: value for key, value in record.items()
                      if key != 'obj'}
               for name, record in client.getPlayers()[number]['types'].items()}
    harness.repository().write_player(
        number, written, client.getPlayerObj(number).budget)
    harness.repository().write_orders(
        number, units_document(board, client.getPlayerObj(number),
                               in_play_only=True))
    harness.repository().mark_committed(number, client.getTurnNumber())


def test_an_over_budget_deployment_is_rejected_at_resolution(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(10, 10, [(1, 50)])
    # three units of a 21-point type: 63 points against a 50-point budget
    _publish_deployments(harness, 1, (1, 10, 10),
                         [('alpha', 0, 0), ('beta', 1, 0), ('gamma', 2, 0)])
    harness.resolve()

    on_board = sorted(unit.name for unit in harness.units().values())
    assert on_board == ['alpha', 'beta']
    reasons = [r['reason'] for r in harness.rejections(1)]
    assert len(reasons) == 1
    assert 'costs 21 points' in reasons[0]
    assert "player 1's 50-point budget" in reasons[0]


def test_the_players_other_orders_still_stand(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(10, 10, [(1, 50), (2, 1000)], default_army=False)
    _publish_deployments(harness, 1, (1, 10, 10),
                         [('alpha', 0, 0), ('beta', 1, 0), ('gamma', 2, 0)])
    _publish_deployments(harness, 2, (1, 10, 10), [('other', 9, 9)])
    harness.resolve()

    on_board = sorted(unit.name for unit in harness.units().values())
    assert on_board == ['alpha', 'beta', 'other']
    # the other player was charged for their own deployment and refused nothing
    assert harness.rejections(2) == []


def test_deployments_are_charged_in_unit_name_order(tmp_path):
    # `beta` is published first and `alpha` second; name order decides, so
    # `alpha` is the one that fits
    harness = GameHarness(tmp_path)
    harness.create(10, 10, [(1, 50)])
    _publish_deployments(harness, 1, (10, 10, 10),
                         [('beta', 0, 0), ('alpha', 1, 0)])
    harness.resolve()

    assert sorted(harness.units()) == ['alpha']
    reasons = [r['reason'] for r in harness.rejections(1)]
    assert len(reasons) == 1


def test_the_same_orders_resolve_the_same_way_whatever_order_they_arrive_in(
        tmp_path):
    placed = []
    for order in (['beta', 'alpha'], ['alpha', 'beta']):
        game = tmp_path / '-'.join(order)
        game.mkdir()
        harness = GameHarness(game)
        harness.create(10, 10, [(1, 50)])
        _publish_deployments(
            harness, 1, (10, 10, 10),
            [(name, index, 0) for index, name in enumerate(order)])
        harness.resolve()
        placed.append(sorted(harness.units()))
    assert placed[0] == placed[1] == ['alpha']


def test_a_loaded_player_file_deploys_what_the_budget_buys(tmp_path):
    written = tmp_path / 'player.yaml'
    written.write_text(
        "number: 1\n"
        "budget: 50\n"
        "types:\n"
        "  Cross: {attack: '1', energy: '10', health: '10', name: Cross,"
        " symbol: X}\n"
        "units:\n"
        + ''.join(
            f"  - {{ id: {index}, player: 1, type: \"Cross\", name: \"{name}\","
            f" symbol: \"X\", attack: \"1\", health: \"10\", energy: \"10\","
            f" x: {index}, y: 0, state: 0, direction: 0, destroyed: False,"
            f" on_board: True }}\n"
            for index, name in enumerate(['alpha', 'beta', 'gamma'])))

    harness = GameHarness(tmp_path)
    server = harness.session(0)
    games.set_board_size(server, SetBoard(size_x=10, size_y=10))
    games.load_player(server, LoadPlayer(path=str(written)))
    assert server.serverSave()
    # the loaded units become orders for the next turn, which the server
    # commits on that player's behalf; that is where they are charged
    harness.resolve()

    assert sorted(harness.units()) == ['alpha', 'beta']
    reasons = [r['reason'] for r in harness.rejections(1)]
    assert any('costs 21 points' in reason for reason in reasons), reasons


# --- the whole flow


def test_two_players_build_armies_against_different_budgets(tmp_path):
    """Setup end to end: two budgets, two prices, and what each buys."""
    harness = GameHarness(tmp_path)
    harness.create(10, 10, [(1, 100), (2, 45)])

    # player 1 takes four cheap units; a fifth would cost 21 of the 16 left
    one = harness.session(1)
    games.perform(one, AddType(name='Cross', symbol='X', attack=1,
                               health=10, energy=10))
    for index in range(4):
        games.perform(one, AddUnit(type_name='Cross', name=f'x{index}',
                                   x=index, y=0))
    assert budget.remaining(one.getBoard(), one.getPlayerObj(1)) == 16
    with pytest.raises(GameError):
        games.perform(one, AddUnit(type_name='Cross', name='x4', x=4, y=0))
    # a setup is refused without a carrier, and carrying costs nothing: the
    # spend asserted below is unchanged by designating one
    games.perform(one, SetFlag(unit='x0'))
    assert one.clientSave()

    # player 2 takes one expensive unit and can afford nothing beside it
    two = harness.session(2)
    games.perform(two, AddType(name='Brute', symbol='B', attack=10,
                               health=10, energy=25))
    games.perform(two, AddUnit(type_name='Brute', name='b0', x=9, y=9))
    assert budget.remaining(two.getBoard(), two.getPlayerObj(2)) == 0
    games.perform(two, AddType(name='Speck', symbol='.', attack=1,
                               health=1, energy=1))
    with pytest.raises(GameError):
        games.perform(two, AddUnit(type_name='Speck', name='s0', x=8, y=9))
    games.perform(two, SetFlag(unit='b0'))
    assert two.clientSave()

    harness.resolve()

    # the board holds exactly what was paid for
    on_board = sorted(harness.units())
    assert on_board == ['b0', 'x0', 'x1', 'x2', 'x3']
    assert harness.rejections(1) == []
    assert harness.rejections(2) == []

    # and the budgets survived the turn unchanged, with the spend derived
    server = harness.session(0)
    board = server.getBoard()
    assert budget.remaining(board, server.getPlayers()[1]['obj']) == 16
    assert budget.remaining(board, server.getPlayers()[2]['obj']) == 0


def test_a_deployment_refused_for_its_square_is_not_charged(tmp_path):
    """A unit that never reaches the board costs nothing.

    Two players ask for one square and both are refused it. Charging the
    refused unit anyway would spend points on nothing, and could push the
    player's other deployment over a budget it actually fits inside.
    """
    harness = GameHarness(tmp_path)
    harness.create(10, 10, [(1, 42), (2, 1000)], default_army=False)
    # player 1 asks for (0, 0) - which player 2 also asks for - and (1, 0).
    # 42 points buys exactly two units of a 21-point type, so if the refused
    # one were charged, `beta` would be refused for cost as well
    _publish_deployments(harness, 1, (1, 10, 10),
                         [('alpha', 0, 0), ('beta', 1, 0)])
    _publish_deployments(harness, 2, (1, 10, 10), [('other', 0, 0)])
    harness.resolve()

    assert sorted(harness.units()) == ['beta']
    reasons = [r['reason'] for r in harness.rejections(1)]
    assert len(reasons) == 1
    assert 'both were refused' in reasons[0]
