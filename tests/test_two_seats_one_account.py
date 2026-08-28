"""One person playing both sides of a game, over HTTP.

The case that decided the shape of the guard. Because one account may hold
several seats, an account no longer says which number it is acting as - so
the number stays in the path and is checked rather than looked up. This
suite is what that buys: somebody can try the game without a second person.

Each seat has to stay a separate identity through all of it. Its own army,
its own orders, its own view, and its own place at the commit barrier.
"""

import pytest

from board_game_concept import Game
from board_game_concept.http.app import create_app
from board_game_concept.service import games as game_ops
from board_game_concept.service.commands import AddPlayer, SetBoard
from board_game_concept.storage.sqlite_repository import SqliteGameRepository

pytestmark = pytest.mark.backend('sqlite')

GAME = 'solo'


@pytest.fixture(name='client')
def _client(tmp_path):
    admin = Game(SqliteGameRepository(GAME, base_path=str(tmp_path)), 0)
    admin.load()
    game_ops.perform(admin, SetBoard(size_x=4, size_y=4))
    game_ops.perform(admin, AddPlayer(number=1))
    game_ops.perform(admin, AddPlayer(number=2))
    admin.serverSave()
    return create_app(base_path=str(tmp_path), backend='sqlite').test_client()


@pytest.fixture(name='ada')
def _ada(client):
    """One account, holding both seats of the game."""
    client.post('/accounts', json={'username': 'ada', 'password': 'secret12'})
    token = client.post('/sessions', json={'username': 'ada',
                                           'password': 'secret12'}
                        ).get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    for number in (1, 2):
        assert client.post(f'/games/{GAME}/seats/{number}',
                           headers=headers).status_code == 201
    return headers


def _command(client, headers, number, record):
    response = client.post(f'/games/{GAME}/players/{number}/commands',
                           json=record, headers=headers)
    assert response.status_code == 204, response.get_json()


def _deploy(client, headers, number, x, y):
    _command(client, headers, number,
             {'kind': 'add_type', 'name': f'Cross{number}', 'symbol': 'X',
              'attack': 1, 'health': 5, 'energy': 10})
    _command(client, headers, number,
             {'kind': 'add_unit', 'type_name': f'Cross{number}',
              'name': f'u{number}', 'x': x, 'y': y})
    # a setup is refused unless a unit carries the seat's flag
    _command(client, headers, number,
             {'kind': 'set_flag', 'unit': f'u{number}'})


def _units(client, headers, number):
    response = client.get(f'/games/{GAME}/players/{number}/views/units',
                          headers=headers)
    assert response.status_code == 200
    return response.get_json()['units']


def test_one_account_plays_both_sides_of_a_whole_turn(client, ada):
    _deploy(client, ada, 1, 0, 0)
    _deploy(client, ada, 2, 3, 3)

    first = client.post(f'/games/{GAME}/players/1/commit', headers=ada)
    assert first.status_code == 202, first.get_json()
    # the barrier counts numbers, not people: holding both seats does not
    # commit both
    assert first.get_json()['waiting_on'] == [2]

    second = client.post(f'/games/{GAME}/players/2/commit', headers=ada)
    assert second.status_code == 200, second.get_json()
    assert second.get_json()['resolved'] is True
    assert second.get_json()['turn_number'] == 1


def test_each_seat_holds_only_its_own_units(client, ada):
    _deploy(client, ada, 1, 0, 0)
    _deploy(client, ada, 2, 3, 3)
    client.post(f'/games/{GAME}/players/1/commit', headers=ada)
    client.post(f'/games/{GAME}/players/2/commit', headers=ada)

    one = _units(client, ada, 1)
    two = _units(client, ada, 2)

    assert [unit['name'] for unit in one] == ['u1']
    assert [unit['name'] for unit in two] == ['u2']
    assert all(unit['player'] == 1 for unit in one)
    assert all(unit['player'] == 2 for unit in two)


def test_neither_seat_is_shown_what_the_other_sees(client, ada):
    """Holding both seats is not a way round the fog of war.

    Visibility is decided by the number, never by who is entitled to it, so
    two seats held by one person see exactly what two seats held by two
    people would.
    """
    _deploy(client, ada, 1, 0, 0)
    _deploy(client, ada, 2, 3, 3)
    client.post(f'/games/{GAME}/players/1/commit', headers=ada)
    client.post(f'/games/{GAME}/players/2/commit', headers=ada)

    for number, mine, theirs in ((1, 'u1', 'u2'), (2, 'u2', 'u1')):
        names = [unit['name'] for unit in _units(client, ada, number)]
        assert mine in names
        assert theirs not in names


def test_an_order_belongs_to_the_seat_that_gave_it(client, ada):
    _deploy(client, ada, 1, 0, 0)
    _deploy(client, ada, 2, 3, 3)
    client.post(f'/games/{GAME}/players/1/commit', headers=ada)
    client.post(f'/games/{GAME}/players/2/commit', headers=ada)

    _command(client, ada, 1, {'kind': 'move', 'unit': 'u1', 'direction': 2})

    ordered = [u for u in _units(client, ada, 1) if u['name'] == 'u1'][0]
    assert ordered['direction'] == 'east'

    # the other seat's unit was not ordered by that
    other = [u for u in _units(client, ada, 2) if u['name'] == 'u2'][0]
    assert other['direction'] is None


def test_a_seat_may_not_order_a_unit_of_the_other_seat(client, ada):
    """Entitlement to both seats is still entitlement to each separately."""
    _deploy(client, ada, 1, 0, 0)
    _deploy(client, ada, 2, 3, 3)
    client.post(f'/games/{GAME}/players/1/commit', headers=ada)
    client.post(f'/games/{GAME}/players/2/commit', headers=ada)

    response = client.post(f'/games/{GAME}/players/1/commands',
                           json={'kind': 'move', 'unit': 'u2',
                                 'direction': 2}, headers=ada)

    assert response.status_code == 400


def test_the_two_seats_keep_separate_uncommitted_work(client, ada):
    _deploy(client, ada, 1, 0, 0)

    # seat 1 has drafted a type and a unit; seat 2 has drafted nothing
    assert [unit['name'] for unit in _units(client, ada, 1)] == ['u1']
    assert _units(client, ada, 2) == []


def test_a_third_seat_is_still_refused(client, ada, tmp_path):
    """Two seats of this game is not a seat of every game."""
    other = Game(SqliteGameRepository('other', base_path=str(tmp_path)), 0)
    other.load()
    game_ops.perform(other, SetBoard(size_x=4, size_y=4))
    game_ops.perform(other, AddPlayer(number=1))
    other.serverSave()

    assert client.get('/games/other/players/1/views/board',
                      headers=ada).status_code == 403
