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
    doctrine = '3 x (a1 h10 e55), spread across the middle, grind forward'
    army = (
        ('G', 'G', 1, 10, 55,
         [(0, 4), (4, 4), (9, 4)]),
    )

    def floor(self, unit):
        # keep half the tank's energy for the grinding it is bought for
        # one point still buys a round of attacking, and this unit only
        # ever spends one a round: holding ten back was ten it never used
        return 1
