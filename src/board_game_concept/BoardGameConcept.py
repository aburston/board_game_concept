#!/usr/bin/env python3

try:
    import board
except ImportError:
    board = None

import copy

DEBUG = False


class Empty:
    def __str__(self):
        return "#"


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


class Player:
    def __init__(self, number):
        self.number = number
        assert (len(str(number)) >= 1), "number must be one or more character"

# Unit
#   name: One or more character
#   symbol: One single character
#   speed: speed 10 is to move once per clock tick and 1 is to move once every 10th tick
#   attack: damage per attack
#   health: total amount of health


class UnitType:

    NONE = 0
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4

    INITIAL = 0
    MOVING = 1
    NOP = 2

    def __init__(self, name, symbol, attack, health, energy):
        self.name = name
        self.type_name = name

        # XXX this is a rather not so nice way of preserving the original type name
        # when this object is copied and turned into a unit
        assert (len(str(name)) >= 1), "name must be one or more character"

        self.symbol = symbol
        assert (len(str(symbol)) == 1), "symbol must be only one character"

        self.attack = attack
        assert isinstance(attack, int), "attack must be an integer value"
        assert ((attack >= 1) and (attack <= 10)
                ), "attack must be a value from 1 to 10"

        self.health = health
        assert isinstance(health, int), "health must be an integer value"
        assert ((health >= 1) and (health <= 10)
                ), "health must be a value from 1 to 10"

        self.energy = energy
        assert isinstance(energy, int), "health must be an integer value"
        assert ((energy >= 1) and (energy <= 100)
                ), "energy must be a value from 1 to 100"

        self.state = UnitType.INITIAL
        self.direction = UnitType.NONE
        self.destroyed = False
        self.on_board = False
        self.seen_by = []
        self.player = None
        # cell this unit vacated during the current turn's preCommit phase, so
        # that an undecided contest can send it back where it came from
        self.moved_from = None

    def move(self, direction):
        self.state = UnitType.MOVING
        self.direction = direction

    def setName(self, name):
        self.name = name

    def setBoard(self, board, board_max_x, board_max_y):
        self.board = board
        self.board_max_x = board_max_x
        self.board_max_y = board_max_y
        self.on_board = True

    def setCoords(self, x, y):
        self.x = x
        self.y = y

    def setHealth(self, health):
        self.health = health

    def setEnergy(self, energy):
        self.energy = energy

    def setDestroyed(self, destroyed):
        self.destroyed = destroyed

    def setOnBoard(self, on_board):
        self.on_board = on_board

    def setPlayer(self, player):
        self.player = player
        assert (type(player) is Player), "player object must be provided"

    def incomingAttack(self, attack):
        if DEBUG:
            print(f"incomingAttack: {self.name} being attacked")
        self.health = self.health - attack
        if self.health <= 0:
            self.destroyed = True

    # calculates attacks and marks units as DESTROYED, creates arrays of units in squares where multiple units are
    # trying to move simultaneously into the same square
    def preCommit(self):
        if self.state == UnitType.INITIAL:
            # deployment is resolved in commit(), and may land on an occupied
            # cell, which starts a contest rather than failing
            pass
        elif self.state == UnitType.MOVING:
            dest_x = self.x
            dest_y = self.y
            if self.direction == UnitType.NORTH:
                dest_y = self.y - 1
                self.direction = UnitType.NONE
                if dest_y < 0:
                    self.y = 0
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.EAST:
                dest_x = self.x + 1
                self.direction = UnitType.NONE
                if dest_x > self.board_max_x - 1:
                    self.x = self.board_max_x - 1
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.SOUTH:
                dest_y = self.y + 1
                self.direction = UnitType.NONE
                if dest_y > self.board_max_y - 1:
                    self.y = self.board_max_y - 1
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.WEST:
                dest_x = self.x - 1
                self.direction = UnitType.NONE
                if dest_x < 0:
                    self.x = 0
                    self.state = UnitType.NOP
                    return
            else:
                self.state = UnitType.NOP
                return

            if type(self.board[dest_x, dest_y]) is Empty:
                energy = self.energy - (self.energy // 100 + 1)
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    self.vacate()
                    self.moved_from = (self.x, self.y)
                    self.setCoords(dest_x, dest_y)
                    self.board[self.x, self.y] = [self]
                    if DEBUG:
                        print(
                            f"preCommit: {self.name} move to [{self.x},{self.y}]"
                        )
            elif type(self.board[dest_x, dest_y]) is list:
                energy = self.energy - (self.energy // 100 + 1)
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    self.vacate()
                    self.moved_from = (self.x, self.y)
                    self.setCoords(dest_x, dest_y)
                    self.board[dest_x, dest_y].append(self)
                    if DEBUG:
                        print(
                            f"preCommit: {self.name} added to list in [{self.x},{self.y}]"
                        )
            elif type(self.board[dest_x, dest_y]) is UnitType:
                # moving into an occupied square starts a combat exchange
                if self.energy >= self.attack:
                    target = self.board[dest_x, dest_y]
                    self.vacate()
                    self.moved_from = (self.x, self.y)
                    self.setCoords(dest_x, dest_y)
                    self.board[dest_x, dest_y] = [target, self]
                    if DEBUG:
                        print(
                            f"preCommit: {self.name} engages {target.name} in [{self.x},{self.y}]"
                        )
            self.state = UnitType.NOP
            return
        else:
            pass

    # takes this unit out of the cell it holds, leaving behind anything else
    # sharing that cell
    def vacate(self):
        cell = self.board[self.x, self.y]
        if not (type(cell) is list):
            self.board[self.x, self.y] = Empty()
            return
        remaining = [unit for unit in cell if unit is not self]
        if not remaining:
            self.board[self.x, self.y] = Empty()
        elif len(remaining) == 1:
            self.board[self.x, self.y] = remaining[0]
        else:
            self.board[self.x, self.y] = remaining

    # sends this unit back to the cell it left this turn, so that an undecided
    # contest leaves the board as it was. Returns True if the unit retreated.
    def retreat(self):
        if self.moved_from is None:
            # nothing to go back to: the unit was already holding this cell, or
            # was deployed onto it this turn
            return False
        from_x, from_y = self.moved_from
        if not (type(self.board[from_x, from_y]) is Empty):
            # something else took the cell during this turn, so there is nowhere
            # to go back to and the unit stays where it is
            return False
        self.setCoords(from_x, from_y)
        self.board[from_x, from_y] = self
        self.moved_from = None
        if DEBUG:
            print(f"retreat: {self.name} falls back to [{from_x},{from_y}]")
        return True

    # resolves the contest in the cell this unit occupies. Attack rounds repeat
    # until at most one contestant is left standing or a round lands no attacks,
    # which is what stops a contest nobody can win from spinning forever. There
    # is friendly fire: a contestant attacks every other unit in the cell,
    # whoever owns it. Running out of energy never destroys a unit, it only
    # makes it inert.
    def resolveContest(self):
        cell_x = self.x
        cell_y = self.y
        contestants = self.board[cell_x, cell_y]
        if DEBUG:
            print(
                f"{self.name} commit process list in [{cell_x},{cell_y}]: "
                f"{contestants}"
            )
        while True:
            # recount the survivors afresh each round, rather than decrementing
            # a running total that counts the same casualty again every round
            standing = [unit for unit in contestants if not unit.destroyed]
            if len(standing) < 2:
                break
            if DEBUG:
                print(
                    f"{self.name} commit process {len(standing)} units in square "
                    f"[{cell_x},{cell_y}]"
                )
            attacked = False
            # attackers and targets are the units standing at the start of the
            # round, so a unit destroyed mid-round still lands its own attack
            for unit in standing:
                for target in standing:
                    if unit is target:
                        continue
                    energy = unit.energy - unit.attack
                    if energy < 0:
                        # too spent to attack: inert, but not destroyed
                        continue
                    unit.energy = energy
                    if DEBUG:
                        print(f"commit: {unit.name} attack {target.name}")
                    target.incomingAttack(unit.attack)
                    # populuate seen_by
                    unit.seen_by.append(target)
                    target.seen_by.append(unit)
                    attacked = True
            if not attacked:
                # no contestant can pay for an attack, so the contest is over
                break

        for unit in contestants:
            if unit.destroyed:
                unit.on_board = False

        survivors = [unit for unit in contestants if not unit.destroyed]
        if len(survivors) > 1:
            # nobody won the cell, so everyone who moved in goes back where it
            # came from and the cell is left as it was
            survivors = [unit for unit in survivors if not unit.retreat()]

        if not survivors:
            self.board[cell_x, cell_y] = Empty()
        elif len(survivors) == 1:
            self.board[cell_x, cell_y] = survivors[0]
            if DEBUG:
                print(
                    f"{self.name} commit add unit to square [{cell_x},{cell_y}]"
                )
        else:
            # no survivor could fall back, so they share the cell
            self.board[cell_x, cell_y] = survivors

    # processes all arrays created in the precommit phase, by calculating attacks and marking units DESTROYED
    # removes all DESTROYED units from the board
    def commit(self):
        if self.state == UnitType.INITIAL:
            # add the unit to the board, joining whatever already holds the
            # cell rather than requiring it to be empty
            occupant = self.board[self.x, self.y]
            if type(occupant) is Empty:
                self.board[self.x, self.y] = self
            elif type(occupant) is list:
                occupant.append(self)
            else:
                self.board[self.x, self.y] = [occupant, self]
            self.state = UnitType.NOP
            if type(self.board[self.x, self.y]) is list:
                # deploying onto an occupied cell contests it, and the contest
                # is settled in this same turn
                self.resolveContest()
        elif self.state == UnitType.MOVING:
            assert not (
                self.state == UnitType.MOVING), "During commit, no unit should be in the MOVING state"
        else:
            if type(self.board[self.x, self.y]) is list:
                self.resolveContest()
            else:
                if self.destroyed:
                    self.vacate()
                    self.on_board = False
                    if DEBUG:
                        print(
                            f"{self.name} commit removing unit from square [{self.x},{self.y}]")

    def dump(self):
        result = (
            f'player: "{self.player.number}", '
            f'type: "{self.type_name}", '
            f'name: "{self.name}", '
            f'symbol: "{self.symbol}", '
            f'attack: "{self.attack}", '
            f'health: "{self.health}", '
            f'energy: "{self.energy}", '
            f'x: {self.x}, y: {self.y}, '
            f'state: {self.state}, direction: {self.direction}, '
            f'destroyed: {self.destroyed}, on_board: {self.on_board}'
        )
        if DEBUG:
            print(result)
        return result

    def __str__(self):
        return (self.symbol)

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
            on_board=True):
        if DEBUG:
            print(type(unit_type))
            print(type(player))
        assert (
            x >= 0 and x < self.size_x and y >= 0 and y < self.size_y
        ), f"coordinates ({x}, {y}) are out of bounds for this board"
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
                ), f"unit {name} already exists for {player.name}"
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
                # a contested cell holds several units: show one of them rather
                # than the repr of the list
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
                for seen in self.units[i].seen_by:
                    # print(f"{player.name} {seen.player.number}")
                    if (player.number == seen.player.number):
                        tmp_str = tmp_str + \
                            "  - { " + f"id: {i}, " + self.units[i].dump() + " }\n"
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
            assert True, f"unit {name} does not exist"

    def getUnitById(self, index):
        assert (
            isinstance(index, int)
            and index >= 0
            and index < len(self.units)
        ), f"Unit {index} does not exist"
        return self.units[index]

    def getUnitByCoords(self, x, y):
        return self.board[x, y]

    def commit(self):
        # clear the seen_by list and the previous turn's origin cell in each
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


