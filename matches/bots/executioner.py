"""Executioner: a type of our own, attack 10, and nine of it.

Attack 10, health 4, energy 12: twenty-six points, a fare of one. Ten is the
most a strike can be and the most health a unit can have, so one strike
destroys anything on the board (R5.11), Keep and Heavy included, and the
carrier of the flag with them. Health 4 rides for a fare of one and dies to a
Heavy's five outright, or to two Runners' strikes.

Nine of them and a Keep for the flag is exactly 250 points. Twelve energy
against a strike of ten is two squares and then a rest for every further
one; a strike leaves a unit ten quiet turns from its next. Each Executioner
is one kill, delivered on foot.
"""

from base import Hunt


class Bot(Hunt):
    name = 'Executioner'
    doctrine = ('9 x Exec (a10 h4 e12, our own type) + Keep with the flag; '
                'every Exec hunts')
    army = (('Exec', 'X', 10, 4, 12,
             [(x, 3) for x in range(8)] + [(4, 2)]),
            ('Keep', 'K', 1, 10, 5, [(3, 0)]))
    flag = 'keep1'
    hunters = ('Exec',)
