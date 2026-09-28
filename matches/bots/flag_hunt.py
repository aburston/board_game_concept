"""Flag Hunt: the stock army, sent at the one square it can see.

Every player is shown where every flag stands (R6.5), from the first turn,
whoever they have met. This doctrine takes that at its word: everything that
can walk goes for the enemy flag square by the shortest route it can find
round its own units - the Runners and Lines with the legs for it, the
Heavies at their own pace, the Pawns a square every other turn, and the
Scouts, which strike nothing but hold a square in the exchange like anything
else. The Keeps hold, and the Walls cannot do otherwise.

The whole army goes because the stock array leaves it no choice: the back
rank is boxed in by the front rank until the front rank moves, so a hunt
that kept the Pawns and Scouts at home would keep the Runners and Lines
there too (game 203 of the series, before this was so). Whatever a hunter
meets on the way, it fights; several may be ordered onto one seen enemy at
once, because it is the strikes landing in one exchange that kill (R5.11).

The carrier is a Keep of ten health behind two Heavies of attack five. Two
Lines and two Runners land ten in one exchange if all four arrive together,
which is exactly one Keep. Whether four can arrive together, past what stands
in front, is the question.
"""

from base import Hunt


class Bot(Hunt):
    name = 'Flag Hunt'
    doctrine = ('the stock army; everything but the Keeps and Walls goes for '
                'the enemy flag square by the shortest route round its own')
    hunters = ('Runner', 'Line', 'Heavy', 'Pawn', 'Scout')
