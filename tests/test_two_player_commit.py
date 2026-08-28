"""Two players set up a game and commit one after the other.

The first game anybody plays with a friend: the administrator sizes a board and
registers two players, each player designs a unit type and deploys a unit, and
then they commit in turn. Nobody has moved and nobody has fought, so the second
commit resolves the setup turn and the game is still there to be played.

It was not, over HTTP. The commit endpoint resolved the turn from a session
opened as the committing player, and a player's session is built from that
player's own published view: it loads no other player's orders and holds no
other player's units. Resolving from one applied a single player's orders and
then republished that half-sighted board as the record of the game - so every
other player was wiped off it, found to have nothing standing, and eliminated.
Whoever committed last won on turn 1, before a single order had been given.

The game is played twice here, once against the service layer that `bgcserver`
and `bgcclient` drive and once over the HTTP endpoint, because a game is one
game whichever transport it is played over. The service layer was right all
along, and saying so here is what makes this file evidence about the defect
rather than about the fix.
"""

from board_game_concept import Game
from board_game_concept.http.app import create_app

from game_harness import DEFAULT_BACKEND, GameHarness, make_repository

# what each player designs and deploys: a unit each, at opposite corners of a
# board too big for them to reach each other on the turn they are deployed
CROSS = {'kind': 'add_type', 'name': 'Cross', 'symbol': 'X',
         'attack': 1, 'health': 5, 'energy': 10}
NOUGHT = {'kind': 'add_type', 'name': 'Nought', 'symbol': 'O',
          'attack': 1, 'health': 5, 'energy': 10}
X1 = {'kind': 'add_unit', 'type_name': 'Cross', 'name': 'x1', 'x': 0, 'y': 0}
O1 = {'kind': 'add_unit', 'type_name': 'Nought', 'name': 'o1', 'x': 5, 'y': 5}
# a setup is refused unless a unit carries the flag, and each side has one
X_FLAG = {'kind': 'set_flag', 'unit': 'x1'}
O_FLAG = {'kind': 'set_flag', 'unit': 'o1'}

GAME = 'duel'


class Web:
    """The API server for one game, driven the way a client drives it."""

    def __init__(self, base_path):
        self.base_path = str(base_path)
        # whichever backend this run is for: the scenario is not about
        # storage, and pinning it to one would leave the other untested
        from conftest import authorising_client
        self.client = authorising_client(
            create_app(base_path=self.base_path, backend=DEFAULT_BACKEND))

    def perform(self, number, record):
        response = self.client.post(
            f'/games/{GAME}/players/{number}/commands', json=record)
        assert response.status_code == 204, response.get_json()

    def commit(self, number):
        return self.client.post(f'/games/{GAME}/players/{number}/commit')

    def view(self, number, subject):
        response = self.client.get(
            f'/games/{GAME}/players/{number}/views/{subject}')
        assert response.status_code == 200, response.get_json()
        return response.get_json()[subject]

    def game(self):
        """The game as the administrator reads it: the record itself."""
        game = Game(make_repository(DEFAULT_BACKEND, GAME, self.base_path), 0)
        game.load()
        return game


def set_up(base_path):
    """A board, two players, and a unit each, with nobody committed yet."""
    web = Web(base_path)
    web.perform(0, {'kind': 'set_board', 'size_x': 6, 'size_y': 6})
    web.perform(0, {'kind': 'add_player', 'number': 1})
    web.perform(0, {'kind': 'add_player', 'number': 2})
    assert web.commit(0).status_code == 200

    web.perform(1, CROSS)
    web.perform(1, X1)
    web.perform(1, X_FLAG)
    web.perform(2, NOUGHT)
    web.perform(2, O1)
    web.perform(2, O_FLAG)
    return web


def standing(game):
    """Whose units are on the board, by name and owner."""
    return {(unit.name, unit.player.number) for unit in game.getBoard().units
            if unit.on_board and not unit.destroyed}


# --- the scenario, over HTTP


def test_the_first_commit_waits_and_the_second_resolves(tmp_path):
    web = set_up(tmp_path)

    first = web.commit(1)
    assert first.status_code == 202, first.get_json()
    assert first.get_json()['resolved'] is False
    assert first.get_json()['waiting_on'] == [2]

    second = web.commit(2)
    assert second.status_code == 200, second.get_json()
    assert second.get_json()['resolved'] is True
    assert second.get_json()['turn_number'] == 1


def test_committing_second_does_not_win_the_game(tmp_path):
    """The defect, said as plainly as it can be said."""
    web = set_up(tmp_path)
    web.commit(1)
    web.commit(2)

    assert web.game().getOutcome() is None
    assert web.commit(2).get_json()['outcome'] is None


def test_neither_player_is_eliminated_by_the_other_committing(tmp_path):
    web = set_up(tmp_path)
    web.commit(1)
    web.commit(2)

    assert web.game().getEliminated() == []


def test_both_players_units_are_on_the_board(tmp_path):
    """A turn resolved by one player used to publish only that player's half."""
    web = set_up(tmp_path)
    web.commit(1)
    web.commit(2)

    assert standing(web.game()) == {('x1', 1), ('o1', 2)}


def test_each_player_is_still_shown_their_own_unit(tmp_path):
    """What the players themselves are told, which is how they would find out."""
    web = set_up(tmp_path)
    web.commit(1)
    web.commit(2)

    for number, name in ((1, 'x1'), (2, 'o1')):
        units = web.view(number, 'units')
        assert [unit['name'] for unit in units] == [name], units

    for number in (1, 2):
        players = web.view(number, 'players')
        assert all(entry['status'] == 'active' for entry in players), players


def test_the_game_goes_on_to_a_second_turn(tmp_path):
    """Not decided, and not stuck either: the next turn resolves the same way."""
    web = set_up(tmp_path)
    web.commit(1)
    web.commit(2)

    assert web.commit(1).status_code == 202
    resolved = web.commit(2)
    assert resolved.status_code == 200, resolved.get_json()
    assert resolved.get_json()['turn_number'] == 2
    assert web.game().getOutcome() is None
    assert standing(web.game()) == {('x1', 1), ('o1', 2)}


# --- and the same game against the service layer, which is what the file
# transport and the command line roles drive


def test_the_same_game_played_locally_is_undecided(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(6, 6, [1, 2])
    harness.deploy(1, [('Cross', 'X', 1, 5, 10)], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [('Nought', 'O', 1, 5, 10)], [('Nought', 'o1', 5, 5)])
    harness.resolve()

    server = harness.session(0)
    assert server.getOutcome() is None
    assert server.getEliminated() == []
    assert standing(server) == {('x1', 1), ('o1', 2)}


    def test_this_surface_is_guarded(self):
        """The requests above authorise themselves; this proves they had to."""
        raw = self.client.raw
        for method, path in (
                ('post', f'/games/{GAME}/players/1/commands'),
                ('post', f'/games/{GAME}/players/1/commit'),
                ('get', f'/games/{GAME}/players/1/state'),
        ):
            response = getattr(raw, method)(path)
            self.assertEqual(response.status_code, 401, path)
