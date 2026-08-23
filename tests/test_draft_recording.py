"""Everything a session does to a game is written down as it does it.

Recording lives behind `games.perform`, so that a caller added later cannot
quietly not record. That would look like working code and lose somebody's army,
which is the failure this change exists to remove - so the coverage of the
grammar is asserted here rather than left to whoever adds the next command.
"""

import pytest

from board_game_concept.cli.grammar import USAGES, Optional, Slot
from board_game_concept.cli.parser import parse
from board_game_concept.service import games
from board_game_concept.service.commands import AddType, AddUnit, Move
from board_game_concept.service.errors import GameError
from game_harness import GameHarness

# the productions that are the session itself rather than something done to a
# game: they end it, explain it, read it, or turn the crank
SESSION_KINDS = {'help', 'exit', 'reload', 'commit', 'show'}

SLOT_WORDS = {
    'unit': 'x1', 'type': 'Cross', 'path': 'players/1.yaml',
    'direction': 'north', 'number': '3', 'name': 'x1', 'symbol': 'X',
}


def _line(usage):
    words = []
    for word in usage.words:
        if isinstance(word, str):
            words.append(word)
        elif isinstance(word, Slot):
            words.append(SLOT_WORDS[word.kind])
        elif isinstance(word, Optional):
            continue
    return ' '.join(words)


WRITE_USAGES = [pytest.param(usage, id=usage.kind)
                for usage in USAGES if usage.kind not in SESSION_KINDS]


@pytest.mark.parametrize('usage', WRITE_USAGES)
def test_every_write_production_is_something_the_service_layer_carries_out(usage):
    """A command that changes a game has a service function, and so is drafted.

    Adding a production to the grammar without one fails here, rather than
    parsing fine and being silently dropped from every player's draft.
    """
    command = parse(_line(usage))

    assert games.carries_out(command)


def test_reading_a_game_is_not_something_to_carry_out():
    for line in ('show units', 'help', 'exit', 'commit', 'reload'):
        assert not games.carries_out(parse(line))


def test_a_session_records_what_it_did_in_the_order_it_did_it(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    client = harness.session(1)

    games.perform(client, AddType(name='Cross', symbol='X', attack=1,
                                  health=1, energy=10))
    games.perform(client, AddUnit(type_name='Cross', name='x1', x=0, y=0))

    draft = harness.repository().read_draft(1)
    assert [record['kind'] for record in draft['commands']] == [
        'add_type', 'add_unit']
    assert draft['commands'][1] == {'kind': 'add_unit', 'type_name': 'Cross',
                                    'name': 'x1', 'x': 0, 'y': 0}


def test_a_draft_is_stamped_with_the_turn_it_was_made_for(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [('Cross', 'X', 1, 5, 10)], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [('Ring', 'O', 1, 5, 10)], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    client = harness.session(1)
    games.perform(client, Move(unit='x1', direction=1))

    draft = harness.repository().read_draft(1)
    assert draft['turn'] == client.getTurnNumber()


def test_a_refused_command_is_not_recorded(tmp_path):
    """The draft holds what was done, not what was attempted."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    client = harness.session(1)
    games.perform(client, AddType(name='Cross', symbol='X', attack=1,
                                  health=1, energy=10))

    with pytest.raises(GameError):
        games.perform(client, AddUnit(type_name='Nothing', name='x1',
                                      x=0, y=0))

    draft = harness.repository().read_draft(1)
    assert [record['kind'] for record in draft['commands']] == ['add_type']


def test_the_administrator_records_setup_too(tmp_path):
    """Setup is the most laborious part of a game and the most costly to lose."""
    harness = GameHarness(tmp_path)
    from board_game_concept import Game
    from board_game_concept.service.commands import AddPlayer, SetBoard

    server = Game(harness.repository(), 0)
    server.load()
    games.perform(server, SetBoard(size_x=5, size_y=6))
    games.perform(server, AddPlayer(number=1))

    draft = harness.repository().read_draft(0)
    assert draft['commands'] == [
        {'kind': 'set_board', 'size_x': 5, 'size_y': 6},
        {'kind': 'add_player', 'number': 1},
    ]


def test_carrying_out_a_command_directly_records_nothing(tmp_path):
    """Replay applies the rules again without writing the draft down twice."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    client = harness.session(1)

    games.carry_out(client, AddType(name='Cross', symbol='X', attack=1,
                                    health=1, energy=10))

    assert harness.repository().read_draft(1) is None


def test_a_command_the_service_layer_does_not_carry_out_is_refused(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    client = harness.session(1)

    with pytest.raises(GameError):
        games.perform(client, parse('show units'))
