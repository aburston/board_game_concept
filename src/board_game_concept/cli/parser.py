"""Reading a line of input as a command.

A recursive descent parser over the grammar in `grammar.py`. Today's grammar is
flat - a verb, sometimes a subject, then arguments - so nothing here descends
into itself yet. It is written this way because the grammar is going to grow
statements that contain other statements, and a dispatch table would have to be
thrown away to get there.

The parser knows about shapes, not about games: how many arguments a command
takes, whether they are numbers, whether a word is one of the directions. It
never asks whose turn it is, whether a square is free, or whether a player owns
a unit. Those are the service layer's to answer, and keeping them out of here
is what lets the same parser serve a caller that is not a terminal.
"""

from ..service import commands
from .grammar import DIRECTIONS, SHOW_FORMAT, SHOW_SUBJECTS

INVALID_COMMAND = 'invalid command'


class ParseError(Exception):
    """A line that is not a command, with the message to show for it."""

    def __init__(self, message, column=None):
        super().__init__(message)
        self.message = message
        self.column = column


class _Tokens:
    """The words of one line, read left to right."""

    def __init__(self, words):
        self.words = words
        self.position = 0

    def peek(self):
        if self.position < len(self.words):
            return self.words[self.position]
        return None

    def take(self):
        word = self.peek()
        if word is not None:
            self.position += 1
        return word

    def at_end(self):
        return self.position >= len(self.words)

    def remaining(self):
        return len(self.words) - self.position


class Parser:
    def __init__(self, line):
        self.tokens = _Tokens(line.split())

    # --- the grammar itself

    def _verbs(self):
        """The words a command can start with, and what reads each.

        Named one by one rather than looked up by building a method name from
        the word typed: that made every `_parse_x` helper reachable as a verb,
        so `add_player 1` was quietly accepted as a command the grammar does
        not contain, and adding a helper would have invented another.
        """
        return {
            'help': self._parse_help,
            'exit': self._parse_exit,
            'reload': self._parse_reload,
            'commit': self._parse_commit,
            'show': self._parse_show,
            'set': self._parse_set,
            'add': self._parse_add,
            'remove': self._parse_remove,
            'load': self._parse_load,
            'move': self._parse_move,
        }

    def parse(self):
        """The command this line asks for, or None if the line is blank."""
        verb = self.tokens.peek()
        if verb is None:
            return None
        parse_verb = self._verbs().get(verb)
        if parse_verb is None:
            raise ParseError(INVALID_COMMAND, self.tokens.position)
        self.tokens.take()
        return parse_verb()

    def _parse_help(self):
        return commands.Help()

    def _parse_exit(self):
        return commands.Exit()

    def _parse_reload(self):
        return commands.Reload()

    def _parse_commit(self):
        return commands.Commit()

    def _parse_show(self):
        subject = self.tokens.take()
        if subject not in SHOW_SUBJECTS:
            raise ParseError('invalid show command', self.tokens.position)
        # `json` is the one word that may follow a subject. Everything else
        # used to be ignored, which meant a mistyped `show units jsno` quietly
        # printed the table the player had not asked for
        show_format = 'table'
        if not self.tokens.at_end():
            word = self.tokens.take()
            if word != SHOW_FORMAT or not self.tokens.at_end():
                raise ParseError('invalid show command', self.tokens.position)
            show_format = SHOW_FORMAT
        return commands.Show(subject=subject, format=show_format)

    def _parse_set(self):
        subject = self._subject('set', ('board', 'flag'))
        if subject == 'board':
            return self._parse_set_board()
        if subject == 'flag':
            return self._parse_set_flag()
        raise ParseError('invalid set command', self.tokens.position)

    def _parse_set_flag(self):
        """`set flag <unit>`, during setup: which unit carries your flag."""
        self._arity(1, 'must provide the name of one of your units')
        return commands.SetFlag(unit=self.tokens.take())

    def _parse_set_board(self):
        self._arity(2, 'must provide x and y for size')
        size_x = self._integer('x and y must be a numbers')
        size_y = self._integer('x and y must be a numbers')
        return commands.SetBoard(size_x=size_x, size_y=size_y)

    def _parse_add(self):
        subject = self._subject('add', ('player', 'type', 'unit'))
        return {
            'player': self._parse_add_player,
            'type': self._parse_add_type,
            'unit': self._parse_add_unit,
        }[subject]()

    def _parse_add_player(self):
        """`add player <number> [<budget>]`.

        The budget is optional: left out, the player is registered with the
        default. It is read here rather than left to the service layer so that
        a word that is not a number is a parse error naming the budget, the
        same as every other number the grammar takes.
        """
        if self.tokens.remaining() not in (1, 2):
            raise ParseError(
                'must provide a player number and an optional budget',
                self.tokens.position)
        number = self._integer('player number must be a number')
        if self.tokens.at_end():
            return commands.AddPlayer(number=number)
        return commands.AddPlayer(
            number=number,
            budget=self._integer('budget must be a number'))

    def _parse_remove(self):
        subject = self._subject('remove', ('player',))
        if subject == 'player':
            return self._parse_remove_player()
        raise ParseError('invalid remove command', self.tokens.position)

    def _parse_remove_player(self):
        """`remove player <number>`, while setup is still being decided."""
        self._arity(1, 'must provide a player number')
        return commands.RemovePlayer(
            number=self._integer('player number must be a number'))

    def _parse_add_type(self):
        self._arity(5, 'must provide 5 args for type')
        name = self.tokens.take()
        symbol = self.tokens.take()
        attack = self._integer('attack, health and energy must be numbers')
        health = self._integer('attack, health and energy must be numbers')
        energy = self._integer('attack, health and energy must be numbers')
        return commands.AddType(name=name, symbol=symbol, attack=attack,
                                health=health, energy=energy)

    def _parse_add_unit(self):
        self._arity(4, 'must provide 4 args for unit')
        type_name = self.tokens.take()
        name = self.tokens.take()
        x = self._integer('x and y must be numbers')
        y = self._integer('x and y must be numbers')
        return commands.AddUnit(type_name=type_name, name=name, x=x, y=y)

    def _parse_load(self):
        subject = self._subject('load', ('board', 'player'))
        self._arity(1, f'must provide 1 args for load {subject}')
        path = self.tokens.take()
        if subject == 'board':
            return commands.LoadBoard(path=path)
        return commands.LoadPlayer(path=path)

    def _parse_move(self):
        self._arity(2, 'must provide 2 args for move')
        unit = self.tokens.take()
        word = self.tokens.take()
        if word not in DIRECTIONS:
            raise ParseError(f'invalid direction {word}', self.tokens.position)
        return commands.Move(unit=unit, direction=DIRECTIONS[word])

    # --- terminals

    def _subject(self, verb, allowed):
        subject = self.tokens.take()
        if subject not in allowed:
            raise ParseError(f'invalid {verb} command', self.tokens.position)
        return subject

    def _arity(self, expected, message):
        if self.tokens.remaining() != expected:
            raise ParseError(message, self.tokens.position)

    def _integer(self, message):
        word = self.tokens.take()
        try:
            return int(word)
        except (TypeError, ValueError):
            raise ParseError(message, self.tokens.position) from None


def parse(line):
    """The command this line asks for, or None if it is blank."""
    return Parser(line).parse()
