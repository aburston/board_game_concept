"""The macro language a program is written in, and the expansion of it.

A unit program is register assembly, and register assembly reads badly:
`MOV r6, r0` says nothing about what r6 is for, and `SUB r0, 2` hides that 2
means "a friend" on the map. This module puts a preprocessor in front of the
parser, in the style of the C preprocessor - the one most people who have
read any already know - so that a program can name its registers and its
numbers and wrap a recurring idiom in a readable inline "function". It is a
cut-down version: `#define`, `#undef`, `#ifdef`, `#ifndef`, `#else`,
`#endif`, `#error`, `##` and `#include` of the headers the game itself holds.
No `#if` with an expression, no stringising, no files.

Two things differ from C, both forced by an assembly with one instruction a
line. A `#define` body continued with `\\` expands to one line per physical
line of the body, not to one long line, which is how a macro stands for
several instructions. And a label written `@name` in a body is private to
each use of the macro - rewritten to a name no player can write - so that a
macro may branch without clashing with itself when it is used twice.

Expansion is a pure function of the text: it reads no file (an `#include`
names a header this module holds, never a path), no clock and no environment,
which is what the game's invariant - a turn is a pure function of the board
and the orders - requires of anything between a program's text and the
instructions that run. Every expanded line remembers the source line it came
from and the macro that produced it, so that a refusal, a listing and a halt
all speak of the text the player wrote.
"""

import re
from collections import namedtuple

# the most instructions an expansion may hold, and the most tokens one
# expanded line may hold, and how deep a macro may expand within a macro.
# Generous - the longest default program expands to under a hundred lines -
# and there to stop a program making the commit path or the check endpoint
# do unbounded work. A macro is never expanded inside its own expansion, as
# in C, so these catch fan-out, not recursion
MAX_LINES = 4096
MAX_LINE_TOKENS = 4096
MAX_DEPTH = 64

# what a label a macro's `@name` becomes: no player can write it, because `@`
# is refused outside a macro body and a name beginning `_m<digit>` is reserved
_PRIVATE = '_m{n}_{name}'
_RESERVED = re.compile(r'^_m\d')

_TOKEN = re.compile(r'\s+|##|@?[A-Za-z_][\w-]*|-?\d+|.')
_NAME = re.compile(r'^[A-Za-z_]\w*$')
_DIRECTIVE = re.compile(r'^#\s*(\w+)\s*(.*)$', re.S)
_FUNCTION_DEFINE = re.compile(r'^([A-Za-z_]\w*)\((.*?)\)\s*(.*)$', re.S)
_OBJECT_DEFINE = re.compile(r'^([A-Za-z_]\w*)\s*(.*)$', re.S)
_INCLUDE = re.compile(r'^<([\w.]+)>$')


class ProgramError(ValueError):
    """A program the machine will not accept, naming the line."""

    def __init__(self, line, message):
        self.line = line
        self.message = message
        super().__init__(f"line {line}: {message}")


# one expanded line: the source line it came from, the outermost macro that
# produced it (None for a line the player wrote with nothing expanded in it)
# and its text with the comment removed
Expanded = namedtuple('Expanded', 'line macro text')

Macro = namedtuple('Macro', 'name params lines line')


# ---------------------------------------------------------------- tokens

def _tokens(text):
    """A line's tokens, whitespace included, so that joining them back gives
    the line again."""
    return _TOKEN.findall(text)


def _is_word(token):
    return bool(token) and (token[0].isalpha() or token[0] in '_@')


def _strip(tokens):
    """Tokens without leading and trailing whitespace."""
    start, end = 0, len(tokens)
    while start < end and tokens[start].isspace():
        start += 1
    while end > start and tokens[end - 1].isspace():
        end -= 1
    return tokens[start:end]


def _text(tokens):
    return ''.join(tokens).strip()


def _normal(tokens):
    """A line's tokens with its whitespace collapsed, for comparing bodies."""
    return ' '.join(token for token in tokens if not token.isspace())


def _comment_free(raw):
    """A line without its `;` comment."""
    return raw.split(';', 1)[0]


# ----------------------------------------------------------- the headers

