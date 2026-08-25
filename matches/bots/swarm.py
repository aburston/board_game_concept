"""Swarm: buy the most bodies the budget allows and sweep abreast.

The bet: the game is won by the last player with *anything* standing (R7.2),
so the cheapest thing that can walk and hit is the most win-conditions per
point. Nine bodies at 11 points each, walking south in nine lanes, search the
whole board in nine turns and cost the enemy a unit for every one they kill.

The weakness it accepts: a single point of health means every fight it starts
is a trade, and one enemy of ten health eats ten of these.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Swarm'
    doctrine = '9 x (a1 h1 e9), line abreast, sweep south'
    army = (('S', 's', 1, 1, 9,
             [(x, 0) for x in range(9)]),)

    def floor(self, unit):
        # a body with one energy left can still land a killing blow, and this
        # unit's whole worth is landing one
        return 1
