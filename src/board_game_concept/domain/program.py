"""The controller a unit runs: its program, and the machine that runs it.

A unit type carries a program; every unit of the type runs it, once a turn,
against what its army knows. The program is a list of instructions for a
small register machine - eight registers, a memory of words, a handful of
sensors that read the army's map and a handful of actuators that give the
unit's order, speak on the radio or send it to sleep. Every instruction has
one tick cost, stated in `TICKS` and nowhere else, and a unit pays for its
ticks in energy through a meter sized by its compute statistic.

Three things make this safe for the invariant that a turn is a pure function
of the board and the orders (R1.2). Nothing here reads anything but the
snapshot it is handed, the unit's own memory and inbox: no clock, no random
number, no object identity. Every "nearest" is settled by distance, then the
row nearer the seat's own edge, then the lower x - the same rule read from
either end of the board, so that a mirror comes out a mirror. And the ticks
an instruction costs never depend on
what it returns, so a program's bill is the same on every board.
"""

import re
from collections import namedtuple

# the longest a unit may sleep in one order. Without a bound a program could
# switch a unit off for the whole game for the price of one tick; with it a
# unit looks at the board at least this often, paying another tick to sleep
# again, which is what "no free compute" means for a unit that would rather
# not think
MAX_SLEEP = 100

# every instruction, and what it costs. One row each: this table is the
# tariff, and a player reads their program's price off it line by line
TICKS = {
    'SELF': 1, 'TURN': 1, 'EXTENT': 1,
    'FLAG': 2, 'CONTACT': 2,
    'MAP': 3, 'NEAREST': 4,
    'RECV': 2, 'FLUSH': 1,
    'SET': 1, 'MOV': 1, 'ADD': 1, 'SUB': 1, 'ABS': 1, 'SIGN': 1, 'DIST': 1,
    'LOAD': 1, 'STORE': 1,
    'JMP': 1, 'JIF': 1, 'HALT': 0,
    'MOVE': 1, 'HOLD': 1, 'SAY': 5, 'SLEEP': 1,
}

# ticks of thinking one energy buys, per point of compute; also the cap on
# ticks in one turn, per point of compute, so a turn's thinking never costs
# more than one energy
TICKS_PER_COMPUTE = 10

DIRECTIONS = {'north': 1, 'east': 2, 'south': 3, 'west': 4}

# what `MAP` answers in r0
MAP_UNKNOWN, MAP_EMPTY, MAP_FRIEND, MAP_ENEMY, MAP_OFF = 0, 1, 2, 3, 4

# the conditions `JIF` tests, and how many registers each names
CONDITIONS = {'zero': 1, 'notzero': 1, 'neg': 1, 'pos': 1, 'eq': 2, 'lt': 2}

REGISTERS = 8

_REGISTER = re.compile(r'^r([0-7])$')
_INTEGER = re.compile(r'^-?\d+$')
_LABEL = re.compile(r'^[A-Za-z_][\w-]*$')
_LABEL_LINE = re.compile(r'^([A-Za-z_][\w-]*):\s*(.*)$')


class ProgramError(ValueError):
    """A program the machine will not accept, naming the line."""

    def __init__(self, line, message):
        self.line = line
        self.message = message
        super().__init__(f"line {line}: {message}")


Instruction = namedtuple('Instruction', 'op args line')


def _operand(token, line):
    """One operand, typed: a register, an integer, or a word."""
    found = _REGISTER.match(token)
    if found:
        return ('reg', int(found.group(1)))
    if _INTEGER.match(token):
        return ('int', int(token))
    return ('word', token)


def _want(args, kinds, op, line):
    """Check an instruction's operands against the kinds it takes.

    `kinds` is a list of sets of accepted operand kinds, one per operand.
    """
    if len(args) != len(kinds):
        raise ProgramError(line, f"{op} takes {len(kinds)} operand(s), "
                                 f"not {len(args)}")
    for index, (arg, accepted) in enumerate(zip(args, kinds)):
        if arg[0] not in accepted:
            raise ProgramError(
                line, f"operand {index + 1} of {op} must be "
                      f"{' or '.join(sorted(accepted))}, not {arg[1]!r}")


