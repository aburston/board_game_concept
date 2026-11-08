"""The board as an army knows it: one map per player, shared by its units.

Nothing in this game is sensed at a distance. A square becomes known because
a friendly unit stood on it, or fought on it, and what the army knows is the
sum of what its units have touched - kept in step across the army for free,
because the radio that would carry it costs nothing to run when it carries
facts. What it does not carry is intent; that is what `SAY` is for.

The map keeps two things with a turn stamp: the squares friendly units have
stood on, and the enemies they have fought, with the design contact revealed.
Friends are not kept, because where the army stands is read off the board
each turn; the map is memory, and the board is the present.
"""

from .program import MAP_EMPTY, MAP_ENEMY, MAP_UNKNOWN


class ArmyMap:

    def __init__(self):
        # square -> the last turn a friendly unit stood on it
        self.visited = {}
        # square -> (turn met, attack, health) of the enemy met there
        self.enemies = {}

    def observe(self, units, player_number, turn):
        """Update from the board as a turn left it.

        Every friendly unit that fought this turn tells the map where the
        enemy it met is standing now and what it is built with; every
        friendly unit standing on a square tells the map the square is
        theirs, which also clears any enemy once recorded there.
        """
        for unit in units:
            if unit.player is None or unit.player.number != player_number:
                continue
            for seen in unit.seen_by:
                if seen.player is None or seen.player.number == player_number:
                    continue
                if seen.destroyed or not seen.on_board:
                    continue
                self.enemies[(seen.x, seen.y)] = (
                    turn, seen.type_attack, seen.type_health)
        for unit in units:
            if unit.player is None or unit.player.number != player_number:
                continue
            if unit.destroyed or not unit.on_board:
                continue
            self.visited[(unit.x, unit.y)] = turn
            self.enemies.pop((unit.x, unit.y), None)

    def at(self, x, y, turn=None):
        """`(kind, turn, attack, health)` for a square, friends aside."""
        met = self.enemies.get((x, y))
        if met is not None:
            return (MAP_ENEMY, met[0], met[1], met[2])
        seen = self.visited.get((x, y))
        if seen is not None:
            return (MAP_EMPTY, seen, -1, -1)
        return (MAP_UNKNOWN, -1, -1, -1)

    def enemy_squares(self):
        return list(self.enemies)

    def record(self):
        """The map as plain data, in a settled order, for storing and hashing."""
        return {
            'visited': [[x, y, turn] for (x, y), turn
                        in sorted(self.visited.items())],
            'enemies': [[x, y, turn, attack, health]
                        for (x, y), (turn, attack, health)
                        in sorted(self.enemies.items())],
        }

    @classmethod
    def from_record(cls, record):
        made = cls()
        for x, y, turn in (record or {}).get('visited', []):
            made.visited[(int(x), int(y))] = int(turn)
        for x, y, turn, attack, health in (record or {}).get('enemies', []):
            made.enemies[(int(x), int(y))] = (int(turn), int(attack),
                                              int(health))
        return made
