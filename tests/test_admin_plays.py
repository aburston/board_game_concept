"""The administrator's seat is an ordinary seat, held to at the contract.

`identity-and-accounts` says the kind of the account holding a seat is not
consulted when the system decides what that seat sees, spends, may command, is
refused, or whether the turn waits for it. That is a statement about two games
rather than about one, so this sets up two: the same game twice, with seat 1
held by a registered player in one and by the administrator in the other.

The equivalence is tested by comparing whole views rather than by asserting
what is in them. Asserting tests what the assertions happen to mention; the
comparison tests everything a view holds, including fields added later, and
fails the day one starts carrying the holder's kind into a seat's answer.

Deliberately not pinned to a backend: nothing here knows how a game is stored.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from conftest import make_admin, make_player, token_for   # noqa: E402
from game_harness import DEFAULT_BACKEND                  # noqa: E402
from board_game_concept.http.app import create_app        # noqa: E402

# every view a seat may read, which is what "the same view" has to range over
SUBJECTS = ('board', 'types', 'units', 'players', 'pending', 'events',
            'designs', 'flags')

EAST, SOUTH, WEST = 2, 3, 4

BUDGET = 100


@pytest.fixture(name='app')
def _app(tmp_path):
    return create_app(base_path=str(tmp_path), backend=DEFAULT_BACKEND)


class Seat:
    """One account acting as one number of one game.

    Holds a bearer token rather than a cookie, so a test can hold several at
    once without a session getting in the way of another.
    """

    def __init__(self, app, account, gameno, number):
        self.client = app.test_client()
        self.account = account
        self.gameno = gameno
        self.number = number
        self.headers = {'Authorization': f'Bearer {token_for(app, account)}'}

    def _path(self, tail=''):
        return f'/games/{self.gameno}/players/{self.number}{tail}'

    def claim(self):
        return self.client.post(f'/games/{self.gameno}/seats/{self.number}',
                                headers=self.headers)

    def perform(self, command):
        return self.client.post(self._path('/commands'), json=command,
                                headers=self.headers)

    def commit(self):
        return self.client.post(self._path('/commit'), headers=self.headers)

    def state(self):
        return self.client.get(self._path('/state'), headers=self.headers)

    def view(self, subject):
        return self.client.get(self._path(f'/views/{subject}'),
                               headers=self.headers)

    def whoami(self):
        return self.client.get('/accounts/current', headers=self.headers)

    def create_game(self):
        return self.client.post('/games', json={'gameno': self.gameno},
                                headers=self.headers)


def _administrator(app, gameno, number):
    return Seat(app, make_admin(app), gameno, number)


def _player(app, username, gameno, number):
    return Seat(app, make_player(app, username), gameno, number)


def _set_up(admin, size=(4, 4), seats=(1, 2)):
    """Size the board and register the seats, as the administrator does."""
    assert admin.create_game().status_code == 201
    assert admin.perform({'kind': 'set_board', 'size_x': size[0],
                          'size_y': size[1]}).status_code == 204
    for number in seats:
        assert admin.perform({'kind': 'add_player', 'number': number,
                              'budget': BUDGET}).status_code == 204
    assert admin.commit().status_code == 200


def _deploy(seat, symbol, square, health=8, energy=10):
    """One type, one unit carrying the flag - a setup that may be committed."""
    name = f'T{seat.number}'
    assert seat.perform({'kind': 'add_type', 'name': name, 'symbol': symbol,
                         'attack': 1, 'health': health,
                         'energy': energy}).status_code == 204
    assert seat.perform({'kind': 'add_unit', 'type_name': name,
                         'name': f'u{seat.number}', 'x': square[0],
                         'y': square[1]}).status_code == 204
    assert seat.perform({'kind': 'set_flag',
                         'unit': f'u{seat.number}'}).status_code == 204


class Pair:
    """The same game twice, differing only in who holds seat 1.

    `player` is the game whose seat 1 a registered account holds; `admin` is
    the game whose seat 1 the administrator holds. Everything else about the
    two is arranged to be identical, because the comparison means nothing
    otherwise.
    """

    def __init__(self, app):
        self.app = app
        self.admin_of_player_game = _administrator(app, 'held-by-player', 0)
        self.admin_of_admin_game = _administrator(app, 'held-by-admin', 0)
        _set_up(self.admin_of_player_game)
        _set_up(self.admin_of_admin_game)

        self.player_seat = _player(app, 'ada', 'held-by-player', 1)
        self.admin_seat = _administrator(app, 'held-by-admin', 1)
        self.player_foe = _player(app, 'bob', 'held-by-player', 2)
        self.admin_foe = _player(app, 'cat', 'held-by-admin', 2)

    def seats(self):
        """The two seats being compared, player's first."""
        return (self.player_seat, self.admin_seat)

    def foes(self):
        return (self.player_foe, self.admin_foe)


