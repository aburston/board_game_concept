"""A bot that walks a route and fights what it bumps into.

Most of the strategies below differ in what they *buy* and where they *walk*,
not in the bookkeeping of walking, so the bookkeeping lives here. Nothing in
this file looks at anything but the view its own player was published.
"""

from common import (enemies, fares, lanes, mine, resolve, serpentine,
                    size, steps_towards)


class Sweeper:
    """Deploy a fixed army, then walk each unit along its own search route.

    Search is walking because contact is the only thing that reveals an enemy
    (R6.2): standing next to one tells you nothing at all.
    """

    name = 'sweeper'
    doctrine = ''
    # each entry: (type name, symbol, attack, health, energy, [squares]),
    # and a square is (x, depth): depth 0 is my own back row and depth 4 is
    # the row against the frontier. Which rows those are depends on which
    # half of the board I hold, so an army is written once and deploys the
    # same way from either side
    army = ()

    # how many turns this doctrine will sit on its deployment before it has to
    # come forward. Nothing here may hold for ever: a game is won by taking
    # the other player's units off the board (R7.1), so a doctrine that never
    # advances cannot win one - the most it can do is not lose, and a series
    # of games neither side is trying to win measures nothing. Patience buys a
    # defender the thing it is built for, which is meeting an attacker on full
    # pockets; it does not buy it the whole game. Contact overrides it: once
    # this player has seen an enemy there is something to go at, and waiting
    # is no longer a plan
    patience = 0

    def floor(self, unit):
        """How much energy a unit refuses to walk below.

        Movement and attacking come out of the same pocket, so a unit that
        spends everything on looking cannot fight what it finds.
        """
        return unit['attack']

    def __init__(self, player):
        self.player = player
        # player 1 holds the north half, player 2 the south. Both know the
        # rule; neither learns anything from it that the other does not
        self.north = player == 1
        self.routes = {}
        self.at = {}
        self.seen = {}          # unit name -> where an enemy was last met
        self.turn = 0           # turns this bot has been asked to order

    # --------------------------------------------------------------- setting up

    def row(self, depth, size_y=10):
        """The board row this depth in my own half is."""
        return depth if self.north else size_y - 1 - depth

    def setup(self, view):
        size_y = size(view)[1]
        commands = []
        for kind in self.army:
            name, symbol, attack, health, energy, squares = kind
            commands.append(
                f'add type {name} {symbol} {attack} {health} {energy}')
            for index, (x, depth) in enumerate(squares):
                commands.append(f'add unit {name} {name.lower()}{index + 1} '
                                f'{x} {self.row(depth, size_y)}')
        return commands

    # ------------------------------------------------------------------ routes

    def plan_routes(self, view):
        """One serpentine lane per unit, out of the squares nobody has swept."""
        size_x, size_y = size(view)
        units = sorted(mine(view), key=lambda u: (u['x'], u['y'], u['name']))
        if len(units) >= size_x:
            # more units than there are columns to give them: each sweeps the
            # column it is standing in, and the ones sharing a column follow
            # each other down it (R4.8)
            share = [[unit['x']] for unit in units]
        else:
            share = lanes(size_x, max(len(units), 1))
        for unit, columns in zip(units, share):
            if unit['name'] in self.routes:
                continue
            downwards = unit['y'] < size_y // 2
            start = unit['y']
            route = serpentine(size_y, columns, start, downwards)
            back = serpentine(size_y, columns,
                              size_y - 1 if downwards else 0, not downwards)
            self.routes[unit['name']] = route + back
            self.at[unit['name']] = 0

    def route_step(self, unit):
        """The steps that carry this unit along its route."""
        route = self.routes.get(unit['name'])
        if not route:
            return []
        index = self.at.get(unit['name'], 0)
        here = (unit['x'], unit['y'])
        while index < len(route) and route[index] == here:
            index += 1
        if index >= len(route):
            index = 0                      # sweep it again rather than idle
            while index < len(route) and route[index] == here:
                index += 1
        self.at[unit['name']] = index
        if index >= len(route):
            return []
        return steps_towards(unit, route[index])

    # ---------------------------------------------------------------- fighting

    def targets(self, view):
        """Where I last saw an enemy — this turn's contacts, and older ones."""
        for enemy in enemies(view):
            self.seen[f"{enemy['player']}:{enemy['name']}"] = (enemy['x'],
                                                               enemy['y'])
        return [(enemy['x'], enemy['y']) for enemy in enemies(view)]

    def engage_step(self, unit, contacts):
        """Step onto an enemy I can reach this turn, if there is one."""
        for x, y in contacts:
            if abs(x - unit['x']) + abs(y - unit['y']) == 1:
                return [(x - unit['x'], y - unit['y'])]
        return []

    # how far a unit will leave its own search lane to go at somebody it has
    # seen. Contact is not cumulative (R6.3), so a sighting is one turn old at
    # best: marching the whole army at a square an enemy has already walked
    # out of is how a sweep turns into a shambles
    reach = 3

    def approach(self, unit, contacts):
        contacts = [square for square in contacts
                    if abs(square[0] - unit['x']) + abs(square[1] - unit['y'])
                    <= self.reach]
        if not contacts:
            return []
        nearest = min(contacts, key=lambda square:
                      abs(square[0] - unit['x']) + abs(square[1] - unit['y']))
        return steps_towards(unit, nearest)

    # ------------------------------------------------------------------ orders

    def wish(self, view, unit, contacts):
        """What this unit would like to do, best step first."""
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts)
                + self.route_step(unit))

    def holding(self, view, contacts):
        """Whether to spend another turn standing where I deployed.

        Only while nothing has been seen and the doctrine's patience has not
        run out. A unit that holds is a unit that rests (R3.9), so waiting is
        not free of consequence for the other side either - but it stops being
        a plan the moment there is an enemy to go at, or the moment the clock
        says this doctrine has had its turn at being a fortress.
        """
        return (self.turn <= self.patience
                and not contacts and not self.seen)

    def orders(self, view):
        self.turn += 1
        self.plan_routes(view)
        contacts = self.targets(view)
        if self.holding(view, contacts):
            return []
        fare = fares(view)
        wishes = {}
        for unit in mine(view):
            # what is left after paying for the step has to clear the floor,
            # and the step costs a quarter of this unit's designed health
            # (R4.3), not the flat 1 every doctrine here was first written
            # against
            if unit['energy'] - fare[unit['name']] < self.floor(unit):
                continue
            wishes[unit['name']] = self.wish(view, unit, contacts)
        return resolve(view, wishes, keep_attack=False)
