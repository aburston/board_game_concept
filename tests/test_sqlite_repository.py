"""The SQLite backend's own shape.

`test_repository.py` is about the YAML backend's directory layout and file
names; this is about the SQLite backend's schema and how each port method
lands as rows. The `parametrise-the-suite` marker system pins these to
SQLite so they do not try to run against YAML.
"""

import os

import pytest

from board_game_concept.service.errors import UnreadableGame
from board_game_concept.storage.sqlite_repository import SqliteGameRepository

pytestmark = pytest.mark.backend('sqlite')


def _one_unit(unit_id=0, player=1, name='x1', flag=False):
    return {
        'id': unit_id, 'player': player, 'type': 'Cross', 'name': name,
        'symbol': 'X', 'attack': 1, 'health': 5, 'energy': 10,
        'type_attack': 1, 'type_health': 5, 'type_energy': 10,
        'x': 2, 'y': 3, 'state': 0, 'direction': 0,
        'destroyed': False, 'on_board': True, 'flag': flag,
    }


def test_ensure_creates_the_database_and_its_tables(tmp_path):
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    assert os.path.isfile(tmp_path / 'games' / '_one' / 'game.sqlite3')

    tables = repository._get(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "ORDER BY name").fetchall()
    names = [row['name'] for row in tables]
    for expected in ('games', 'memberships', 'unit_types', 'units', 'orders',
                     'commits', 'drafts', 'rejections', 'sightings',
                     'turn_events', 'eliminated'):
        assert expected in names, f'{expected} missing from {names}'


def test_units_round_trip(tmp_path):
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_units({'board': {'size_x': 4, 'size_y': 4},
                            'turn': 0, 'player': None,
                            'units': [_one_unit()]})
    got = repository.read_units()
    assert len(got) == 1
    assert got[0]['name'] == 'x1'
    assert got[0]['x'] == 2 and got[0]['y'] == 3
    assert got[0]['destroyed'] is False


def test_orders_round_trip(tmp_path):
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_orders(1, {'units': [_one_unit()]})
    got = repository.read_orders(1)
    assert got is not None
    assert got['units'][0]['name'] == 'x1'
    assert repository.has_orders(1) is True

    repository.clear_orders()
    assert repository.has_orders(1) is False
    assert repository.read_orders(1) is None


def test_commits_have_a_turn(tmp_path):
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.mark_committed(1, turn=3)
    repository.mark_committed(2, turn=4)
    assert repository.committed_players() == [1, 2]
    assert repository.committed_players(turn=3) == [1]
    assert repository.has_committed(1) is True

    # `clear_commits` spends the turn but leaves the marker
    repository.clear_commits()
    assert repository.has_committed(1) is True
    assert repository.committed_players(turn=3) == []
    assert repository.committed_players() == [1, 2]


def test_drafts_round_trip(tmp_path):
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    assert repository.read_draft(1) is None
    repository.write_draft(1, {'turn': 0, 'commands': [
        {'kind': 'AddUnit', 'name': 'x1'}]})
    read = repository.read_draft(1)
    assert read == {'turn': 0, 'commands': [
        {'kind': 'AddUnit', 'name': 'x1'}]}
    repository.clear_draft(1)
    assert repository.read_draft(1) is None


def test_read_view_is_the_visibility_join(tmp_path):
    """A view is `units` joined against `sightings` for that viewer."""
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()

    # player 1 sees x1 and player 2 sees y1; each viewer's `read_view` is
    # exactly those units and nothing else
    x1 = _one_unit(unit_id=0, player=1, name='x1')
    y1 = _one_unit(unit_id=1, player=2, name='y1')
    repository.write_units({'units': [x1, y1]})

    repository.write_view(1, {'units': [x1]})
    repository.write_view(2, {'units': [y1]})

    assert [unit['name'] for unit in repository.read_view(1)] == ['x1']
    assert [unit['name'] for unit in repository.read_view(2)] == ['y1']

    # a rewrite replaces, not accumulates
    repository.write_view(1, {'units': [y1]})
    assert [unit['name'] for unit in repository.read_view(1)] == ['y1']


def test_progress_round_trips_with_and_without_an_outcome(tmp_path):
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    assert repository.read_progress() is None

    repository.write_progress({'turn': 3, 'eliminated': [2]})
    got = repository.read_progress()
    assert got == {'turn': 3, 'eliminated': [2]}

    repository.write_progress({'turn': 4, 'eliminated': [2],
                               'outcome': {'decided': True, 'winner': 1,
                                           'turn': 4}})
    got = repository.read_progress()
    assert got['outcome'] == {'decided': True, 'winner': 1, 'turn': 4}


def test_turn_events_are_written(tmp_path):
    """The combat log lands as rows even though nothing reads it yet."""
    class Event:
        def __init__(self, kind, detail):
            self.kind = kind
            self.detail = detail

    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_turn_events(3, [
        Event('refused', {'unit': 'x1', 'reason': 'destroyed'}),
        Event('moved', {'unit': 'y1'}),
    ])
    rows = repository._get(
        'SELECT turn_no, seq, kind, payload FROM turn_events '
        'ORDER BY seq').fetchall()
    assert [row['kind'] for row in rows] == ['refused', 'moved']
    assert rows[0]['turn_no'] == 3


def test_the_port_says_what_an_implementation_owes(tmp_path):
    """A partial implementation fails loudly rather than silently."""
    from board_game_concept.storage.repository import GameRepository

    class Half(GameRepository):
        pass

    with pytest.raises(NotImplementedError):
        Half().read_board()


def test_a_budget_round_trips(tmp_path):
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_player(1, {}, 150)
    assert repository.read_player(1)['budget'] == 150
    # re-registering the same player carries the new budget, rather than
    # leaving the row as `INSERT OR IGNORE` would have
    repository.write_player(1, {}, 60)
    assert repository.read_player(1)['budget'] == 60


def test_a_membership_without_a_budget_column_is_refused(tmp_path):
    # a database written before budgets existed. `CREATE TABLE IF NOT EXISTS`
    # will not add the column, and this change carries no migration, so the
    # read is refused the way a YAML record with no budget is
    repository = SqliteGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_player(1, {}, 100)
    connection = repository._get()
    connection.execute('DROP TABLE memberships')
    connection.execute(
        'CREATE TABLE memberships (player_number INTEGER PRIMARY KEY)')
    connection.execute('INSERT INTO memberships VALUES (1)')
    with pytest.raises(UnreadableGame) as raised:
        repository.read_player(1)
    assert 'budget' in str(raised.value)
