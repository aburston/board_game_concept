"""Taking back a unit you deployed and have not committed.

A deployment is a setup decision like the board's size or a seat, and every
other one can be taken back until it is committed. This one could not: a
player who put a unit on the wrong square had to live with it, and a setup
refused for clashing with another player's square could not be fixed at all.

Once the setup is committed the units are published and playing, and what
happens to them is the game's business rather than the player's.
"""

import pytest

from board_game_concept.domain import Player
from board_game_concept.service import games
from board_game_concept.service.commands import (AddType, AddUnit, Move,
                                                 RemoveUnit, SetFlag)
from board_game_concept.service.errors import GameError

from game_harness import GameHarness


def a_setup(tmp_path, players=(1,)):
    harness = GameHarness(tmp_path)
    harness.create(5, 5, players, budget=Player.MAX_BUDGET)
    client = harness.session(players[0])
    games.perform(client, AddType(name='T', symbol='T', attack=1, health=4,
                                  energy=10))
    return harness, client


def names(client, number=1):
    return sorted(unit.name for unit in client.getBoard().units
                  if unit.player.number == number)


def test_a_deployed_unit_can_be_taken_back(tmp_path):
    _harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))
    assert names(client) == ['u1']

    games.perform(client, RemoveUnit(name='u1'))

    assert names(client) == []


def test_the_square_it_stood_on_is_free_again(tmp_path):
    _harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=2, y=2))
    assert client.getBoard().squareIsFree(2, 2) is False

    games.perform(client, RemoveUnit(name='u1'))

    assert client.getBoard().squareIsFree(2, 2) is True
    # and something else can be put there
    games.perform(client, AddUnit(type_name='T', name='u2', x=2, y=2))
    assert names(client) == ['u2']


def test_the_name_can_be_used_again(tmp_path):
    _harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))
    games.perform(client, RemoveUnit(name='u1'))

    games.perform(client, AddUnit(type_name='T', name='u1', x=1, y=1))

    unit = client.getBoard().getUnitByName('u1')[0]
    assert (unit.x, unit.y) == (1, 1)


def test_the_points_come_back(tmp_path):
    """Spend is derived from the board, so a unit taken back is unspent."""
    harness = GameHarness(tmp_path)
    harness.create(5, 5, [1], budget=100)
    client = harness.session(1)
    games.perform(client, AddType(name='T', symbol='T', attack=1, health=4,
                                  energy=10))
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))
    spent = 1 + 4 + 10
    assert budget_left(client) == 100 - spent

    games.perform(client, RemoveUnit(name='u1'))

    assert budget_left(client) == 100


def budget_left(client, number=1):
    from board_game_concept.domain import budget
    player = client.getPlayerObj(number)
    return budget.remaining(client.getBoard(), player)


def test_taking_back_the_flag_carrier_leaves_no_flag(tmp_path):
    """And the setup cannot be committed until another unit carries it."""
    harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))
    games.perform(client, SetFlag(unit='u1'))
    assert client.getBoard().flagOf(1) is not None

    games.perform(client, RemoveUnit(name='u1'))

    assert client.getBoard().flagOf(1) is None
    with pytest.raises(GameError) as refused:
        client.clientSave()
    assert 'flag' in str(refused.value)


def test_a_unit_that_is_not_yours_is_not_yours_to_take_back(tmp_path):
    harness, client = a_setup(tmp_path, players=(1, 2, 3))
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))

    other = harness.session(2)
    games.perform(other, AddType(name='T2', symbol='2', attack=1, health=4,
                                 energy=10))
    games.perform(other, AddUnit(type_name='T2', name='u2', x=1, y=1))

    with pytest.raises(GameError) as refused:
        games.perform(client, RemoveUnit(name='u2'))
    assert 'no unit of yours' in str(refused.value)
    assert names(other, 2) == ['u2'], 'and it is still theirs'


def test_a_unit_that_does_not_exist_says_so(tmp_path):
    _harness, client = a_setup(tmp_path)
    with pytest.raises(GameError) as refused:
        games.perform(client, RemoveUnit(name='nobody'))
    assert 'no unit of yours' in str(refused.value)