@pytest.fixture(name='pair')
def _pair(app):
    return Pair(app)


def _in_both(seats, action):
    """Do the same thing in both games and return what each answered."""
    return tuple(action(seat) for seat in seats)


# --- 2.1 the two games are set up alike, and both seats are claimed

def test_both_seats_are_claimed_and_the_games_match(pair):
    for seat in pair.seats() + pair.foes():
        assert seat.claim().status_code == 201, seat.gameno

    assert (pair.admin_seat.whoami().get_json()['seats']
            == [{'gameno': 'held-by-admin', 'number': 1}])

    listed = {}
    for seat in pair.seats():
        games = seat.client.get('/games', headers=seat.headers).get_json()
        entry = [g for g in games['games'] if g['gameno'] == seat.gameno][0]
        listed[seat.gameno] = (entry['state'], entry['open_seats'],
                               [s['number'] for s in entry['seats']])
    assert (listed['held-by-player'][0] == listed['held-by-admin'][0])
    assert (listed['held-by-player'][1] == listed['held-by-admin'][1] == 0)
    assert (listed['held-by-player'][2] == listed['held-by-admin'][2])


# --- 2.2 and 2.3 the same calls, and then the same views

def _claim_and_play(pair):
    """Drive both games through the same calls in the same order."""
    for seat in pair.seats() + pair.foes():
        assert seat.claim().status_code == 201

    for seat in pair.seats():
        _deploy(seat, 'X', (0, 0))
    for foe in pair.foes():
        _deploy(foe, 'O', (3, 3))

    first = _in_both(pair.seats(), lambda s: s.commit())
    assert [r.status_code for r in first] == [202, 202]
    second = _in_both(pair.foes(), lambda s: s.commit())
    assert [r.status_code for r in second] == [200, 200]

    moved = _in_both(pair.seats(),
                     lambda s: s.perform({'kind': 'move', 'unit': 'u1',
                                          'direction': EAST}))
    assert [r.status_code for r in moved] == [204, 204]
    turn_one = _in_both(pair.seats(), lambda s: s.commit())
    assert [r.status_code for r in turn_one] == [202, 202]
    turn_two = _in_both(pair.foes(), lambda s: s.commit())
    assert [r.status_code for r in turn_two] == [200, 200]
    assert (turn_two[0].get_json()['turn_number']
            == turn_two[1].get_json()['turn_number'] == 2)


def test_the_same_calls_answer_the_same_way_in_both_games(pair):
    _claim_and_play(pair)


def test_every_view_of_the_seat_is_the_same_whoever_holds_it(pair):
    """The requirement itself: the two seats are answered identically."""
    _claim_and_play(pair)

    differed = []
    for subject in SUBJECTS + ('state',):
        held_by_player, held_by_admin = _in_both(
            pair.seats(),
            lambda s, w=subject: (s.state() if w == 'state' else s.view(w)))
        assert held_by_player.status_code == held_by_admin.status_code, subject
        if held_by_player.get_json() != held_by_admin.get_json():
            differed.append((subject, held_by_player.get_json(),
                             held_by_admin.get_json()))

    assert not differed, '\n'.join(
        f'{subject}:\n  held by a player: {player}\n'
        f'  held by the administrator: {admin}'
        for subject, player, admin in differed)


# --- 2.4 the seat is blinkered, and it is the seat that blinkers it

