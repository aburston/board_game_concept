"""Screen: the stock army, with the Scouts put in the way.

A Scout is attack 0, health 2, energy 12, for fourteen points: it strikes
nothing, but it holds a square like anything else and it has twelve squares
of walking in it. This doctrine walks the two Scouts to the frontier row in
the two middle columns - the straight line from the enemy's half to the
Keeps - and leaves them there. Anything coming for the flag has to spend a
strike on a body that cost fourteen points, and fall back to do it (R5.8),
before it can take the square.

Everything else plays as Advance does: Pawns and Heavies step forward when
they can afford to, the back rank holds. The Heavies in the middle columns
find a Scout in front of them and rest behind it, which is the price of the
screen and part of what it tests.
"""

from advance import Bot as Advance
from common import depth_row, steps_towards

# where the screen stands: the row against the frontier, in the columns the
# Keeps are in, so that a unit walking straight at the flag walks into it
SCREEN = {'scout1': (3, 3), 'scout2': (4, 3)}


class Bot(Advance):
    name = 'Screen'
    doctrine = ('the stock army; the Scouts stand on the frontier row in '
                'front of the Keeps, the rest play as Advance')

    def wish(self, view, unit, contacts):
        if unit['type'] == 'Scout':
            post = SCREEN.get(unit['name'])
            if post is None:
                return []
            x, depth = post
            target = (x, depth_row(view, depth))
            if (unit['x'], unit['y']) == target:
                return []
            return steps_towards(unit, target)
        return super().wish(view, unit, contacts)
