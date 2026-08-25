"""Hunter: two champions with thirty energy each, quartering the board.

The bet: attack 10 wins every duel it does not tie, ten health survives ten
small attackers, and thirty energy is both the search range to find an enemy
who is hiding and the three kills to finish them.

The weakness it accepts: two units means two lives. Any attack-10 unit the
enemy owns trades evenly with a champion that cost fifty points.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Hunter'
    doctrine = '4 x (a10 h10 e30), lawnmower sweep of a quarter of the board each'
    army = (('H', 'H', 10, 10, 30, [(0, 2), (3, 2), (6, 2), (9, 2)]),)

    def floor(self, unit):
        return 10