# the headers a program may include, by the name it includes them under.
# Plain text in the language itself, held here and nowhere else, so that an
# `#include` reads nothing but this table. Every helper expands to exactly
# the instructions written beside it, so a program using one costs what the
# same program written out costs; a helper that writes registers says which
UNIT_H = """\
; unit.h - names for the machine, so a program can say what it means.
;
; Every helper here expands to exactly the instructions named beside it, so
; using one costs what writing it out costs. A helper that writes registers
; says which; the sensors write the ones SELF, FLAG, NEAREST and MAP write.

; where MOVE goes, as the numbers a register may hold
#define NORTH 1
#define EAST 2
#define SOUTH 3
#define WEST 4

; what MAP answers in SEEN about a square
#define UNKNOWN 0
#define EMPTY 1
#define FRIEND 2
#define ENEMY 3
#define OFF_BOARD 4

; what SELF writes
#define MY_X r0
#define MY_Y r1
#define MY_HEALTH r2
#define MY_ENERGY r3
#define HAVE_FLAG r4
#define MY_NUMBER r5

; what FLAG and NEAREST write: a square and how far, or -1 for none
#define FOUND_X r0
#define FOUND_Y r1
#define FOUND_DIST r2

; what MAP writes: the kind of square, when it was last known, and the
; attack and health of an enemy met there
#define SEEN r0
#define SEEN_TURN r1
#define SEEN_ATTACK r2
#define SEEN_HEALTH r3

; what RECV writes: 1 if a message was read, and its three words
#define GOT_MESSAGE r0
#define WORD1 r1
#define WORD2 r2
#define WORD3 r3

; branching: one JIF each
#define GOTO(where) JMP where
#define IF_ZERO(r, where) JIF zero r, where
#define IF_NONZERO(r, where) JIF notzero r, where
#define IF_NEG(r, where) JIF neg r, where
#define IF_POS(r, where) JIF pos r, where
#define IF_EQ(a, b, where) JIF eq a, b, where
#define IF_BELOW(a, b, where) JIF lt a, b, where
#define IF_NONE(r, where) JIF neg r, where
#define IF_FOUND(r, where) JIF pos r, where

; what my map says of the square (x, y): SEEN, with SEEN_TURN and the
; enemy's SEEN_ATTACK and SEEN_HEALTH
#define LOOK_AT(x, y) MAP x, y

; after LOOK_AT: off to `where` if the square is of `kind` - UNKNOWN, EMPTY,
; FRIEND, ENEMY or OFF_BOARD. Writes SEEN_TURN
#define IF_SEEN(kind, where) SET SEEN_TURN, kind \\
    JIF eq SEEN, SEEN_TURN, where

; acting: a step and the end of the turn, a hold, or a rest
#define STEP(dir) MOVE dir \\
    HALT
#define STAY HOLD \\
    HALT
#define REST SLEEP 1
#define REST_LONG SLEEP 100

; SELF, then off to `where` unless MY_ENERGY covers `need`. Writes r0-r5
; as SELF does and leaves MY_ENERGY less `need`
#define UNLESS_AFFORD(need, where) SELF \\
    SUB MY_ENERGY, need \\
    JIF neg MY_ENERGY, where

; the direction number for a step along the row by way_x (-1 west, 1 east)
; or down the column by way_y (-1 north, 1 south), into `into`
#define ROW_STEP(way_x, into) SET into, 3 \\
    SUB into, way_x
#define COLUMN_STEP(way_y, into) SET into, 2 \\
    ADD into, way_y
"""

HEADERS = {'unit.h': UNIT_H}


# ----------------------------------------------------------- expansion

