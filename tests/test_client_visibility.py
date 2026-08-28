"""A player's session is given only what that player may see.

The client used to load the record of every unit on the board and hide the
parts its player was not entitled to when it drew them, so every enemy position
was in its memory and readable on its disk. It now loads its own published view
and nothing else.
"""

from board_game_concept.cli.views import types_view
from board_game_concept.domain import Player, UnitType

from game_harness import GameHarness


def apart(tmp_path):
    """Two players who have not met."""
    harness = GameHarness(tmp_path)
    harness.create(4, 3, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('Sneaky', 'X', 9, 9, 90)], [('Sneaky', 'x1', 0, 0)])
    harness.deploy(2, [('Brute', 'O', 2, 2, 20)], [('Brute', 'o1', 3, 2)])
    harness.resolve()
    return harness


def names(harness, player_number):
    return sorted(unit.name for unit in
                  harness.session(player_number).getBoard().units)


def types_listed(harness, player_number):
    """The unit types this player's session knows of, as `show types` reads them."""
    return types_view(harness.session(player_number).getPlayers())


def type_names(harness, player_number):
    return [entry['name'] for entry in types_listed(harness, player_number)]


def test_a_player_sees_only_their_own_units_before_contact(tmp_path):
    harness = apart(tmp_path)
    assert names(harness, 1) == ['x1']
    assert names(harness, 2) == ['o1']


def test_the_observer_and_the_server_see_everything(tmp_path):
    harness = apart(tmp_path)
    assert names(harness, 0) == ['o1', 'x1']


def test_no_enemy_type_is_listed_before_contact(tmp_path):
    harness = apart(tmp_path)
    assert 'Brute' not in type_names(harness, 1)
    assert 'Sneaky' not in type_names(harness, 2)


def touching(tmp_path):
    """Two players whose units fight, and survive to tell of it.

    The fare is a unit's health, so ten of the fourteen goes on the square
    itself. That leaves four against an attack of 3: each can land one blow
    and no more, so they trade one, the contest ends undecided, and both fall
    back.

    Fourteen rather than thirteen, so that the blow does not leave both units
    on nothing: a player whose every unit is spent is out (R7.1), and a game
    that has been decided resolves no further turn.
    """
    harness = GameHarness(tmp_path)
    harness.create(4, 3, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('Sneaky', 'X', 3, 10, 14)], [('Sneaky', 'x1', 0, 0)])
    harness.deploy(2, [('Brute', 'O', 3, 10, 14)], [('Brute', 'o1', 2, 0)])
    harness.resolve()
    # both step into (1, 0) and fight there
    harness.turn({1: [('x1', UnitType.EAST)], 2: [('o1', UnitType.WEST)]})
    return harness


def test_contact_reveals_the_enemy_unit(tmp_path):
    harness = touching(tmp_path)
    assert names(harness, 1) == ['o1', 'x1']
    assert names(harness, 2) == ['o1', 'x1']


def test_contact_reveals_the_enemy_type_as_it_was_designed(tmp_path):
    harness = touching(tmp_path)
    listed = types_listed(harness, 1)
    brute = [entry for entry in listed if entry['name'] == 'Brute']
    assert len(brute) == 1
    # the design, not the state the unit happened to be in when it was met
    assert brute[0]['attack'] == 3
    assert brute[0]['health'] == 10
    assert brute[0]['energy'] == 14


def test_an_enemy_type_drops_out_when_contact_lapses(tmp_path):
    harness = touching(tmp_path)
    # disengage: neither orders anything, so no contact is made this turn
    harness.turn({1: [], 2: []})
    assert names(harness, 1) == ['x1']
    assert 'Brute' not in type_names(harness, 1)


def test_a_client_with_no_view_yet_shows_what_it_deployed(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 3, [1, 2], budget=Player.MAX_BUDGET)
    client = harness.deploy(1, [('X', 'X', 1, 5, 50)], [('X', 'x1', 0, 0)])
    assert [unit.name for unit in client.getBoard().units] == ['x1']


def test_a_players_pending_orders_are_their_own_and_nobody_elses(tmp_path):
    """`show pending` is a player reading back what they published.

    Their session is built from their own view and loads no other player's
    orders, so this is what there is to leak and there is nothing in it.
    """
    from board_game_concept.http import views

    harness = GameHarness(tmp_path)
    harness.create(5, 3, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 1, 4, 8)], [('X', 'x1', 0, 0)])
    harness.deploy(2, [('O', 'O', 1, 4, 8)], [('O', 'o1', 4, 2)])
    harness.resolve()
    harness.order(1, [('x1', UnitType.EAST)])
    harness.order(2, [('o1', UnitType.WEST)])

    for number, mine in ((1, 'x1'), (2, 'o1')):
        session = harness.session(number)
        pending = views.pending_view(session.getPlayers(), session.getBoard())
        assert [entry['unit'] for entry in pending] == [mine]
        assert {entry['player'] for entry in pending} == {number}
