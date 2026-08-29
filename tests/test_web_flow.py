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

    def read_events(self, gameno, number):
        return self.read_view(gameno, number, 'events')

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


def _deploy(page, gameno, number, symbol, square, health=8, energy=10,
            flag=True):
    assert page.perform(gameno, number, {
        'kind': 'add_type', 'name': f'T{number}', 'symbol': symbol,
        'attack': 1, 'health': health, 'energy': energy}).status_code == 204
    assert page.perform(gameno, number, {
        'kind': 'add_unit', 'type_name': f'T{number}', 'name': f'u{number}',
        'x': square[0], 'y': square[1]}).status_code == 204
    # a setup is refused without a carrier, so the one unit deployed here
    # carries the flag unless a test is about not having one
    if flag:
        assert page.perform(gameno, number, {
            'kind': 'set_flag', 'unit': f'u{number}'}).status_code == 204


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


def test_a_committed_move_is_still_readable_from_the_pending_view(app):
    """What the board draws its committed arrows from, once the turn is locked.

    While a player is ordering, the order rides on the units view: the server
    replays their draft, so a unit ordered east reads back `direction: east`
    and the board draws an arrow. Committing publishes the draft and clears
    it, and the units view is the resolved board of last turn - so it carries
    no unresolved order, and the arrows would vanish. The committed orders are
    in the pending view, which is where the board reads them back to keep
    drawing them.
    """
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (3, 3))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)                       # the first turn resolves

    # a second turn: ada orders u1 east. Before committing, the order is on
    # the units view, which is what draws the arrow in flight
    assert ada.perform(GAME, 1, {'kind': 'move', 'unit': 'u1',
                                 'direction': EAST}).status_code == 204
    before = [unit for unit
              in ada.read_view(GAME, 1, 'units').get_json()['units']
              if unit['name'] == 'u1'][0]
    assert before['direction'] == 'east'

    # ada commits; bob has not, so the turn is committed and unresolved
    assert ada.commit(GAME, 1).status_code == 202

    # the units view has let the order go - it is the resolved board, and the
    # move has not resolved - so the arrow would vanish from a board drawn
    # from it alone
    after = [unit for unit
             in ada.read_view(GAME, 1, 'units').get_json()['units']
             if unit['name'] == 'u1'][0]
    assert after['direction'] is None

    # but the pending view still carries the committed move, from the square
    # the unit still stands on: this is what the board draws the arrow from
    pending = ada.read_view(GAME, 1, 'pending').get_json()['pending']
    mine = [entry for entry in pending if entry['unit'] == 'u1'][0]
    assert mine['order'] == 'move east'
    assert (mine['x'], mine['y']) == (0, 0)


def test_a_seat_reads_where_it_may_deploy(app):
    """The area the browser greys the rest of the board from.

    Published per seat so a client can show the limit without knowing the
    rule, and read from the same helper that refuses a deployment, so what a
    seat is shown and what it will be allowed cannot come apart.
    """
    admin = _administrator(app)
    _set_up(admin, size=(4, 5))          # five rows, so there is a neutral one
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)

    mine = ada.read_view(GAME, 1, 'placement').get_json()['placement']
    assert mine == {'size_x': 4, 'size_y': 5, 'rows': [0, 1],
                    'neutral_row': 2, 'restricted': True}
    theirs = bob.read_view(GAME, 2, 'placement').get_json()['placement']
    assert theirs['rows'] == [3, 4], 'the halves do not overlap'
    assert theirs['restricted'] is True

    # and what it says is what the server enforces
    assert ada.perform(GAME, 1, {
        'kind': 'add_type', 'name': 'T1', 'symbol': 'X',
        'attack': 1, 'health': 4, 'energy': 10}).status_code == 204
    allowed = ada.perform(GAME, 1, {'kind': 'add_unit', 'type_name': 'T1',
                                    'name': 'a1', 'x': 0, 'y': 1})
    assert allowed.status_code == 204
    refused = ada.perform(GAME, 1, {'kind': 'add_unit', 'type_name': 'T1',
                                    'name': 'a2', 'x': 0, 'y': 2})
    assert refused.status_code == 400
    assert 'neutral' in refused.get_json()['error']


