"""Drain: the sponge with the legs to reach everybody.

Game 38 showed the shape of the idea and the flaw in the first cut: sponges
took ten energy off every camper that killed one, but only five of the twelve
had the energy to reach a camper at all, so the camp finished the game half
drained and entirely intact.

This is the same unit with nine energy rather than six, ten of them rather
than twelve, one to a column. Each walks into the enemy half and keeps walking
until something kills it - and whatever kills it pays its attack value every
round for ten rounds to do it, which is a camper's whole pocket. Ten sponges
against ten campers is ten empty pockets.

This design was briefly illegal. While a move cost a unit its whole designed
health, a type had to hold at least its health in energy, so ten health on
nine was refused and the doctrine had to be rebuilt at ten energy - where it
could afford exactly one step and never moved at all. The fare is a quarter of
the health now, so ten health costs three a square and nine energy is three
squares: the original army is back, and it can walk.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Drain'
    doctrine = '4 x (a1 h10 e39), walk in and soak'
    army = (
        ('D', 'D', 1, 10, 39,
         [(0, 4), (3, 4), (6, 4), (9, 4)]),
    )

    def floor(self, unit):
        return 1
