"""What a caller is asking the game to do.

Parsing produces one of these; the service layer acts on it. They are the
vocabulary shared between the two, so a command object and the function that
carries it out are named for the same thing.

Every node carries its children, even though today's commands are all leaves.
The grammar is going to grow statements that contain other statements, and the
things that will walk this tree - an interpreter, and whatever prices a program
by its size - are visitors over that shape.
"""


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
    fields = ('subject',)


class SetBoard(Node):
    kind = 'set_board'
    fields = ('size_x', 'size_y')


class AddPlayer(Node):
    kind = 'add_player'
    fields = ('number',)


class AddType(Node):
    kind = 'add_type'
    fields = ('name', 'symbol', 'attack', 'health', 'energy')


class AddUnit(Node):
    kind = 'add_unit'
    fields = ('type_name', 'name', 'x', 'y')


class LoadBoard(Node):
    kind = 'load_board'
    fields = ('path',)


class LoadPlayer(Node):
    kind = 'load_player'
    fields = ('path',)


class Move(Node):
    kind = 'move'
    fields = ('unit', 'direction')