def test_a_game_that_is_not_two_player_reads_the_whole_board(app):
    """The null case, over the contract: nothing greyed, nothing refused."""
    admin = _administrator(app)
    _set_up(admin, seats=(1, 2, 3), size=(4, 5))
    ada = _player(app, 'ada')
    ada.claim_seat(GAME, 1)

    area = ada.read_view(GAME, 1, 'placement').get_json()['placement']
    assert area['rows'] == [0, 1, 2, 3, 4]
    assert area['restricted'] is False
    assert area['neutral_row'] is None


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
    from board_game_concept.service.commands import (AddType, AddUnit,
                                                     SetFlag)

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
    game_ops.perform(session, SetFlag(unit='r2'))
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


def test_what_the_last_turn_did_is_readable(app):
    """The feed is where the page's account of the turn comes from.

    Two units on a 2x2 board, one ordered into the other: the page has to be
    able to say who struck whom, for how much, and on which square - none of
    which it could say before, so a player watched their units lose health
    for reasons the server knew and never mentioned.
    """
    admin = _administrator(app)
    _set_up(admin, size=(2, 2))
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (0, 1))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    ada.perform(GAME, 1, {'kind': 'move', 'unit': 'u1', 'direction': SOUTH})
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    answer = ada.read_events(GAME, 1)
    assert answer.status_code == 200
    events = answer.get_json()['events']

    attacks = [entry for entry in events if entry['kind'] == 'attacked']
    assert attacks, 'the page was told nothing about the fight'
    for attack in attacks:
        assert {'unit', 'target', 'damage'} <= set(attack['detail'])
        assert (attack['detail']['x'], attack['detail']['y']) == (0, 1)
        assert attack['text']
        assert attack['fighting'] is True
    assert {entry['turn'] for entry in events} <= {1, 2}


def test_a_seat_is_told_only_what_it_could_see(app):
    """Two players out of contact are told about their own deployment only."""
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (3, 3))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    events = ada.read_events(GAME, 1).get_json()['events']
    named = {entry['detail'].get('unit') for entry in events}
    assert 'u1' in named
    assert 'u2' not in named


def test_a_seat_cannot_read_another_seats_feed(app):
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)

    assert ada.read_events(GAME, 2).status_code == 403


def test_the_observer_reads_the_whole_log(app):
    """It sees every unit of every player, so it is told about every one."""
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

    events = observer.read_events(GAME, 1000).get_json()['events']
    deployed = {entry['detail']['unit'] for entry in events
                if entry['kind'] == 'deployed'}
    assert deployed == {'u1', 'u2'}


def test_designating_a_carrier_through_the_contract(app):
    """`set_flag` is a command like any other, sent the way they all are."""
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0), flag=False)

    assert ada.perform(GAME, 1, {'kind': 'set_flag',
                                 'unit': 'u1'}).status_code == 204

    mine = [unit for unit
            in ada.read_view(GAME, 1, 'units').get_json()['units']
            if unit['name'] == 'u1'][0]
    assert mine['flag'] is True


def test_a_setup_with_no_carrier_is_refused(app):
    """The rule the whole feature rests on, at the contract."""
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0), flag=False)

    refused = ada.commit(GAME, 1)

    assert refused.status_code == 400
    assert 'flag' in refused.get_json()['error']
    assert ada.read_view(GAME, 1, 'pending').get_json()['pending'] == [], (
        'a refused commit published an army')


def test_a_flag_is_read_by_a_seat_that_has_met_nobody(app):
    """The one thing shown without contact: the square, and whose it is."""
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (3, 3))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    flags = ada.read_view(GAME, 1, 'flags').get_json()['flags']

    assert [flag['player'] for flag in flags] == [1, 2]
    theirs = [flag for flag in flags if flag['player'] == 2][0]
    assert (theirs['x'], theirs['y']) == (3, 3)
    assert theirs['standing'] is True

    # and the unit standing there is still nobody they have met
    seen = {unit['name'] for unit
            in ada.read_view(GAME, 1, 'units').get_json()['units']}
    assert seen == {'u1'}


def test_a_flag_says_nothing_about_the_unit_carrying_it(app):
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (3, 3))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    flags = ada.read_view(GAME, 1, 'flags').get_json()['flags']

    for flag in flags:
        assert set(flag) == {'player', 'x', 'y', 'standing'}


