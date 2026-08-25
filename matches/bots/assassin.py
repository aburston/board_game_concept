"""Assassin: attack 10, health 1 - kills anything it touches, dies to anything.

The bet: a round of combat is simultaneous (R5.2) and ceil(health / attack)
decides it, so attack 10 destroys any unit in the game in one round. At 32
points a piece these trade one-for-one against anything, including a champion
that cost fifty.

The weakness it accepts: an attack of 10 costs 10 energy a round, so each of
these has exactly one kill in it, and one point of health means every trade
is mutual.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Assassin'
    doctrine = '3 x (a10 h1 e21), spread west edge, hunt'
    army = (('A', 'A', 10, 1, 21, [(0, 0), (0, 5), (0, 9)]),)

    def floor(self, unit):
        # never walk below the ten energy the one kill costs
        return 10
