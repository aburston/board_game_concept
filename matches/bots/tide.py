"""Tide: the swarm again, with the legs it was missing.

Round one's swarm was nine bodies with nine energy: eight steps and one punch.
It found the enemy, traded three of itself for one point of damage, and then
stood still for forty turns. This is the same idea with a third more energy
each, one body fewer, and no reason to stop walking.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Tide'
    doctrine = '8 x (a1 h1 e10), line abreast, sweep and keep sweeping'
    army = (('W', 'w', 1, 1, 10, [(x, 0) for x in range(1, 9)]),)

    def floor(self, unit):
        return 1
