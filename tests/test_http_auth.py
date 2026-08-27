"""The guard in front of the served game, and the account routes.

This is the suite that drives the raw test client rather than the
authorising one in `conftest.py`: what is under test here is the refusal
itself, so nothing may arrange entitlement behind it.
"""

import pytest

from board_game_concept import Game
from board_game_concept.http.app import create_app
from board_game_concept.service import games as game_ops
from board_game_concept.service.commands import AddPlayer, SetBoard
from board_game_concept.storage.sqlite_repository import SqliteGameRepository

pytestmark = pytest.mark.backend('sqlite')

GAME = 'one'


def _game(base_path, gameno=GAME, players=(1, 2)):
    admin = Game(SqliteGameRepository(gameno, base_path=str(base_path)), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    for number in players:
        game_ops.perform(admin, AddPlayer(number=number))
    admin.serverSave()


@pytest.fixture(name='app')
def _app(tmp_path):
    _game(tmp_path)
    return create_app(base_path=str(tmp_path), backend='sqlite')


@pytest.fixture(name='client')
def _client(app):
    return app.test_client()


def _sign_in(client, username, password):
    response = client.post('/sessions',
                           json={'username': username, 'password': password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()['token']


def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def _usable_admin(client):
    """The administrator past the password gate, and its token."""
    token = _sign_in(client, 'admin', 'admin')
    changed = client.post('/accounts/current/password',
                          json={'current': 'admin', 'new': 'admin-secret'},
                          headers=_bearer(token))
    assert changed.status_code == 200
    return token


def _seated_player(client, name='ada', number=2, gameno=GAME):
    """A registered account holding a seat, and its token."""
    assert client.post('/accounts', json={'username': name,
                                          'password': 'secret12'}
                       ).status_code == 201
    token = _sign_in(client, name, 'secret12')
    claimed = client.post(f'/games/{gameno}/seats/{number}',
                          headers=_bearer(token))
    assert claimed.status_code == 201, claimed.get_json()
    return token


# --- no credential at all

GAME_PATHS = [
    ('get', f'/games/{GAME}/players/1/state'),
    ('get', f'/games/{GAME}/players/1/views/board'),
    ('get', f'/games/{GAME}/players/1/views/units'),
    ('post', f'/games/{GAME}/players/1/commands'),
    ('post', f'/games/{GAME}/players/1/commit'),
    ('get', f'/games/{GAME}/players/1/wait/turn'),
    ('get', f'/games/{GAME}/players/1/wait/commit'),
    ('get', f'/games/{GAME}/players'),
    ('get', f'/games/{GAME}/seats'),
]


@pytest.mark.parametrize('method,path', GAME_PATHS)
def test_a_request_with_no_token_is_refused(client, method, path):
    response = getattr(client, method)(path)
    assert response.status_code == 401


@pytest.mark.parametrize('method,path', GAME_PATHS)
def test_a_refused_request_returns_nothing_of_the_game(client, method, path):
    body = getattr(client, method)(path).get_json()
    assert set(body) == {'error'}
    for leak in ('board', 'units', 'rows', 'players', 'turn_number', 'types'):
        assert leak not in body


def test_a_token_that_was_never_issued_is_refused(client):
    response = client.get(f'/games/{GAME}/players/1/views/board',
                          headers=_bearer('never-issued'))
    assert response.status_code == 401


def test_an_ended_token_is_refused(client):
    token = _seated_player(client)
    assert client.get(f'/games/{GAME}/players/2/views/board',
                      headers=_bearer(token)).status_code == 200

    client.delete('/sessions/current', headers=_bearer(token))

    assert client.get(f'/games/{GAME}/players/2/views/board',
                      headers=_bearer(token)).status_code == 401


def test_naming_a_different_number_does_not_help(client):
    """The number alone proves nothing, whichever number it is."""
    for number in (0, 1, 2, 999, 1000):
        assert client.get(
            f'/games/{GAME}/players/{number}/state').status_code == 401


def test_health_needs_no_credential(client):
    assert client.get('/_/health').status_code == 200


# --- the password gate

def test_the_administrator_is_refused_until_it_changes_its_password(client):
    token = _sign_in(client, 'admin', 'admin')

    response = client.get(f'/games/{GAME}/players/0/state',
                          headers=_bearer(token))

    assert response.status_code == 403
    assert response.get_json()['must_change_password'] is True


def test_the_observer_is_refused_until_it_changes_its_password(client):
    token = _sign_in(client, 'observer', 'observer')
    response = client.get(f'/games/{GAME}/players/1000/views/board',
                          headers=_bearer(token))
    assert response.status_code == 403


def test_signing_in_says_the_password_must_change(client):
    body = client.post('/sessions', json={'username': 'admin',
                                          'password': 'admin'}).get_json()
    assert body['must_change_password'] is True


def test_changing_the_password_lifts_the_gate(client):
    token = _usable_admin(client)
    assert client.get(f'/games/{GAME}/players/0/state',
                      headers=_bearer(token)).status_code == 200


def test_the_old_password_stops_working(client):
    _usable_admin(client)
    refused = client.post('/sessions', json={'username': 'admin',
                                             'password': 'admin'})
    assert refused.status_code == 401


def test_a_registered_account_is_not_gated(client):
    token = _seated_player(client)
    assert client.get(f'/games/{GAME}/players/2/state',
                      headers=_bearer(token)).status_code == 200


# --- may_act_as, over HTTP

def test_a_player_reads_its_own_seat(client):
    token = _seated_player(client, number=2)
    response = client.get(f'/games/{GAME}/players/2/views/board',
                          headers=_bearer(token))
    assert response.status_code == 200
    assert 'board' in response.get_json()


def test_a_player_may_not_read_another_seat(client):
    token = _seated_player(client, number=2)
    response = client.get(f'/games/{GAME}/players/1/views/board',
                          headers=_bearer(token))
    assert response.status_code == 403
    assert 'board' not in response.get_json()


def test_a_player_may_not_order_for_another_seat(client):
    token = _seated_player(client, number=2)
    response = client.post(f'/games/{GAME}/players/1/commands',
                           json={'kind': 'move', 'unit': 'x1',
                                 'direction': 1},
                           headers=_bearer(token))
    assert response.status_code == 403


def test_a_player_may_not_be_the_administrator_or_the_observer(client):
    token = _seated_player(client, number=2)
    for number in (0, 1000):
        assert client.get(f'/games/{GAME}/players/{number}/state',
                          headers=_bearer(token)).status_code == 403


def test_the_administrator_may_act_as_the_observer(client):
    token = _usable_admin(client)
    assert client.get(f'/games/{GAME}/players/1000/views/board',
                      headers=_bearer(token)).status_code == 200


def test_the_administrator_is_not_a_player_without_a_seat(client):
    token = _usable_admin(client)
    assert client.get(f'/games/{GAME}/players/1/state',
                      headers=_bearer(token)).status_code == 403


def test_a_seat_in_another_game_is_not_a_seat_in_this_one(client, tmp_path):
    _game(tmp_path, gameno='other', players=(1, 2))
    token = _seated_player(client, number=2, gameno=GAME)

    assert client.get(f'/games/other/players/2/views/board',
                      headers=_bearer(token)).status_code == 403


def test_the_cookie_carries_the_token_too(client):
    """A browser sends a cookie; a role sends a header; one token behind both."""
    client.post('/accounts', json={'username': 'ada', 'password': 'secret12'})
    _sign_in(client, 'ada', 'secret12')  # sets the cookie on this client
    token = _sign_in(client, 'ada', 'secret12')
    client.post(f'/games/{GAME}/seats/2', headers=_bearer(token))

    # no explicit header: the cookie set by signing in is what identifies it
    assert client.get(
        f'/games/{GAME}/players/2/views/board').status_code == 200


# --- registering

def test_registering_a_reserved_name_is_refused(client):
    for name in ('admin', 'Admin', 'observer', 'OBSERVER'):
        response = client.post('/accounts', json={'username': name,
                                                  'password': 'secret12'})
        assert response.status_code == 400
        assert 'reserved' in response.get_json()['error']


def test_registering_a_taken_name_in_another_case_is_refused(client):
    assert client.post('/accounts', json={'username': 'Ada',
                                          'password': 'secret12'}
                       ).status_code == 201
    assert client.post('/accounts', json={'username': 'ada',
                                          'password': 'secret12'}
                       ).status_code == 400


def test_registering_a_short_password_is_refused(client):
    response = client.post('/accounts', json={'username': 'ada',
                                              'password': 'short'})
    assert response.status_code == 400
    assert '8' in response.get_json()['error']


def test_a_wrong_password_and_an_unknown_name_refuse_alike(client):
    client.post('/accounts', json={'username': 'ada', 'password': 'secret12'})
    wrong = client.post('/sessions', json={'username': 'ada',
                                           'password': 'not-the-one'})
    unknown = client.post('/sessions', json={'username': 'nobody',
                                             'password': 'not-the-one'})

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()


# --- passwords over HTTP

def test_a_player_cannot_reset_another_account(client):
    client.post('/accounts', json={'username': 'ada', 'password': 'secret12'})
    client.post('/accounts', json={'username': 'bob', 'password': 'secret12'})
    token = _sign_in(client, 'bob', 'secret12')

    response = client.post('/accounts/ada/password',
                           json={'new': 'stolen-secret'},
                           headers=_bearer(token))

    assert response.status_code == 403
    assert client.post('/sessions', json={'username': 'ada',
                                          'password': 'secret12'}
                       ).status_code == 200


def test_the_administrator_resets_another_account(client):
    admin_token = _usable_admin(client)
    client.post('/accounts', json={'username': 'ada', 'password': 'secret12'})

    response = client.post('/accounts/ada/password',
                           json={'new': 'reset-secret'},
                           headers=_bearer(admin_token))

    assert response.status_code == 200
    assert client.post('/sessions', json={'username': 'ada',
                                          'password': 'reset-secret'}
                       ).status_code == 200


def test_changing_with_the_wrong_current_password_is_refused(client):
    client.post('/accounts', json={'username': 'ada', 'password': 'secret12'})
    token = _sign_in(client, 'ada', 'secret12')

    response = client.post('/accounts/current/password',
                           json={'current': 'not-the-one', 'new': 'new-one12'},
                           headers=_bearer(token))

    assert response.status_code == 403


# --- tokens

def test_a_minted_token_works_and_survives_a_logout(client):
    login = _seated_player(client, number=2)
    minted = client.post('/tokens', json={'label': 'reaper-bot'},
                         headers=_bearer(login))
    assert minted.status_code == 201
    minted_token = minted.get_json()['token']

    client.delete('/sessions/current', headers=_bearer(login))

    assert client.get(f'/games/{GAME}/players/2/views/board',
                      headers=_bearer(login)).status_code == 401
    assert client.get(f'/games/{GAME}/players/2/views/board',
                      headers=_bearer(minted_token)).status_code == 200


def test_listing_tokens_does_not_hand_them_out(client):
    token = _seated_player(client)
    client.post('/tokens', json={'label': 'a-bot'}, headers=_bearer(token))

    listed = client.get('/tokens', headers=_bearer(token)).get_json()

    assert any(row['label'] == 'a-bot' for row in listed['tokens'])
    assert token not in str(listed)


def test_a_token_can_be_revoked(client):
    login = _seated_player(client, number=2)
    minted = client.post('/tokens', json={'label': 'a-bot'},
                         headers=_bearer(login)).get_json()['token']

    assert client.delete(f'/tokens/{minted}',
                         headers=_bearer(login)).status_code == 200
    assert client.get(f'/games/{GAME}/players/2/views/board',
                      headers=_bearer(minted)).status_code == 401


def test_one_account_cannot_revoke_another_accounts_token(client):
    ada = _seated_player(client, name='ada', number=2)
    client.post('/accounts', json={'username': 'bob', 'password': 'secret12'})
    bob = _sign_in(client, 'bob', 'secret12')

    assert client.delete(f'/tokens/{ada}',
                         headers=_bearer(bob)).status_code == 404
    assert client.get(f'/games/{GAME}/players/2/views/board',
                      headers=_bearer(ada)).status_code == 200


def test_whoami_names_the_seats_held(client):
    token = _seated_player(client, number=2)
    body = client.get('/accounts/current', headers=_bearer(token)).get_json()

    assert body['username'] == 'ada'
    assert body['kind'] == 'player'
    assert {'gameno': GAME, 'number': 2} in body['seats']
