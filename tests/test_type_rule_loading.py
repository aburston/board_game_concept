"""Reading a game stored before a type could be refused for its energy.

A type that can move must hold at least its health in energy, because a move
costs its health. Two reading paths predate that rule and must not break on it:
a player's own file, which may have been written when the rule did not exist,
and the reconstruction of an enemy's type from a unit seen in contact, which
falls back to what play has worn that unit down to.
"""

import pytest

from board_game_concept import Game, YamlGameRepository
from board_game_concept.service.errors import UnreadableGame

pytestmark = pytest.mark.backend('yaml')


def a_player_file(tmp_path, types):
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_board(6, 3)
    repository.write_player(1, types, 100)
    return repository


def a_seen_unit(**overrides):
    """A unit record as it arrives from a sighting, with no design attached."""
    record = {
        'type': 'Seen', 'symbol': 'S', 'name': 's1',
        'attack': '3', 'health': '5', 'energy': '1',
    }
    record.update(overrides)
    return record


def a_session(repository):
    session = Game(repository, 1)
    session.players = {1: {'number': 1, 'obj': None, 'types': {}}}
    return session


# --- a player's own file


def test_a_stored_type_that_cannot_afford_a_move_is_refused(tmp_path):
    repository = a_player_file(tmp_path, {
        'Heavy': {'name': 'Heavy', 'symbol': 'H',
                  'attack': '3', 'health': '6', 'energy': '5'},
    })
    with pytest.raises(UnreadableGame) as raised:
        Game(repository, 1).load()
    assert 'Heavy' in str(raised.value)
    assert 'energy' in str(raised.value)


def test_a_stored_type_that_can_afford_a_move_still_loads(tmp_path):
    repository = a_player_file(tmp_path, {
        'Heavy': {'name': 'Heavy', 'symbol': 'H',
                  'attack': '3', 'health': '6', 'energy': '6'},
    })
    session = Game(repository, 1)
    session.load()
    assert session.players[1]['types']['Heavy']['obj'].move_cost == 6


# --- an enemy type rebuilt from a sighting


def test_a_sighting_of_a_spent_unit_is_read_not_refused(tmp_path):
    # 1 energy against 5 health is what spending looks like, not an illegal
    # design. Refusing it would turn a legitimate sighting into a crash
    session = a_session(a_player_file(tmp_path, {}))
    rebuilt = session._type_for(1, a_seen_unit())
    assert rebuilt.type_health == 5
    assert rebuilt.type_energy == 5, 'floored to the fare it must be able to pay'


def test_a_sighting_of_a_wall_keeps_its_nothing(tmp_path):
    # a wall's 0 energy is not spending: floored to its health it would stop
    # being a wall, and the wall rule would refuse it
    session = a_session(a_player_file(tmp_path, {}))
    rebuilt = session._type_for(
        1, a_seen_unit(type='Wall', symbol='W', attack='0', energy='0'))
    assert rebuilt.attack == 0
    assert rebuilt.energy == 0


def test_a_sighting_that_carries_the_design_is_left_alone(tmp_path):
    # the floor is for records that lost the design. A record that carries it
    # is read as written, spent energy and all
    session = a_session(a_player_file(tmp_path, {}))
    rebuilt = session._type_for(1, a_seen_unit(
        type_attack='3', type_health='5', type_energy='40'))
    assert rebuilt.type_energy == 40
    assert rebuilt.type_health == 5


def test_a_carried_design_below_the_rule_is_not_floored(tmp_path):
    # a design from before the rule, arriving inside a sighting. It is what the
    # record says it is; the floor does not reach in and rewrite it
    session = a_session(a_player_file(tmp_path, {}))
    with pytest.raises(AssertionError):
        session._type_for(1, a_seen_unit(
            type_attack='3', type_health='6', type_energy='5'))
