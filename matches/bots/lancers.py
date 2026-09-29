"""Lancers: eleven Lances and a Keep to carry the flag.

The Lance is in the catalogue and not in the stock array (R2.13): attack 8,
health 2, energy 10, twenty points, a fare of one. Under one strike a turn a
kill is a strike that reaches the health on its own (R5.11), and eight
reaches everything in the stock army but a Keep or a Heavy - and two Lances
arriving together reach those. Every Lance dies to any strike of two.

Eleven of them are 220 points; the Keep that carries the flag is sixteen.
A Lance holds ten energy against a strike costing eight, so it walks two
squares and then rests a turn for every further one, and once it has struck
it is eight quiet turns from striking again. The doctrine is one blow each.
"""

from base import Hunt


class Bot(Hunt):
    name = 'Lancers'
    doctrine = '11 x Lance (a8 h2 e10) + Keep with the flag; every Lance hunts'
    army = (('Lance', '!', 8, 2, 10,
             [(x, 3) for x in range(8)] + [(1, 2), (4, 2), (6, 2)]),
            ('Keep', 'K', 1, 10, 5, [(3, 0)]))
    flag = 'keep1'
    hunters = ('Lance',)
