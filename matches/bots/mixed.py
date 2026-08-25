"""Combined arms: a scout to find them, a champion and a tank to kill them.

The bet: the expensive thing in this game is information. One cheap unit with
thirty energy and nothing else can walk the whole board, and the contact that
kills it is what tells the other two where to go (R6.2). The assassin then
spends its one kill on something worth killing rather than on whatever it
stumbled into, and the grinder mops up whatever is small.

The weakness it accepts: three units, one of which is bought to die.
"""

from base import Sweeper
from common import mine, serpentine, size


class Bot(Sweeper):
    name = 'Mixed'
    doctrine = 'scout (a1 h1 e30) + assassin (a10 h1 e21) + tank (a1 h10 e20)'
    army = (('C', 'C', 1, 1, 30, [(0, 0)]),
            ('A', 'A', 10, 1, 21, [(0, 2)]),
            ('G', 'G', 1, 10, 20, [(0, 4)]))

    def floor(self, unit):
        return 1 if unit['type'] == 'C' else unit['attack']

    def plan_routes(self, view):
        """Only the scout sweeps. The other two wait on what it finds."""
        size_x, size_y = size(view)
        for unit in mine(view):
            if unit['type'] != 'C' or unit['name'] in self.routes:
                continue
            route = serpentine(size_y, list(range(size_x)), 0, True)
            self.routes[unit['name']] = route
            self.at[unit['name']] = 0

    def wish(self, view, unit, contacts):
        remembered = list(self.seen.values())
        if unit['type'] == 'C':
            # the scout is bought to look, not to fight: it walks its sweep
            # and steps around anything it has found
            return self.route_step(unit)
        # the killers go to the last place anybody was seen, and stand still
        # until there is one
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts or remembered))