def test_a_fallen_flag_is_on_no_square(app):
    admin = _administrator(app)
    _set_up(admin, size=(2, 2))
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0), health=8, energy=20)
    _deploy(bob, GAME, 2, 'O', (0, 1), health=1, energy=3)
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    ada.perform(GAME, 1, {'kind': 'move', 'unit': 'u1', 'direction': SOUTH})
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    flags = ada.read_view(GAME, 1, 'flags').get_json()['flags']
    theirs = [flag for flag in flags if flag['player'] == 2][0]
    assert theirs['standing'] is False
    assert (theirs['x'], theirs['y']) == (None, None)

    # and losing it ended the game
    assert ada.read_state(GAME, 1).get_json()['outcome']['winner'] == 1


def test_a_committed_setup_is_readable_before_the_first_turn(app):
    """What a player has committed, in the gap before the turn resolves.

    Committing a setup publishes the army as orders. Until the first turn
    resolves it is on no board anywhere, so the units view is empty - and the
    interface drew an empty board, the lobby sent the player back to the
    armoury because the game was still "setting up", and the armoury refused
    every command with "can't add units after first turn" for a turn that had
    not happened. Three screens, one missing fact: this is that fact.
    """
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    assert ada.commit(GAME, 1).status_code == 202

    # the army is not on any board yet
    assert ada.read_view(GAME, 1, 'units').get_json()['units'] == []

    # and it is here, with enough of the unit to draw it
    pending = ada.read_view(GAME, 1, 'pending').get_json()['pending']
    assert [entry['unit'] for entry in pending] == ['u1']
    assert pending[0]['order'] == 'deploy'
    assert (pending[0]['x'], pending[0]['y']) == (0, 0)
    assert pending[0]['symbol'] == 'X'
    assert pending[0]['type'] == 'T1'
    assert pending[0]['health'] == 8


def test_a_first_turn_that_refuses_every_deployment_is_shown_as_decided(app):
    """The state a browser was left in with nothing left to do.

    Seats deployed onto the same square, so their deployments were refused
    and the first turn put nothing on the board. The seat read an empty
    board, no outcome and a setup it could not add to: the interface had
    nothing true to draw, because the game had nothing true to say.

    Three seats, because two cannot ask for one square any more: each of two
    players is given their own half of the board by `placement-zones`.
    """
    admin = _administrator(app)
    _set_up(admin, seats=(1, 2, 3))
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    cass = _player(app, 'cass')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    cass.claim_seat(GAME, 3)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (0, 0))
    _deploy(cass, GAME, 3, 'S', (0, 0))
    assert ada.commit(GAME, 1).status_code == 202
    assert bob.commit(GAME, 2).status_code == 202
    assert cass.commit(GAME, 3).status_code == 200

    state = ada.read_state(GAME, 1).get_json()
    assert state['turn_number'] == 1
    assert state['outcome'] == {'decided': True, 'winner': None, 'turn': 1}
    assert ada.read_view(GAME, 1, 'units').get_json()['units'] == []
    # and the page's own reading of "you are out": a flag that is not
    # standing, for a carrier that never reached a square
    flags = ada.read_view(GAME, 1, 'flags').get_json()['flags']
    assert flags == [{'player': 1, 'x': None, 'y': None, 'standing': False},
                     {'player': 2, 'x': None, 'y': None, 'standing': False},
                     {'player': 3, 'x': None, 'y': None, 'standing': False}]
    # and the refusal says why there is nothing there
    assert 'deployed at (0, 0)' in state['rejected'][0]['reason']


def test_committing_a_setup_with_no_board_is_refused_and_says_so(app):
    """The answer used to be 200, and the game was not set up at all.

    An administrator who committed a game before sizing its board was told
    the setup was committed, went back to the lobby, and found the game still
    asking to be set up - because it was. `resolve` had refused and said so
    to the server's own output, which nobody reading a browser can see.
    """
    admin = _administrator(app)
    assert admin.create_game(GAME).status_code == 201
    admin.perform(GAME, 0, {'kind': 'add_player', 'number': 1, 'budget': 100})

    refused = admin.commit(GAME, 0)

    assert refused.status_code == 400
    assert 'board' in refused.get_json()['error']

    listed = [entry for entry in admin.list_games().get_json()['games']
              if entry['gameno'] == GAME][0]
    assert listed['size_x'] is None, 'a refused commit published a board'

    # and with a board it goes through
    admin.perform(GAME, 0, {'kind': 'set_board', 'size_x': 4, 'size_y': 4})
    assert admin.commit(GAME, 0).status_code == 200
    listed = [entry for entry in admin.list_games().get_json()['games']
              if entry['gameno'] == GAME][0]
    assert listed['size_x'] == 4


