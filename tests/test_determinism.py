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
        board.add(player, x, y, name,
                  UnitType(name, name[0].upper(), attack, health, energy))
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
        squares = rng.sample([(x, y) for x in range(4) for y in range(3)],
                           how_many)
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
