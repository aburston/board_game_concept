"""The language the three roles share.

One grammar, described once. Which parts of it a given role may use is a
separate question, answered by `roles.py`; how a line is read is answered by
`parser.py`. Keeping the vocabulary here means `help` can be generated from
the same description the parser works to, rather than maintained by hand
alongside it and drifting.

Each command is described as the words it is typed as: literal words, and
slots standing for what the person supplies. That form is what lets one
description serve three readers - `help` renders it as a usage line,
`complete.py` walks it to say what may be typed next, and `parser.py` is held
to it by a test that every usage here parses as the command it names. A
display string alone could only be read by a person, and a second table of
completable words beside this one is the drift this file exists to prevent.
"""

from ..domain import UnitType

DIRECTIONS = {
    'north': UnitType.NORTH,
    'east': UnitType.EAST,
    'south': UnitType.SOUTH,
    'west': UnitType.WEST,
}

SHOW_SUBJECTS = ('board', 'types', 'units', 'players', 'pending')

# the one word a `show` may end in, asking for the answer as JSON rather than
# as a table
SHOW_FORMAT = 'json'

# what a slot stands for, and so where its candidates come from. A closed set:
# the first four can be completed, and the last three are the person naming or
# numbering something that only they know
UNIT = 'unit'
TYPE = 'type'
PATH = 'path'
DIRECTION = 'direction'
NUMBER = 'number'
NAME = 'name'
SYMBOL = 'symbol'


class Slot:
    """A word the person supplies, and what kind of thing it names."""

    def __init__(self, display, kind):
        self.display = display
        self.kind = kind

    def text(self):
        return f'<{self.display}>'


class Optional:
    """An element that may be typed here, or left out.

    Holds either a fixed word - the trailing `json` of a `show` - or a `Slot`,
    for an argument a command takes when it is given and does without when it
    is not. What it renders as and what it completes to are asked of what it
    holds rather than assumed to be a word, which is what lets one class serve
    both without a second optional-shaped thing beside it.
    """

    def __init__(self, word):
        self.word = word

    def holds_slot(self):
        return isinstance(self.word, Slot)

    def text(self):
        return f'[{word_text(self.word)}]'


def word_text(word):
    """One element of a command, as `help` writes it."""
    if isinstance(word, str):
        return word
    return word.text()


class Usage:
    """How one command is written, and what it does."""

    def __init__(self, kind, words, description, subject=None):
        self.kind = kind
        # the command as it is typed: literal strings, `Slot`s and `Optional`s
        self.words = tuple(words)
        self.description = description
        # `show` is one production with several subjects, and a role may hold
        # some of them and not others, so each is listed on its own
        self.subject = subject

    @property
    def usage(self):
        """The usage line, generated rather than kept beside the words."""
        return ' '.join(word_text(word) for word in self.words)


def _show(subject, description):
    """One `show` production: a subject, and the optional `json` after it."""
    return Usage('show', ('show', subject, Optional(SHOW_FORMAT)),
                 description, subject=subject)


# every production the parser can produce, in the order help lists them
USAGES = (
    Usage('add_player', ('add', 'player', Slot('number', NUMBER),
                         Optional(Slot('budget', NUMBER))),
          'add a player to the game, before it starts, with an optional '
          'point budget'),
    Usage('add_type', ('add', 'type', Slot('name', NAME),
                       Slot('symbol', SYMBOL), Slot('attack', NUMBER),
                       Slot('health', NUMBER), Slot('energy', NUMBER)),
          'define a unit type'),
    Usage('add_unit', ('add', 'unit', Slot('type', TYPE), Slot('name', NAME),
                       Slot('x', NUMBER), Slot('y', NUMBER)),
          'deploy a unit of a type you have defined'),
    Usage('load_board', ('load', 'board', Slot('file', PATH)),
          'load the board size from a file'),
    Usage('load_player', ('load', 'player', Slot('file', PATH)),
          'load a player, their types and their units, from a file'),
    Usage('set_board', ('set', 'board', Slot('size_x', NUMBER),
                        Slot('size_y', NUMBER)),
          'set the size of the board, before the game starts'),
    _show('board', 'show the board as you see it, as a table or as JSON'),
    _show('types', 'show the unit types you know of, as a table or as JSON'),
    _show('units', 'show the units you know of, as a table or as JSON'),
    _show('players', 'show the registered players, as a table or as JSON'),
    _show('pending',
          'show the orders queued for the next turn, as a table or as JSON'),
    Usage('move', ('move', Slot('unit', UNIT),
                   Slot('|'.join(DIRECTIONS), DIRECTION)),
          'order one of your units to move'),
    Usage('commit', ('commit',),
          'commit the actions you have taken; this cannot be undone'),
    Usage('reload', ('reload',),
          'read the game again from disk'),
    Usage('help', ('help',),
          'display this information'),
    Usage('exit', ('exit',),
          'leave the session'),
)
