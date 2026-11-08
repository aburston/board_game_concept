"""The one description of the language, checked against its two readers.

`grammar.py` describes each command as the words it is typed as. `help` renders
those words as a usage line and `complete.py` walks them; the parser reads the
same commands by hand. These tests hold the three together: the usage lines
must not have moved, every usage must parse as the command it claims to be, and
what a role is offered must be what a role is allowed.
"""

import pytest

from board_game_concept.cli import roles
from board_game_concept.cli.grammar import (NAME, NUMBER, Optional, PATH,
                                            Slot, SYMBOL, TYPE, UNIT, USAGES)
from board_game_concept.cli.parser import parse

# every usage line `help` prints, in the order it prints them. A player gives
# no orders - every move is a controller's, running its type's program - so
# `move` and `hold` are gone, and the program and the record have arrived
USAGE_LINES = [
    'add player <number> [<budget>]',
    'remove player <number>',
    'remove unit <unit>',
    'add type <name> <symbol> <attack> <health> <energy> [<compute>]',
    'add unit <type> <name> <x> <y>',
    'load board <file>',
    'load player <file>',
    'set board <size_x> <size_y>',
    'set flag <unit>',
    'set program <type> <file>',
    'show board [json]',
    'show types [json]',
    'show units [json]',
    'show players [json]',
    'show pending [json]',
    'show events [json]',
    'show designs [json]',
    'show flags [json]',
    'show placement [json]',
    'show program <type> [json]',
    'show turn <n> [known] [json]',
    'next',
    'prev',
    'commit',
    'reload',
    'login [<username>]',
    'logout',
    'whoami',
    'passwd',
    'help',
    'exit',
]

# a word that would plausibly be typed into each kind of slot
FILLERS = {
    UNIT: 'alpha',
    TYPE: 'tank',
    PATH: 'board.yaml',
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
                # an optional holds either a fixed word or a slot, and a slot
                # is filled the same way a required one is
                words.append(FILLERS[word.word.kind] if word.holds_slot()
                             else word.word)
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
    program = [usage for usage in USAGES
               if usage.kind == 'set_program_file'][0]

    type_slot, file_slot = program.words[2], program.words[3]

    assert isinstance(type_slot, Slot) and type_slot.kind == TYPE
    assert isinstance(file_slot, Slot) and file_slot.kind == PATH


def test_there_is_no_order_in_the_grammar():
    """A player gives no orders: every move comes from a controller."""
    from board_game_concept.cli.parser import ParseError

    assert not any(usage.kind in ('move', 'hold') for usage in USAGES)
    for line in ('move alpha north', 'hold alpha'):
        with pytest.raises(ParseError):
            parse(line)


def test_a_type_is_defined_with_or_without_compute():
    assert parse('add type Runner r 2 4 10').compute == 0
    assert parse('add type Runner r 2 4 10 5').compute == 5


def test_a_turn_of_the_record_is_asked_for_by_number():
    shown = parse('show turn 12')
    assert (shown.subject, shown.turn, shown.known) == ('turn', 12, False)
    assert parse('show turn 12 known').known is True
    assert parse('show program Keep').name == 'Keep'


@pytest.mark.parametrize('role', [roles.SERVER, roles.CLIENT, roles.OBSERVER],
                         ids=lambda role: role.name)
@pytest.mark.parametrize('line, kind', [
    ('login', 'login'),
    ('login ada', 'login'),
    ('logout', 'logout'),
    ('whoami', 'whoami'),
    ('passwd', 'passwd'),
], ids=lambda value: value if isinstance(value, str) else value)
def test_every_role_offers_the_account_commands(role, line, kind):
    """Who you are is not a thing one role may ask and another may not."""
    command = parse(line)

    assert command.kind == kind
    assert role.allows(command)
    assert any(usage.kind == kind for usage in USAGES if role.offers(usage))


def test_a_login_carries_no_password():
    """A command gets written down; a password that did would be leaked."""
    from board_game_concept.service.commands import (ChangePassword, Login,
                                                     Logout, Whoami)

    for node in (Login, Logout, Whoami, ChangePassword):
        assert 'password' not in node.fields
    assert parse('login ada').username == 'ada'
    assert parse('login').username is None


@pytest.mark.parametrize('line', ['login ada secret', 'passwd new-secret'])
def test_a_password_typed_as_an_argument_is_refused_by_name(line):
    from board_game_concept.cli.parser import ParseError

    with pytest.raises(ParseError) as refused:
        parse(line)

    assert 'password' in refused.value.message
