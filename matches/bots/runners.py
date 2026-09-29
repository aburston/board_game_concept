"""Runners: fourteen Runners and a Keep.

Attack 2, health 4, energy 10, sixteen points, a fare of one: the cheapest
unit in the catalogue that both walks and strikes, and health 4 is the best
value on the board (R4.3 - the fare is a step, and four health rides for the
price of one). Ten energy is eight squares with a strike kept in hand.

One Runner's two kills nothing but a Scout or a Lance. Three arriving on one
square land six, which is a Line; five land ten, which is a Keep or a Heavy.
The doctrine is numbers on one square at once, which the one-strike rule
made the only way to kill something big in a turn (R5.11).
"""

from base import Hunt


class Bot(Hunt):
    name = 'Runners'
    doctrine = '14 x Runner (a2 h4 e10) + Keep with the flag; every Runner hunts'
    army = (('Runner', 'r', 2, 4, 10,
             [(x, 3) for x in range(8)]
             + [(0, 2), (1, 2), (2, 2), (5, 2), (6, 2), (7, 2)]),
            ('Keep', 'K', 1, 10, 5, [(3, 0)]))
    flag = 'keep1'
    hunters = ('Runner',)
