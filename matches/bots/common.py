"""What every bot needs, and nothing about any particular strategy.

A bot is handed one thing: the view its own player is published (R6.4). These
helpers only ever read that view.
"""

DIRECTIONS = {'north': (0, -1), 'south': (0, 1),
              'east': (1, 0), 'west': (-1, 0)}
STEP = {step: name for name, step in DIRECTIONS.items()}


def size(view):
    board = view.get('board') or {}
    return board.get('size_x', 10), board.get('size_y', 10)


def on_board(view, x, y):
    size_x, size_y = size(view)
    return 0 <= x < size_x and 0 <= y < size_y


def mine(view):
    """My units that are standing on the board."""
    return [unit for unit in view['units']
            if unit['player'] == view['me'] and unit.get('x') is not None]


def enemies(view):
    """Enemy units in my view — which means ones I fought last turn (R6.2)."""
    return [unit for unit in view['units']
            if unit['player'] != view['me'] and unit.get('x') is not None]


def budget(view):
    for player in view.get('players', []):
        if player['player'] == view['me']:
            return player.get('left') or player.get('budget') or 100
    return 100


def steps_towards(unit, target):
    """The one-square steps that shorten the distance to a target square."""
    x, y = unit['x'], unit['y']
    tx, ty = target
    options = []
    if abs(tx - x) >= abs(ty - y):
        if tx != x:
            options.append((1, 0) if tx > x else (-1, 0))
        if ty != y:
            options.append((0, 1) if ty > y else (0, -1))
    else:
        if ty != y:
            options.append((0, 1) if ty > y else (0, -1))
        if tx != x:
            options.append((1, 0) if tx > x else (-1, 0))
    return options


def fares(view):
    """What a step costs each of my units: the health its type was designed
    with (R4.3).

    Not the health it is standing on now - damage is not weight shed - so it
    is read from my own type list, which is mine to know. A unit whose type is
    somehow missing falls back to its current health, which is the same number
    while the unit is whole.
    """
    designs = {kind['name']: kind['health'] for kind in view.get('types', ())
               if kind.get('player', view['me']) == view['me']}
    return {unit['name']: designs.get(unit['type'], unit['health'])
            for unit in mine(view)}


def can_move(unit, fare, keep_attack=True):
    """Whether to spend the fare on a step.

    Movement and attacking come out of the same pocket (R2.5), so a unit that
    walks itself below its attack value is inert until it has rested the
    difference back (R5.10, R3.9). `keep_attack` is a bot saying it would
    rather stand still than be unable to fight.
    """
    if unit['energy'] < fare:
        return False
    if keep_attack and unit['energy'] - fare < unit['attack']:
        return False
    return True


def resolve(view, wishes, keep_attack=True):
    """Turn each unit's wished-for steps into orders that do not self-destruct.

    A wish is a list of steps, best first. Two of my own units on one square
    fight each other (R4.10, R5.7), so a step that would put one there is
    passed over rather than ordered, and the next wish is tried. Units are
    considered in name order, so the same wishes always produce the same
    orders.
    """
    standing = {(unit['x'], unit['y']): unit['name'] for unit in mine(view)}
    fare = fares(view)

    def pass_over(leaving):
        moving_out = set(leaving)
        taken = set()
        chosen = []
        for unit in sorted(mine(view), key=lambda u: u['name']):
            steps = wishes.get(unit['name']) or []
            if isinstance(steps, tuple):
                steps = [steps]
            if not can_move(unit, fare[unit['name']], keep_attack):
                continue
            for step in steps:
                x, y = unit['x'] + step[0], unit['y'] + step[1]
                if not on_board(view, x, y):
                    continue
                if (x, y) in taken:
                    continue
                held_by = standing.get((x, y))
                if held_by is not None and held_by not in moving_out:
                    continue
                taken.add((x, y))
                moving_out.add(unit['name'])
                chosen.append((unit['name'], step))
                break
        return chosen

    # a unit that follows another out of its square arrives cleanly (R4.8),
    # but only if the one in front is known to be leaving. The first pass
    # works out who is leaving; the second lets the followers move up
    first = pass_over(set())
    second = pass_over({name for name, _ in first})
    return [f'move {name} {STEP[step]}' for name, step in second]


def serpentine(size_y, columns, start_row, downwards=True):
    """A lawnmower route over a block of columns, as a list of squares.

    You only ever learn an enemy is somewhere by stepping onto it (R6.2), so
    searching means visiting squares, not looking at them.
    """
    route = []
    rows = range(start_row, size_y) if downwards else range(start_row, -1, -1)
    for index, y in enumerate(rows):
        order = columns if index % 2 == 0 else list(reversed(columns))
        for x in order:
            route.append((x, y))
    return route


def lanes(size_x, count):
    """Split the columns between `count` units, left to right.

    Columns that do not divide evenly go to the rightmost lanes, so that a
    line of units standing one to a column from the left edge each keep the
    column they are standing in.
    """
    base, over = divmod(size_x, count)
    share = []
    x = 0
    for index in range(count):
        width = base + (1 if index >= count - over else 0)
        share.append(list(range(x, x + width)))
        x += width
    return share
