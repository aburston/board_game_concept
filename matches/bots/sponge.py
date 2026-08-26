"""Sponge: units bought to be attacked, not to attack.

The win condition changed: a unit at zero energy is no longer counted, even
though it is still on the board. That turns energy into something you can take
off an opponent rather than only something they spend, because a defender pays
its attack value every round of every fight it is in, and it goes on paying
until one side is destroyed.

So: ten health, and almost no energy. **Which the movement rule has since made
illegal.** A move costs a unit its designed health, and a type must hold at
least its health in energy or it could never move at all, so the cheap soaker
cannot be built any more. What is left is the legal minimum - ten health and
ten energy - which buys exactly one step. The doctrine survives only as a line
that shuffles one square forward and then absorbs.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Sponge'
    doctrine = '9 x (a1 h10 e10) + 1 x (a1 h5 e5), one step in and soak'
    army = (('S', 'S', 1, 10, 10,
             [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
              (8, 4)]),
            ('D', 'D', 1, 5, 5, [(4, 3)]))

    def floor(self, unit):
        # a sponge spends everything on getting there. Holding a point back
        # would buy one round of attacking, and attacking is not the job
        return 1
