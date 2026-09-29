"""Garrison: the stock army, exactly as handed, and nobody moves.

The control. A seat that keeps what the game gave it and gives no order at
all: every unit rests every turn (R3.9), and the only fighting it does is
striking back at whatever walks into one of its squares (R5.2). What the
other nineteen games show about a doctrine is measured against what this one
shows about the army alone.
"""

from base import Doctrine


class Bot(Doctrine):
    name = 'Garrison'
    doctrine = 'the stock army as given; no unit is ever ordered'

    def orders(self, view):
        return []
