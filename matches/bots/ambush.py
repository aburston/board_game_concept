"""Ambush: the turtle, moved to where the traffic is - and with an end in mind.

Round one's turtle put its units on the edges and the corners and was never
found, which is a way of not losing and no way of winning. These ten stand two
squares apart on the ground a sweep of the board has to cross, so that nothing
can reach two of them in one step, and every point of energy is kept for the
fight: an attacker that has walked ten squares to get here meets a defender
that has walked none.

Where it differs from the doctrine it replaces is what happens when nobody
comes. Waiting used to be the whole plan, and a plan that cannot win is not
one. Fifteen turns is what the ambush is given - it sits closer to the middle
than the turtle does, so it does not need as long for the traffic to arrive -
and then it stops being an ambush and becomes an advance.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Ambush'
    doctrine = '5 x (a1 h5 e34), on the traffic lanes, hold 15 turns then advance'
    army = (
        ('A', 'A', 1, 5, 34,
         [(0, 3), (3, 3), (6, 3), (9, 3), (4, 2)]),
    )

    patience = 15
