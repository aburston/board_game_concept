"""A doctrine: what to do with the seat you are handed, and then each turn.

A seat opens holding the stock army (R2.13): sixteen units in the two rows at
the player's own edge, the catalogue of eight types, and the flag on `keep1`.
A doctrine that keeps it returns nothing from `setup`. One that rebuilds
states its army as data and `setup` takes the given units back and deploys
its own through the ordinary commands; what the game refuses, it refuses.

Most doctrines differ in what they *buy* and where they *walk*, not in the
bookkeeping of walking, so the bookkeeping lives here. Nothing in this file
looks at anything but the view its own player was published.
"""

from common import (depth_row, distance, enemies, enemy_flags, fares, lanes,
                    mine, path_step, resolve, serpentine, size, steps_towards)


class Doctrine:
    """Keep or rebuild the army handed to you, then play it by a routine."""

    name = 'doctrine'
    doctrine = ''
    # a rebuilt army: each entry (type name, symbol, attack, health, energy,
    # [squares]), and a square is (x, depth): depth 0 is my own edge row and
    # depth 1 the row in front of it. Which rows those are depends on which
    # half of the board I hold, so an army is written once and deploys the
    # same way from either side. Empty means the stock army is kept
    army = ()
    # the unit that carries the flag in a rebuilt army, by the name `deploy`
    # gives it: the type's name in lower case and its number, `keep1`
    flag = None

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
        """The commands that turn the seat as handed into my army."""
        if not self.army:
            return []
        return self.take_back_all(view) + self.deploy(view)

    @staticmethod
    def take_back_all(view):
        """Take back every unit the seat was handed (R2.12)."""
        return [f'remove unit {unit["name"]}'
                for unit in sorted(mine(view), key=lambda u: u['name'])]

    def deploy(self, view):
        """My army as commands: a type, its units, and the flag."""
        commands = []
        for name, symbol, attack, health, energy, squares in self.army:
            commands.append(
                f'add type {name} {symbol} {attack} {health} {energy}')
            for index, (x, depth) in enumerate(squares):
                commands.append(f'add unit {name} {name.lower()}{index + 1} '
                                f'{x} {depth_row(view, depth)}')
        if self.flag:
            commands.append(f'set flag {self.flag}')
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
        """Where I last saw an enemy - this turn's contacts, and older ones."""
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
                    if distance(square, (unit['x'], unit['y'])) <= self.reach]
        if not contacts:
            return []
        nearest = min(contacts, key=lambda square:
                      distance(square, (unit['x'], unit['y'])))
        return steps_towards(unit, nearest)

    def flag_step(self, view, unit):
        """The steps that carry this unit towards the nearest enemy flag:
        the first step of a route round my own units, then the plain steps
        that shorten the distance, for when there is no route yet."""
        flags = [(x, y) for _player, x, y in enemy_flags(view)]
        if not flags:
            return []
        nearest = min(flags, key=lambda square:
                      distance(square, (unit['x'], unit['y'])))
        step = path_step(view, unit, nearest)
        steps = [step] if step else []
        return steps + [s for s in steps_towards(unit, nearest)
                        if s != step]

    # ------------------------------------------------------------------ orders

    def wish(self, view, unit, contacts):
        """What this unit would like to do, best step first."""
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts)
                + self.route_step(unit))

    def orders(self, view):
        self.plan_routes(view)
        contacts = self.targets(view)
        fare = fares(view)
        wishes = {}
        for unit in mine(view):
            # what is left after paying for the step has to clear the floor
            if unit['energy'] - fare[unit['name']] < self.floor(unit):
                continue
            wishes[unit['name']] = self.wish(view, unit, contacts)
        return resolve(view, wishes, keep_attack=False, together=contacts)


class Hunt(Doctrine):
    """Go for the enemy flag square, which every player can see (R6.5).

    The units of the types in `hunters` head for the nearest enemy flag by
    the shortest route, fighting whatever they meet; every other unit holds
    its square and strikes back at what walks in. Several hunters may be
    ordered onto one seen enemy, or onto the flag square itself, at once:
    the strikes that land in one exchange are what kill (R5.11).
    """

    hunters = ()
    reach = 2

    def wish(self, view, unit, contacts):
        steps = self.engage_step(unit, contacts)
        if unit['type'] in self.hunters:
            steps += self.approach(unit, contacts)
            steps += self.flag_step(view, unit)
        return steps

    def orders(self, view):
        contacts = self.targets(view)
        fare = fares(view)
        wishes = {}
        for unit in mine(view):
            if unit['energy'] - fare[unit['name']] < self.floor(unit):
                continue
            wishes[unit['name']] = self.wish(view, unit, contacts)
        together = contacts + [(x, y) for _p, x, y in enemy_flags(view)]
        return resolve(view, wishes, keep_attack=False, together=together)
