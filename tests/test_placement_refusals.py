"""A deployment outside a player's half, refused at both the places it can be.

Where a player may deploy is `domain/placement.py`, and it is asked twice: by
the client, so a placement typed at a prompt is refused before anything is
put on the board, and by the resolution, so an order file written by hand or
loaded from disk is bound by the same rule. `budget` is enforced in the same
two places for the same reason, and this follows it.

`test_placement_zones.py` holds the rule itself; this holds the enforcement.
"""

import pytest

from board_game_concept.domain import Player
from board_game_concept.service import games
from board_game_concept.service.commands import AddType, AddUnit
from board_game_concept.service.errors import GameError
from board_game_concept.storage.serialise import units_document

from game_harness import GameHarness


def two_player_game(tmp_path, size_x=6, size_y=4):
    """A game whose halves are player 1's rows and player 2's rows."""
    harness = GameHarness(tmp_path)
    harness.create(size_x, size_y, [1, 2], budget=Player.MAX_BUDGET)
    return harness


def a_type(client, number, name='X', stats=(1, 5, 50)):
    attack, health, energy = stats
    games.perform(client, AddType(name=name, symbol=name[0], attack=attack,
                                  health=health, energy=energy))
    return client.getPlayers()[number]['types'][name]['obj']


# --- the client refuses, and leaves the board as it was


def test_a_deployment_in_the_other_half_is_refused(tmp_path):
    harness = two_player_game(tmp_path)
    client = harness.session(1)
    a_type(client, 1)

    # rows 0 and 1 are player 1's; row 2 is player 2's
    with pytest.raises(GameError) as refused:
        games.deploy_unit(client, AddUnit(type_name='X', name='x1',
                                          x=0, y=2))

    assert "other player's half" in str(refused.value)
    assert client.getBoard().units == [], 'the board was left as it was'


def test_a_deployment_in_the_neutral_row_is_refused(tmp_path):
    harness = two_player_game(tmp_path, size_y=5)
    client = harness.session(1)
    a_type(client, 1)

    # five rows: 0 and 1 are player 1's, 2 is neutral, 3 and 4 are player 2's
    with pytest.raises(GameError) as refused:
        games.deploy_unit(client, AddUnit(type_name='X', name='x1',
                                          x=0, y=2))

    assert 'neutral row' in str(refused.value)
    assert client.getBoard().units == []


def test_a_deployment_in_a_players_own_half_is_allowed(tmp_path):
    harness = two_player_game(tmp_path, size_y=5)
    for number, row in ((1, 1), (2, 4)):
        client = harness.session(number)
        a_type(client, number)
        games.deploy_unit(client, AddUnit(type_name='X', name=f'u{number}',
                                          x=0, y=row))
        held = [unit.name for unit in client.getBoard().units]
        assert held == [f'u{number}']


def test_the_higher_numbered_player_owns_the_bottom_half(tmp_path):
    harness = two_player_game(tmp_path)
    client = harness.session(2)
    a_type(client, 2)

    with pytest.raises(GameError):
        games.deploy_unit(client, AddUnit(type_name='X', name='o1',
                                          x=0, y=0))

    games.deploy_unit(client, AddUnit(type_name='X', name='o1', x=0, y=3))
    assert [unit.name for unit in client.getBoard().units] == ['o1']


# --- and a game that is not two-player is refused nothing for where it is


@pytest.mark.parametrize('numbers', [[1], [1, 2, 3]])
def test_a_game_that_is_not_two_player_may_deploy_anywhere(tmp_path, numbers):
    """The null case: exactly what these deployments did before the rule."""
    harness = GameHarness(tmp_path)
    harness.create(4, 5, numbers, budget=Player.MAX_BUDGET)
    client = harness.session(numbers[0])
    a_type(client, numbers[0])

    for y in range(5):
        games.deploy_unit(client, AddUnit(type_name='X', name=f'u{y}',
                                          x=0, y=y))

    assert len(client.getBoard().units) == 5, 'every row was open'


# --- the resolution refuses one that never went through a client


def _publish_out_of_area(harness, number, name, x, y):
    """Put a deployment in front of the server without a client refusing it.

    A player's orders are written straight to the repository, which is what a
    loaded player file and a hand-written client both amount to. The board it
    is built from is this player's own session board, so the unit is a
    deployment the server has never seen.
    """
    client = harness.session(number)
    unit_type = a_type(client, number)
    board = client.getBoard()
    board.add(client.getPlayerObj(number), x, y, name, unit_type)
    board.commit()
    harness.repository().write_player(
        number,
        {'X': {'name': 'X', 'symbol': 'X', 'attack': 1, 'health': 5,
               'energy': 50}},
        client.getPlayerObj(number).budget)
    harness.repository().write_orders(
        number, units_document(board, client.getPlayerObj(number),
                               in_play_only=True))
    harness.repository().mark_committed(number, client.getTurnNumber())


def test_an_out_of_area_deployment_is_rejected_at_resolution(tmp_path):
    harness = two_player_game(tmp_path)
    # player 1 is given a deployment in player 2's half, behind the client's
    # back, and player 2 one of their own that is perfectly legal
    _publish_out_of_area(harness, 1, 'x1', 0, 3)
    _publish_out_of_area(harness, 2, 'o1', 1, 3)
    harness.resolve()

    assert 'x1' not in harness.units(), 'it was never placed'
    assert 'o1' in harness.units()

    refused = harness.rejections(1)
    assert [entry['unit'] for entry in refused] == ['x1']
    assert "other player's half" in refused[0]['reason']


def test_a_neutral_row_deployment_is_rejected_at_resolution(tmp_path):
    harness = two_player_game(tmp_path, size_y=5)
    _publish_out_of_area(harness, 1, 'x1', 0, 2)
    harness.resolve()

    assert 'x1' not in harness.units()
    refused = harness.rejections(1)
    assert [entry['unit'] for entry in refused] == ['x1']
    assert 'neutral row' in refused[0]['reason']


def test_resolution_refuses_nothing_for_place_in_a_three_player_game(tmp_path):
    """The null case again, at the second enforcement point."""
    harness = GameHarness(tmp_path)
    harness.create(4, 5, [1, 2, 3], budget=Player.MAX_BUDGET)
    _publish_out_of_area(harness, 1, 'x1', 0, 4)
    harness.resolve()

    assert 'x1' in harness.units(), 'every row is open to three players'
    assert harness.rejections(1) == []
