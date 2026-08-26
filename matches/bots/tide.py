"""Tide: the swarm again, with the legs it was missing.

Round one's swarm was nine bodies with nine energy: eight steps and one punch.
It found the enemy, traded three of itself for one point of damage, and then
stood still for forty turns. This is the same idea with a third more energy
each, one body fewer, and no reason to stop walking.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Tide'
    doctrine = '6 x (a1 h1 e31), a rank abreast, sweep and keep sweeping'
    army = (
        ('W', 'w', 1, 1, 31,
         [(0, 4), (2, 4), (4, 4), (5, 4), (7, 4), (9, 4)]),
    )

    def floor(self, unit):
        return 1
