"""Swarm at the old hundred-point budget, for the control game.

Identical doctrine to Swarm, half the points: nine bodies rather than
eighteen. It exists so that one pairing can be played at 100 points and at 200
points across the same frontier, and the difference attributed to the budget
rather than to the board being split.
"""

from swarm import Bot as Swarm


class Bot(Swarm):
    name = 'Swarm-100'
    doctrine = '9 x (a1 h1 e9) on 100 points, one rank abreast'
    army = (('S', 's', 1, 1, 9, [(x, 4) for x in range(9)]),)
