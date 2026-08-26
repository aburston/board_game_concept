"""Duellist: two champions that win every fight, and a scout to find them one.

Attack 10 destroys any unit in the game in a single round (health stops at
10), so a champion never loses a duel it does not tie. What it cannot do is
find anybody: at ten energy a round it can afford three fights, and every step
it takes looking for one is a point off that. So the legs are bought
separately, in the form of one cheap scout, and the champions sit in the
middle of the board - where a sweep has to come to them - until it reports.
"""

from base import Sweeper
from common import mine, serpentine, size


class Bot(Sweeper):
    name = 'Duellist'
    doctrine = '2 x (a10 h10 e60) + 1 x (a1 h1 e38), champions and an eye'
    army = (
        ('C', 'C', 10, 10, 60,
         [(3, 3), (6, 3)]),
        ('S', 's', 1, 1, 38,
         [(0, 4)]),
    )

    # a champion is worth walking a long way for
    reach = 6

    def floor(self, unit):
        return 10 if unit['type'] == 'C' else 1

    def plan_routes(self, view):
        """The scout sweeps the board; a champion takes a post, then sweeps.

        The post used to be the whole of a champion's route, so a champion
        that reached it stood on it for the rest of the game waiting for
        somebody to walk past. A champion with sixty energy has twenty
        squares in it, and standing on one of them is not what they were
        bought for: the post is where the sweep starts, not where it ends.
        """
        size_x, size_y = size(view)
        for unit in mine(view):
            if unit['name'] in self.routes:
                continue
            if unit['type'] == 'S':
                self.routes[unit['name']] = serpentine(
                    size_y, list(range(size_x)), 0, True)
            else:
                north = unit['y'] < size_y // 2
                post = (4, 3) if north else (5, 6)
                half = list(range(size_x // 2)) if north \
                    else list(range(size_x // 2, size_x))
                self.routes[unit['name']] = [post] + serpentine(
                    size_y, half, post[1], north)
            self.at[unit['name']] = 0

    def wish(self, view, unit, contacts):
        remembered = list(self.seen.values())
        if unit['type'] == 'S':
            return self.route_step(unit)
        return (self.engage_step(unit, contacts)
                + self.approach(unit, contacts or remembered)
                + self.route_step(unit))
