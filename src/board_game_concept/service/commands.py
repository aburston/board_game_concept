"""What a caller is asking the game to do.

Parsing produces one of these; the service layer acts on it. They are the
vocabulary shared between the two, so a command object and the function that
carries it out are named for the same thing.

Every node carries its children, even though today's commands are all leaves.
The grammar is going to grow statements that contain other statements, and the
things that will walk this tree - an interpreter, and whatever prices a program
by its size - are visitors over that shape.
"""

from ..domain import Player
from .errors import GameError


class Node:
    """One node of a parsed tree."""

    kind = 'node'
    fields = ()

    def __init__(self, **values):
        missing = [name for name in self.fields if name not in values]
        if missing:
            raise TypeError(f"{self.kind} needs {', '.join(missing)}")
        unexpected = [name for name in values if name not in self.fields]
        if unexpected:
            raise TypeError(f"{self.kind} has no {', '.join(unexpected)}")
        for name in self.fields:
            setattr(self, name, values[name])

    def children(self):
        """The nodes below this one, in the order they were written."""
        return ()

    def accept(self, visitor):
        """Hand this node to a visitor, by kind."""
        method = getattr(visitor, f'visit_{self.kind}', None)
        if method is None:
            method = visitor.generic_visit
        return method(self)

    def __eq__(self, other):
        return (type(other) is type(self)
                and all(getattr(self, name) == getattr(other, name)
                        for name in self.fields))

    def __repr__(self):
        described = ', '.join(f'{name}={getattr(self, name)!r}'
                              for name in self.fields)
        return f'{type(self).__name__}({described})'


class Visitor:
    """Walks a tree of nodes. Override visit_<kind> for the ones you care about."""

    def visit(self, node):
        return node.accept(self)

    def generic_visit(self, node):
        for child in node.children():
            self.visit(child)


class Help(Node):
    kind = 'help'


class Exit(Node):
    kind = 'exit'


class Reload(Node):
    kind = 'reload'


class Commit(Node):
    kind = 'commit'


class Show(Node):
    kind = 'show'
    # how the answer is to be written: as a table for a person, or as JSON for
    # whatever is reading the session that is not one
    fields = ('subject', 'format')

    def __init__(self, **values):
        values.setdefault('format', 'table')
        super().__init__(**values)


class SetBoard(Node):
    kind = 'set_board'
    fields = ('size_x', 'size_y')


class AddPlayer(Node):
    kind = 'add_player'
    # the budget is defaulted rather than required, so that a draft written
    # before budgets existed still replays as the command it was, and a caller
    # that does not care about the budget need not name one
    fields = ('number', 'budget')

    def __init__(self, **values):
        values.setdefault('budget', Player.DEFAULT_BUDGET)
        super().__init__(**values)


class RemovePlayer(Node):
    kind = 'remove_player'
    fields = ('number',)


class SetFlag(Node):
    kind = 'set_flag'
    fields = ('unit',)


class AddType(Node):
    kind = 'add_type'
    fields = ('name', 'symbol', 'attack', 'health', 'energy')


class AddUnit(Node):
    kind = 'add_unit'
    fields = ('type_name', 'name', 'x', 'y')


class RemoveUnit(Node):
    kind = 'remove_unit'
    fields = ('name',)


class LoadBoard(Node):
    kind = 'load_board'
    fields = ('path',)


class LoadPlayer(Node):
    kind = 'load_player'
    fields = ('path',)


class Move(Node):
    kind = 'move'
    fields = ('unit', 'direction')


class Hold(Node):
    kind = 'hold'
    fields = ('unit',)


class SetNewGame(Node):
    """The setter that marks setup done. Only the administrator sends this,
    and only over the HTTP tier - the local flow calls `data.setNewGame`
    directly. Kept as a command so the wire has one shape for every
    mutation."""

    kind = 'set_new_game'
    fields = ('new_game',)


def _descendants(cls):
    """Every class below this one, however deep.

    Walked rather than listed, so a command added to this module is available
    to be rebuilt without anything else being told about it. The recursion is
    what makes it keep working when the grammar grows statements that contain
    other statements and a command becomes a subclass of a command.
    """
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _descendants(subclass)


def command_type(kind):
    """The command class that names itself with this kind, or None."""
    for subclass in _descendants(Node):
        if subclass.kind == kind:
            return subclass
    return None


def as_record(command):
    """One command as plain data: its kind, and the fields it was given."""
    record = {'kind': command.kind}
    for name in command.fields:
        record[name] = getattr(command, name)
    return record


def from_record(record):
    """The command a record describes.

    Raises `GameError` rather than returning None for anything it cannot
    rebuild: a draft is replayed through the same rules that first accepted
    it, so a record that is not a command is refused the way a line that is
    not a command is.
    """
    if not isinstance(record, dict) or 'kind' not in record:
        raise GameError(f"not a command: {record!r}")
    values = dict(record)
    kind = values.pop('kind')
    node = command_type(kind)
    if node is None:
        raise GameError(f"no such command: {kind}")
    try:
        return node(**values)
    except TypeError as e:
        raise GameError(f"command {kind} cannot be read back", e) from e
