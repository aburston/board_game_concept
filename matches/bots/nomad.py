"""Nomad: three runners that never fight and are never caught.

A game is decided when one player has nothing standing (R7.2), so a unit that
survives is a veto on losing. These are the cheapest units that can keep
moving for thirty turns, and their doctrine is to spend that on being
somewhere else: a unit is only found by something stepping onto the square it
is standing on, and every destination this turn is chosen before anybody sees
anybody move (R3.4), so a unit that is always moving is a unit nobody can aim
at.

It cannot win. One point of health means every fight it takes is a fight it
loses, so it never takes one.
"""

from base import Sweeper
from common import DIRECTIONS


class Bot(Sweeper):
    name = 'Nomad'
    doctrine = '3 x (a1 h1 e30), keep moving, never fight'
    army = (('N', 'N', 1, 1, 30, [(2, 9), (5, 9), (8, 9)]),)

    def floor(self, unit):
        return 0

    def wish(self, view, unit, contacts):
        """Away from anything that has been seen, and otherwise onward."""
        away = []
        for x, y in contacts:
            dx = unit['x'] - x
            dy = unit['y'] - y
            if abs(dx) >= abs(dy) and dx:
                away.append((1 if dx > 0 else -1, 0))
            elif dy:
                away.append((0, 1 if dy > 0 else -1))
        return away + self.route_step(unit) + list(DIRECTIONS.values())