def test_the_administrators_seat_does_not_see_the_whole_board(pair):
    _claim_and_play(pair)

    seat_units = pair.admin_seat.view('units').get_json()['units']
    assert [unit['name'] for unit in seat_units] == ['u1']
    seat_board = pair.admin_seat.view('board').get_json()['board']
    assert 'O' not in [square for row in seat_board['rows'] for square in row]

    # ... and it is the seat that hides it, not the account: the same account
    # asked as player 0 of the same game is shown what the seat is not
    whole = pair.admin_of_admin_game.view('units').get_json()['units']
    assert sorted(unit['name'] for unit in whole) == ['u1', 'u2']


# --- 2.5 the barrier waits for it

def test_the_turn_waits_for_a_seat_the_administrator_holds(pair):
    for seat in pair.seats() + pair.foes():
        assert seat.claim().status_code == 201
    for seat in pair.seats():
        _deploy(seat, 'X', (0, 0))
    for foe in pair.foes():
        _deploy(foe, 'O', (3, 3))

    alone = pair.admin_seat.commit()

    assert alone.status_code == 202
    body = alone.get_json()
    assert body['resolved'] is False
    assert body['turn_number'] == 0
    assert body['waiting_on'] == [2]

    # and it resolves only once the other seat has committed
    assert pair.admin_foe.commit().get_json()['resolved'] is True


# --- 2.6 a refusal is the ordinary refusal

def test_a_refusal_is_the_one_a_player_would_be_given(pair):
    for seat in pair.seats() + pair.foes():
        assert seat.claim().status_code == 201

    # a design nobody could afford
    over_budget = _in_both(
        pair.seats(),
        lambda s: s.perform({'kind': 'add_type', 'name': 'Vast', 'symbol': 'V',
                             'attack': 50, 'health': 50, 'energy': 50}))
    dear = _in_both(
        pair.seats(),
        lambda s: s.perform({'kind': 'add_unit', 'type_name': 'Vast',
                             'name': 'costly', 'x': 1, 'y': 1}))
    assert over_budget[0].status_code == over_budget[1].status_code
    assert dear[0].status_code == dear[1].status_code
    assert dear[0].status_code == 400
    assert dear[0].get_json() == dear[1].get_json()

    # an order for a unit that is not this seat's
    for seat in pair.seats():
        _deploy(seat, 'X', (0, 0))
    for foe in pair.foes():
        _deploy(foe, 'O', (3, 3))
    for seat in pair.seats() + pair.foes():
        seat.commit()

    trespass = _in_both(
        pair.seats(),
        lambda s: s.perform({'kind': 'move', 'unit': 'u2',
                             'direction': WEST}))
    assert trespass[0].status_code == trespass[1].status_code
    assert trespass[0].status_code == 400
    assert trespass[0].get_json() == trespass[1].get_json()


# --- 2.7 administering a game it plays in

def test_administering_a_game_it_holds_a_seat_in(pair):
    _claim_and_play(pair)

    before = {subject: pair.admin_seat.view(subject).get_json()
              for subject in SUBJECTS}

    as_zero = pair.admin_of_admin_game.view('board')
    assert as_zero.status_code == 200

    after = {subject: pair.admin_seat.view(subject).get_json()
             for subject in SUBJECTS}
    assert before == after


# --- one account playing a whole game
#
# The interesting part is not that the claims are accepted; it is that the
# commit barrier does not collapse when one account commits every side. So
# these play a real game rather than asserting on memberships.

SOLO = 'solo'


def _solo_game(app, seats=(1, 2), size=(4, 4)):
    """The administrator, holding every seat of a game it set up itself."""
    admin = _administrator(app, SOLO, 0)
    _set_up(admin, size=size, seats=seats)
    held = {}
    for number in seats:
        seat = _administrator(app, SOLO, number)
        assert seat.claim().status_code == 201
        held[number] = seat
    return admin, held


