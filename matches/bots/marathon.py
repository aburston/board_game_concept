"""Marathon: the same hunt, with enough points to pay for the walking.

This is the control on what ten undecided games suggested: that nobody loses
on a ten by ten board for a hundred points because searching it costs more
energy than a hundred points can buy. Same doctrine as Attrition - health 10,
attack 1, sweep a lane and grind whatever is standing in it - and nothing
different but the energy, which is the maximum a type may carry (R2.4).

Three units at 111 points each is 333 of a 400-point budget: 300 energy
against Attrition's 76.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Marathon'
    doctrine = '3 x (a1 h10 e100) on a 400-point budget, sweep until it ends'
    army = (('M', 'M', 1, 10, 100, [(0, 0), (0, 2), (0, 4)]),)

    def floor(self, unit):
        # walk down to the last point: one energy still buys an attack round,
        # and this unit has enough of them to grind anything it finds
        return 1
