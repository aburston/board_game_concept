"""Reaper: two champions carrying almost nothing but energy.

What the split board changes is that hunting is affordable: an enemy is
somewhere in fifty squares rather than a hundred, and it is not going to be
behind you. What two hundred points changes is that you can buy the energy to
do the hunting and the killing out of the same pocket.

Attack 10 destroys any unit in one round, which costs ten energy and takes one
point of damage in return. Ten health is therefore ten kills - and eighty
energy is five of them plus thirty squares of walking. Two of these have
between them enough kills for a full camp and enough legs to find it.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Reaper'
    doctrine = '2 x (a10 h10 e80), sweep the enemy half and clear it'
    army = (
        ('R', 'R', 10, 10, 80,
         [(2, 3), (7, 3)]),
    )

    reach = 6

    def floor(self, unit):
        return 10
