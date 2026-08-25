"""A bot that walks a route and fights what it bumps into.

Most of the strategies below differ in what they *buy* and where they *walk*,
not in the bookkeeping of walking, so the bookkeeping lives here. Nothing in
this file looks at anything but the view its own player was published.
"""

from common import (enemies, lanes, mine, resolve, serpentine, size,
                    steps_towards)


class Sweeper:
    """Deploy a fixed army, then walk each unit along its own search route.

    Search is walking because contact is the only thing that reveals an enemy
    (R6.2): standing next to one tells you nothing at all.
    """

    name = 'sweeper'
    doctrine = ''
    # each entry: (type name, symbol, attack, health, energy, [squares])
    army = ()

    def floor(self, unit):
        """How much energy a unit refuses to walk below.

        Movement and attacking come out of the same pocket, so a unit that
        spends everything on looking cannot fight what it finds.
        """
        return unit['attack']

    def __init__(self, player):
        self.player = player
        self.routes = {}
        self.at = {}
        self.seen = {}          # unit name -> where an enemy was last met

    # --------------------------------------------------------------- setting up

    def setup(self, view):
        commands = []
        for kind in self.army:
            name, symbol, attack, health, energy, squares = kind
            commands.append(
                f'add type {name} {symbol} {attack} {health} {energy}')
            for index, (x, y) in enumerate(squares):
                commands.append(
                    f'add unit {name} {name.lower()}{index + 1} {x} {y}')
        return commands

    # ------------------------------------------------------------------ routes

    def plan_routes(self, view):
        """One serpentine lane per unit, out of the squares nobody has swept."""
        size_x, size_y = size(view)
        units = sorted(mine(view), key=lambda u: (u['x'], u['y'], u['name']))
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

    def orders(self, view):
        self.plan_routes(view)
        contacts = self.targets(view)
        wishes = {}
        for unit in mine(view):
            if unit['energy'] - 1 < self.floor(unit):
                continue
            wishes[unit['name']] = self.wish(view, unit, contacts)
        return resolve(view, wishes, keep_attack=False)