REG = {'reg'}
INT = {'int'}
REG_OR_INT = {'reg', 'int'}
WORD = {'word'}


def _check(op, args, line):
    """Refuse an instruction the set does not accept, naming the line."""
    if op not in TICKS:
        raise ProgramError(line, f"{op} is not an instruction")
    if op in ('SELF', 'TURN', 'EXTENT', 'CONTACT', 'RECV', 'FLUSH', 'HOLD',
              'HALT'):
        _want(args, [], op, line)
    elif op == 'FLAG':
        _want(args, [WORD], op, line)
        if args[0][1] not in ('mine', 'enemy'):
            raise ProgramError(line, "FLAG takes mine or enemy")
    elif op == 'NEAREST':
        _want(args, [WORD], op, line)
        if args[0][1] not in ('friend', 'enemy', 'unknown'):
            raise ProgramError(line, "NEAREST takes friend, enemy or unknown")
    elif op in ('MAP', 'MOV', 'DIST'):
        _want(args, [REG, REG], op, line)
    elif op == 'SET':
        _want(args, [REG, INT], op, line)
    elif op in ('ADD', 'SUB', 'LOAD', 'STORE'):
        _want(args, [REG, REG_OR_INT], op, line)
    elif op in ('ABS', 'SIGN'):
        _want(args, [REG], op, line)
    elif op == 'JMP':
        _want(args, [WORD], op, line)
    elif op == 'JIF':
        if not args or args[0][0] != 'word' or args[0][1] not in CONDITIONS:
            raise ProgramError(
                line, "JIF takes a condition: zero, notzero, neg, pos, eq "
                      "or lt")
        arity = CONDITIONS[args[0][1]]
        _want(args, [WORD] + [REG] * arity + [WORD], op, line)
    elif op == 'MOVE':
        _want(args, [{'reg', 'word'}], op, line)
        if args[0][0] == 'word' and args[0][1] not in DIRECTIONS:
            raise ProgramError(
                line, "MOVE takes north, east, south, west or a register")
    elif op == 'SAY':
        _want(args, [WORD, REG_OR_INT, REG_OR_INT, REG_OR_INT], op, line)
    elif op == 'SLEEP':
        _want(args, [INT], op, line)
        if not 1 <= args[0][1] <= MAX_SLEEP:
            raise ProgramError(
                line, f"SLEEP takes a number from 1 to {MAX_SLEEP}")


def _parse(text):
    """The instructions and labels of a program's text."""
    instructions = []
    labels = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        found = _LABEL_LINE.match(line)
        if found:
            label, line = found.group(1), found.group(2).strip()
            if label in labels:
                raise ProgramError(number, f"label {label} is defined twice")
            labels[label] = len(instructions)
            if not line:
                continue
        parts = [part for part in re.split(r'[\s,]+', line) if part]
        op = parts[0].upper()
        args = [_operand(part, number) for part in parts[1:]]
        if op == 'SAY' and args:
            # the recipient is a unit's name, whatever it looks like: a unit
            # called `r1` is addressed by that name, not by a register
            args[0] = ('word', parts[1])
        _check(op, args, number)
        instructions.append(Instruction(op, tuple(args), number))
    for instruction in instructions:
        if instruction.op in ('JMP', 'JIF'):
            target = instruction.args[-1][1]
            if target not in labels:
                raise ProgramError(instruction.line,
                                   f"no label called {target}")
    return instructions, labels


class Program:
    """A parsed program: what a type carries and every unit of it runs."""

    def __init__(self, text):
        self.text = text if text is not None else ''
        self.instructions, self.labels = _parse(self.text)

    def __len__(self):
        return len(self.instructions)

    def __eq__(self, other):
        return isinstance(other, Program) and other.text == self.text

    def __hash__(self):
        return hash(self.text)

    @property
    def ticks(self):
        """What a straight run through the program costs."""
        return sum(TICKS[instruction.op] for instruction in self.instructions)

    def listing(self):
        """Each source line with the ticks it costs, for a player to read."""
        by_line = {instruction.line: TICKS[instruction.op]
                   for instruction in self.instructions}
        return [(number, raw, by_line.get(number))
                for number, raw in enumerate(self.text.splitlines(), 1)]


