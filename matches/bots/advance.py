"""Advance: the stock army, and the front rank walks at the enemy as a line.

The rank the game puts nearest the frontier - four Pawns and two Heavies,
with two Walls that cannot move - steps forward one square a turn as a line,
and rests whenever a step would leave a unit unable to strike (R5.10). The
back rank holds: the Keeps carry the flag and can barely move (fare 3 on five
energy), and the Runners, Lines and Scouts stay with them. Every contact is
pressed next turn by whatever stands beside it.

A Pawn has two energy and a fare of one, so it walks every other turn. A
Heavy has fifteen against a fare of three and a strike of five: three squares,
then two turns' rest for every further square. The line does not wait for its
slowest member, so it stretches; what a rank of unequal legs does under one
strike a turn is the question this doctrine asks.
"""

from base import Doctrine
from common import north, on_board, resolve, fares, mine

FRONT = ('Pawn', 'Heavy')


class Bot(Doctrine):
    name = 'Advance'
    doctrine = ('the stock army; Pawns and Heavies step towards the enemy '
                'each turn they can afford to, the back rank holds')

    def forward(self, view):
        """The step that carries a unit out of my half."""
        return (0, 1) if north(view) else (0, -1)

    def wish(self, view, unit, contacts):
        steps = self.engage_step(unit, contacts)
        if unit['type'] in FRONT:
            steps += self.approach(unit, contacts)
            dx, dy = self.forward(view)
            if on_board(view, unit['x'] + dx, unit['y'] + dy):
                steps.append((dx, dy))
        return steps

    def orders(self, view):
        contacts = self.targets(view)
        fare = fares(view)
        wishes = {}
        for unit in mine(view):
            if unit['energy'] - fare[unit['name']] < self.floor(unit):
                continue
            wishes[unit['name']] = self.wish(view, unit, contacts)
        return resolve(view, wishes, keep_attack=False, together=contacts)
