"""A setup commit that lands on a square another player has already taken.

Nobody can see anybody else's units while they are setting up, so two players
can choose one square without knowing it. That used to be found only when the
turn resolved, and both deployments were refused: each player lost the unit,
was told afterwards, and could do nothing about it, because their setup was
committed and closed.

The commit is refused instead. Nothing is published and nothing is marked
committed, so the setup stays open: the player moves the unit and commits
again. The setup committed first keeps the square.

With two players this cannot arise at all - `placement-zones` gives each of
them their own half - so these are three-player games, which is where it
matters.
"""

import pytest

from board_game_concept.domain import Player
from board_game_concept.service import games
from board_game_concept.service.commands import (AddType, AddUnit,
                                                 RemoveUnit, SetFlag)
from board_game_concept.service.errors import GameError

from game_harness import GameHarness


def a_game(tmp_path, players=(1, 2, 3)):
    harness = GameHarness(tmp_path)
    harness.create(5, 5, players, budget=Player.MAX_BUDGET)
    return harness


def setup(harness, number, square, name=None, commit=True):
    """Design a type, deploy one unit on a square, carry the flag, commit."""
    unit = name or f'u{number}'
    client = harness.session(number)
    games.perform(client, AddType(name=f'T{number}', symbol=str(number),
                                  attack=1, health=4, energy=10))
    games.perform(client, AddUnit(type_name=f'T{number}', name=unit,
                                  x=square[0], y=square[1]))
    games.perform(client, SetFlag(unit=unit))
    if commit:
        assert client.clientSave()
    return client


def test_a_setup_commit_onto_a_committed_square_is_refused(tmp_path):
    harness = a_game(tmp_path)
    setup(harness, 1, (2, 2))

    client = harness.session(2)
    games.perform(client, AddType(name='T2', symbol='2', attack=1, health=4,
                                  energy=10))
    games.perform(client, AddUnit(type_name='T2', name='u2', x=2, y=2))
    games.perform(client, SetFlag(unit='u2'))

    with pytest.raises(GameError) as refused:
        client.clientSave()

    said = str(refused.value)
    assert '(2, 2)' in said, said
    assert 'commit again' in said


def test_the_refused_setup_is_left_open_and_unchanged(tmp_path):
    harness = a_game(tmp_path)
    setup(harness, 1, (2, 2))

    client = harness.session(2)
    games.perform(client, AddType(name='T2', symbol='2', attack=1, health=4,
                                  energy=10))
    games.perform(client, AddUnit(type_name='T2', name='u2', x=2, y=2))
    games.perform(client, SetFlag(unit='u2'))
    with pytest.raises(GameError):
        client.clientSave()

    # nothing was published and nothing was marked committed
    assert harness.repository().read_orders(2) in (None, {}, {'units': None})
    assert 2 not in harness.repository().committed_players()

    # and a session opened again still has the setup to do, with its unit
    reopened = harness.session(2)
    assert reopened.getNewGame() is True
    assert [unit.name for unit in reopened.getBoard().units
            if unit.player.number == 2] == ['u2']


def test_the_refused_player_takes_the_unit_back_and_commits(tmp_path):
    """The refusal is only worth making because this is what follows it."""
    harness = a_game(tmp_path)
    setup(harness, 1, (2, 2))

    client = harness.session(2)
    games.perform(client, AddType(name='T2', symbol='2', attack=1, health=4,
                                  energy=10))
    games.perform(client, AddUnit(type_name='T2', name='u2', x=2, y=2))
    games.perform(client, SetFlag(unit='u2'))
    with pytest.raises(GameError):
        client.clientSave()

    # take the clashing unit back, put it somewhere free, and commit again
    games.perform(client, RemoveUnit(name='u2'))
    games.perform(client, AddUnit(type_name='T2', name='u2', x=4, y=4))
    games.perform(client, SetFlag(unit='u2'))

    assert client.clientSave()
    assert 2 in harness.repository().committed_players()


def test_a_setup_that_clashes_with_nothing_is_committed(tmp_path):
    harness = a_game(tmp_path)
    setup(harness, 1, (0, 0))
    setup(harness, 2, (1, 1))
    setup(harness, 3, (4, 4))

    assert sorted(harness.repository().committed_players()) == [1, 2, 3]


def test_the_first_commit_keeps_the_square(tmp_path):
    harness = a_game(tmp_path)
    setup(harness, 1, (3, 3))

    client = harness.session(2)
    games.perform(client, AddType(name='T2', symbol='2', attack=1, health=4,
                                  energy=10))
    games.perform(client, AddUnit(type_name='T2', name='u2', x=3, y=3))
    games.perform(client, SetFlag(unit='u2'))
    with pytest.raises(GameError):
        client.clientSave()

    # the first is committed and stays that way; only the second was refused
    assert 1 in harness.repository().committed_players()
    assert 2 not in harness.repository().committed_players()


def test_a_two_player_game_cannot_clash_at_all(tmp_path):
    """The halves do not overlap, so there is nothing here for it to find."""
    harness = a_game(tmp_path, players=(1, 2))
    setup(harness, 1, (0, 0))
    setup(harness, 2, (0, 4))

    assert sorted(harness.repository().committed_players()) == [1, 2]


def test_a_player_is_not_refused_by_their_own_deployment(tmp_path):
    """Its own published orders are not somebody else's."""
    harness = a_game(tmp_path)
    client = setup(harness, 1, (2, 2))
    assert 1 in harness.repository().committed_players()
    assert client is not None