def test_the_lobby_says_whether_a_game_has_been_set_up(app):
    """The board is published by the setup commit and by nothing else.

    That is how the lobby tells a game with a setup still to do from one
    whose setup is committed - they are both "setting up" until a turn
    resolves, so it offered the administrator a setup screen for both, and
    every command that screen could send on a committed game is refused.
    """
    admin = _administrator(app)
    assert admin.create_game(GAME).status_code == 201

    def listed():
        return [entry for entry in admin.list_games().get_json()['games']
                if entry['gameno'] == GAME][0]

    assert listed()['size_x'] is None, 'a game nobody set up has no board'

    admin.perform(GAME, 0, {'kind': 'set_board', 'size_x': 4, 'size_y': 4})
    admin.perform(GAME, 0, {'kind': 'add_player', 'number': 1, 'budget': 100})
    assert listed()['size_x'] is None, (
        'a board that has not been committed is not published')

    admin.commit(GAME, 0)

    assert listed()['size_x'] == 4
    assert listed()['state'] == registry.SETTING_UP, (
        'the game is still being set up by its players')


def test_an_administrator_cannot_set_up_a_committed_game(app):
    """Which is why the lobby stops offering it - the screen is a dead end."""
    admin = _administrator(app)
    _set_up(admin)

    refused = admin.perform(GAME, 0, {'kind': 'set_board',
                                      'size_x': 6, 'size_y': 6})
    assert refused.status_code == 400
    also = admin.perform(GAME, 0, {'kind': 'add_player', 'number': 3})
    assert also.status_code == 400


def test_the_lobby_says_which_seats_have_committed(app):
    """So it can send a committed seat to the board rather than the armoury."""
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))

    def seats():
        listed = [entry for entry in ada.list_games().get_json()['games']
                  if entry['gameno'] == GAME][0]
        return {seat['number']: seat['committed'] for seat in listed['seats']}

    assert seats() == {1: False, 2: False}
    ada.commit(GAME, 1)
    assert seats() == {1: True, 2: False}, (
        'the lobby cannot tell a committed seat from one still deploying')


def test_deploying_after_committing_a_setup_says_what_is_true(app):
    """The refusal described a turn that had not happened.

    A player who has just committed is looking at a board with nothing of
    theirs on it, so "can't add units after first turn" reads as the game
    having lost their work rather than as setup being closed.
    """
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    ada.commit(GAME, 1)

    refused = ada.perform(GAME, 1, {
        'kind': 'add_unit', 'type_name': 'T1', 'name': 'u9', 'x': 2, 'y': 2})
    assert refused.status_code == 400
    said = refused.get_json()['error']
    assert 'committed' in said
    assert 'first turn' not in said, said

    # and once a turn really has been played, it says that instead
    _deploy(bob, GAME, 2, 'O', (3, 3))
    bob.commit(GAME, 2)
    later = ada.perform(GAME, 1, {
        'kind': 'add_unit', 'type_name': 'T1', 'name': 'u9', 'x': 2, 'y': 2})
    assert "can't add units after first turn" in later.get_json()['error']


