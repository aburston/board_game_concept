"""Sharpshooter: attack 2, which is the whole difference between a kill and a
mutual funeral.

A fight is decided by ceil(health / attack) - how many rounds each side needs
- and everything on both sides of the first eleven games was attack 1 against
health 10, which is ten rounds each way and two corpses (R5.11). Attack 2
kills the same unit in five rounds and walks away with half its health. It
costs one point more than attack 1 and it costs the same energy per kill,
because a round costs the attacker its attack value and it needs half as many
rounds.

Two of those, and a scout to spend its whole life looking.
"""

from base import Sweeper
from common import mine, serpentine, size


class Bot(Sweeper):
    name = 'Sharpshooter'
    doctrine = '2 x (a2 h10 e28) + scout (a1 h1 e18), duel-winning statistics'
    army = (('K', 'K', 2, 10, 28, [(9, 0), (9, 9)]),
            ('S', 's', 1, 1, 18, [(9, 5)]))

    reach = 6

    def floor(self, unit):
        return 2 if unit['type'] == 'K' else 1

    def plan_routes(self, view):
        size_x, size_y = size(view)
        for unit in mine(view):
            if unit['name'] in self.routes:
                continue
            if unit['type'] == 'S':
                route = serpentine(size_y, list(range(size_x)), 0,
                                   True)
            else:
                columns = list(range(size_x // 2, size_x)) \
                    if unit['y'] < size_y // 2 else list(range(size_x // 2))
                route = serpentine(size_y, columns, unit['y'],
                                   unit['y'] < size_y // 2)
            self.routes[unit['name']] = route
            self.at[unit['name']] = 0

    def wish(self, view, unit, contacts):
        remembered = list(self.seen.values())
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts or remembered)
                + self.route_step(unit))
