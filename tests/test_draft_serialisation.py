"""A draft is written down as the commands that made it, and read back as them.

Every production the grammar has is driven through the round trip, so a command
added to `commands.py` without a way to write it down fails here rather than
silently dropping a player's work.
"""

import pytest
import yaml

from board_game_concept.cli.grammar import USAGES, Optional, Slot
from board_game_concept.cli.parser import parse
from board_game_concept.service.commands import (as_record, command_type,
                                                 from_record)
from board_game_concept.service.errors import GameError
from board_game_concept.storage.serialise import restore_draft, serialise_draft

# something to put in each slot the grammar leaves for the person to fill in.
# The parser converts numbers, so what goes in has to be readable as one
SLOT_WORDS = {
    'unit': 'x1',
    'type': 'Cross',
    'path': 'players/1.yaml',
    'direction': 'north',
    'number': '3',
    'name': 'x1',
    'symbol': 'X',
}


def _line(usage):
    """One line that parses as the command this usage describes."""
    words = []
    for word in usage.words:
        if isinstance(word, str):
            words.append(word)
        elif isinstance(word, Optional):
            continue
        elif isinstance(word, Slot):
            words.append(SLOT_WORDS[word.kind])
    return ' '.join(words)


ALL_USAGES = [pytest.param(usage, id=usage.kind + (
    f'-{usage.subject}' if usage.subject else '')) for usage in USAGES]


@pytest.mark.parametrize('usage', ALL_USAGES)
def test_every_command_survives_a_draft(usage):
    """A command written into a draft comes back as the command it was."""
    command = parse(_line(usage))
    assert command is not None

    document = yaml.safe_dump(serialise_draft([command], turn=2))
    restored = restore_draft(yaml.safe_load(document), turn=2)

    assert restored == [command]


def test_a_draft_keeps_the_order_it_was_given_in():
    commands = [parse('add type Cross X 1 1 10'),
                parse('add unit Cross x1 0 0'),
                parse('move x1 north')]

    document = yaml.safe_dump(serialise_draft(commands, turn=0))

    assert restore_draft(yaml.safe_load(document), turn=0) == commands


def test_a_draft_for_another_turn_is_not_restored():
    """Work left behind by a session that ended mid-resolution is discarded."""
    document = yaml.safe_dump(
        serialise_draft([parse('move x1 north')], turn=3))

    assert restore_draft(yaml.safe_load(document), turn=4) == []
    assert restore_draft(yaml.safe_load(document), turn=2) == []


def test_no_draft_at_all_is_not_an_error():
    assert restore_draft(None, turn=1) == []
    assert restore_draft({}, turn=1) == []
    assert restore_draft({'turn': 1, 'commands': None}, turn=1) == []


def test_a_record_that_is_not_a_command_is_refused():
    with pytest.raises(GameError):
        from_record({'kind': 'fly', 'unit': 'x1'})
    with pytest.raises(GameError):
        from_record({'unit': 'x1'})
    with pytest.raises(GameError):
        from_record('move x1 north')


def test_a_command_with_the_wrong_fields_is_refused():
    with pytest.raises(GameError):
        from_record({'kind': 'move', 'unit': 'x1'})
    with pytest.raises(GameError):
        from_record({'kind': 'move', 'unit': 'x1', 'direction': 1, 'speed': 2})


def test_a_record_holds_the_kind_and_the_fields():
    command = parse('add unit Cross x1 2 3')

    assert as_record(command) == {
        'kind': 'add_unit', 'type_name': 'Cross',
        'name': 'x1', 'x': 2, 'y': 3,
    }


def test_every_production_has_a_command_type():
    """The lookup finds a class for every kind the grammar can produce."""
    for usage in USAGES:
        assert command_type(usage.kind) is not None


def test_an_unknown_kind_has_no_command_type():
    assert command_type('fly') is None
