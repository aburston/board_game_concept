"""The registry over HTTP: listing games, and making one.

Both behind the guard, so this drives the raw client and arranges its own
credentials - what a lobby may see and who may create a game are part of what
is under test.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from game_harness import GameHarness, DEFAULT_BACKEND       # noqa: E402
from board_game_concept.http.app import create_app          # noqa: E402
from board_game_concept.domain import army
from board_game_concept.service import registry             # noqa: E402


@pytest.fixture(name='base_path')
def _base_path(tmp_path):
    return tmp_path


@pytest.fixture(name='client')
def _client(base_path):
    return create_app(base_path=str(base_path),
                      backend=DEFAULT_BACKEND).test_client()


def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def _sign_in(client, username, password):
    response = client.post('/sessions',
                           json={'username': username, 'password': password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()['token']


def _admin(client):
    """The administrator past the password gate. Safe to call twice."""
    body = client.post('/sessions',
                       json={'username': 'admin', 'password': 'admin'})
    if body.status_code == 200:
        token = body.get_json()['token']
        assert client.post('/accounts/current/password',
                           json={'current': 'admin', 'new': 'admin-secret'},
                           headers=_bearer(token)).status_code == 200
        return _bearer(token)
    return _bearer(_sign_in(client, 'admin', 'admin-secret'))


def _player(client, name='ada'):
    assert client.post('/accounts', json={'username': name,
                                          'password': 'secret12'}
                       ).status_code == 201
    return _bearer(_sign_in(client, name, 'secret12'))


def _game(base_path, gameno, players=(1, 2)):
    harness = GameHarness(base_path, gameno=gameno, backend=DEFAULT_BACKEND)
    harness.create(5, 5, list(players))
    return harness


def _find(body, gameno):
    return [game for game in body['games'] if game['gameno'] == gameno][0]


# --- guarded

def test_listing_needs_an_account(client):
    assert client.get('/games').status_code == 401


def test_creating_needs_an_account(client):
    assert client.post('/games', json={'gameno': 'x'}).status_code == 401


def test_a_player_may_list(client, base_path):
    _game(base_path, 'one')
    assert client.get('/games', headers=_player(client)).status_code == 200


def test_a_player_may_not_create(client):
    response = client.post('/games', json={'gameno': 'x'},
                           headers=_player(client))

    assert response.status_code == 403
    assert registry.game_numbers(str(client.application.config['BASE_PATH'])
                                 ) == []


def test_the_administrator_is_gated_until_its_password_changes(client):
    token = _sign_in(client, 'admin', 'admin')
    assert client.post('/games', json={'gameno': 'x'},
                       headers=_bearer(token)).status_code == 403


# --- listing

def test_an_empty_tree_lists_nothing(client):
    assert client.get('/games', headers=_player(client)).get_json() == {
        'games': []}


def test_a_game_is_listed_with_its_state_and_turn(client, base_path):
    _game(base_path, 'one')

    body = client.get('/games', headers=_player(client)).get_json()

    listed = _find(body, 'one')
    assert listed['state'] == registry.SETTING_UP
    assert listed['turn_number'] == 0
    assert (listed['size_x'], listed['size_y']) == (5, 5)


def test_a_game_is_listed_whether_or_not_the_caller_holds_a_seat(client,
                                                                 base_path):
    _game(base_path, 'one')
    body = client.get('/games', headers=_player(client, 'nobody')).get_json()
    assert _find(body, 'one')


def test_the_listing_names_each_seat_and_who_holds_it(client, base_path):
    _game(base_path, 'one')
    ada = _player(client, 'ada')
    assert client.post('/games/one/seats/2', headers=ada).status_code == 201

    body = client.get('/games', headers=ada).get_json()

    seats = _find(body, 'one')['seats']
    assert [seat['number'] for seat in seats] == [1, 2]
    assert [seat['held_by'] for seat in seats] == [None, 'ada']
    assert [seat['open'] for seat in seats] == [True, False]


def test_a_game_being_set_up_says_how_many_seats_are_open(client, base_path):
    _game(base_path, 'one', players=(1, 2, 3))
    ada = _player(client, 'ada')
    client.post('/games/one/seats/2', headers=ada)

    body = client.get('/games', headers=ada).get_json()

    assert _find(body, 'one')['open_seats'] == 2


def test_the_listing_carries_nothing_private(client, base_path):
    """A username, a number, and whether that seat has committed.

    `committed` is how the lobby knows to send a player who has committed to
    the board rather than back to the armoury, where every command they could
    give would be refused. It says that somebody has finished their turn and
    nothing whatever about what is in it - the same fact the barrier already
    tells the players it is waiting on.
    """
    _game(base_path, 'one')
    ada = _player(client, 'ada')
    client.post('/games/one/seats/2', headers=ada)

    listed = _find(client.get('/games', headers=ada).get_json(), 'one')

    for leaked in ('units', 'types', 'rows', 'budget', 'spent', 'password'):
        assert leaked not in listed
    for seat in listed['seats']:
        assert set(seat) == {'number', 'held_by', 'open', 'committed'}
        assert isinstance(seat['committed'], bool)


def test_a_game_made_by_a_role_appears_without_registration(client,
                                                            base_path):
    ada = _player(client)
    assert client.get('/games', headers=ada).get_json()['games'] == []

    _game(base_path, 'made-elsewhere')

    body = client.get('/games', headers=ada).get_json()
    assert _find(body, 'made-elsewhere')


# --- creating

def test_the_administrator_creates_a_game(client, base_path):
    response = client.post('/games', json={'gameno': 'new-one'},
                           headers=_admin(client))

    assert response.status_code == 201
    body = response.get_json()
    assert body['gameno'] == 'new-one'
    assert body['state'] == registry.SETTING_UP
    assert body['size_x'] == army.DEFAULT_SIZE_X
    assert body['size_y'] == army.DEFAULT_SIZE_Y
    assert body['seats'] == []
    assert registry.exists('new-one', str(base_path))


def test_a_created_game_is_listed(client):
    admin = _admin(client)
    client.post('/games', json={'gameno': 'new-one'}, headers=admin)

    body = client.get('/games', headers=admin).get_json()
    assert _find(body, 'new-one')['state'] == registry.SETTING_UP


def test_creating_a_number_already_in_use_is_refused(client, base_path):
    _game(base_path, 'one')

    response = client.post('/games', json={'gameno': 'one'},
                           headers=_admin(client))

    assert response.status_code == 409
    listed = _find(client.get('/games', headers=_admin(client)).get_json(),
                   'one')
    assert (listed['size_x'], listed['size_y']) == (5, 5)
    assert [seat['number'] for seat in listed['seats']] == [1, 2]


def test_creating_without_a_number_is_refused(client):
    response = client.post('/games', json={}, headers=_admin(client))
    assert response.status_code == 400


def test_a_created_game_is_set_up_by_the_ordinary_commands(client,
                                                           base_path):
    admin = _admin(client)
    client.post('/games', json={'gameno': 'new-one'}, headers=admin)

    for record in ({'kind': 'set_board', 'size_x': 6, 'size_y': 6},
                   {'kind': 'add_player', 'number': 1, 'budget': 100}):
        assert client.post('/games/new-one/players/0/commands', json=record,
                           headers=admin).status_code == 204
    assert client.post('/games/new-one/players/0/commit',
                       headers=admin).status_code == 200

    listed = _find(client.get('/games', headers=admin).get_json(), 'new-one')
    assert (listed['size_x'], listed['size_y']) == (6, 6)
    assert [seat['number'] for seat in listed['seats']] == [1]


def test_the_lobby_shows_what_is_committed_and_not_what_is_drafted(client):
    """A command is drafted until it is committed, and the registry reads the
    game rather than anybody's session - so a board the administrator has
    typed but not committed is not a board the lobby reports."""
    admin = _admin(client)
    client.post('/games', json={'gameno': 'new-one'}, headers=admin)
    client.post('/games/new-one/players/0/commands',
                json={'kind': 'set_board', 'size_x': 6, 'size_y': 6},
                headers=admin)

    listed = _find(client.get('/games', headers=admin).get_json(), 'new-one')
    assert listed['size_x'] == army.DEFAULT_SIZE_X, 'the board it was created with, not the one being drafted'

    client.post('/games/new-one/players/0/commit', headers=admin)

    listed = _find(client.get('/games', headers=admin).get_json(), 'new-one')
    assert listed['size_x'] == 6
