"""A whole game through exactly the calls `api.js` makes.

The interface is a client of the served contract and of nothing else, so this
drives that contract the way the page does: registering, signing in, listing
games, taking a seat, designing a type, deploying, ordering, committing,
waiting, and reading what the turn did.

If something the page needs cannot be done here, that is a gap in the
contract rather than a reason for a private route - which is the whole reason
this test exists rather than a test of the JavaScript.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from game_harness import DEFAULT_BACKEND                    # noqa: E402
from board_game_concept.http.app import create_app          # noqa: E402
from board_game_concept.service import registry             # noqa: E402


STATIC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'src', 'board_game_concept', 'http', 'static')

GAME = 'one'

# what `api.js` calls each direction, checked against the engine below
NORTH, EAST, SOUTH, WEST = 1, 2, 3, 4


@pytest.fixture(name='base_path')
def _base_path(tmp_path):
    return tmp_path


@pytest.fixture(name='app')
def _app(base_path):
    return create_app(base_path=str(base_path), backend=DEFAULT_BACKEND)


class Page:
    """One browser: a test client that keeps its session cookie.

    The page never sees a token - the cookie the server set is `HttpOnly` -
    so this holds nothing either, and every call below is exactly what
    `api.js` issues.
    """

    def __init__(self, app):
        self.client = app.test_client()

    # --- accounts
    def register(self, username, password):
        return self.client.post('/accounts', json={'username': username,
                                                   'password': password})

    def sign_in(self, username, password):
        return self.client.post('/sessions', json={'username': username,
                                                   'password': password})

    def whoami(self):
        return self.client.get('/accounts/current')

    def change_password(self, current, new):
        return self.client.post('/accounts/current/password',
                                json={'current': current, 'new': new})

    # --- the lobby
    def list_games(self):
        return self.client.get('/games')

    def create_game(self, gameno):
        return self.client.post('/games', json={'gameno': gameno})

    def claim_seat(self, gameno, number):
        return self.client.post(f'/games/{gameno}/seats/{number}')

    def release_seat(self, gameno, number):
        return self.client.delete(f'/games/{gameno}/seats/{number}')

    # --- one seat
    def read_state(self, gameno, number):
        return self.client.get(f'/games/{gameno}/players/{number}/state')

    def read_view(self, gameno, number, subject):
        return self.client.get(
            f'/games/{gameno}/players/{number}/views/{subject}')

    def perform(self, gameno, number, command):
        return self.client.post(f'/games/{gameno}/players/{number}/commands',
                                json=command)

    def commit(self, gameno, number):
        return self.client.post(f'/games/{gameno}/players/{number}/commit')

    def wait_for_turn(self, gameno, number, budget=0.2):
        return self.client.get(
            f'/games/{gameno}/players/{number}/wait/turn?budget={budget}')

    def wait_for_commit(self, gameno, number, budget=0.2):
        return self.client.get(
            f'/games/{gameno}/players/{number}/wait/commit?budget={budget}')


def _administrator(app):
    page = Page(app)
    assert page.sign_in('admin', 'admin').status_code == 200
    assert page.change_password('admin', 'admin-secret').status_code == 200
    return page


def _player(app, username):
    page = Page(app)
    assert page.register(username, 'secret12').status_code == 201
    assert page.sign_in(username, 'secret12').status_code == 200
    return page


def _set_up(admin, gameno=GAME, seats=(1, 2), size=(4, 4)):
    assert admin.create_game(gameno).status_code == 201
    assert admin.perform(gameno, 0, {'kind': 'set_board', 'size_x': size[0],
                                     'size_y': size[1]}).status_code == 204
    for number in seats:
        assert admin.perform(gameno, 0, {'kind': 'add_player',
                                         'number': number,
                                         'budget': 100}).status_code == 204
    assert admin.commit(gameno, 0).status_code == 200


def _deploy(page, gameno, number, symbol, square, health=8):
    assert page.perform(gameno, number, {
        'kind': 'add_type', 'name': f'T{number}', 'symbol': symbol,
        'attack': 1, 'health': health, 'energy': 10}).status_code == 204
    assert page.perform(gameno, number, {
        'kind': 'add_unit', 'type_name': f'T{number}', 'name': f'u{number}',
        'x': square[0], 'y': square[1]}).status_code == 204


# --- the flow

def test_a_whole_game_through_the_pages_own_calls(app, base_path):
    admin = _administrator(app)
    _set_up(admin)

    # the lobby lists it, with two open seats
    ada = _player(app, 'ada')
    listed = ada.list_games().get_json()['games']
    game = [entry for entry in listed if entry['gameno'] == GAME][0]
    assert game['state'] == registry.SETTING_UP
    assert game['open_seats'] == 2

    # two people take a seat each
    bob = _player(app, 'bob')
    assert ada.claim_seat(GAME, 1).status_code == 201
    assert bob.claim_seat(GAME, 2).status_code == 201

    # the lobby now shows who holds what, and each knows their own seat
    seats = [entry for entry in ada.list_games().get_json()['games']
             if entry['gameno'] == GAME][0]['seats']
    assert [seat['held_by'] for seat in seats] == ['ada', 'bob']
    assert {'gameno': GAME, 'number': 1} in ada.whoami().get_json()['seats']

    # each designs a type and deploys a unit
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (3, 3))

    # the armoury's numbers come from the players view
    mine = [player for player
            in ada.read_view(GAME, 1, 'players').get_json()['players']
            if player['player'] == 1][0]
    assert mine['budget'] == 100
    assert mine['spent'] == 19          # 1 + 8 + 10
    assert mine['left'] == 81

    # both commit; the turn resolves on the second
    first = ada.commit(GAME, 1)
    assert first.status_code == 202
    assert first.get_json()['waiting_on'] == [2]

    second = bob.commit(GAME, 2)
    assert second.status_code == 200
    assert second.get_json()['resolved'] is True
    assert second.get_json()['turn_number'] == 1

    # the wait endpoint the page polls says the turn is done
    waited = ada.wait_for_turn(GAME, 1).get_json()
    assert waited['resolved'] is True
    assert waited['turn_number'] == 1

    # and an order can be given for the next turn
    assert ada.perform(GAME, 1, {'kind': 'move', 'unit': 'u1',
                                 'direction': EAST}).status_code == 204
    ordered = [unit for unit
               in ada.read_view(GAME, 1, 'units').get_json()['units']
               if unit['name'] == 'u1'][0]
    assert ordered['direction'] == 'east'

    # the game is now being played, which the lobby says
    playing = [entry for entry in ada.list_games().get_json()['games']
               if entry['gameno'] == GAME][0]
    assert playing['state'] == registry.BEING_PLAYED
    assert playing['turn_number'] == 1


def test_each_seat_is_shown_only_what_it_may_see(app):
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (3, 3))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    for page, number, mine, theirs in ((ada, 1, 'u1', 'u2'),
                                       (bob, 2, 'u2', 'u1')):
        names = [unit['name'] for unit
                 in page.read_view(GAME, number, 'units').get_json()['units']]
        assert mine in names
        assert theirs not in names


def test_a_seat_cannot_read_another_seat(app):
    admin = _administrator(app)
    _set_up(admin)
    ada = _player(app, 'ada')
    ada.claim_seat(GAME, 1)

    assert ada.read_view(GAME, 2, 'units').status_code == 403
    assert ada.read_state(GAME, 2).status_code == 403


def test_uncommitted_orders_survive_the_page_being_closed(app):
    """The draft is the contract's, so the page needs no local storage."""
    admin = _administrator(app)
    _set_up(admin)
    ada = _player(app, 'ada')
    ada.claim_seat(GAME, 1)
    _deploy(ada, GAME, 1, 'X', (0, 0))

    # a second browser, signing in again as the same account
    reopened = Page(app)
    reopened.sign_in('ada', 'secret12')

    units = reopened.read_view(GAME, 1, 'units').get_json()['units']
    assert [unit['name'] for unit in units] == ['u1']


