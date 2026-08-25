"""Duellist: two champions that win every fight, and a scout to find them one.

Attack 10 destroys any unit in the game in a single round (health stops at
10), so a champion never loses a duel it does not tie. What it cannot do is
find anybody: at ten energy a round it can afford three fights, and every step
it takes looking for one is a point off that. So the legs are bought
separately, in the form of one cheap scout, and the champions sit in the
middle of the board - where a sweep has to come to them - until it reports.
"""

from base import Sweeper
from common import mine, serpentine, size


class Bot(Sweeper):
    name = 'Duellist'
    doctrine = '4 x (a10 h10 e20) + 2 scouts (a1 h1 e18), champions hold the frontier'
    army = (('C', 'C', 10, 10, 20, [(2, 2), (4, 2), (5, 2), (7, 2)]),
            ('S', 's', 1, 1, 18, [(0, 4), (9, 4)]))

    # a champion is worth walking a long way for
    reach = 6

    def floor(self, unit):
        return 10 if unit['type'] == 'C' else 1

    def plan_routes(self, view):
        """The scout sweeps the board; the champions only walk to the middle."""
        size_x, size_y = size(view)
        for unit in mine(view):
            if unit['name'] in self.routes:
                continue
            if unit['type'] == 'S':
                self.routes[unit['name']] = serpentine(
                    size_y, list(range(size_x)), 0, True)
            else:
                post = (4, 3) if unit['y'] < size_y // 2 else (5, 6)
                self.routes[unit['name']] = [post]
            self.at[unit['name']] = 0

    def wish(self, view, unit, contacts):
        remembered = list(self.seen.values())
        if unit['type'] == 'S':
            return self.route_step(unit)
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts or remembered)
                + self.route_step(unit))