def test_a_type_met_is_remembered_after_contact_is_lost(app):
    """What you have met outlives the sighting; where it is does not.

    `types` is what is in contact now, and drops an enemy the moment contact
    is lost - that is `visibility` working. A player who has fought a design
    and cannot say what it was built with is being asked to keep notes on
    paper, so what has been met is kept separately.
    """
    admin = _administrator(app)
    _set_up(admin, size=(4, 4))
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    # little energy each, so the contest ends undecided and both survive it -
    # a fight to the death would end the game and there would be no turn
    # afterwards in which contact could be lost
    _deploy(ada, GAME, 1, 'X', (0, 1), energy=3)
    _deploy(bob, GAME, 2, 'O', (0, 2), energy=3)
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    # nothing met yet: they were deployed out of contact
    assert ada.read_view(GAME, 1, 'designs').get_json()['designs'] == []

    # ada walks into bob, which is contact
    ada.perform(GAME, 1, {'kind': 'move', 'unit': 'u1', 'direction': SOUTH})
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    met = ada.read_view(GAME, 1, 'designs').get_json()['designs']
    assert [entry['name'] for entry in met] == ['T2']
    assert met[0]['player'] == 2
    assert met[0]['attack'] == 1 and met[0]['health'] == 8
    assert met[0]['first_seen'] == 2

    # a turn with no contact: the types view forgets, and this does not
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    types = ada.read_view(GAME, 1, 'types').get_json()['types']
    assert [entry['name'] for entry in types] == ['T1'], (
        'the types view is what is in contact now')
    still = ada.read_view(GAME, 1, 'designs').get_json()['designs']
    assert [entry['name'] for entry in still] == ['T2']


def test_a_type_never_met_is_not_remembered(app):
    admin = _administrator(app)
    _set_up(admin)
    ada, bob = _player(app, 'ada'), _player(app, 'bob')
    ada.claim_seat(GAME, 1)
    bob.claim_seat(GAME, 2)
    _deploy(ada, GAME, 1, 'X', (0, 0))
    _deploy(bob, GAME, 2, 'O', (3, 3))
    ada.commit(GAME, 1)
    bob.commit(GAME, 2)

    assert ada.read_view(GAME, 1, 'designs').get_json()['designs'] == []


def test_the_observer_is_given_every_type_as_met(app):
    """It has met everything by definition, and reads one shape for both."""
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

    met = observer.read_view(GAME, 1000, 'designs').get_json()['designs']
    assert {entry['name'] for entry in met} == {'T1', 'T2'}
    assert all({'attack', 'health', 'energy', 'cost'} <= set(entry)
               for entry in met)


def test_the_observer_can_read_every_units_statistics(app):
    """The watching screen has no orders tray, so this is where they are."""
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
    for unit in units:
        assert {'attack', 'health', 'energy'} <= set(unit)


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


def test_every_seat_endpoint_the_page_calls_exists(app):
    """`api.js` names paths; the app has to have them.

    The page can only reach the game through the served contract, so a path
    it builds and the server does not offer is a screen that half-loads -
    which is what a feed added to one side and not the other would be.
    """
    source = _static('api.js')
    called = set(re.findall(r'\$\{seatPath\(gameno, number\)\}/([\w/]+)',
                            source))
    offered = {str(rule) for rule in app.url_map.iter_rules()}
    seat = '/games/<gameno>/players/<int:number>/'
    for path in called:
        # what the page fills in - a view's subject, a wait's budget - stops
        # the comparison being a string match, so it is the literal part of
        # the path that has to name a route
        literal = path.rstrip('/')
        assert any(route == seat + literal
                   or route.startswith(seat + literal + '/')
                   for route in offered), (
            f'api.js calls {path} and no route serves it')


def test_every_view_the_page_reads_is_readable_from_a_command_line():
    """One contract, and both clients can say everything it says.

    The interface is a client of the served contract, and so are the roles.
    A view the browser draws and no role can ask for is a thing you can only
    find out by opening a browser - which is how the browser stops being a
    client and starts being the product.
    """
    from board_game_concept.cli import roles
    from board_game_concept.http.app import VIEW_BUILDERS

    offered = set()
    for role in (roles.SERVER, roles.CLIENT, roles.OBSERVER):
        offered |= set(role.show_subjects)

    missing = sorted(set(VIEW_BUILDERS) - offered)
    assert not missing, (
        f'no command-line role can show {", ".join(missing)}')


def test_every_command_the_page_sends_can_be_typed():
    """Same rule for the commands: `api.js` builds them, the grammar takes them."""
    from board_game_concept.cli.grammar import USAGES

    source = _static('api.js')
    built = set(re.findall(r"kind: '(\w+)'", source))
    typed = {usage.kind for usage in USAGES}
    # `set_new_game` is the HTTP tier's own setter and has no line to type:
    # the local flow calls it directly rather than sending it
    missing = sorted(built - typed - {'set_new_game'})
    assert not missing, (
        f'the page sends {", ".join(missing)} and the grammar has no line '
        'for it')


