"""The Flask app that serves the read side, exercised through its test client.

The Flask `app.test_client()` runs the WSGI stack without a socket, which is
what the unit tests need: one request, one response, no background thread.
The end-to-end observer coverage lives in `test_observer_over_http.py`.
"""

import pytest

from board_game_concept import Game
from board_game_concept.domain import Board, Player, UnitType
from board_game_concept.http.app import create_app
from board_game_concept.service import games as game_ops
from board_game_concept.service.commands import (AddPlayer, AddType, AddUnit,
                                                 SetBoard)
from board_game_concept.storage.sqlite_repository import SqliteGameRepository

pytestmark = pytest.mark.backend('sqlite')


def _set_up(base_path, gameno='one'):
    """A game with one player who has deployed one unit, resolved once."""
    admin = Game(SqliteGameRepository(gameno, base_path=str(base_path)), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    game_ops.perform(admin, AddPlayer(number=1))
    admin.serverSave()

    player = Game(SqliteGameRepository(gameno, base_path=str(base_path)), 1)
    player.load()
    game_ops.perform(player, AddType(name='Cross', symbol='X',
                                     attack=1, health=5, energy=10))
    game_ops.perform(player, AddUnit(type_name='Cross', name='x1',
                                     x=2, y=3))
    player.clientSave()

    server = Game(SqliteGameRepository(gameno, base_path=str(base_path)), 0)
    server.load()
    server.serverSave()


def _client(base_path):
    return create_app(base_path=str(base_path),
                      backend='sqlite').test_client()


def test_health_answers(tmp_path):
    _set_up(tmp_path)
    response = _client(tmp_path).get('/_/health')
    assert response.status_code == 200
    assert response.get_json() == {'ok': True}


def test_players_lists_the_numbers_registered(tmp_path):
    _set_up(tmp_path)
    response = _client(tmp_path).get('/games/one/players')
    assert response.status_code == 200
    assert response.get_json() == {'players': [1]}


def test_state_returns_the_reading_half_data(tmp_path):
    _set_up(tmp_path)
    response = _client(tmp_path).get('/games/one/players/1/state')
    assert response.status_code == 200
    state = response.get_json()
    assert state['turn_number'] == 1
    assert state['outcome'] is None
    assert state['new_game'] is False
    assert state['unprocessed_moves'] is False
    assert state['rejected'] == []
    assert state['dropped'] == []


def test_views_return_the_same_json_the_show_command_renders(tmp_path):
    _set_up(tmp_path)
    client = _client(tmp_path)

    board = client.get('/games/one/players/1/views/board').get_json()
    assert board['board']['size_x'] == 4
    assert 'X' in board['board']['rows'][3]

    units = client.get('/games/one/players/1/views/units').get_json()
    assert [u['name'] for u in units['units']] == ['x1']

    types = client.get('/games/one/players/1/views/types').get_json()
    assert [t['name'] for t in types['types']] == ['Cross']

    players = client.get('/games/one/players/1/views/players').get_json()
    assert players['players'] == [{'player': 1, 'status': 'active'}]


def test_a_missing_game_is_404(tmp_path):
    _set_up(tmp_path)
    response = _client(tmp_path).get('/games/nosuch/players/1/state')
    assert response.status_code == 404


def test_an_unknown_view_is_404(tmp_path):
    _set_up(tmp_path)
    response = _client(tmp_path).get('/games/one/players/1/views/nosuch')
    assert response.status_code == 404


def test_a_player_who_does_not_exist_is_404(tmp_path):
    _set_up(tmp_path)
    response = _client(tmp_path).get('/games/one/players/99/state')
    assert response.status_code == 404
