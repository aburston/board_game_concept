"""Ambush: the turtle, moved to where the traffic is.

Round one's turtle put its five units on the edges and the corners and was
never found, which is a way of not losing and no way of winning. The same
five units stand in the middle here, two squares apart so that nothing can
reach two of them in one step, on the squares a sweep of the board has to
cross. Every point of energy is kept for the fight, so an attacker that has
walked ten squares to get here meets a defender with full pockets.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Ambush'
    doctrine = '4 x (a1 h10 e10) + 1 x (a1 h5 e10), centre squares, never move'
    army = (('A', 'A', 1, 10, 10, [(3, 3), (6, 3), (3, 6), (6, 6)]),
            ('B', 'B', 1, 5, 10, [(5, 5)]))

    def orders(self, view):
        return []
