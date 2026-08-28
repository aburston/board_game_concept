"""A server from nothing to a resolved turn, through accounts.

Starts with an empty directory: no store, no accounts, no game. Everything
below happens through the served contract, which is what makes this the test
that the whole thing hangs together rather than each piece working alone.

The last of it is the point of the change: each player's board holds only
what `visibility` entitles them to, over HTTP, enforced rather than assumed.
"""

import os

import pytest

from board_game_concept.domain import Empty
from board_game_concept.http.app import create_app

# deliberately not pinned to a backend. Everything below happens over HTTP,
# so there is nothing here that knows how a game is stored - and one backend
# choice drives both the game and the account store, so this is where that is
# held to.
GAME = 'one'


@pytest.fixture(name='backend', params=['sqlite', 'yaml'])
def _backend(request):
    return request.param


def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def _sign_in(client, username, password):
    response = client.post('/sessions',
                           json={'username': username, 'password': password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _command(client, headers, number, record, gameno=GAME):
    response = client.post(f'/games/{gameno}/players/{number}/commands',
                           json=record, headers=headers)
    assert response.status_code == 204, response.get_json()


@pytest.fixture(name='base_path')
def _base_path(tmp_path):
    assert os.listdir(str(tmp_path)) == []
    return tmp_path


@pytest.fixture(name='client')
def _client(base_path, backend):
    return create_app(base_path=str(base_path),
                      backend=backend).test_client()


def _store_exists(base_path, backend):
    kept = {'sqlite': 'accounts.sqlite3', 'yaml': 'accounts'}[backend]
    other = {'sqlite': 'accounts', 'yaml': 'accounts.sqlite3'}[backend]
    assert not os.path.exists(os.path.join(str(base_path), other)), (
        'a deployment is one backend or the other, never a mixture')
    return os.path.exists(os.path.join(str(base_path), kept))


def test_a_whole_game_from_an_empty_directory(client, base_path, backend):
    # --- the store is made, with the two system accounts in it, and it is
    #     the one this backend keeps - never the other backend's
    assert _store_exists(base_path, backend)

    # --- the administrator signs in with what it was created with, and is
    #     refused everything until it changes that
    first = _sign_in(client, 'admin', 'admin')
    assert first['must_change_password'] is True
    admin = _bearer(first['token'])

    refused = client.get(f'/games/{GAME}/players/0/state', headers=admin)
    assert refused.status_code == 403
    assert refused.get_json()['must_change_password'] is True

    changed = client.post('/accounts/current/password',
                          json={'current': 'admin', 'new': 'admin-secret'},
                          headers=admin)
    assert changed.status_code == 200

    # --- and now sets a game up: a board and two players
    _command(client, admin, 0, {'kind': 'set_board', 'size_x': 4, 'size_y': 4})
    _command(client, admin, 0, {'kind': 'add_player', 'number': 1,
                                'budget': 100})
    _command(client, admin, 0, {'kind': 'add_player', 'number': 2,
                                'budget': 100})
    assert client.post(f'/games/{GAME}/players/0/commit',
                       headers=admin).status_code == 200

    # --- two people register and take a seat each
    seats = {}
    for name, number in (('ada', 1), ('bob', 2)):
        assert client.post('/accounts', json={'username': name,
                                              'password': 'secret12'}
                           ).status_code == 201
        token = _sign_in(client, name, 'secret12')['token']
        seats[name] = _bearer(token)
        claimed = client.post(f'/games/{GAME}/seats/{number}',
                              headers=seats[name])
        assert claimed.status_code == 201, claimed.get_json()

    listed = client.get(f'/games/{GAME}/seats',
                        headers=seats['ada']).get_json()['seats']
    assert [seat['held_by'] for seat in listed] == ['ada', 'bob']

    # --- each designs a type and deploys a unit, well apart on the board
    _command(client, seats['ada'], 1,
             {'kind': 'add_type', 'name': 'Cross', 'symbol': 'X',
              'attack': 1, 'health': 5, 'energy': 10})
    _command(client, seats['ada'], 1,
             {'kind': 'add_unit', 'type_name': 'Cross', 'name': 'a1',
              'x': 0, 'y': 0})
    _command(client, seats['bob'], 2,
             {'kind': 'add_type', 'name': 'Circle', 'symbol': 'O',
              'attack': 1, 'health': 5, 'energy': 10})
    _command(client, seats['bob'], 2,
             {'kind': 'add_unit', 'type_name': 'Circle', 'name': 'b1',
              'x': 3, 'y': 3})

    # --- and both commit; the turn resolves on the second
    ada_commit = client.post(f'/games/{GAME}/players/1/commit',
                             headers=seats['ada'])
    assert ada_commit.status_code == 202
    assert ada_commit.get_json()['waiting_on'] == [2]

    bob_commit = client.post(f'/games/{GAME}/players/2/commit',
                             headers=seats['bob'])
    assert bob_commit.status_code == 200
    assert bob_commit.get_json()['resolved'] is True
    assert bob_commit.get_json()['turn_number'] == 1


def _play_a_turn(client):
    """Everything the test above does, as a fixture for the ones below."""
    first = _sign_in(client, 'admin', 'admin')
    admin = _bearer(first['token'])
    client.post('/accounts/current/password',
                json={'current': 'admin', 'new': 'admin-secret'},
                headers=admin)
    _command(client, admin, 0, {'kind': 'set_board', 'size_x': 4, 'size_y': 4})
    for number in (1, 2):
        _command(client, admin, 0, {'kind': 'add_player', 'number': number,
                                    'budget': 100})
    client.post(f'/games/{GAME}/players/0/commit', headers=admin)

    seats = {}
    for name, number, symbol, square in (('ada', 1, 'X', (0, 0)),
                                         ('bob', 2, 'O', (3, 3))):
        client.post('/accounts', json={'username': name,
                                       'password': 'secret12'})
        seats[name] = _bearer(_sign_in(client, name, 'secret12')['token'])
        client.post(f'/games/{GAME}/seats/{number}', headers=seats[name])
        _command(client, seats[name], number,
                 {'kind': 'add_type', 'name': f'T{number}', 'symbol': symbol,
                  'attack': 1, 'health': 5, 'energy': 10})
        _command(client, seats[name], number,
                 {'kind': 'add_unit', 'type_name': f'T{number}',
                  'name': f'u{number}', 'x': square[0], 'y': square[1]})
    client.post(f'/games/{GAME}/players/1/commit', headers=seats['ada'])
    client.post(f'/games/{GAME}/players/2/commit', headers=seats['bob'])
    return admin, seats


def test_each_seat_is_given_only_what_visibility_entitles_it_to(client):
    """The guarantee this change exists to make true of the HTTP tier.

    Two units, never in contact, so neither player may see the other's. The
    engine has always got this right; what was missing was anything stopping
    a caller asking in the other player's name.
    """
    _admin, seats = _play_a_turn(client)

    for name, number, mine, theirs in (('ada', 1, 'u1', 'u2'),
                                       ('bob', 2, 'u2', 'u1')):
        units = client.get(f'/games/{GAME}/players/{number}/views/units',
                           headers=seats[name]).get_json()['units']
        names = [unit['name'] for unit in units]
        assert mine in names, name
        assert theirs not in names, name

        board = client.get(f'/games/{GAME}/players/{number}/views/board',
                           headers=seats[name]).get_json()['board']
        # the empty square's glyph is the domain's to choose, so it is asked
        # rather than assumed
        empty = str(Empty())
        symbols = {symbol for row in board['rows'] for symbol in row}
        assert symbols == {empty, 'X' if number == 1 else 'O'}, name
        drawn = [entry['symbol'] for entry in board['legend']]
        assert len(drawn) == 1, f'{name} should see only their own symbol'


def test_asking_in_another_players_name_is_refused(client):
    """What the guarantee above rests on."""
    _admin, seats = _play_a_turn(client)

    refused = client.get(f'/games/{GAME}/players/2/views/units',
                         headers=seats['ada'])
    assert refused.status_code == 403
    assert 'units' not in refused.get_json()


def test_the_observer_changes_its_password_and_then_sees_both_armies(client):
    _admin, _seats = _play_a_turn(client)

    first = _sign_in(client, 'observer', 'observer')
    assert first['must_change_password'] is True
    observer = _bearer(first['token'])

    refused = client.get(f'/games/{GAME}/players/1000/views/units',
                         headers=observer)
    assert refused.status_code == 403

    assert client.post('/accounts/current/password',
                       json={'current': 'observer',
                             'new': 'observer-secret'},
                       headers=observer).status_code == 200

    units = client.get(f'/games/{GAME}/players/1000/views/units',
                       headers=observer).get_json()['units']
    assert {unit['name'] for unit in units} == {'u1', 'u2'}


def test_the_administrator_sees_the_whole_game_too(client):
    admin, _seats = _play_a_turn(client)

    units = client.get(f'/games/{GAME}/players/1000/views/units',
                       headers=admin).get_json()['units']
    assert {unit['name'] for unit in units} == {'u1', 'u2'}


def test_the_store_survives_a_restart_of_the_server(client, base_path,
                                                    backend):
    """A second app over the same directory finds the accounts it left."""
    _admin, seats = _play_a_turn(client)

    restarted = create_app(base_path=str(base_path),
                           backend=backend).test_client()

    # the changed password is the one that works, and `admin` is not
    assert restarted.post('/sessions', json={'username': 'admin',
                                             'password': 'admin'}
                          ).status_code == 401
    assert restarted.post('/sessions', json={'username': 'admin',
                                             'password': 'admin-secret'}
                          ).status_code == 200

    # and a seat claimed before the restart is still held
    token = _sign_in(restarted, 'ada', 'secret12')['token']
    assert restarted.get(f'/games/{GAME}/players/1/views/units',
                         headers=_bearer(token)).status_code == 200
