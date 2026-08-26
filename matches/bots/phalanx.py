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
    doctrine = '6 x (a1 h4 e28), a rank abreast, no gaps'
    army = (
        ('P', 'P', 1, 4, 28,
         [(0, 4), (2, 4), (4, 4), (5, 4), (7, 4), (9, 4)]),
    )

    def floor(self, unit):
        # a reserve of one, which is what an attack of 1 costs. This was 5
        # when the rank was health-5 units on a fare of 5 a square; on the
        # quarter fare a health-4 unit pays 1, and holding back five energy
        # it has no use for just stops the rank moving
        return 1

    def wish(self, view, unit, contacts):
        """Hold the rank: everybody steps the same way unless there is contact."""
        engage = self.engage_step(unit, contacts) + self.approach(unit, contacts)
        if engage:
            return engage
        # forward is across the frontier, which is whichever way the other
        # half of the board lies
        forward = (0, 1) if self.north else (0, -1)
        return [forward, (1, 0), (-1, 0)]