def test_a_game_played_partly_through_a_role_is_readable_by_the_page(
        app, base_path):
    """Neither client leaves the other in a state it cannot read."""
    from game_harness import GameHarness
    from board_game_concept.service import games as game_ops
    from board_game_concept.service.commands import AddType, AddUnit

    admin = _administrator(app)
    _set_up(admin, gameno='shared')

    ada = _player(app, 'ada')
    ada.claim_seat('shared', 1)
    _deploy(ada, 'shared', 1, 'X', (0, 0))

    # seat 2 is played by the service layer directly, as a role would
    harness = GameHarness(base_path, gameno='shared', backend=DEFAULT_BACKEND)
    session = harness.session(2)
    game_ops.perform(session, AddType(name='R', symbol='O', attack=1,
                                      health=8, energy=10))
    game_ops.perform(session, AddUnit(type_name='R', name='r2', x=3, y=3))
    session.clientSave()

    assert ada.commit('shared', 1).get_json()['resolved'] is True

    # the page reads the resolved game
    state = ada.read_state('shared', 1).get_json()
    assert state['turn_number'] == 1
    assert [unit['name'] for unit
            in ada.read_view('shared', 1, 'units').get_json()['units']] == ['u1']


def test_what_the_last_turn_refused_is_readable(app):
    """`rejected` is where the page's "last turn" panel comes from."""
    admin = _administrator(app)
    _set_up(admin, size=(2, 2))
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (1, 1))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    # north off the top of the board: refused while it is applied
    ada.perform(GAME, 1, {'kind': 'move', 'unit': 'u1', 'direction': NORTH})
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    state = ada.read_state(GAME, 1).get_json()
    assert isinstance(state['rejected'], list)
    assert any(entry['unit'] == 'u1' for entry in state['rejected'])
    assert all({'unit', 'x', 'y', 'reason'} <= set(entry)
               for entry in state['rejected'])


