"""Bulwark: a wall across the frontier, and two swords behind it.

A wall is attack 0 and energy 0 - ten health standing on a square for ten
points, which can never move, never strike and never rest. Ten of them laid
along the frontier row close the board: an enemy that wants into this half has
to break one, and breaking ten health costs about ten energy however it is
done. That is a tenth of an army's pocket spent before the fighting starts,
and it is spent in a square the defender chose.

The other hundred points is two units of attack 2 - enough to win a duel
against ten health in five rounds rather than ten - waiting behind the line
for whoever comes through the hole they make.
"""

from base import Sweeper
from common import lanes, mine, serpentine, size


class Bot(Sweeper):
    name = 'Bulwark'
    doctrine = '6 x wall (a0 h10 e0) across the frontier + 1 x (a2 h10 e70) + 1 x (a1 h4 e53)'
    army = (
        ('W', 'W', 0, 10, 0,
         [(0, 4), (2, 4), (4, 4), (5, 4), (7, 4), (9, 4)]),
        ('K', 'K', 2, 10, 70,
         [(3, 2)]),
        ('S', 's', 1, 4, 53,
         [(6, 2)]),
    )

    reach = 4

    # a line is worth holding while there is a chance somebody walks into
    # it; after that the two units behind it have to go and win the game
    patience = 25

    def floor(self, unit):
        return 2 if unit['type'] == 'K' else 1

    def plan_routes(self, view):
        """Each mobile unit patrols its own half of the ground behind the line.

        This used to plan nothing at all - the swords held their squares and
        waited for somebody to walk onto them. Against an army that never came
        that produced eighty-one turns without a single order, which is not a
        defence, it is an absence. A wall line holds ground; the units behind
        it are the only things that can win the game, and they cannot win it
        standing still.
        """
        size_x, size_y = size(view)
        movers = sorted((unit for unit in mine(view) if unit['attack'] > 0),
                        key=lambda u: u['name'])
        share = lanes(size_x, max(len(movers), 1))
        for index, unit in enumerate(movers):
            if unit['name'] in self.routes:
                continue
            # patrol my own ground first, then go through my own line and
            # sweep theirs - the walls do not block me, they are mine to
            # walk around
            self.routes[unit['name']] = serpentine(
                size_y, share[index], unit['y'], not self.north) + serpentine(
                size_y, share[index], 0 if self.north else size_y - 1,
                self.north)
            self.at[unit['name']] = 0

    def wish(self, view, unit, contacts):
        remembered = list(self.seen.values())
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts or remembered)
                + self.route_step(unit))
