"""The invariant: no randomness in the resolution of the rules.

A turn is a pure function of the board and the orders given. The same orders on
the same board always resolve the same way, and nothing about the answer depends
on the order a collection happens to hold its members in.

That is not a property of how the engine is currently written, to be preserved
by care. It is a rule of the game, and this is what holds it to it. A rule
decided by list position is unpredictable to a player in exactly the way a die
roll would be, while being harder to see.
"""

import ast
import itertools
import pathlib
import random

from board_game_concept import Board, Player, UnitType
from board_game_concept.domain import describe

SRC = pathlib.Path(__file__).resolve().parent.parent / 'src' / 'board_game_concept'

DIRECTIONS = (UnitType.NONE, UnitType.NORTH, UnitType.EAST, UnitType.SOUTH,
              UnitType.WEST)


def build(spec, order, size=(4, 3)):
    """One board holding the same units, registered in the order given."""
    board = Board(*size)
    players = {}
    for index in order:
        number, name, x, y, attack, health, energy, _ = spec[index]
        player = players.setdefault(number, Player(number))
        # the type is designed holding at least the fare one move costs it,
        # which is its health; the drawn energy is what play has left the unit
        # with, and is set on the unit below
        board.add(player, x, y, name,
                  UnitType(name, name[0].upper(), attack, health,
                           max(energy, health)))
    board.commit()
    for index in order:
        number, name, x, y, attack, health, energy, direction = spec[index]
        unit = board.getUnitByName(name)[0]
        unit.setEnergy(energy)
        if direction != UnitType.NONE:
            unit.move(direction)
    return board


def outcome(board):
    events = board.commit()
    state = tuple(sorted(
        (unit.name, unit.x, unit.y, unit.health, unit.energy,
         unit.destroyed, unit.on_board,
         tuple(sorted(seen.name for seen in unit.seen_by)))
        for unit in board.units))
    return state, describe(events)


def scenarios(count, seed=20260823):
    """Random boards and orders, drawn once from a fixed seed.

    The scenarios are random; nothing about resolving one is. Drawing them from
    a seed means a failure can be reproduced exactly.
    """
    rng = random.Random(seed)
    for _ in range(count):
        how_many = rng.choice([2, 3])
        squares = rng.sample(
            [(x, y) for x in range(4) for y in range(3)], how_many)
        yield [(rng.choice([1, 2]), f'u{i}', x, y,
                rng.randint(1, 4), rng.randint(1, 6), rng.randint(1, 8),
                rng.choice(DIRECTIONS))
               for i, (x, y) in enumerate(squares)]


def test_the_order_units_are_registered_in_does_not_change_the_outcome():
    divergent = []
    for spec in scenarios(300):
        states = {repr(outcome(build(spec, order))[0])
                  for order in itertools.permutations(range(len(spec)))}
        if len(states) > 1:
            divergent.append(spec)
    assert not divergent, (
        f"{len(divergent)} scenario(s) resolved to a different state depending "
        f"on the order units were registered in; first: {divergent[0]}")


def test_the_same_things_happen_whatever_order_units_are_registered_in():
    """The log may narrate in the board's own order; it may not differ in what
    it says happened."""
    divergent = []
    for spec in scenarios(300):
        logs = {tuple(sorted(outcome(build(spec, order))[1].splitlines()))
                for order in itertools.permutations(range(len(spec)))}
        if len(logs) > 1:
            divergent.append((spec, logs))
    assert not divergent, (
        f"{len(divergent)} scenario(s) reported different events depending on "
        f"the order units were registered in; first: {divergent[0]}")


def test_the_same_turn_resolved_twice_gives_the_same_answer():
    for spec in scenarios(100, seed=11):
        order = tuple(range(len(spec)))
        assert outcome(build(spec, order)) == outcome(build(spec, order)), spec


def test_the_same_turn_gives_the_same_events_in_the_same_order():
    for spec in scenarios(100, seed=7):
        order = tuple(range(len(spec)))
        assert outcome(build(spec, order))[1] == outcome(build(spec, order))[1]


FORBIDDEN = {
    'random': 'a random number generator',
    'secrets': 'a random number generator',
    'time': 'a clock',
    'datetime': 'a clock',
    'uuid': 'an identity that varies between runs',
}


def test_the_rules_import_no_source_of_randomness():
    """Nothing that resolves a turn may reach outside the board and the orders.

    Checked by reading the imports rather than by trusting a convention, so a
    later change that reaches for `random` to break a tie fails here first.
    """
    offences = []
    for path in sorted((SRC / 'domain').rglob('*.py')):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or '']
            for name in names:
                root = name.split('.')[0]
                if root in FORBIDDEN:
                    offences.append(f"{path.name} imports {name} "
                                    f"({FORBIDDEN[root]})")
    assert not offences, offences


def test_the_rules_do_not_order_anything_by_identity():
    """`id()` and `hash()` vary between runs, so a rule using one is not a rule."""
    offences = []
    for path in sorted((SRC / 'domain').rglob('*.py')):
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in ('id', 'hash')):
                continue
            line = source.splitlines()[node.lineno - 1]
            # identity is fine for telling two units apart; it is ordering or
            # sorting by it that would decide a rule by something that varies
            if any(word in line for word in ('sort', 'min(', 'max(', 'key=')):
                offences.append(f"{path.name}:{node.lineno}: {line.strip()}")
    assert not offences, offences


