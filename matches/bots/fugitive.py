"""Fugitive: the flag on a Runner that keeps moving, and Lances in front.

Everybody can see where a flag is (R6.5), and every other doctrine here
carries it on a Keep - ten health that can barely move. This one puts it on
a Runner (attack 2, health 4, energy 10, fare 1) and walks it along the back
row every turn it can, resting only when a step would leave it unable to
strike. A hunter aiming at the flag square is aiming at where the carrier
was; the square it is told next turn is a different one.

The rest of the points are eleven Lances, played as the Lancers play them.
The question is whether a flag that moves is harder to take than one that
does not, or just one that runs out of energy sooner.
"""

from base import Hunt
from common import on_board


class Bot(Hunt):
    name = 'Fugitive'
    doctrine = ('the flag on a Runner that walks the back row every turn it '
                'can + 11 x Lance (a8 h2 e10) that hunt')
    army = (('Lance', '!', 8, 2, 10,
             [(x, 3) for x in range(8)] + [(1, 2), (4, 2), (6, 2)]),
            ('Runner', 'r', 2, 4, 10, [(3, 0)]))
    flag = 'runner1'
    hunters = ('Lance',)

    def __init__(self, player):
        super().__init__(player)
        self.heading = 1        # which way along the back row the carrier goes

    def wish(self, view, unit, contacts):
        if unit.get('flag'):
            # the carrier: away from any enemy it can see, else on along the
            # row, turning at the edge. It never leaves its edge row
            for x, y in contacts:
                if y == unit['y'] and abs(x - unit['x']) <= 2:
                    self.heading = -1 if x > unit['x'] else 1
            if not on_board(view, unit['x'] + self.heading, unit['y']):
                self.heading = -self.heading
            return [(self.heading, 0)]
        return super().wish(view, unit, contacts)