def test_the_page_asks_only_for_views_that_exist():
    """A subject the page names has to be one `VIEW_BUILDERS` offers."""
    from board_game_concept.http.app import VIEW_BUILDERS

    for subject in re.findall(r"readView\([^,]+,[^,]+, '(\w+)'\)",
                              _static('app.js') + _static('play.js')
                              + _static('armoury.js')):
        assert subject in VIEW_BUILDERS, subject


# --- the lobby offers a seat by entitlement, not by kind

def _observer(app):
    page = Page(app)
    assert page.sign_in('observer', 'observer').status_code == 200
    assert page.change_password('observer',
                                'observer-secret').status_code == 200
    return page


def test_the_administrator_takes_a_seat_from_the_lobby(app):
    """Exactly the calls `lobby.js` makes to take a seat, as the admin."""
    admin = _administrator(app)
    _set_up(admin)

    listed = [entry for entry in admin.list_games().get_json()['games']
              if entry['gameno'] == GAME][0]
    assert listed['open_seats'] == 2

    assert admin.claim_seat(GAME, 1).status_code == 201

    seats = [entry for entry in admin.list_games().get_json()['games']
             if entry['gameno'] == GAME][0]['seats']
    assert [seat['held_by'] for seat in seats] == ['admin', None]
    assert {'gameno': GAME, 'number': 1} in admin.whoami().get_json()['seats']


def test_the_observer_is_offered_no_seat(app):
    admin = _administrator(app)
    _set_up(admin)
    observer = _observer(app)

    refused = observer.claim_seat(GAME, 1)

    # 403: it said who it is, and the answer is no
    assert refused.status_code == 403
    assert 'holds a seat in none' in refused.get_json()['error']
    seats = [entry for entry in admin.list_games().get_json()['games']
             if entry['gameno'] == GAME][0]['seats']
    assert [seat['held_by'] for seat in seats] == [None, None]


def test_the_lobby_offers_a_seat_to_exactly_who_the_server_would_let_take_one(
        app):
    """The button and the refusal cannot fall out of step.

    `lobby.js` asks one question - may this account hold a seat - and this
    asks the server the same question of each kind. A kind the page would
    offer the button to and the server would refuse is a dead button; a kind
    the server would accept and the page withholds from is a seat nobody can
    take.
    """
    source = _static('lobby.js')
    assert re.search(r'function mayHoldASeat\(account\) \{\s*'
                     r"return account\.kind !== 'observer';", source), (
        'lobby.js should decide by whether the account may hold a seat')
    assert 'mayHoldASeat(state.account)' in source

    admin = _administrator(app)
    _set_up(admin, gameno='w', seats=(1, 2, 3))
    would_offer = {'admin': True, 'player': True, 'observer': False}
    pages = {'admin': admin, 'player': _player(app, 'ada'),
             'observer': _observer(app)}

    # a free seat each, so a refusal is the account being refused and not the
    # seat already being held by the account tried before it
    for seat, (kind, page) in enumerate(pages.items(), start=1):
        accepted = page.claim_seat('w', seat)
        assert (accepted.status_code == 201) is would_offer[kind], (
            f'{kind}: the page offers the button to {would_offer[kind]} and '
            f'the server answered {accepted.status_code}')


def test_the_administrators_own_ways_in_are_offered_beside_its_seat(app):
    """Playing a seat and administering the game are both reachable."""
    admin = _administrator(app)
    _set_up(admin)
    assert admin.claim_seat(GAME, 1).status_code == 201

    entry = [game for game in admin.list_games().get_json()['games']
             if game['gameno'] == GAME][0]
    held = [seat['number'] for seat in entry['seats']
            if seat['held_by'] == 'admin']
    assert held == [1]

    # the seat's own screens answer, and so do the administrator's
    assert admin.read_state(GAME, 1).status_code == 200
    assert admin.read_view(GAME, 0, 'board').status_code == 200
    assert admin.read_view(GAME, 1000, 'board').status_code == 200

    # and the lobby draws the administrator's ways in for an admin account
    source = _static('lobby.js')
    assert "link('Watch'" in source
    assert "link('Set this game up'" in source
