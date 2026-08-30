"""What a player finds waiting for them when they open a seat.

A game used to start empty and a player had to invent everything before they
could play. They are given a catalogue when they are registered and an army
when they open the seat, and both are ordinary setup decisions: charged,
placement checked, and taken back by the commands that take back anything
else.

`test_default_army.py` checks the tables themselves. This checks the seeding -
when it happens, when it does not, and that it happens once.
"""

import pytest
import yaml

from board_game_concept.domain import Player, army, budget
from board_game_concept.service import games
from board_game_concept.service.commands import (AddType, AddUnit, LoadPlayer,
                                                 RemoveUnit, SetBoard,
                                                 SetFlag)

from game_harness import GameHarness


def units_of(session, number=1):
    return sorted(unit.name for unit in session.getBoard().units
                  if unit.player is not None and unit.player.number == number)


def left(session, number=1):
    return budget.remaining(session.getBoard(), session.getPlayerObj(number))


# --- the catalogue, given when a player is registered


def test_a_registered_player_holds_the_catalogue(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])

    session = harness.session(1)

    assert sorted(session.getPlayers()[1]['types']) == sorted(army.types())


def test_the_catalogue_costs_nothing_until_it_is_used(tmp_path):
    """A 4x4 board seeds no army, so nothing has been deployed."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])

    session = harness.session(1)

    assert units_of(session) == []
    assert left(session) == Player.DEFAULT_BUDGET


def test_a_player_redefines_a_catalogue_type(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    session = harness.session(1)

    games.perform(session, AddType(name='Heavy', symbol='H', attack=7,
                                   health=4, energy=12))

    types = session.getPlayers()[1]['types']
    assert types['Heavy']['obj'].attack == 7
    assert types['Line']['obj'].attack == 3, 'the rest is untouched'
    assert sorted(types) == sorted(army.types()), 'and nothing was added'


def test_a_player_adds_a_type_of_their_own(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    session = harness.session(1)

    games.perform(session, AddType(name='Cross', symbol='+', attack=2,
                                   health=2, energy=6))

    types = session.getPlayers()[1]['types']
    assert set(army.types()) < set(types)
    assert 'Cross' in types


def test_a_player_taken_from_a_file_is_not_given_the_catalogue(tmp_path):
    """The file says what that player has designed; nothing is added to it."""
    harness = GameHarness(tmp_path)
    path = tmp_path / 'player2.yaml'
    path.write_text(yaml.safe_dump({
        'number': 2, 'budget': 100,
        'types': {'Cross': {'name': 'Cross', 'symbol': '+', 'attack': 2,
                            'health': 2, 'energy': 6}},
        'units': {}}))
    # set up by hand rather than through the harness, because a player is
    # loaded from a file while the setup is still open
    server = harness.session(0)
    games.perform(server, SetBoard(size_x=4, size_y=4))

    games.perform(server, LoadPlayer(path=str(path)))

    assert list(server.getPlayers()[2]['types']) == ['Cross']


# --- the army, given when the seat is opened


def a_default_game(tmp_path, players=(1, 2), budget=None):
    harness = GameHarness(tmp_path)
    harness.create(army.DEFAULT_SIZE_X, army.DEFAULT_SIZE_Y, list(players),
                   budget=budget)
    return harness


def test_a_seat_opened_holds_the_array(tmp_path):
    harness = a_default_game(tmp_path)

    session = harness.session(1)

    assert len(units_of(session)) == 16
    assert sorted(units_of(session)) == sorted(
        name for _depth, _x, _type, name in army.ARRAY)


def test_the_keep_carries_the_flag(tmp_path):
    harness = a_default_game(tmp_path)

    session = harness.session(1)

    carrier = session.getBoard().flagOf(1)
    assert carrier is not None
    keep = session.getBoard().getUnitByName(army.FLAG_UNIT)[0]
    assert keep.flag is True


def test_the_array_stands_in_the_players_own_half(tmp_path):
    harness = a_default_game(tmp_path)

    one = {(unit.x, unit.y) for unit in harness.session(1).getBoard().units}
    two = {(unit.x, unit.y) for unit in harness.session(2).getBoard().units}

    assert all(y in (0, 1) for _x, y in one)
    assert all(y in (6, 7) for _x, y in two)
    assert not (one & two), 'the two armies do not overlap'


def test_the_seeded_setup_commits_as_it_stands(tmp_path):
    """Press commit twice and the game begins. That is the whole point."""
    harness = a_default_game(tmp_path)

    assert harness.session(1).clientSave()
    assert harness.session(2).clientSave()
    harness.resolve()

    server = harness.session(0)
    assert server.getTurnNumber() == 1
    # counted from the board rather than from the harness's name-keyed view
    standing = server.getBoard().units
    assert len(standing) == 32, 'both armies reached the board'
    assert len([unit for unit in standing if unit.player.number == 1]) == 16


def test_the_array_is_charged_like_any_deployment(tmp_path):
    harness = a_default_game(tmp_path)

    session = harness.session(1)

    assert left(session) == Player.DEFAULT_BUDGET - army.cost()
    assert left(session) == 8


def test_a_unit_taken_back_returns_its_points(tmp_path):
    harness = a_default_game(tmp_path)
    session = harness.session(1)
    before = left(session)

    games.perform(session, RemoveUnit(name='heavy1'))

    assert left(session) == before + 30


# --- and given once


def test_opening_the_seat_again_does_not_deploy_it_twice(tmp_path):
    harness = a_default_game(tmp_path)
    harness.session(1)

    reopened = harness.session(1)

    assert len(units_of(reopened)) == 16


def test_an_edited_array_is_left_alone(tmp_path):
    harness = a_default_game(tmp_path)
    session = harness.session(1)
    games.perform(session, RemoveUnit(name='heavy1'))
    games.perform(session, AddUnit(type_name='Line', name='line3', x=3, y=1))

    reopened = harness.session(1)

    names = units_of(reopened)
    assert 'line3' in names
    assert 'heavy1' not in names, 'nothing was restored'
    assert len(names) == 16


def test_taking_the_whole_array_back_leaves_a_player_with_nothing(tmp_path):
    harness = a_default_game(tmp_path)
    session = harness.session(1)
    for name in list(units_of(session)):
        games.perform(session, RemoveUnit(name=name))

    reopened = harness.session(1)

    assert units_of(reopened) == [], 'and it was not seeded again'
    assert left(reopened) == Player.DEFAULT_BUDGET


def test_a_player_who_took_it_back_sets_up_by_hand(tmp_path):
    harness = a_default_game(tmp_path)
    session = harness.session(1)
    for name in list(units_of(session)):
        games.perform(session, RemoveUnit(name=name))

    games.perform(session, AddUnit(type_name='Line', name='mine', x=0, y=0))
    games.perform(session, SetFlag(unit='mine'))

    assert session.clientSave()


# --- where it is not given


def test_a_three_player_game_is_given_no_array(tmp_path):
    harness = a_default_game(tmp_path, players=(1, 2, 3))

    for number in (1, 2, 3):
        session = harness.session(number)
        assert units_of(session, number) == [], number
        assert sorted(session.getPlayers()[number]['types']) == sorted(
            army.types()), number


def test_a_one_player_game_is_given_no_array(tmp_path):
    harness = a_default_game(tmp_path, players=(1,))

    session = harness.session(1)

    assert units_of(session) == []
    assert sorted(session.getPlayers()[1]['types']) == sorted(army.types())


@pytest.mark.parametrize('size', [(5, 5), (4, 8), (8, 2), (8, 3)])
def test_a_board_too_small_is_given_no_array(tmp_path, size):
    harness = GameHarness(tmp_path)
    harness.create(size[0], size[1], [1, 2])

    session = harness.session(1)

    assert units_of(session) == []
    assert sorted(session.getPlayers()[1]['types']) == sorted(army.types())


def test_a_budget_too_small_is_given_no_array(tmp_path):
    """Half an army is worse than none, so nothing at all is deployed."""
    harness = a_default_game(tmp_path, budget=army.cost() - 1)

    session = harness.session(1)

    assert units_of(session) == []
    assert left(session) == army.cost() - 1
    assert sorted(session.getPlayers()[1]['types']) == sorted(army.types())


def test_a_player_given_no_army_sets_up_by_hand(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    session = harness.session(1)

    games.perform(session, AddUnit(type_name='Line', name='mine', x=0, y=0))
    games.perform(session, SetFlag(unit='mine'))

    assert session.clientSave()


def test_the_administrator_is_given_no_army(tmp_path):
    """A session that sees everything is watching, not deploying."""
    harness = a_default_game(tmp_path)

    server = harness.session(0)

    assert server.getBoard().units == []
    assert server.getDraft() == []