def test_a_committed_setup_cannot_be_taken_back(tmp_path):
    harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))
    games.perform(client, SetFlag(unit='u1'))
    assert client.clientSave()

    reopened = harness.session(1)
    with pytest.raises(GameError) as refused:
        games.perform(reopened, RemoveUnit(name='u1'))
    assert 'committed' in str(refused.value)


def test_a_unit_in_play_cannot_be_taken_back(tmp_path):
    """Once it is on the board it is the game's, not the player's."""
    harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))
    games.perform(client, SetFlag(unit='u1'))
    client.clientSave()
    harness.resolve()

    playing = harness.session(1)
    with pytest.raises(GameError):
        games.perform(playing, RemoveUnit(name='u1'))
    # and it is still standing
    assert names(playing) == ['u1']


def test_taking_back_survives_the_session_being_reopened(tmp_path):
    """The draft records it, so replaying the draft does not bring it back."""
    harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))
    games.perform(client, AddUnit(type_name='T', name='u2', x=1, y=1))
    games.perform(client, RemoveUnit(name='u1'))

    reopened = harness.session(1)

    assert names(reopened) == ['u2']


def test_an_order_is_not_a_deployment(tmp_path):
    """A unit under orders in a played game is refused for being in play."""
    harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))
    games.perform(client, SetFlag(unit='u1'))
    client.clientSave()
    harness.resolve()

    playing = harness.session(1)
    games.perform(playing, Move(unit='u1', direction=3))
    with pytest.raises(GameError):
        games.perform(playing, RemoveUnit(name='u1'))


# --- taking back an order, which is the same idea a turn later


def a_played_game(tmp_path):
    """One player, one unit, past setup: there are orders to give now."""
    harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=1, y=1))
    games.perform(client, SetFlag(unit='u1'))
    client.clientSave()
    harness.resolve()
    return harness


def test_an_order_can_be_taken_back(tmp_path):
    from board_game_concept.service.commands import Hold
    harness = a_played_game(tmp_path)

    client = harness.session(1)
    games.perform(client, Move(unit='u1', direction=3))
    assert client.getBoard().getUnitByName('u1')[0].direction == 3

    games.perform(client, Hold(unit='u1'))

    unit = client.getBoard().getUnitByName('u1')[0]
    assert unit.direction == 0, 'it holds no direction'
    assert unit.state == 2, 'and is holding rather than moving'


def test_a_unit_whose_order_was_taken_back_does_not_move(tmp_path):
    from board_game_concept.service.commands import Hold
    harness = a_played_game(tmp_path)

    client = harness.session(1)
    games.perform(client, Move(unit='u1', direction=3))
    games.perform(client, Hold(unit='u1'))
    client.clientSave()
    harness.resolve()

    unit = harness.units()['u1']
    assert (unit.x, unit.y) == (1, 1), 'it stayed where it was'


def test_a_unit_whose_order_was_taken_back_rests(tmp_path):
    """Holding is the absence of an order, so it rests like any quiet unit."""
    from board_game_concept.service.commands import Hold
    harness = a_played_game(tmp_path)
    # spend a point first, so resting has something to give back: energy
    # never goes above what the type was designed with
    harness.turn({1: [('u1', 3)]})
    before = harness.units()['u1'].energy
    assert before < 10, 'the move cost it something'

    client = harness.session(1)
    games.perform(client, Move(unit='u1', direction=3))
    games.perform(client, Hold(unit='u1'))
    client.clientSave()
    harness.resolve()

    assert harness.units()['u1'].energy == before + 1


def test_taking_back_an_order_before_the_first_turn_says_so(tmp_path):
    from board_game_concept.service.commands import Hold
    _harness, client = a_setup(tmp_path)
    games.perform(client, AddUnit(type_name='T', name='u1', x=0, y=0))

    with pytest.raises(GameError) as refused:
        games.perform(client, Hold(unit='u1'))
    assert 'first turn' in str(refused.value)


def test_taking_back_an_order_for_a_unit_that_is_not_there(tmp_path):
    from board_game_concept.service.commands import Hold
    harness = a_played_game(tmp_path)
    client = harness.session(1)

    with pytest.raises(GameError):
        games.perform(client, Hold(unit='nobody'))
