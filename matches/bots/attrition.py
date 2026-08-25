"""Attrition: buy energy, not statistics, and keep hunting to the last point.

What the first five games taught: a unit stops being a unit the moment it
cannot afford to walk, and every army in round one froze around turn fifteen
with its statistics intact and its pockets empty. Energy is the game. It is
also the cheapest way to kill: a round of attacking costs the attacker its
attack value, so killing a unit of health h costs about h energy whatever your
attack is, and attack 1 is what makes that "about" exact.

Two tanks of ten health and thirty energy, and a scout with nothing but legs.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Attrition'
    doctrine = '2 x (a1 h10 e30) + scout (a1 h1 e16), sweep and grind'
    army = (('T', 'T', 1, 10, 30, [(0, 0), (0, 9)]),
            ('S', 's', 1, 1, 16, [(0, 5)]))

    def floor(self, unit):
        # the tanks keep ten energy back, which is a whole enemy of full
        # health; the scout spends everything it has on walking
        return 10 if unit['type'] == 'T' else 1