class _Expander:
    """One expansion of one program's text, line by line."""

    def __init__(self, headers):
        self.headers = headers
        self.macros = {}
        self.included = set()
        self.out = []
        self.uses = 0
        # lines produced so far, counted as they are made rather than when
        # they are kept, so that a fan-out is stopped early, not expanded
        # in full and then refused
        self.produced = 0
        # the conditional stack: (line of the #if, keeping, seen #else)
        self.conditions = []

    # -- the directives

    def directive(self, raw, number, source):
        found = _DIRECTIVE.match(raw.strip())
        if not found:
            raise ProgramError(number, "a line beginning # is a directive")
        name, rest = found.group(1), found.group(2).strip()
        if name in ('ifdef', 'ifndef'):
            if not _NAME.match(rest):
                raise ProgramError(number, f"#{name} takes a name")
            keeping = self.keeping() and ((rest in self.macros)
                                          == (name == 'ifdef'))
            self.conditions.append([number, keeping, False])
            return
        if name == 'else':
            if not self.conditions or self.conditions[-1][2]:
                raise ProgramError(number, "#else without #ifdef")
            top = self.conditions[-1]
            outer = all(keep for _line, keep, _seen in self.conditions[:-1])
            top[1] = outer and not top[1]
            top[2] = True
            return
        if name == 'endif':
            if not self.conditions:
                raise ProgramError(number, "#endif without #ifdef")
            self.conditions.pop()
            return
        if not self.keeping():
            return
        if name == 'define':
            self.define(rest, number)
        elif name == 'undef':
            if not _NAME.match(rest):
                raise ProgramError(number, "#undef takes a name")
            self.macros.pop(rest, None)
        elif name == 'error':
            raise ProgramError(number, rest or "#error")
        elif name == 'include':
            self.include(rest, number, source)
        else:
            raise ProgramError(number, f"#{name} is not a directive")

    def keeping(self):
        return all(keep for _line, keep, _seen in self.conditions)

    def define(self, rest, number):
        found = _FUNCTION_DEFINE.match(rest)
        if found:
            name, params, body = found.groups()
            params = [param.strip() for param in params.split(',')]
            if params == ['']:
                params = []
            for param in params:
                if not _NAME.match(param):
                    raise ProgramError(
                        number, f"{param!r} is not a parameter name")
            if len(set(params)) != len(params):
                raise ProgramError(number, "a parameter is named twice")
        else:
            found = _OBJECT_DEFINE.match(rest)
            if not found:
                raise ProgramError(number, "#define takes a name")
            name, body = found.groups()
            params = None
        lines = [_strip(_tokens(line)) for line in body.split('\n')]
        for tokens in lines:
            for token in tokens:
                if _is_word(token) and _RESERVED.match(token):
                    raise ProgramError(
                        number, f"names beginning _m<digit> are reserved")
        macro = Macro(name, params, lines, number)
        held = self.macros.get(name)
        if held is not None and not self.same(held, macro):
            raise ProgramError(
                number, f"{name} is already defined, at line {held.line}; "
                        f"#undef it first")
        self.macros[name] = macro

    @staticmethod
    def same(a, b):
        return (a.params == b.params
                and [_normal(line) for line in a.lines]
                == [_normal(line) for line in b.lines])

    def include(self, rest, number, source):
        found = _INCLUDE.match(rest)
        if not found:
            raise ProgramError(
                number, "#include takes a header the game holds, as "
                        "<unit.h>; it never reads a file")
        name = found.group(1)
        if name not in self.headers:
            raise ProgramError(number, f"there is no header <{name}>")
        if name in self.included:
            return
        self.included.add(name)
        self.lines(self.headers[name], number, body=True)

    # -- the lines

    def lines(self, text, at=None, body=False):
        """Expand a text's lines. `at` is the source line every line of it
        is attributed to - a header's lines belong to the #include line -
        and `body` says `@` labels are allowed, as they are in a header."""
        pending = []
        start = None
        for number, raw in enumerate(text.splitlines(), 1):
            source = number if at is None else at
            line = _comment_free(raw)
            if pending or line.lstrip().startswith('#'):
                stripped = line.rstrip()
                if pending:
                    pending.append(stripped[:-1] if stripped.endswith('\\')
                                   else stripped)
                else:
                    start = source
                    pending = [stripped[:-1] if stripped.endswith('\\')
                               else stripped]
                if stripped.endswith('\\'):
                    continue
                self.directive('\n'.join(pending), start, source)
                pending = []
                continue
            if not self.keeping():
                continue
            if not line.strip():
                continue
            self.line(line, source, body)
        if pending:
            raise ProgramError(start, "a directive ends in \\ with no "
                                      "line to continue onto")

    def line(self, line, source, body):
        tokens = _tokens(line)
        for token in tokens:
            if _is_word(token):
                if token[0] == '@' and not body:
                    raise ProgramError(
                        source, f"{token}: a label beginning @ belongs in a "
                                f"macro body")
                if _RESERVED.match(token):
                    raise ProgramError(
                        source, f"{token}: names beginning _m<digit> are "
                                f"reserved")
        for expanded, macro in self.expand(tokens, frozenset(), 0, source):
            text = _text(expanded)
            if not text:
                continue
            if len(self.out) >= MAX_LINES:
                raise ProgramError(
                    source, f"the program expands to more than {MAX_LINES} "
                            f"lines")
            self.out.append(Expanded(source, macro, text))
        self.produced = len(self.out)

    def expand(self, tokens, hidden, depth, source):
        """Expand one line's tokens into one or more lines, as (tokens,
        macro) pairs, `macro` naming the outermost macro that produced the
        line or None."""
        if depth > MAX_DEPTH:
            raise ProgramError(
                source, f"macros nest deeper than {MAX_DEPTH}")
        lines = []
        current = []
        tag = [None]
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if len(current) > MAX_LINE_TOKENS:
                raise ProgramError(
                    source, f"a line expands to more than {MAX_LINE_TOKENS} "
                            f"tokens")
            macro = (self.macros.get(token)
                     if _is_word(token) and token not in hidden else None)
            if macro is None:
                current.append(token)
                index += 1
                continue
            if macro.params is None:
                args = None
                index += 1
            else:
                index, args = self.arguments(tokens, index + 1, macro,
                                             source)
                if args is None:
                    # a function-like macro's name with no ( after it is
                    # just a word, as in C
                    current.append(token)
                    continue
                args = [self.argument(arg, hidden, depth, source)
                        for arg in args]
            body = self.body(macro, args, source)
            produced = []
            for body_line in body:
                produced.extend(self.expand(body_line, hidden | {macro.name},
                                            depth + 1, source))
            if tag[0] is None:
                tag[0] = macro.name
            if not produced:
                continue
            first, *rest = produced
            current.extend(first[0])
            for line_tokens, _tag in rest:
                self.count(source)
                lines.append((current, tag[0]))
                current = list(line_tokens)
        lines.append((current, tag[0]))
        return lines

    def count(self, source):
        self.produced += 1
        if self.produced > MAX_LINES:
            raise ProgramError(
                source, f"the program expands to more than {MAX_LINES} "
                        f"lines")

    def arguments(self, tokens, index, macro, source):
        """The arguments of a function-like macro use starting at `index`,
        and where the use ends; (index, None) if no ( follows the name."""
        at = index
        while at < len(tokens) and tokens[at].isspace():
            at += 1
        if at >= len(tokens) or tokens[at] != '(':
            return index, None
        at += 1
        depth = 0
        args = [[]]
        while at < len(tokens):
            token = tokens[at]
            if token == '(':
                depth += 1
            elif token == ')':
                if depth == 0:
                    found = [_strip(arg) for arg in args]
                    if found == [[]]:
                        found = []
                    if len(found) != len(macro.params):
                        raise ProgramError(
                            source, f"{macro.name} takes "
                                    f"{len(macro.params)} argument(s), "
                                    f"not {len(found)}")
                    return at + 1, found
                depth -= 1
            elif token == ',' and depth == 0:
                args.append([])
                at += 1
                continue
            args[-1].append(token)
            at += 1
        raise ProgramError(source, f"{macro.name}( is never closed")

    def argument(self, tokens, hidden, depth, source):
        """An argument, expanded before it is substituted, as C does."""
        produced = self.expand(tokens, hidden, depth + 1, source)
        if len(produced) != 1:
            raise ProgramError(
                source, "a macro argument may not expand to more than one "
                        "line")
        return produced[0][0]

    def body(self, macro, args, source):
        """The macro's body lines with its private labels made private to
        this use, its parameters replaced and its ## pasted."""
        self.uses += 1
        n = self.uses
        by_name = (dict(zip(macro.params, args))
                   if macro.params is not None else {})
        lines = []
        for body_line in macro.lines:
            tokens = []
            for token in body_line:
                if _is_word(token) and token[0] == '@':
                    tokens.append(_PRIVATE.format(n=n, name=token[1:]))
                elif token in by_name:
                    tokens.extend(by_name[token])
                else:
                    tokens.append(token)
            lines.append(self.paste(tokens, source))
        return lines

    @staticmethod
    def paste(tokens, source):
        """Join the tokens either side of each ## into one."""
        if '##' not in tokens:
            return tokens
        out = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token != '##':
                out.append(token)
                index += 1
                continue
            while out and out[-1].isspace():
                out.pop()
            index += 1
            while index < len(tokens) and tokens[index].isspace():
                index += 1
            if not out or index >= len(tokens):
                raise ProgramError(source, "## needs a token on each side")
            out[-1] = out[-1] + tokens[index]
            index += 1
        return out

    def finish(self):
        if self.conditions:
            raise ProgramError(self.conditions[0][0],
                               "#ifdef is never closed by #endif")
        return self.out


def expand(text, headers=None):
    """A program's text expanded: a list of `Expanded(line, macro, text)`,
    one per instruction or label line the machine will read, in order.

    `headers` is what `#include` may name; the game's own by default.
    """
    expander = _Expander(HEADERS if headers is None else headers)
    expander.lines(text or '')
    return expander.finish()
