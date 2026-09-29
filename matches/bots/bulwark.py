"""Bulwark: a wall across the frontier, and four Heavies behind it.

Eight Walls (attack 0, health 10, energy 0, ten points each) along the row
against the frontier close the half: nothing gets in without breaking one,
and under one strike a turn a Wall takes a Line four turns, a Runner five
and a Heavy two, with the attacker falling back after every strike that
does not finish it (R5.8). Behind the line, four Heavies wait for whatever
comes through the hole it makes, and go no further than two squares to meet
it. A Keep carries the flag at the edge, with a Runner and a Scout beside it.

246 points. Nobody hunts: this doctrine cannot take a flag, only keep one,
and what it tests is whether a flag can be kept on this board at all.
"""

from base import Doctrine
from common import fares, mine, resolve


class Bot(Doctrine):
    name = 'Bulwark'
    doctrine = ('8 x Wall across the frontier row + 4 x Heavy behind + Keep '
                'with the flag, Runner, Scout; nobody hunts')
    army = (('Wall', 'W', 0, 10, 0, [(x, 3) for x in range(8)]),
            ('Heavy', 'H', 5, 10, 15, [(1, 2), (3, 2), (4, 2), (6, 2)]),
            ('Keep', 'K', 1, 10, 5, [(3, 0)]),
            ('Runner', 'r', 2, 4, 10, [(4, 0)]),
            ('Scout', 'o', 0, 2, 12, [(0, 0)]))
    flag = 'keep1'
    reach = 2

    def wish(self, view, unit, contacts):
        steps = self.engage_step(unit, contacts)
        if unit['type'] == 'Heavy':
            steps += self.approach(unit, contacts)
        return steps

    def orders(self, view):
        contacts = self.targets(view)
        fare = fares(view)
        wishes = {}
        for unit in mine(view):
            if unit['energy'] - fare[unit['name']] < self.floor(unit):
                continue
            wishes[unit['name']] = self.wish(view, unit, contacts)
        return resolve(view, wishes, keep_attack=False, together=contacts)
