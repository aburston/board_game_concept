"""Which part of the grammar each role may use.

The parser reads the whole language whatever the caller is; what a caller is
allowed to *do* is decided here, in one table, rather than by each session
loop checking for itself. That is what keeps the three roles honest about
their differences: the observer is read-only because it is not given the
commands that write, not because it happens not to implement them.
"""

from .parser import INVALID_COMMAND


class Role:
    def __init__(self, name, kinds, show_subjects):
        self.name = name
        self.kinds = frozenset(kinds)
        self.show_subjects = frozenset(show_subjects)

    def offers(self, usage):
        """Whether this role may run the command this usage describes.

        The same two sets `allows` reads, asked of a usage rather than of a
        command, so what is offered before a line is entered and what is
        accepted after it cannot come apart. `help.py` lists by this, and
        `complete.py` completes by it.
        """
        if usage.kind not in self.kinds:
            return False
        if usage.subject is not None:
            return usage.subject in self.show_subjects
        return True

    def allows(self, command):
        if command.kind not in self.kinds:
            return False
        if command.kind == 'show':
            return command.subject in self.show_subjects
        return True

    def refusal(self, command):
        """What to say when this role may not run this command."""
        if command.kind == 'show':
            return 'invalid show command'
        return INVALID_COMMAND


SERVER = Role(
    'server',
    kinds=('help', 'exit', 'commit', 'show',
           'set_board', 'add_player', 'remove_player',
           'load_board', 'load_player'),
    show_subjects=('board', 'types', 'units', 'players', 'pending',
                   'events', 'designs', 'flags', 'placement'))

CLIENT = Role(
    'client',
    kinds=('help', 'exit', 'commit', 'show', 'add_type', 'add_unit',
           'remove_unit', 'set_flag', 'move', 'hold'),
    # `pending` is this player's own published orders and nobody else's - a
    # session holds only its own - and it is the only way to read back an
    # army that has been committed and not yet deployed. The browser shows
    # it; withholding it here made the two clients answer differently
    show_subjects=('board', 'types', 'units', 'players', 'pending',
                   'events', 'designs', 'flags', 'placement'))

OBSERVER = Role(
    'observer',
    kinds=('help', 'exit', 'reload', 'show'),
    show_subjects=('board', 'types', 'units', 'players', 'pending',
                   'events', 'designs', 'flags', 'placement'))
