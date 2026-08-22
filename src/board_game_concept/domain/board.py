try:
    import board
except ImportError:
    board = None

import copy

from .cell import Empty
from .player import Player
from .unit import UnitType

DEBUG = False


class _FallbackBoard:
    def __init__(self, dimensions):
        self.size_x, self.size_y = dimensions
        self._cells = {}

    def __getitem__(self, key):
        return self._cells.get(key, Empty())

    def __setitem__(self, key, value):
        self._cells[key] = value

    def draw(self, callback=None):
        for y in range(self.size_y):
            row = ''
            for x in range(self.size_x):
                unit = self[x, y]
                row += callback(unit) if callback is not None else str(unit)
            print(row)


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

        self.board = board.Board((size_x, size_y)) if board is not None else _FallbackBoard((size_x, size_y))
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
        if DEBUG:
            print(type(unit_type))
            print(type(player))
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

    def print(self, player=None):
        def _render_cell(cell):
            if type(cell) is Empty:
                return cell.__str__()
            if type(cell) is list:
                # a contested square holds several units: show one of them
                # rather than the repr of the list
                occupants = [unit for unit in cell if not unit.destroyed]
                if not occupants:
                    return Empty().__str__()
                if player is None:
                    return occupants[0].__str__()
                for unit in occupants:
                    if unit.player == player:
                        return unit.__str__()
                return Empty().__str__()
            if player is None or cell.player == player:
                return cell.__str__()
            return Empty().__str__()
        self.board.draw(callback=_render_cell)

    def listTypes(self, player=None):
        typesStr = "types:\n"
        for player in self.types.keys():
            for type_name in self.types[player].keys():
                unit_type = self.types[player][type_name]
                typesStr = typesStr + (
                    f'- {{ player: "{player}", name: "{unit_type.name}", '
                    f'symbol: "{unit_type.symbol}", attack: "{unit_type.attack}", '
                    f'health: "{unit_type.health}", energy: "{unit_type.energy}" }}\n'
                )
        return typesStr

    def listUnits(self, player=None):
        # board information
        units_str = "board: {" + \
            f" size_x: {self.size_x}, size_y: {self.size_y}" + "}\n"

        # player making request
        if player is None:
            units_str = units_str + f"player: {player}\n"
        else:
            units_str = units_str + f"player: {player.number}\n"

        # units seen by player
        i = 0
        tmp_str = ""
        while i < len(self.units):
            if player is None:
                tmp_str = tmp_str + \
                    "  - { " + f"id: {i}, " + self.units[i].dump() + " }\n"
            elif self.units[i].player == player:
                tmp_str = tmp_str + \
                    "  - { " + f"id: {i}, " + self.units[i].dump() + " }\n"
            else:
                # a unit seen by several of this player's units is still one
                # unit, so it is listed once
                for seen in self.units[i].seen_by:
                    if (player.number == seen.player.number):
                        tmp_str = tmp_str + \
                            "  - { " + f"id: {i}, " + self.units[i].dump() + " }\n"
                        break
            i = i + 1
        if tmp_str == "":
            units_str = units_str + "units: None\n"
        else:
            units_str = units_str + "units:\n" + tmp_str

        return units_str

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
        # clear the seen_by list and the previous turn's origin square in each
        # unit on the board
        for unit in self.units:
            if unit.on_board:
                unit.seen_by = []
                unit.moved_from = None
        # pre_commit the actions required
        for unit in self.units:
            if unit.on_board:
                unit.preCommit()
        # commit the changes
        for unit in self.units:
            if unit.on_board:
                unit.commit()