def cap(compute):
    """The ticks a turn's thinking may spend, and the meter's capacity."""
    return TICKS_PER_COMPUTE * compute


class Snapshot:
    """What every controller of one army reads: the turn as it began.

    Built once per army per turn by the board, before any controller runs, so
    that no controller sees another's order, message or move from the same
    turn. `friends` maps each standing friendly unit's name to its square;
    `flags` maps each player with a standing carrier to its square; `army_map`
    is the army's shared knowledge of the board; `edge` is the row of the
    seat's own edge of the board - 0 for the player placed nearer row 0, the
    last row for the other - which is what a tie for the nearest square is
    settled towards, so that the two seats of a mirror make mirrored choices.
    """

    def __init__(self, turn, size_x, size_y, player, friends, flags,
                 army_map, edge=0):
        self.turn = turn
        self.size_x = size_x
        self.size_y = size_y
        self.player = player
        self.friends = dict(friends)
        self.flags = dict(flags)
        self.army_map = army_map
        self.edge = edge
        self.friend_squares = set(self.friends.values())

    def on_board(self, x, y):
        return 0 <= x < self.size_x and 0 <= y < self.size_y

    def flag_mine(self):
        return self.flags.get(self.player)

    def flag_enemy(self, origin):
        squares = [square for number, square in self.flags.items()
                   if number != self.player]
        return nearest_of(squares, origin, self.edge)

    def map_at(self, x, y):
        """`(kind, turn, attack, health)` for a square."""
        if not self.on_board(x, y):
            return (MAP_OFF, -1, -1, -1)
        if (x, y) in self.friend_squares:
            return (MAP_FRIEND, self.turn, -1, -1)
        return self.army_map.at(x, y, self.turn)

    def nearest(self, kind, origin):
        """`(x, y, distance)` of the nearest square of a kind, or None."""
        if kind == 'friend':
            squares = [square for square in self.friend_squares
                       if square != origin]
            found = nearest_of(squares, origin, self.edge)
            return found and (found[0], found[1], distance(found, origin))
        if kind == 'enemy':
            found = nearest_of(self.army_map.enemy_squares(), origin,
                               self.edge)
            return found and (found[0], found[1], distance(found, origin))
        # unknown: every square the army has nothing on, settled by the
        # same tie-break as everywhere else
        squares = [(x, y) for y in range(self.size_y)
                   for x in range(self.size_x)
                   if (x, y) not in self.friend_squares
                   and self.army_map.at(x, y, self.turn)[0] == MAP_UNKNOWN]
        found = nearest_of(squares, origin, self.edge)
        return found and (found[0], found[1], distance(found, origin))


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def nearest_of(squares, origin, edge=0):
    """The nearest square to an origin, ties going to the row nearer the
    seat's own edge of the board, then the lower x."""
    best = None
    for square in squares:
        key = (distance(square, origin), abs(square[1] - edge), square[0])
        if best is None or key < best[0]:
            best = (key, square)
    return None if best is None else best[1]


class Result:
    """What one run of a controller did, for the turn and for the trace."""

    def __init__(self):
        self.order = None          # None, 'hold', or a direction 1..4
        self.said = []             # (to, w1, w2, w3)
        self.sleep = None          # turns to sleep, or None
        self.ticks = 0
        self.halted = None         # the line it stopped at, or None
        self.charged = 0           # energy the meter took
        self.meter = 0             # the meter after the run


