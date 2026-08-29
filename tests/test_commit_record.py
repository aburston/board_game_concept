"""Committing is a fact that is recorded, and spent when its turn resolves.

It used to be inferred from `players/<n>_units.yaml` existing, which meant
"committed for this turn" only because the server deletes that file when it
resolves one. Both tests below are for what that inference was quietly doing
for free, and what broke when it stopped.
"""

import os

import pytest

from board_game_concept.service import games
from board_game_concept.service.commands import (
    AddPlayer, AddType, AddUnit, SetBoard, SetFlag)
from game_harness import GameHarness

CROSS = ('Cross', 'X', 1, 5, 10)
RING = ('Ring', 'O', 1, 5, 10)


def test_a_commit_is_spent_when_its_turn_is_resolved(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])

    assert harness.repository().committed_players(0) == [1, 2]
    harness.resolve()

    server = harness.session(0)
    assert server.committedPlayerCount() == 0


def test_a_turn_that_advances_nothing_does_not_resolve_itself_again(tmp_path):
    """The spin a recorded commit invites, if nothing ever spends it.

    When two players deploy onto one square both are refused, so no unit
    reaches the board. Under a commit that outlives its turn, the barrier is
    still satisfied by the commits that opened it, and the server resolves the
    same turn for ever.
    """
    harness = GameHarness(tmp_path)
    # three players, because two cannot contest a deployment square any more:
    # `placement-zones` gives each of two players their own half of the board
    harness.create(4, 4, [1, 2, 3])
    # published past the commit: a clash cannot be committed any more, and
    # this is about what the resolution does with one that reaches it anyway
    harness.publish_setup(1, [CROSS], [('Cross', 'x1', 1, 1)])
    harness.publish_setup(2, [RING], [('Ring', 'o1', 1, 1)])
    harness.publish_setup(3, [('Star', 'S', 1, 5, 10)], [('Star', 's1', 1, 1)])

    harness.resolve()

    server = harness.session(0)
    # the turn was resolved, even though nothing reached the board: the
    # players' setups were carried out, and what they left is the game
    assert server.getTurnNumber() == 1
    # and nobody is holding a commit for it any more
    assert server.committedPlayerCount() == 0
    assert harness.repository().committed_players(1) == []
    assert harness.repository().committed_players(0) == []


def test_a_commit_belongs_to_one_turn(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    harness.order(1, [('x1', 1)])

    repository = harness.repository()
    assert repository.committed_players(1) == [1]
    # the turn that has been resolved is not the turn now open
    assert repository.committed_players(0) == []


def test_the_turn_is_held_open_for_a_player_who_has_not_committed(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])

    server = harness.session(0)

    assert server.committedPlayerCount() == 1
    assert sorted(server.getPlayers()) == [1, 2]


def test_having_ever_committed_survives_the_turn_being_resolved(tmp_path):
    """It is a different fact, and it is what ends setup for a player."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    assert harness.repository().has_committed(1) is True
    # and so the player is past setup and may no longer deploy
    client = harness.session(1)
    assert client.getNewGame() is False


@pytest.mark.backend('yaml')
def test_a_game_whose_markers_predate_the_turn_being_recorded(tmp_path):
    """A game set up by an older version opens, and still resolves turns."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    client = harness.session(1)
    games.perform(client, AddType(name='Cross', symbol='X', attack=1,
                                  health=5, energy=10))
    games.perform(client, AddUnit(type_name='Cross', name='x1', x=0, y=0))
    games.perform(client, SetFlag(unit='x1'))
    assert client.clientSave()

    # as the marker was written before a commit recorded which turn it was for
    repository = harness.repository()
    # reaching into the layout on purpose: what is being set up is a game
    # an older version wrote, which no public operation can produce
    with open(repository._commit_marker(1), 'w', encoding='utf-8') as file:
        file.write('')

    reopened = harness.session(1)
    assert reopened.getNewGame() is False
    assert repository.has_committed(1) is True
    # the stale commit does not satisfy the barrier for the turn now open
    assert repository.committed_players(0) == []


@pytest.mark.backend('yaml')
def test_the_server_commits_for_a_player_it_loaded_units_for(tmp_path):
    """Nobody types `commit` for a player who arrived in a file.

    The server writes their units as orders for the turn about to be resolved.
    That is committing on their behalf, and it used to be one because writing
    the order file was what committing meant.
    """
    harness = GameHarness(tmp_path)
    server = harness.session(0)
    games.perform(server, SetBoard(size_x=4, size_y=4))
    games.perform(server, AddPlayer(number=1))
    server.getPlayers()[1]['units'] = [{
        'player': 1, 'type': 'Cross', 'name': 'x1', 'symbol': 'X',
        'attack': 1, 'health': 5, 'energy': 10, 'x': 0, 'y': 0,
        'state': 0, 'direction': 0, 'destroyed': False, 'on_board': False,
    }]
    server.getPlayers()[1]['types']['Cross'] = {
        'name': 'Cross', 'symbol': 'X', 'attack': 1, 'health': 5,
        'energy': 10,
    }
    assert server.serverSave()

    repository = harness.repository()
    assert os.path.exists(repository._orders_file(1))
    # so the turn those orders are for is not held open waiting for a player
    # who has nobody to commit for them
    assert repository.committed_players(server.getTurnNumber()) == [1]
