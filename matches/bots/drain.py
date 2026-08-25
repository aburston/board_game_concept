"""Drain: the sponge with the legs to reach everybody.

Game 38 showed the shape of the idea and the flaw in the first cut: sponges
took ten energy off every camper that killed one, but only five of the twelve
had the energy to reach a camper at all, so the camp finished the game half
drained and entirely intact.

This is the same unit with nine energy rather than six, ten of them rather
than twelve, one to a column. Each walks into the enemy half and keeps walking
until something kills it - and whatever kills it pays its attack value every
round for ten rounds to do it, which is a camper's whole pocket. Ten sponges
against ten campers is ten empty pockets, and a player with nothing left
holding energy is out.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Drain'
    doctrine = '10 x (a1 h10 e9), one per column, walk in and soak'
    army = (('D', 'D', 1, 10, 9, [(x, 4) for x in range(10)]),)

    def floor(self, unit):
        return 1