def test_one_account_holds_every_seat_and_sets_each_one_up(app):
    _, held = _solo_game(app)

    assert (sorted(seat['number']
                   for seat in held[1].whoami().get_json()['seats'])
            == [1, 2])

    _deploy(held[1], 'X', (0, 0))
    _deploy(held[2], 'O', (3, 3))
    assert held[1].commit().status_code == 202
    assert held[2].commit().status_code == 200


def test_the_barrier_holds_within_one_account(app):
    _, held = _solo_game(app)
    _deploy(held[1], 'X', (0, 0))
    _deploy(held[2], 'O', (3, 3))

    setup_first = held[1].commit()
    assert setup_first.status_code == 202
    assert setup_first.get_json()['resolved'] is False
    assert setup_first.get_json()['waiting_on'] == [2]
    setup_last = held[2].commit()
    assert setup_last.status_code == 200
    assert setup_last.get_json()['resolved'] is True
    assert setup_last.get_json()['turn_number'] == 1

    # and again for a turn of play, so it is the barrier being tested rather
    # than the one-off that ends setup
    assert held[1].perform({'kind': 'move', 'unit': 'u1',
                            'direction': EAST}).status_code == 204
    turn_first = held[1].commit()
    assert turn_first.status_code == 202
    assert turn_first.get_json()['resolved'] is False
    assert turn_first.get_json()['waiting_on'] == [2]
    turn_last = held[2].commit()
    assert turn_last.status_code == 200
    assert turn_last.get_json()['resolved'] is True
    assert turn_last.get_json()['turn_number'] == 2


def test_one_account_plays_a_game_to_an_outcome(app):
    """Set up, driven together, and decided - with nobody else at the table."""
    _, held = _solo_game(app)
    # adjacent, and alike in everything a move costs, so what decides the
    # fight is the attack and not one of them running out of energy first
    assert held[1].perform({'kind': 'add_type', 'name': 'T1', 'symbol': 'X',
                            'attack': 5, 'health': 5,
                            'energy': 20}).status_code == 204
    assert held[1].perform({'kind': 'add_unit', 'type_name': 'T1',
                            'name': 'u1', 'x': 0, 'y': 0}).status_code == 204
    assert held[1].perform({'kind': 'set_flag',
                            'unit': 'u1'}).status_code == 204
    assert held[2].perform({'kind': 'add_type', 'name': 'T2', 'symbol': 'O',
                            'attack': 1, 'health': 5,
                            'energy': 20}).status_code == 204
    # row 2 is seat 2's: a two-player board is halved by rows, so the two
    # face each other down a column rather than along a row
    assert held[2].perform({'kind': 'add_unit', 'type_name': 'T2',
                            'name': 'u2', 'x': 0, 'y': 2}).status_code == 204
    assert held[2].perform({'kind': 'set_flag',
                            'unit': 'u2'}).status_code == 204
    assert held[1].commit().status_code == 202
    assert held[2].commit().status_code == 200

    # seat 1 walks onto seat 2's square; seat 2 stands its ground
    outcome = None
    for _ in range(10):
        held[1].perform({'kind': 'move', 'unit': 'u1', 'direction': SOUTH})
        held[1].commit()
        last = held[2].commit()
        outcome = last.get_json().get('outcome')
        if outcome:
            break

    assert outcome, 'one account playing every seat never reached an outcome'
    assert outcome['decided'] is True
    assert outcome['winner'] == 1


def test_two_seats_of_one_account_stay_two_identities(app):
    """One account, two seats, two drafts - and one commit moves only one."""
    _, held = _solo_game(app)
    _deploy(held[1], 'X', (0, 0))
    _deploy(held[2], 'O', (3, 3))
    held[1].commit()
    held[2].commit()

    assert held[1].perform({'kind': 'move', 'unit': 'u1',
                            'direction': EAST}).status_code == 204
    # committing seat 1 publishes seat 1's order and nothing of seat 2's, and
    # the turn is still held open for seat 2
    held_open = held[1].commit()
    assert held_open.status_code == 202
    assert held_open.get_json()['waiting_on'] == [2]

    ordered = held[1].view('pending').get_json()['pending']
    assert [entry['unit'] for entry in ordered] == ['u1']
    assert held[2].view('pending').get_json()['pending'] == []
