"""Where a game is kept, and the fact that only one module knows.

The repository reads and writes; it holds no rules. These tests are about the
shape of what it stores and about the seam itself - that a game can be put
somewhere chosen by the caller, rather than wherever the process happens to be
running.
"""

import os

import pytest

from board_game_concept import Game, YamlGameRepository
from board_game_concept.domain import Board, Player, UnitType
from board_game_concept.storage.repository import GameRepository


def test_a_game_is_kept_where_it_is_told(tmp_path):
    # the base path used to be read from the process working directory, which
    # made the caller's current directory part of the storage contract
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    assert os.path.isdir(tmp_path / 'games' / '_one' / 'data')
    assert os.path.isdir(tmp_path / 'games' / '_one' / 'players')


def test_games_are_kept_apart_by_number(tmp_path):
    for number in ('one', 'two'):
        YamlGameRepository(number, base_path=str(tmp_path)).ensure()
    assert sorted(os.listdir(tmp_path / 'games')) == ['_one', '_two']


def test_the_layout_is_the_one_the_spec_describes(tmp_path):
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_board(4, 5)
    repository.write_player(1, {'Cross': {'name': 'Cross', 'symbol': 'X',
                                          'attack': 1, 'health': 1,
                                          'energy': 10}})
    repository.mark_committed(1)
    repository.write_orders(1, 'units: None\n')
    repository.write_rejections(1, [])
    repository.write_view(1, 'units: None\n')
    repository.write_units('units: None\n')

    data = sorted(os.listdir(tmp_path / 'games' / '_one' / 'data'))
    players = sorted(os.listdir(tmp_path / 'games' / '_one' / 'players'))
    assert data == ['board.yaml', 'units.yaml']
    assert players == ['1.yaml', '1_rejected.yaml', '1_units.yaml',
                       '1_units_seen.yaml', 'commit_1']


def test_what_goes_in_comes_back(tmp_path):
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()

    assert repository.read_board() is None
    repository.write_board(4, 5)
    assert repository.read_board() == (4, 5)

    assert repository.player_numbers() == []
    repository.write_player(2, {})
    assert repository.player_numbers() == [2]
    assert repository.read_player(2)['number'] == 2

    assert repository.has_committed(2) is False
    repository.mark_committed(2)
    assert repository.has_committed(2) is True

    assert repository.read_rejections(2) == []
    repository.write_rejections(2, [{'unit': 'x1', 'reason': 'occupied'}])
    assert repository.read_rejections(2)[0]['unit'] == 'x1'


def test_orders_are_consumed_once(tmp_path):
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_orders(1, 'units: None\n')
    repository.write_orders(2, 'units: None\n')
    repository.write_view(1, 'units: None\n')

    assert repository.committed_players() == [1, 2]
    assert repository.has_orders(1) is True

    repository.clear_orders()
    assert repository.committed_players() == []
    assert repository.has_orders(1) is False
    # a player's view is not an order, and survives the turn
    assert repository.read_view(1) == []


def test_a_view_is_not_mistaken_for_an_order(tmp_path):
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_view(11, 'units: None\n')
    assert repository.committed_players() == []


def test_a_player_number_is_matched_exactly(tmp_path):
    # a substring match let commit_1 match commit_11
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.mark_committed(11)
    assert repository.has_committed(11) is True
    assert repository.has_committed(1) is False


def test_a_game_survives_being_written_and_read_again(tmp_path):
    """The whole round trip, through the layer that stores it."""
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    game = Game(repository, 0)
    game.load()

    game.setBoard(Board(4, 4))
    game.getPlayers()[1] = {'number': 1, 'obj': Player(1), 'types': {}}
    unit_type = UnitType('Cross', 'X', 1, 5, 10)
    game.getPlayers()[1]['types']['Cross'] = {
        'name': 'Cross', 'symbol': 'X', 'attack': 1, 'health': 5,
        'energy': 10, 'obj': unit_type}
    game.getBoard().add(Player(1), 2, 3, 'x1', unit_type)
    game.getBoard().commit()
    assert game.serverSave() is True

    reopened = Game(YamlGameRepository('one', base_path=str(tmp_path)), 0)
    reopened.load()
    assert reopened.getSizeX() == 4 and reopened.getSizeY() == 4
    assert list(reopened.getPlayers()) == [1]
    restored = reopened.getBoard().getUnitByName('x1')[0]
    assert (restored.x, restored.y) == (2, 3)
    assert restored.health == 5
    assert restored.energy == 10


def test_the_port_says_what_an_implementation_owes(tmp_path):
    # a partial implementation fails loudly rather than silently
    class Half(GameRepository):
        pass

    with pytest.raises(NotImplementedError):
        Half().read_board()


# --- work a session has not committed yet


def test_a_draft_round_trips(tmp_path):
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    draft = {'turn': 2, 'commands': [{'kind': 'move', 'unit': 'x1',
                                      'direction': 1}]}

    repository.write_draft(1, draft)

    assert repository.read_draft(1) == draft


def test_a_draft_that_was_never_written_reads_as_nothing(tmp_path):
    """An absent draft is a session with no work outstanding, not an error."""
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()

    assert repository.read_draft(1) is None


def test_a_draft_can_be_cleared_twice(tmp_path):
    # committing clears a draft, and so does abandoning one. Neither has to
    # know whether the other happened first
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_draft(1, {'turn': 0, 'commands': []})

    repository.clear_draft(1)
    repository.clear_draft(1)

    assert repository.read_draft(1) is None


def test_each_session_holds_its_own_draft(tmp_path):
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()

    repository.write_draft(1, {'turn': 0, 'commands': [{'kind': 'commit'}]})
    repository.write_draft(2, {'turn': 0, 'commands': []})

    assert repository.read_draft(1)['commands'] == [{'kind': 'commit'}]
    assert repository.read_draft(2)['commands'] == []


def test_a_draft_is_not_mistaken_for_a_player(tmp_path):
    """The two places that classify a player file by its name must skip it.

    Reading a file by guessing at its name is what produced divergence 10 in
    `SPEC_COVERAGE.md`, so a new file beside the player files is held to it
    rather than left to inspection.
    """
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_player(1, {})
    repository.write_draft(1, {'turn': 0, 'commands': []})

    assert repository.player_numbers() == [1]


def test_a_draft_is_not_mistaken_for_published_orders(tmp_path):
    """A player who has drafted and not committed has not committed."""
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_draft(1, {'turn': 0, 'commands': []})

    assert repository.committed_players() == []
    assert repository.has_orders(1) is False
