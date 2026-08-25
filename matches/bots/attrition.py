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
    doctrine = '4 x (a1 h10 e30) + 2 scouts (a1 h1 e16), sweep and grind'
    army = (('T', 'T', 1, 10, 30, [(1, 2), (4, 2), (6, 2), (9, 2)]),
            ('S', 's', 1, 1, 16, [(0, 4), (9, 4)]))

    def floor(self, unit):
        # the tanks keep ten energy back, which is a whole enemy of full
        # health; the scout spends everything it has on walking
        # attack 1 spends one energy a round, so two in hand is a fight in
        # hand. The rest is legs
        return 2 if unit['type'] == 'T' else 1
