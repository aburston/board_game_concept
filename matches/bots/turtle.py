"""Turtle: five units that never move, and are therefore never seen.

The bet: an enemy is invisible until it is fought (R6.2), so a unit that never
moves is a hidden square somebody has to step on to find. Energy is only spent
by moving and attacking, so a unit that never moves keeps all ten points of
its energy for the fight it is walked into - and a defender that is stepped on
is fighting with full pockets against an attacker who has spent theirs walking.

The weakness it accepts: it can never win. Holding still kills nobody who does
not come to it, so the best it can do is not lose.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Turtle'
    doctrine = '9 x (a1 h10 e10) + 1 x (a1 h5 e5), dispersed at the back, never move'
    army = (('F', 'F', 1, 10, 10,
             [(0, 0), (3, 0), (6, 0), (9, 0), (1, 1), (5, 1), (8, 1),
              (2, 2), (7, 2)]),
            ('T', 'T', 1, 5, 5, [(4, 2)]))

    def orders(self, view):
        return []
