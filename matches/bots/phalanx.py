"""Phalanx: one rank of five, advancing in step.

The bet: a line abreast sweeps a five-wide corridor without ever leaving a
gap, and five units of five health are hard for small attackers to chew
through while being numerous enough to survive a champion or two.

The weakness it accepts: a rank is a compromise - too shallow to absorb an
attack-10 champion, too expensive to out-number a swarm.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Phalanx'
    doctrine = '5 x (a1 h5 e10) + 1 x (a1 h5 e5), rank abreast, advance north'
    army = (('P', 'P', 1, 5, 10, [(x, 9) for x in range(2, 7)]),
            ('R', 'R', 1, 5, 5, [(0, 9)]))

    def floor(self, unit):
        return 5

    def wish(self, view, unit, contacts):
        """Hold the rank: everybody steps the same way unless there is contact."""
        engage = self.engage_step(unit, contacts) + self.approach(unit, contacts)
        if engage:
            return engage
        return [(0, -1), (1, 0), (-1, 0)]
