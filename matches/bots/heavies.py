"""Heavies: seven Heavies, a Keep and a Runner.

The dearest thing in the catalogue, seven times: attack 5, health 10, energy
15, thirty points and a fare of three. Nothing in the stock army destroys a
Heavy in one exchange short of two Lances arriving together, and a Heavy's
five destroys a Pawn, a Runner, a Scout or a Lance outright and a Line in two.

Fifteen energy against a fare of three and a strike of five is three squares,
then two turns' rest for every further one - and the board is eight rows, so
a Heavy that starts on the frontier row is four squares from the far edge.
The Heavies go for the flag; the Keep and the Runner stay at the edge.
"""

from base import Hunt


class Bot(Hunt):
    name = 'Heavies'
    doctrine = ('7 x Heavy (a5 h10 e15) + Keep with the flag + Runner; '
                'the Heavies hunt')
    army = (('Heavy', 'H', 5, 10, 15,
             [(x, 3) for x in range(1, 7)] + [(4, 2)]),
            ('Keep', 'K', 1, 10, 5, [(3, 0)]),
            ('Runner', 'r', 2, 4, 10, [(4, 0)]))
    flag = 'keep1'
    hunters = ('Heavy',)
