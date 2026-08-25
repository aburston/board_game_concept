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
    doctrine = '12 x (a1 h5 e10), a full rank on the frontier, advance in step'
    army = (('P', 'P', 1, 5, 10,
             [(x, 4) for x in range(10)] + [(4, 3), (5, 3)]),)

    def floor(self, unit):
        return 5

    def wish(self, view, unit, contacts):
        """Hold the rank: everybody steps the same way unless there is contact."""
        engage = self.engage_step(unit, contacts) + self.approach(unit, contacts)
        if engage:
            return engage
        # forward is across the frontier, which is whichever way the other
        # half of the board lies
        forward = (0, 1) if self.north else (0, -1)
        return [forward, (1, 0), (-1, 0)]