def run(program, snapshot, me, contact, memory, inbox, compute, energy,
        meter):
    """Run a unit's program once, against a snapshot. Returns a `Result`.

    `me` is the unit's own state as a dict (x, y, health, energy, flag,
    number); `contact` is the enemy this unit fought last turn as (x, y,
    attack, health) or None; `memory` is the unit's own word store and is
    written in place; `inbox` is its list of (w1, w2, w3) and is consumed in
    place. The meter is advanced and the energy it charges returned; the
    caller deducts it.
    """
    result = Result()
    limit = cap(compute)
    if limit <= 0 or program is None or not program.instructions:
        result.meter = meter
        return result
    registers = [0] * REGISTERS
    instructions = program.instructions
    pc = 0

    def value(arg):
        return registers[arg[1]] if arg[0] == 'reg' else arg[1]

    while 0 <= pc < len(instructions):
        instruction = instructions[pc]
        op, args = instruction.op, instruction.args
        cost = TICKS[op]
        if result.ticks + cost > limit:
            result.halted = instruction.line
            break
        if (meter + result.ticks + cost) // limit > energy:
            result.halted = instruction.line
            break
        result.ticks += cost
        pc += 1

        if op == 'SELF':
            registers[0], registers[1] = me['x'], me['y']
            registers[2], registers[3] = me['health'], me['energy']
            registers[4] = 1 if me['flag'] else 0
            registers[5] = me['number']
        elif op == 'TURN':
            registers[0] = snapshot.turn
        elif op == 'EXTENT':
            registers[0], registers[1] = snapshot.size_x, snapshot.size_y
        elif op == 'FLAG':
            square = (snapshot.flag_mine() if args[0][1] == 'mine'
                      else snapshot.flag_enemy((me['x'], me['y'])))
            registers[0], registers[1] = square if square else (-1, -1)
        elif op == 'MAP':
            kind, seen, attack, health = snapshot.map_at(value(args[0]),
                                                         value(args[1]))
            registers[0], registers[1] = kind, seen
            registers[2], registers[3] = attack, health
        elif op == 'NEAREST':
            found = snapshot.nearest(args[0][1], (me['x'], me['y']))
            registers[0], registers[1], registers[2] = found or (-1, -1, -1)
        elif op == 'CONTACT':
            if contact is None:
                registers[0] = -1
            else:
                registers[0], registers[1] = contact[0], contact[1]
                registers[2], registers[3] = contact[2], contact[3]
        elif op == 'RECV':
            if inbox:
                words = inbox.pop(0)
                registers[0] = 1
                registers[1], registers[2], registers[3] = words
            else:
                registers[0] = 0
        elif op == 'FLUSH':
            del inbox[:]
        elif op == 'SET' or op == 'MOV':
            registers[args[0][1]] = value(args[1])
        elif op == 'ADD':
            registers[args[0][1]] += value(args[1])
        elif op == 'SUB':
            registers[args[0][1]] -= value(args[1])
        elif op == 'ABS':
            registers[args[0][1]] = abs(registers[args[0][1]])
        elif op == 'SIGN':
            held = registers[args[0][1]]
            registers[args[0][1]] = (held > 0) - (held < 0)
        elif op == 'DIST':
            registers[0] = distance((value(args[0]), value(args[1])),
                                    (me['x'], me['y']))
        elif op == 'LOAD':
            registers[args[0][1]] = memory.get(value(args[1]), 0)
        elif op == 'STORE':
            memory[value(args[1])] = registers[args[0][1]]
        elif op == 'JMP':
            pc = program.labels[args[0][1]]
        elif op == 'JIF':
            cond = args[0][1]
            a = registers[args[1][1]]
            if cond == 'zero':
                true = a == 0
            elif cond == 'notzero':
                true = a != 0
            elif cond == 'neg':
                true = a < 0
            elif cond == 'pos':
                true = a > 0
            else:
                b = registers[args[2][1]]
                true = a == b if cond == 'eq' else a < b
            if true:
                pc = program.labels[args[-1][1]]
        elif op == 'MOVE':
            direction = (DIRECTIONS[args[0][1]] if args[0][0] == 'word'
                         else registers[args[0][1]])
            if direction in DIRECTIONS.values():
                result.order = direction
        elif op == 'HOLD':
            result.order = 'hold'
        elif op == 'SAY':
            result.said.append((args[0][1], value(args[1]), value(args[2]),
                                value(args[3])))
        elif op == 'SLEEP':
            result.sleep = args[0][1]
            break
        elif op == 'HALT':
            break

    if result.halted is not None:
        # a controller that was stopped gives no order: whatever it had
        # decided before the cap was a thought it did not finish
        result.order = None
    total = meter + result.ticks
    result.charged = total // limit
    result.meter = total % limit
    return result
