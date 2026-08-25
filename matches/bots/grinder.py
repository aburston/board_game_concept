"""Grinder: three units of ten health that kill by attrition.

The bet: energy spent to kill an enemy is about its health, whatever your
attack (a x ceil(h/a)), so attack 1 is the cheapest killer there is against
small units - and ten health absorbs ten separate attackers. Three of these
can absorb thirty attacks and pay for thirty points of enemy health.

The weakness it accepts: ceil(h/a) decides a duel, so attack 1 loses every
straight fight against a big attacker. It beats crowds, not champions.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Grinder'
    doctrine = '3 x (a1 h10 e20), column 8, sweep west'
    army = (('G', 'G', 1, 10, 20, [(8, 1), (8, 5), (8, 9)]),)

    def floor(self, unit):
        # keep half the tank's energy for the grinding it is bought for
        return 10
