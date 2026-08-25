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


class Bot(Sweeper):
    name = 'Bulwark'
    doctrine = '10 x wall (a0 h10 e0) across the frontier + 2 x (a2 h10 e28)'
    army = (('W', 'W', 0, 10, 0, [(x, 4) for x in range(10)]),
            ('K', 'K', 2, 10, 28, [(3, 2), (6, 2)]),
            ('S', 's', 1, 1, 18, [(0, 0)]))

    reach = 4

    def floor(self, unit):
        return 2 if unit['type'] == 'K' else 1

    def plan_routes(self, view):
        """Nobody sweeps. The swords hold their ground until something comes."""
        return

    def wish(self, view, unit, contacts):
        remembered = list(self.seen.values())
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts or remembered))
