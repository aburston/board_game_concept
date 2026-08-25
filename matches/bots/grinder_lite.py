"""Grinder at the old hundred-point budget, for the control game."""

from grinder import Bot as Grinder


class Bot(Grinder):
    name = 'Grinder-100'
    doctrine = '3 x (a1 h10 e20) on 100 points, spread across the middle'
    army = (('G', 'G', 1, 10, 20, [(0, 3), (4, 3), (9, 3)]),)
