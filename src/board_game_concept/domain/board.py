import copy

from .cell import Empty
from .unit import UnitType



class _Grid:
    """What each square of the board holds, addressed as grid[x, y].

    A unit is handed this object when it is placed and moves itself between
    squares through it, so it stays a plain mapping with no behaviour of its
    own.
    """

    def __init__(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y
        self._cells = {}

    def __getitem__(self, key):
        return self._cells.get(key, Empty())

    def __setitem__(self, key, value):
        self._cells[key] = value


# Board
#   size_x: board size x
#   size_y: board size y


class Board:
    def __init__(self, size_x, size_y):
        self.size_x = size_x
        assert isinstance(size_x, int), "size_x must be an integer value"
        assert (
            (size_x >= 2) and (size_x <= 10)
        ), "size_x must be a value from 2 to 10"

        self.size_y = size_y
        assert isinstance(size_y, int), "size_x must be an integer value"
        assert (
            (size_y >= 2) and (size_y <= 10)
        ), "size_y must be a value from 2 to 10"

        self.board = _Grid(size_x, size_y)
        for x in range(0, size_x):
            for y in range(0, size_y):
                self.board[x, y] = Empty()

        self.units = []
        self.unit_dict = {}
        self.types = {}

    def add(
            self,
            player,
            x,
            y,
            name,
            unit_type,
            health=None,
            energy=None,
            destroyed=False,
            on_board=True,
            restoring=False):
        assert (
            x >= 0 and x < self.size_x and y >= 0 and y < self.size_y
        ), f"coordinates ({x}, {y}) are out of bounds for this board"
        # a brand new unit may only be deployed onto a free square. Restoring a
        # saved game is not a deployment: it puts back whatever was there,
        # including a square more than one unit ended up sharing
        assert (
            restoring or self.squareIsFree(x, y)
        ), f"can't deploy {name} at ({x}, {y}), that square is occupied"
        # restoring a unit the board already holds for this player is not a
        # second unit: a player can be told about the same unit more than once,
        # so put the saved state back into the unit that is already there
        # rather than refusing the whole load
        if restoring:
            existing = self.findUnit(name, player)
            if existing is not None:
                self.types.setdefault(player.number, {})[
                    unit_type.name] = unit_type
                existing.setCoords(x, y)
                if health is not None:
                    existing.setHealth(health)
                if energy is not None:
                    existing.setEnergy(energy)
                existing.setDestroyed(destroyed)
                existing.setOnBoard(on_board)
                return self.units.index(existing) + 1
        # add the unit to a dictionary of types organised by player
        if not (player.number in self.types.keys()):
            self.types[player.number] = {}
        self.types[player.number][unit_type.name] = unit_type
        # make a shallow copy of the unit type to create a new unit instance
        unit = copy.copy(unit_type)
        # reset the unit name
        unit.setName(name)
        # set the player
        unit.setPlayer(player)
        # add a ref to the board into the unit + the size
        unit.setBoard(self.board, self.size_x, self.size_y)
        # keep a copy of the unit coords in the unit
        unit.setCoords(x, y)
        # if the health value has been supplied, set it
        if health is not None:
            unit.setHealth(health)
        # if the energy value has been supplied, set it
        if energy is not None:
            unit.setEnergy(energy)
        # mark the unit destroyed if required (needed when loading ongoing
        # games)
        unit.setDestroyed(destroyed)
        # mark the unit on the board (needed when loading ongoing games)
        unit.setOnBoard(on_board)
        # set the coordinates
        unit.setCoords(x, y)
        # add it to the unit list
        self.units.append(unit)
        # add it to the unit dict
        if name in self.unit_dict:
            for instance in self.unit_dict[name]:
                assert (
                    instance.player != player
                ), f"unit {name} already exists for player {player.number}"
            self.unit_dict[name].append(unit)
        else:
            self.unit_dict[name] = [unit]
        # return the unit id
        return len(self.units)

    def rows(self):
        """The squares of the board, row by row, as whatever occupies them.

        A square holds an Empty, a unit, or - while a contest is unresolved -
        a list of the units on it. Deciding what any of those should look like
        belongs to whoever is displaying the board, not here.
        """
        return [[self.board[x, y] for x in range(self.size_x)]
                for y in range(self.size_y)]

    def getUnitByName(self, name, player=None):
        if player is None:
            assert name in self.unit_dict, f"Unit {name} does not exist"
            return self.unit_dict[name]
        else:
            assert name in self.unit_dict, f"Unit {name} does not exist"
            for unit in self.unit_dict[name]:
                if unit.player == player:
                    return [unit]
            assert False, (
                f"unit {name} does not exist for player {player.number}"
            )

    # the unit this player holds by this name, or None if it holds no such
    # unit. Unlike getUnitByName this answers rather than asserting, so callers
    # can ask whether a unit is already known
    def findUnit(self, name, player):
        for unit in self.unit_dict.get(name, []):
            if unit.player == player:
                return unit
        return None

    def getUnitById(self, index):
        assert (
            isinstance(index, int)
            and index >= 0
            and index < len(self.units)
        ), f"Unit {index} does not exist"
        return self.units[index]

    def getUnitByCoords(self, x, y):
        return self.board[x, y]

    # a square is free when nothing holds it and nothing is waiting to deploy
    # onto it, which matters because deployments are only placed on the board
    # when the turn is resolved
    def squareIsFree(self, x, y):
        if not (type(self.board[x, y]) is Empty):
            return False
        for unit in self.units:
            if (unit.state == UnitType.INITIAL
                    and unit.on_board
                    and not unit.destroyed
                    and unit.x == x
                    and unit.y == y):
                return False
        return True

    def commit(self):
        """Resolve the turn, and report what happened while doing it.

        The events come back in the order they occurred. Nothing here decides
        whether they are shown, logged or dropped.
        """
        events = []
        # clear the seen_by list and the previous turn's origin square in each
        # unit on the board
        for unit in self.units:
            if unit.on_board:
                unit.seen_by = []
                unit.moved_from = None
        # pre_commit the actions required
        for unit in self.units:
            if unit.on_board:
                unit.preCommit(events)
        # commit the changes
        for unit in self.units:
            if unit.on_board:
                unit.commit(events)
        return events
