"""Sponge: units bought to be attacked, not to attack.

The idea is that energy is something you can take off an opponent rather than
only something they spend: a defender pays its attack value every round of
every fight it is in, and goes on paying until one side is destroyed. So: ten
health, and almost no energy. Let them come, and let them pay.

This design was briefly illegal too. While a move cost a unit its whole
designed health, a type had to hold at least its health in energy, and the
whole point of a sponge is to hold much less. The fare is a quarter of the
health now, so ten health costs three a square, and six energy buys two steps
and a little change. The rear unit is the nearly-empty one, at the floor the
rule now sets.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Sponge'
    doctrine = '11 x (a1 h10 e6) + 1 x (a1 h9 e3), a line bought to be hit'
    army = (('S', 'S', 1, 10, 6,
             [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
              (8, 4), (9, 4), (4, 3)]),
            ('D', 'D', 1, 9, 3, [(5, 3)]))

    def floor(self, unit):
        # a sponge spends everything on getting there. Holding a point back
        # would buy one round of attacking, and attacking is not the job
        return 1
