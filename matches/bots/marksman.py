"""Marksman: the control, run properly.

Marathon tested whether a bigger budget breaks a camp and answered no, but it
answered the wrong question: at attack 1 against health 10 it killed its
enemies by dying on them. This is the same 400-point budget with the one
statistic that matters put right. Attack 5 kills a ten-health defender in two
rounds for ten energy and takes two damage doing it, and 100 energy is fifty
of those.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Marksman'
    doctrine = '3 x (a5 h10 e100) on a 400-point budget, sweep and clear'
    army = (('M', 'M', 5, 10, 100, [(0, 0), (0, 4), (0, 9)]),)

    def floor(self, unit):
        return 5