def test_the_observer_watches_through_the_same_calls(app):
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (3, 3))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    observer = Page(app)
    observer.sign_in('observer', 'observer')
    observer.change_password('observer', 'observer-secret')

    units = observer.read_view(GAME, 1000, 'units').get_json()['units']
    assert {unit['name'] for unit in units} == {'u1', 'u2'}


# --- the page and the contract agree about the words they use

def _static(name):
    with open(os.path.join(STATIC, name), encoding='utf-8') as file:
        return file.read()


def test_the_pages_directions_are_the_engines():
    """`api.js` names the four directions; the engine numbers them."""
    from board_game_concept.domain import UnitType

    source = _static('api.js')
    for word, value in (('north', UnitType.NORTH), ('east', UnitType.EAST),
                        ('south', UnitType.SOUTH), ('west', UnitType.WEST)):
        pattern = rf"word: '{word}', value: {value}\b"
        assert re.search(pattern, source), f'{word} should be {value}'


def test_the_pages_command_records_are_the_ones_the_service_reads():
    """Every `kind` the page builds is a command the service can rebuild."""
    from board_game_concept.service.commands import command_type

    for kind in re.findall(r"kind: '(\w+)'", _static('api.js')):
        assert command_type(kind) is not None, kind


def test_the_page_asks_only_for_views_that_exist():
    """A subject the page names has to be one `VIEW_BUILDERS` offers."""
    from board_game_concept.http.app import VIEW_BUILDERS

    for subject in re.findall(r"readView\([^,]+,[^,]+, '(\w+)'\)",
                              _static('app.js') + _static('play.js')
                              + _static('armoury.js')):
        assert subject in VIEW_BUILDERS, subject
