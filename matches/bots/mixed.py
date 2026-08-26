"""Combined arms: a scout to find them, a champion and a tank to kill them.

The bet: the expensive thing in this game is information. One cheap unit with
thirty energy and nothing else can walk the whole board, and the contact that
kills it is what tells the other two where to go (R6.2). The assassin then
spends its one kill on something worth killing rather than on whatever it
stumbled into, and the grinder mops up whatever is small.

The weakness it accepts: three units, one of which is bought to die.
"""

from base import Sweeper
from common import lanes, mine, serpentine, size


class Bot(Sweeper):
    name = 'Mixed'
    doctrine = '1 scout (a1 h1 e60) + 2 x (a10 h1 e30) + 1 x (a1 h10 e45), combined arms'
    # the type letters matter: `plan_routes` and `wish` below key off them, so
    # the scout has to be a C and anything that fights must not be
    army = (
        ('C', 'c', 1, 1, 60,
         [(0, 4)]),
        ('A', 'A', 10, 1, 30,
         [(3, 4), (6, 4)]),
        ('G', 'G', 1, 10, 45,
         [(9, 3)]),
    )

    def floor(self, unit):
        return unit['attack'] if unit['type'] == 'A' else 1

    def plan_routes(self, view):
        """The scout sweeps the whole board; everybody else gets a lane.

        The killers used to get no route at all, on the theory that they
        should wait on what the scout finds. What that produced was a bot
        that gave no order for sixty-six turns of a hundred: the scout was
        killed early, no intelligence ever arrived, and two units with an
        attack of ten stood on their deployment squares until the game ran
        out. Waiting on a scout is only a plan while there is a scout.
        """
        size_x, size_y = size(view)
        units = sorted(mine(view), key=lambda u: u['name'])
        others = [unit for unit in units if unit['type'] != 'C']
        share = lanes(size_x, max(len(others), 1))
        # sweep away from my own back row, which is into enemy ground
        downwards = self.north
        start = 0 if downwards else size_y - 1
        for unit in units:
            if unit['name'] in self.routes:
                continue
            if unit['type'] == 'C':
                columns = list(range(size_x))
            else:
                columns = share[others.index(unit) % len(share)]
            self.routes[unit['name']] = serpentine(
                size_y, columns, start, downwards)
            self.at[unit['name']] = 0

    def wish(self, view, unit, contacts):
        remembered = list(self.seen.values())
        if unit['type'] == 'C':
            # the scout is bought to look, not to fight: it walks its sweep
            # and steps around anything it has found
            return self.route_step(unit)
        # the killers go to the last place anybody was seen - and when nobody
        # has been seen, they go looking themselves rather than stand
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts or remembered)
                + self.route_step(unit))
