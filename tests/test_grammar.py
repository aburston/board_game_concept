"""The one description of the language, checked against its two readers.

`grammar.py` describes each command as the words it is typed as. `help` renders
those words as a usage line and `complete.py` walks them; the parser reads the
same commands by hand. These tests hold the three together: the usage lines
must not have moved, every usage must parse as the command it claims to be, and
what a role is offered must be what a role is allowed.
"""

import pytest

from board_game_concept.cli import roles
from board_game_concept.cli.grammar import (DIRECTION, NAME, NUMBER, Optional,
                                            PATH, Slot, SYMBOL, TYPE, UNIT,
                                            USAGES)
from board_game_concept.cli.parser import parse

# every usage line as it read before the grammar was described as words rather
# than as sentences. `help` prints these, and this change was meant to be
# invisible in what it prints
USAGE_LINES = [
    'add player <number>',
    'add type <name> <symbol> <attack> <health> <energy>',
    'add unit <type> <name> <x> <y>',
    'load board <file>',
    'load player <file>',
    'set board <size_x> <size_y>',
    'show board [json]',
    'show types [json]',
    'show units [json]',
    'show players [json]',
    'show pending [json]',
    'move <unit> <north|east|south|west>',
    'commit',
    'reload',
    'help',
    'exit',
]

# a word that would plausibly be typed into each kind of slot
FILLERS = {
    UNIT: 'alpha',
    TYPE: 'tank',
    PATH: 'board.yaml',
    DIRECTION: 'north',
    NUMBER: '1',
    NAME: 'alpha',
    SYMBOL: 'X',
}


def typed(usage, with_optionals=True):
    """One line that this usage describes, as a person would type it."""
    words = []
    for word in usage.words:
        if isinstance(word, str):
            words.append(word)
        elif isinstance(word, Optional):
            if with_optionals:
                words.append(word.word)
        else:
            words.append(FILLERS[word.kind])
    return ' '.join(words)


def test_the_usage_lines_are_the_ones_help_has_always_printed():
    assert [usage.usage for usage in USAGES] == USAGE_LINES


@pytest.mark.parametrize('usage', USAGES, ids=lambda u: u.usage)
def test_every_usage_parses_as_the_command_it_describes(usage):
    command = parse(typed(usage))

    assert command.kind == usage.kind


@pytest.mark.parametrize('usage', USAGES, ids=lambda u: u.usage)
def test_every_usage_parses_without_its_optional_words(usage):
    command = parse(typed(usage, with_optionals=False))

    assert command.kind == usage.kind


@pytest.mark.parametrize('role', [roles.SERVER, roles.CLIENT, roles.OBSERVER],
                         ids=lambda role: role.name)
@pytest.mark.parametrize('usage', USAGES, ids=lambda u: u.usage)
def test_what_a_role_is_offered_is_what_it_is_allowed(role, usage):
    # the offer made before a line is entered and the refusal made after it
    # read the same two sets, and this is what says so
    command = parse(typed(usage))

    assert role.offers(usage) == role.allows(command)


def test_a_slot_knows_what_it_stands_for():
    move = [usage for usage in USAGES if usage.kind == 'move'][0]

    unit, direction = move.words[1], move.words[2]

    assert isinstance(unit, Slot) and unit.kind == UNIT
    assert isinstance(direction, Slot) and direction.kind == DIRECTION
