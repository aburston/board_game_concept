"""Turtle: hold the back, meet the attacker on full pockets, then finish it.

The bet is that an enemy is invisible until it is fought (R6.2), so a unit
that has not moved is a hidden square somebody has to step on to find. Energy
is only spent by moving and attacking, so a unit that stands still keeps its
whole pocket for the fight it is walked into - and it rests besides (R3.9),
which the attacker crossing the board does not.

What this doctrine used to do was hold for ever, and its own docstring
admitted the weakness: holding still kills nobody who does not come to you, so
the best it could do was not lose. That is not a strategy, it is a refusal to
play, and two of them in a series produce games that measure nothing. So the
hold is now a phase rather than the whole plan. Twenty turns as a fortress -
long enough for any attacker on the board to arrive and be met on full
pockets - and then the line comes forward and goes looking, whatever it has or
has not seen.
"""

from base import Sweeper


class Bot(Sweeper):
    name = 'Turtle'
    doctrine = '4 x (a1 h7 e42), dispersed at the back, hold 20 turns then advance'
    army = (
        ('F', 'F', 1, 7, 42,
         [(1, 0), (8, 0), (4, 1), (6, 2)]),
    )

    # a health-7 unit pays 2 a square, so forty-two energy is twenty-one
    # squares - twice the width of the board. It can afford to spend twenty
    # turns standing still and still cross the board twice afterwards, which
    # is what makes the hold a phase rather than a surrender
    patience = 20
