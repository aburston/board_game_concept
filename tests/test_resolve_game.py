"""A game is resolved to its end the moment the last setup is committed.

Nobody is waited for from there: every order is a controller's, and the game
stops when it is decided, when its whole state repeats - the controllers are
deterministic, so such a game can never change again - or at the turn cap.
Every turn is recorded as it goes.
"""

import pytest

from board_game_concept.service import turn as turn_service

from game_harness import GameHarness


HOLD = 'HOLD'
WALK_SOUTH = 'MOVE south'
WALK_NORTH = 'MOVE north'
# a hunter that walks at the enemy flag, which on a two-column board is
# straight down the column it stands in
HUNT = ('SELF\nMOV r6, r1\nFLAG enemy\nSUB r1, r6\nJIF pos r1, south\n'
        'MOVE north\nHALT\nsouth: MOVE south')


def a_game(tmp_path, mine, theirs, my_unit=('X', 'x1', 0, 0),
           their_unit=('O', 'o1', 0, 5), size=(2, 6)):
    """Two players, one type each, one unit each, on a two-by-six board."""
    harness = GameHarness(tmp_path)
    harness.create(*size, [1, 2], default_army=False)
    harness.deploy(1, [('X', 'X', *mine)], [my_unit])
    harness.deploy(2, [('O', 'O', *theirs)], [their_unit])
    return harness


def test_two_armies_that_never_move_stop_where_the_state_repeats(tmp_path):
    harness = a_game(tmp_path, (1, 4, 10, 2, HOLD), (1, 4, 10, 2, HOLD))
    server = harness.play()
    outcome = server.getOutcome()
    assert outcome['decided'] is False
    assert outcome['reason'] == 'repeated'
    # turn 1 places the units and both rest to full; turn 2 changes nothing
    # but the meter, turn 3 the same... the state repeats once the meters
    # have cycled, which with a one-tick program on compute 2 is twenty
    # turns, and no later than that
    assert 2 <= outcome["turn"] <= 22
    assert outcome['since'] < outcome['turn']
    assert server.getTurnNumber() == outcome['turn']


def test_a_decided_game_records_its_deciding_turn(tmp_path):
    # a lance walks down the column at a keep that cannot move: the keep's
    # ten health goes in two strikes, and its flag with it. The lance is
    # given four health and forty energy so that it survives the keep's
    # two blows and can pay for its own
    harness = a_game(tmp_path, (8, 4, 40, 3, HUNT), (1, 10, 5, 0),
                     my_unit=('X', 'x1', 0, 0), their_unit=('O', 'o1', 0, 5))
    server = harness.play()
    outcome = server.getOutcome()
    assert outcome['decided'] is True
    assert outcome['winner'] == 1
    assert outcome['turn'] == server.getTurnNumber()
    assert harness.units()['o1'].destroyed


def test_a_game_that_never_repeats_stops_at_the_cap(tmp_path, monkeypatch):
    # a counter that never sleeps and never repeats: its memory grows every
    # turn, so no two states are alike
    monkeypatch.setattr(turn_service, 'TURN_CAP', 7)
    count = 'LOAD r0, 0\nADD r0, 1\nSTORE r0, 0\nHOLD'
    harness = a_game(tmp_path, (1, 4, 10, 5, count), (1, 4, 10, 2, HOLD))
    server = harness.play()
    outcome = server.getOutcome()
    assert outcome == {'decided': False, 'winner': None, 'turn': 7,
                       'reason': 'cap'}


def test_every_turn_is_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(turn_service, 'TURN_CAP', 5)
    count = 'LOAD r0, 0\nADD r0, 1\nSTORE r0, 0\nHOLD'
    harness = a_game(tmp_path, (1, 4, 10, 5, count), (1, 4, 10, 2, HOLD))
    harness.play()
    repository = harness.repository()
    assert repository.turn_numbers() == [0, 1, 2, 3, 4, 5]
    third = repository.read_turn(3)
    assert third['turn'] == 3
    assert third['board'] == {'size_x': 2, 'size_y': 6}
    names = {unit['name']: unit for unit in third['units']}
    assert names['x1']['memory'] == [[0, 2]]        # counted on turns 2, 3
    assert {flag['player'] for flag in third['flags']} == {1, 2}
    assert any(entry['kind'] == 'thought' for entry in third['events'])
    assert set(third['maps']) == {'1', '2'}
    traces = {trace['unit']: trace for trace in third['traces']}
    assert traces['x1']['ticks'] == 4 and traces['o1']['ticks'] == 1
    assert third['progress']['turn'] == 3
    last = repository.read_turn(5)
    assert last['progress']['outcome']['reason'] == 'cap'


def test_nobody_is_waited_for(tmp_path):
    harness = a_game(tmp_path, (1, 4, 10, 2, HOLD), (1, 4, 10, 2, HOLD))
    harness.play()
    # a player's session opens on a resolved game and may give it nothing
    client = harness.session(1)
    assert client.getOutcome() is not None
    assert client.repository.has_orders(1) is False


def test_the_maps_and_the_controllers_survive_a_session(tmp_path,
                                                        monkeypatch):
    """A session that resolves turns needs what the last turn left, and a
    game is read back whole: the maps from the record, the controller state
    from the units."""
    monkeypatch.setattr(turn_service, 'TURN_CAP', 3)
    count = 'LOAD r0, 0\nADD r0, 1\nSTORE r0, 0\nSAY all, 1, 2, 3\nHOLD'
    harness = a_game(tmp_path, (1, 4, 10, 5, count), (1, 4, 10, 2, HOLD))
    harness.play()
    server = harness.session(0)
    x1 = harness.units()['x1']
    assert x1.memory == {0: 2}
    assert x1.meter == (4 + 5) * 2            # two turns of nine ticks
    assert server.getBoard().maps[1].at(0, 0)[0] != 0
    assert server.getBoard().turn == 3
