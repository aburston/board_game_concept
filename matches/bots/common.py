"""What every bot needs, and nothing about any particular strategy.

A bot is handed one thing: the view its own player is published (R6.4), read
subject by subject from its own client - board, units, types, players, flags
and placement. These helpers only ever read that view. Nothing here consults
a random number, a clock or an identity: a doctrine is a function of its view
and its own memory, as the rules themselves are of the board and the orders.
"""

DIRECTIONS = {'north': (0, -1), 'south': (0, 1),
              'east': (1, 0), 'west': (-1, 0)}
STEP = {step: name for name, step in DIRECTIONS.items()}


# ----------------------------------------------------------------- the view

def size(view):
    """The board's size, as the board subject states it. No fallback: a
    doctrine that guessed a size would be playing a board it was not given."""
    board = view['board']
    return board['size_x'], board['size_y']


def on_board(view, x, y):
    size_x, size_y = size(view)
    return 0 <= x < size_x and 0 <= y < size_y


def mine(view):
    """My units that are standing on the board."""
    return [unit for unit in view['units']
            if unit['player'] == view['me'] and unit.get('x') is not None]


def enemies(view):
    """Enemy units in my view - which means ones I fought last turn (R6.2)."""
    return [unit for unit in view['units']
            if unit['player'] != view['me'] and unit.get('x') is not None]


def rows(view):
    """The rows I may deploy in, as the placement subject publishes them
    (R2.6a): the whole board where the game does not halve it."""
    return list(view['placement']['rows'])


def north(view):
    """Whether my half is the one nearer row 0."""
    return rows(view)[0] == 0


def depth_row(view, depth):
    """The board row at this depth into my own half, counted from my edge.

    Depth 0 is the row at my edge, depth 1 the one in front of it. Which rows
    those are depends on which half I hold, so an army is written once and
    deploys the same way from either side.
    """
    mine_rows = rows(view)
    return mine_rows[depth] if north(view) else mine_rows[-1 - depth]


def my_flag(view):
    """Where my flag stands, or None once it has fallen."""
    for flag in view.get('flags', []):
        if flag['player'] == view['me']:
            return (flag['x'], flag['y']) if flag.get('standing') else None
    return None


def enemy_flags(view):
    """Every other player's flag that still stands, as (player, x, y).

    A flag is the one thing shown without contact (R6.5): this is the only
    place a doctrine can learn where an enemy is without having fought it.
    """
    return [(flag['player'], flag['x'], flag['y'])
            for flag in view.get('flags', [])
            if flag['player'] != view['me'] and flag.get('standing')
            and flag.get('x') is not None]


def budget(view):
    """What my budget is, as the players subject states it."""
    for player in view.get('players', []):
        if player['player'] == view['me']:
            return player.get('budget')
    return None


def left(view):
    """What I have left to spend."""
    for player in view.get('players', []):
        if player['player'] == view['me']:
            return player.get('left')
    return None


def designs(view):
    """My own types, by name, as the types subject lists them."""
    return {kind['name']: kind for kind in view.get('types', ())
            if kind.get('player', view['me']) == view['me']}


# --------------------------------------------------------------- arithmetic

def fare_for(health):
    """A quarter of a health, rounded up, in whole numbers (R4.3)."""
    return (health + 3) // 4


def fares(view):
    """What a step costs each of my units: a quarter of the health its type
    was designed with, rounded up (R4.3).

    Not the health it is standing on now - damage is not weight shed - so it
    is read from my own type list, which is mine to know. A unit whose type is
    somehow missing falls back to its current health, which is the same number
    while the unit is whole.
    """
    health = {name: kind['health'] for name, kind in designs(view).items()}
    return {unit['name']: fare_for(health.get(unit['type'], unit['health']))
            for unit in mine(view)}


def lethal(attacks, health):
    """Whether the strikes landing in one exchange destroy a unit of this
    health (R5.11). One exchange a turn: what does not kill now leaves the
    contest undecided and the movers fall back."""
    return sum(attacks) >= health


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


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def path_step(view, unit, target):
    """The first step of the shortest way to a square, round my own units.

    My own standing units block me (R4.10), and a rank that fills its rows
    boxes in everything behind it, so a step that merely shortens the
    distance can be a step into a unit of mine that is going nowhere. This
    searches the board for the shortest route that walks round them and
    returns its first step, or None where no route exists. Squares I cannot
    see into are taken as free: an enemy standing on one is found by walking
    into it, which is the only way of finding anything (R6.2). Neighbours are
    tried in one fixed order, so the same board gives the same step.
    """
    start = (unit['x'], unit['y'])
    if start == target:
        return None
    blocked = {(other['x'], other['y']) for other in mine(view)
               if other['name'] != unit['name']}
    size_x, size_y = size(view)
    came_from = {start: None}
    queue = [start]
    while queue:
        here = queue.pop(0)
        if here == target:
            break
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            there = (here[0] + dx, here[1] + dy)
            if not (0 <= there[0] < size_x and 0 <= there[1] < size_y):
                continue
            if there in came_from or (there in blocked and there != target):
                continue
            came_from[there] = here
            queue.append(there)
    if target not in came_from:
        return None
    square = target
    while came_from[square] != start:
        square = came_from[square]
    return (square[0] - start[0], square[1] - start[1])


# ------------------------------------------------------------------ orders

def resolve(view, wishes, keep_attack=True, together=()):
    """Turn each unit's wished-for steps into orders that do not self-destruct.

    A wish is a list of steps, best first. Two of my own units on one empty
    square fight each other (R4.10, R5.7), so a step that would put one there
    is passed over rather than ordered, and the next wish is tried. A square
    in `together` is one an enemy is known to hold: several of my units may
    be ordered into it at once, because the strikes that land in one exchange
    are what kill (R5.11) and the survivors fall back rather than share
    (R5.8a). Units are considered in name order, so the same wishes always
    produce the same orders.
    """
    standing = {(unit['x'], unit['y']): unit['name'] for unit in mine(view)}
    fare = fares(view)
    together = set(together)

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
                if (x, y) in taken and (x, y) not in together:
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
    rows_ = range(start_row, size_y) if downwards else range(start_row, -1, -1)
    for index, y in enumerate(rows_):
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
