"""Sponge: units bought to be attacked, not to attack.

The win condition changed: a unit at zero energy is no longer counted, even
though it is still on the board. That turns energy into something you can take
off an opponent rather than only something they spend, because a defender pays
its attack value every round of every fight it is in, and it goes on paying
until one side is destroyed.

So: ten health, and almost no energy. This unit walks into an enemy, lands one
round of attacks if it can afford to, and then simply absorbs. The enemy pays
to hit it every round for ten rounds. A seventeen-point sponge takes ten
energy off whatever kills it - the whole pocket of a camper, half of a
champion - and its owner is not out while any other sponge still has a point.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Sponge'
    doctrine = '11 x (a1 h10 e6) + 1 x (a1 h10 e2), walk in and soak'
    army = (('S', 'S', 1, 10, 6,
             [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
              (8, 4), (9, 4), (4, 3)]),
            ('D', 'D', 1, 10, 2, [(5, 3)]))

    def floor(self, unit):
        # a sponge spends everything on getting there. Holding a point back
        # would buy one round of attacking, and attacking is not the job
        return 1
