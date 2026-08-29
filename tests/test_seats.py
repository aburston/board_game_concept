"""Taking a seat of a game, and giving one up.

A seat is a player number the administrator registered. Claiming one is not
registering a player, and this suite holds it to that.
"""

import pytest

from board_game_concept import Game
from board_game_concept.http.app import create_app
from board_game_concept.service import games as game_ops
from board_game_concept.service.commands import (
    AddPlayer, AddType, AddUnit, SetBoard, SetFlag)
from board_game_concept.storage.sqlite_repository import SqliteGameRepository

pytestmark = pytest.mark.backend('sqlite')

GAME = 'one'


def _repository(base_path, gameno=GAME):
    return SqliteGameRepository(gameno, base_path=str(base_path))


def _set_up(base_path, gameno=GAME, players=(1, 2)):
    admin = Game(_repository(base_path, gameno), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    for number in players:
        game_ops.perform(admin, AddPlayer(number=number))
    admin.serverSave()


def _play_a_turn(base_path, gameno=GAME, players=(1, 2)):
    """Deploy for each player and resolve, so the turn number reaches 1."""
    for index, number in enumerate(players):
        session = Game(_repository(base_path, gameno), number)
        session.load()
        game_ops.perform(session, AddType(name='Cross', symbol='X', attack=1,
                                          health=1, energy=10))
        # each player deploys in the half a two-player setup gives them: the
        # first on the top row, the rest along the bottom one
        row = 0 if index == 0 else session.getBoard().size_y - 1
        game_ops.perform(session, AddUnit(type_name='Cross',
                                          name=f'u{number}', x=index, y=row))
        game_ops.perform(session, SetFlag(unit=f'u{number}'))
        session.clientSave()
    resolver = Game(_repository(base_path, gameno), 0)
    resolver.load()
    resolver.resolveWhenReady()


@pytest.fixture(name='client')
def _client(tmp_path):
    _set_up(tmp_path)
    return create_app(base_path=str(tmp_path), backend='sqlite').test_client()


def _account(client, name='ada'):
    assert client.post('/accounts', json={'username': name,
                                          'password': 'secret12'}
                       ).status_code == 201
    token = client.post('/sessions', json={'username': name,
                                           'password': 'secret12'}
                        ).get_json()['token']
    return {'Authorization': f'Bearer {token}'}


def test_the_seats_of_a_game_are_listed(client):
    ada = _account(client)
    body = client.get(f'/games/{GAME}/seats', headers=ada).get_json()

    assert [seat['number'] for seat in body['seats']] == [1, 2]
    assert all(seat['open'] for seat in body['seats'])
    assert all(seat['held_by'] is None for seat in body['seats'])


def test_listing_seats_needs_an_account(client):
    assert client.get(f'/games/{GAME}/seats').status_code == 401


def test_a_seat_is_claimed_and_then_shows_its_holder(client):
    ada = _account(client)

    assert client.post(f'/games/{GAME}/seats/2',
                       headers=ada).status_code == 201

    body = client.get(f'/games/{GAME}/seats', headers=ada).get_json()
    taken = [seat for seat in body['seats'] if seat['number'] == 2][0]
    assert taken['held_by'] == 'ada'
    assert taken['open'] is False


def test_claiming_a_seat_that_is_held_is_refused(client):
    ada = _account(client, 'ada')
    bob = _account(client, 'bob')
    client.post(f'/games/{GAME}/seats/2', headers=ada)

    assert client.post(f'/games/{GAME}/seats/2',
                       headers=bob).status_code == 400

    body = client.get(f'/games/{GAME}/seats', headers=bob).get_json()
    assert [s for s in body['seats'] if s['number'] == 2][0]['held_by'] == 'ada'


def test_claiming_a_number_the_game_has_not_registered(client):
    ada = _account(client)
    response = client.post(f'/games/{GAME}/seats/7', headers=ada)

    assert response.status_code == 400
    assert 'no player 7' in response.get_json()['error']


def test_claiming_does_not_register_a_player(client, tmp_path):
    ada = _account(client)
    client.post(f'/games/{GAME}/seats/2', headers=ada)

    assert _repository(tmp_path).player_numbers() == [1, 2]


def test_one_account_may_hold_two_seats_of_one_game(client):
    ada = _account(client)

    assert client.post(f'/games/{GAME}/seats/1',
                       headers=ada).status_code == 201
    assert client.post(f'/games/{GAME}/seats/2',
                       headers=ada).status_code == 201

    body = client.get('/accounts/current', headers=ada).get_json()
    assert {'gameno': GAME, 'number': 1} in body['seats']
    assert {'gameno': GAME, 'number': 2} in body['seats']


def test_a_seat_is_given_up_before_the_game_starts(client):
    ada = _account(client, 'ada')
    bob = _account(client, 'bob')
    client.post(f'/games/{GAME}/seats/2', headers=ada)

    assert client.delete(f'/games/{GAME}/seats/2',
                         headers=ada).status_code == 200
    assert client.post(f'/games/{GAME}/seats/2',
                       headers=bob).status_code == 201


def test_only_the_holder_gives_up_a_seat(client):
    ada = _account(client, 'ada')
    bob = _account(client, 'bob')
    client.post(f'/games/{GAME}/seats/2', headers=ada)

    assert client.delete(f'/games/{GAME}/seats/2',
                         headers=bob).status_code == 403

    body = client.get(f'/games/{GAME}/seats', headers=bob).get_json()
    assert [s for s in body['seats'] if s['number'] == 2][0]['held_by'] == 'ada'


def test_a_seat_may_be_claimed_after_setup_and_before_the_first_turn(client):
    """The window a lobby exists for: the board is set and nobody has moved."""
    ada = _account(client)
    assert client.post(f'/games/{GAME}/seats/2',
                       headers=ada).status_code == 201


def test_claiming_is_refused_once_a_turn_has_resolved(client, tmp_path):
    _play_a_turn(tmp_path)
    ada = _account(client)

    response = client.post(f'/games/{GAME}/seats/2', headers=ada)

    assert response.status_code == 400
    assert 'started' in response.get_json()['error']


def test_giving_up_is_refused_once_a_turn_has_resolved(client, tmp_path):
    ada = _account(client)
    client.post(f'/games/{GAME}/seats/2', headers=ada)
    _play_a_turn(tmp_path)

    response = client.delete(f'/games/{GAME}/seats/2', headers=ada)

    assert response.status_code == 400
    assert 'started' in response.get_json()['error']


def test_claiming_needs_an_account(client):
    assert client.post(f'/games/{GAME}/seats/2').status_code == 401
    assert client.delete(f'/games/{GAME}/seats/2').status_code == 401