# class testing
if __name__ == "__main__":
    white = UnitType("White", "W", 1, 2, 100)
    black = UnitType("Black", "B", 1, 1, 100)

    p1 = Player(1)
    p2 = Player(2)

    b = Board(4, 4)
    b.print()

    w1_id = b.add(p1, 0, 0, "w1", white)
    b.add(p1, 0, 1, "w2", white)
    b.add(p1, 0, 2, "w3", white)
    b.add(p1, 0, 3, "w4", white)

    b.add(p2, 3, 0, "b1", black)
    b.add(p2, 3, 1, "b2", black)
    b.add(p2, 3, 2, "b3", black)
    b.add(p2, 3, 3, "b4", black)
    b.add(p2, 2, 2, "b5", black)
    b.commit()

    w1 = b.getUnitById(0)
    b1 = b.getUnitByName("b1")[0]
    w2 = b.getUnitByName("w2")[0]
    b2 = b.getUnitByName("b2")[0]
    b3 = b.getUnitByName("b3")[0]
    b4 = b.getUnitByName("b4")[0]
    b5 = b.getUnitByName("b5")[0]
    w4 = b.getUnitByName("w4")[0]

    b.print()
    print(b.listUnits())

    w1.move(UnitType.EAST)
    b1.move(UnitType.WEST)
    w2.move(UnitType.EAST)
    b.commit()

    b.print()
    print(b.listUnits())
    print(b.listUnits(p1))
    print(b.listUnits(p2))

    w1.move(UnitType.EAST)
    w2.move(UnitType.EAST)
    b2.move(UnitType.WEST)
    b5.move(UnitType.NORTH)

    b.commit()
    b.print()
    print(b.listUnits())
    print(b.listUnits(p1))
    print(b.listUnits(p2))

    w1.move(UnitType.NORTH)
    w4.move(UnitType.WEST)
    b3.move(UnitType.EAST)
    b4.move(UnitType.SOUTH)

    b.commit()
    b.print()
    print(b.listUnits())
