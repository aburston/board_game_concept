"""The language the three roles share.

One grammar, described once. Which parts of it a given role may use is a
separate question, answered by `roles.py`; how a line is read is answered by
`parser.py`. Keeping the vocabulary here means `help` can be generated from
the same description the parser works to, rather than maintained by hand
alongside it and drifting.
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


class Usage:
    """How one command is written, and what it does."""

    def __init__(self, kind, usage, description, subject=None):
        self.kind = kind
        self.usage = usage
        self.description = description
        # `show` is one production with several subjects, and a role may hold
        # some of them and not others, so each is listed on its own
        self.subject = subject


# every production the parser can produce, in the order help lists them
USAGES = (
    Usage('add_player', 'add player <number>',
          'add a player to the game, before it starts'),
    Usage('add_type', 'add type <name> <symbol> <attack> <health> <energy>',
          'define a unit type'),
    Usage('add_unit', 'add unit <type> <name> <x> <y>',
          'deploy a unit of a type you have defined'),
    Usage('load_board', 'load board <file>',
          'load the board size from a file'),
    Usage('load_player', 'load player <file>',
          'load a player, their types and their units, from a file'),
    Usage('set_board', 'set board <size_x> <size_y>',
          'set the size of the board, before the game starts'),
    Usage('show', 'show board [json]',
          'show the board as you see it, as a table or as JSON',
          subject='board'),
    Usage('show', 'show types [json]',
          'show the unit types you know of, as a table or as JSON',
          subject='types'),
    Usage('show', 'show units [json]',
          'show the units you know of, as a table or as JSON',
          subject='units'),
    Usage('show', 'show players [json]',
          'show the registered players, as a table or as JSON',
          subject='players'),
    Usage('show', 'show pending [json]',
          'show the orders queued for the next turn, as a table or as JSON',
          subject='pending'),
    Usage('move', 'move <unit> <' + '|'.join(DIRECTIONS) + '>',
          'order one of your units to move'),
    Usage('commit', 'commit',
          'commit the actions you have taken; this cannot be undone'),
    Usage('reload', 'reload',
          'read the game again from disk'),
    Usage('help', 'help',
          'display this information'),
    Usage('exit', 'exit',
          'leave the session'),
)
