import copy

from .square import Empty
from .events import Event
from .unit import (UnitType, resolveCollision, resolveContest)


class _Grid:
    """What each square of the board holds, addressed as grid[x, y].

    A unit is handed this object when it is placed and moves itself between
    squares through it, so it stays a plain mapping with no behaviour of its
    own.
    """

    def __init__(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y
        self._squares = {}

    def __getitem__(self, key):
        return self._squares.get(key, Empty())

    def __setitem__(self, key, value):
        self._squares[key] = value


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
        """Put a unit on the board, either as a deployment or as a restore.

        Everything that can refuse the placement is checked before anything is
        registered, so a refused placement leaves the board exactly as it was.
        It used to append the unit and then check its name, which left a unit
        nothing could reach behind every refusal - and the next turn deployed
        it.
        """
        assert (
            x >= 0 and x < self.size_x and y >= 0 and y < self.size_y
        ), f"coordinates ({x}, {y}) are out of bounds for this board"
        # a brand new unit may only be deployed onto a free square. Restoring a
        # saved game is not a deployment: it puts back whatever was there,
        # including a square more than one unit ended up sharing
        assert (
            restoring or self.squareIsFree(x, y)
        ), f"can't deploy {name} at ({x}, {y}), that square is occupied"
        existing = self.findUnit(name, player)
        assert (
            restoring or existing is None
        ), f"unit {name} already exists for player {player.number}"

        # restoring a unit the board already holds for this player is not a
        # second unit: a player can be told about the same unit more than once,
        # so put the saved state back into the unit that is already there
        # rather than refusing the whole load
        if restoring and existing is not None:
            self.types.setdefault(player.number, {})[unit_type.name] = unit_type
            existing.vacate()
            if health is not None:
                existing.setHealth(health)
            if energy is not None:
                existing.setEnergy(energy)
            existing.setDestroyed(destroyed)
            existing.setOnBoard(on_board)
            self._settle(existing, x, y)
            return self.units.index(existing) + 1

        # nothing below here can refuse the placement
        self.types.setdefault(player.number, {})[unit_type.name] = unit_type
        # make a shallow copy of the unit type to create a new unit instance
        unit = copy.copy(unit_type)
        unit.setName(name)
        unit.setPlayer(player)
        # a ref to the board into the unit, plus the size
        unit.setBoard(self.board, self.size_x, self.size_y)
        if health is not None:
            unit.setHealth(health)
        if energy is not None:
            unit.setEnergy(energy)
        # needed when loading ongoing games
        unit.setDestroyed(destroyed)
        unit.setOnBoard(on_board)
        # a unit is a copy of a type, and a type's state is INITIAL, which means
        # "waiting to be deployed". A deployment is exactly that and is placed
        # when the turn resolves; a restore is not, and is put back here and now
        unit.state = UnitType.NOP if restoring else UnitType.INITIAL
        unit.direction = UnitType.NONE
        unit.seen_by = []
        unit.moved_from = None
        self._settle(unit, x, y)
        self.units.append(unit)
        self.unit_dict.setdefault(name, []).append(unit)
        # return the unit id
        return len(self.units)

    def _settle(self, unit, x, y):
        """Give a unit its coordinates, and the square if it is standing on it.

        A deployment is not settled onto the board here: it takes its square
        when the turn resolves. A restored unit already holds its square, and a
        destroyed one holds none.
        """
        unit.setCoords(x, y)
        if unit.state == UnitType.INITIAL or unit.destroyed or not unit.on_board:
            return
        occupant = self.board[x, y]
        if type(occupant) is Empty:
            self.board[x, y] = unit
        elif type(occupant) is list:
            if unit not in occupant:
                occupant.append(unit)
        elif occupant is not unit:
            self.board[x, y] = [occupant, unit]

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

        Three phases: units waiting to be deployed are placed, then every move
        is planned against the board as the turn began and applied together,
        then every square more than one unit finished in is fought out.

        Movement used to be each unit resolving itself against a live board, so
        what a unit found at its destination depended on who had already moved.
        The same orders could produce different outcomes, and two units ordered
        at each other walked straight through one another.

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
        self._deploy(events)
        pairs, free = self._move(events)
        self._fight(events, pairs, free)
        return events

    def _deploy(self, events):
        """Place the units waiting to be put on the board."""
        for unit in self.units:
            if unit.on_board and not unit.destroyed and unit.state == UnitType.INITIAL:
                unit.occupy(unit.x, unit.y)
                unit.state = UnitType.NOP
                events.append(Event(
                    'deployed', unit=unit.name, x=unit.x, y=unit.y))

    def _move(self, events):
        """Plan every move against the board as the turn began, then apply them.

        Returns the head-on pairs to be fought out, and the set of squares the
        movement left empty - judged once, so that one contest resolving cannot
        change where another contest's survivors may fall back to.
        """
        plans = []
        for unit in self.units:
            if not unit.on_board or unit.destroyed:
                continue
            destination, refusal = unit.planMove()
            if refusal is not None:
                events.append(Event(
                    'refused', unit=unit.name, x=unit.x, y=unit.y,
                    reason=refusal))
            if destination is not None:
                plans.append([unit, (unit.x, unit.y), destination])
            # the order is consumed whether or not it was carried out
            if unit.state == UnitType.MOVING:
                unit.state = UnitType.NOP
                unit.direction = UnitType.NONE

        # two units each ordered into the square the other is leaving collide
        # rather than trading places
        by_origin = {origin: plan for plan, origin in
                     ((plan, plan[1]) for plan in plans)}
        pairs = []
        paired = set()
        for unit, origin, destination in plans:
            if id(unit) in paired:
                continue
            other = by_origin.get(destination)
            if other is None or id(other[0]) in paired:
                continue
            if other[2] == origin:
                pairs.append(tuple(sorted(
                    (unit, other[0]),
                    key=lambda u: (u.player.number, u.name))))
                paired.add(id(unit))
                paired.add(id(other[0]))
        # fought in a settled order, so that two collisions resolving in the
        # same turn cannot depend on which was noticed first
        pairs.sort(key=lambda pair: (pair[0].player.number, pair[0].name))

        # everything planned is paid for, whether it arrives or collides
        for unit, origin, destination in plans:
            unit.energy = unit.energy - UnitType.MOVE_COST

        movers = [plan for plan in plans if id(plan[0]) not in paired]

        # how each move reads is decided from the plan, before any of it is
        # applied. Reading it off the destination square as each unit was
        # placed made it depend on which mover went first, so two units
        # arriving together were narrated as one engaging the other, and which
        # one was whichever the board happened to hold first
        standing = {}
        for x in range(self.size_x):
            for y in range(self.size_y):
                occupant = self.board[x, y]
                if type(occupant) is UnitType:
                    standing[(x, y)] = occupant
        leaving = {id(plan[0]) for plan in movers}
        arrivals = {}
        for unit, origin, destination in movers:
            arrivals[destination] = arrivals.get(destination, 0) + 1

        # vacate every mover's origin before placing any of them, so that a
        # chain of units advancing together needs no ordering rule
        for unit, origin, destination in movers:
            unit.vacate()
        for unit, origin, destination in movers:
            unit.moved_from = origin
            unit.occupy(*destination)
            held_by = standing.get(destination)
            if held_by is not None and id(held_by) not in leaving:
                detail = {'target': held_by.name}
                kind = 'engaged'
            elif arrivals[destination] > 1:
                detail = {}
                kind = 'joined'
            else:
                detail = {}
                kind = 'moved'
            events.append(Event(
                kind, unit=unit.name, x=destination[0], y=destination[1],
                **detail))

        free = {(x, y) for x in range(self.size_x) for y in range(self.size_y)
                if type(self.board[x, y]) is Empty}
        return pairs, free

    def _fight(self, events, pairs, free):
        """Fight out every square more than one unit finished the turn in."""
        for x in range(self.size_x):
            for y in range(self.size_y):
                square = self.board[x, y]
                if not (type(square) is list):
                    continue
                if len(square) > 1:
                    resolveContest(self.board, x, y, list(square), free, events)
                else:
                    self.board[x, y] = square[0]

        # a collision is fought between whoever is still standing after the
        # squares have been decided
        for first, second in pairs:
            if first.destroyed or second.destroyed:
                continue
            resolveCollision(first, second, events)

        # a destroyed unit holds no square
        for unit in self.units:
            if unit.destroyed and unit.on_board:
                unit.vacate()
                unit.on_board = False
                events.append(Event('removed', unit=unit.name))