# --- the controllers

PROGRAMS = [
    # a hunter: step towards the nearest enemy flag along the longer axis
    ('hunter',
     'SELF\nFLAG enemy\nJIF neg r0, done\nSUB r0, r6\nSUB r1, r7\n'
     'MOV r2, r0\nABS r2\nMOV r3, r1\nABS r3\nJIF lt r2, r3, vertical\n'
     'SIGN r0\nJIF pos r0, east\nMOVE west\nJMP done\n'
     'east: MOVE east\nJMP done\n'
     'vertical: SIGN r1\nJIF pos r1, south\nMOVE north\nJMP done\n'
     'south: MOVE south\ndone: HALT'),
    # a crier: tells everybody where it stands, and reads what it is told
    ('crier', 'SELF\nSAY all, r0, r1, r2\nRECV\nSTORE r1, 0\nSTORE r2, 1'),
    # a sleeper: looks, then sleeps
    ('sleeper', 'NEAREST enemy\nSTORE r0, 0\nSTORE r1, 1\nSLEEP 1'),
    # a reader: walks to the nearest unknown square and remembers where
    ('reader',
     'NEAREST unknown\nJIF neg r0, done\nSTORE r0, 5\nSTORE r1, 6\n'
     'SELF\nLOAD r2, 5\nSUB r2, r0\nSIGN r2\nJIF pos r2, east\n'
     'JIF neg r2, west\nLOAD r3, 6\nSUB r3, r1\nSIGN r3\n'
     'JIF pos r3, south\nMOVE north\nJMP done\n'
     'east: MOVE east\nJMP done\nwest: MOVE west\nJMP done\n'
     'south: MOVE south\ndone: HALT'),
    # a counter: counts its turns in memory and holds
    ('counter', 'LOAD r0, 0\nADD r0, 1\nSTORE r0, 0\nHOLD'),
]


def build_programmed(spec, order, size=(5, 4)):
    """A board of programmed units, registered in the order given, with the
    setup turn resolved and the first unit of each player carrying the flag."""
    board = Board(*size)
    players = {}
    carriers = set()
    for index in order:
        number, name, x, y, attack, health, energy, compute, program = spec[index]
        player = players.setdefault(number, Player(number))
        board.add(player, x, y, name,
                  UnitType(name, name[0].upper(), attack, health, energy,
                           compute, dict(PROGRAMS)[program]))
    for number, player in players.items():
        # the flag goes to the player's first unit by name, whatever the
        # registration order, so every permutation plays the same game
        first = min(unit.name for unit in board.units
                    if unit.player is player)
        board.findUnit(first, player).flag = True
        carriers.add((number, first))
    board.commit(turn=0)
    return board


def programmed_outcome(board, turns=3):
    logs = []
    for turn in range(1, turns + 1):
        logs.append(describe(board.commit(turn=turn)))
    state = tuple(sorted(
        (unit.player.number, unit.name, unit.x, unit.y, unit.health,
         unit.energy, unit.destroyed, unit.on_board, unit.meter,
         unit.asleep, tuple(sorted(unit.memory.items())), tuple(unit.inbox))
        for unit in board.units))
    maps = tuple((number, repr(board.maps[number].record()))
                 for number in sorted(board.maps))
    return state, maps, logs


def programmed_scenarios(count, seed=20261108):
    rng = random.Random(seed)
    for _ in range(count):
        how_many = rng.choice([2, 3, 4])
        squares = rng.sample(
            [(x, y) for x in range(5) for y in range(4)], how_many)
        spec = []
        for i, (x, y) in enumerate(squares):
            health = rng.randint(1, 6)
            spec.append((
                rng.choice([1, 2]), f'u{i}', x, y,
                rng.randint(1, 4), health,
                rng.randint((health + 3) // 4, 8), rng.randint(1, 5),
                rng.choice([name for name, _ in PROGRAMS])))
        if len({number for number, *_ in spec}) < 2:
            spec[-1] = (3 - spec[0][0],) + spec[-1][1:]
        yield spec


def test_the_order_controllers_are_registered_in_does_not_change_the_game():
    """Every controller reads the turn as it began, so which runs first cannot
    matter: the state, the maps and the words said are the same under every
    permutation of the units."""
    divergent = []
    for spec in programmed_scenarios(150):
        answers = {repr(programmed_outcome(build_programmed(spec, order))[:2])
                   for order in itertools.permutations(range(len(spec)))}
        if len(answers) > 1:
            divergent.append(spec)
    assert not divergent, (
        f"{len(divergent)} programmed scenario(s) played differently "
        f"depending on the order units were registered in; first: "
        f"{divergent[0]}")


def test_the_same_programmed_game_twice_tells_the_same_story():
    for spec in programmed_scenarios(60, seed=3):
        order = tuple(range(len(spec)))
        first = programmed_outcome(build_programmed(spec, order))
        second = programmed_outcome(build_programmed(spec, order))
        assert first == second, spec
        # the log may narrate in the board's own order; it may not differ in
        # what it says happened
        reversed_order = programmed_outcome(
            build_programmed(spec, order[::-1]))
        for told, told_again in zip(first[2], reversed_order[2]):
            assert sorted(told.splitlines()) == sorted(
                told_again.splitlines()), spec
