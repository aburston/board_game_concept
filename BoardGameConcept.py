#!/usr/bin/env python3

import board
import copy

DEBUG = False

class Empty:
    def __str__(self):
        return "#"

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

    NONE = 0;
    NORTH = 1;
    EAST = 2;
    SOUTH = 3;
    WEST = 4;

    INITIAL = 0;
    MOVING = 1;
    NOP = 2;

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
        assert ((attack >= 1) and (attack <= 10)), "attack must be a value from 1 to 10"

        self.health = health
        assert isinstance(health, int), "health must be an integer value"
        assert ((health >= 1) and (health <= 10)), "health must be a value from 1 to 10"

        self.energy = energy
        assert isinstance(energy, int), "health must be an integer value"
        assert ((energy >= 1) and (energy <= 100)), "energy must be a value from 1 to 100"

        self.state = UnitType.INITIAL
        self.direction = UnitType.NONE
        self.destroyed = False
        self.on_board = False
        self.seen_by = []
        self.player = None

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
            # make sure that location on the board is empty
            assert type(self.board[self.x, self.y]) is Empty, f"can't add {self.name} to board at ({self.x},{self.y})"
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
                    self.board[self.x, self.y] = Empty()
                    self.setCoords(dest_x, dest_y)
                    self.board[self.x, self.y] = [ self ]
                    if DEBUG:
                        print(f"preCommit: {self.name} move to [{self.x},{self.y}]")
            elif type(self.board[dest_x, dest_y]) is list:
                energy = self.energy - (self.energy // 100 + 1)
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    self.board[self.x, self.y] = Empty()
                    self.setCoords(dest_x, dest_y)
                    self.board[dest_x, dest_y].append(self)
                    if DEBUG:
                        print(f"preCommit: {self.name} added to list in [{self.x},{self.y}]")
            elif type(self.board[dest_x, dest_y]) is UnitType:
                energy = self.energy - self.attack
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    target = self.board[dest_x, dest_y]
                    target.incomingAttack(self.attack)
                    # populuate seen_by
                    self.seen_by.append(target)
                    target.seen_by.append(self)
                    if DEBUG:
                        print(f"preCommit: {self.name} attack {target.name}")
            self.state = UnitType.NOP
            return
        else:
            pass

    # processes all arrays created in the precommit phase, by calculating attacks and marking units DESTROYED
    # removes all DESTROYED units from the board
    def commit(self):
        if self.state == UnitType.INITIAL:
            # make sure that location on the board is empty
            assert type(self.board[self.x, self.y]) is Empty, f"can't add {name} to board at ({x},{y})"
            # add the unit to the board
            self.board[self.x, self.y] = self
            self.state = UnitType.NOP
        elif self.state == UnitType.MOVING:
            assert not(self.state == UnitType.MOVING), "During commit, no unit should be in the MOVING state"
        else:
            if type(self.board[self.x, self.y]) is list:
                unit_count = len(self.board[self.x, self.y])
                if DEBUG:
                    print(f"{self.name} commit process list in [{self.x},{self.y}]: {self.board[self.x, self.y]}")
                while unit_count > 1:
                    if DEBUG:
                        print(f"{self.name} commit process {unit_count} units in square [{self.x},{self.y}]")
                    for unit in self.board[self.x, self.y]:
                        for target in self.board[self.x, self.y]:
                            if DEBUG:
                                print(f"{self.name} commit processing {unit.name} -> {target.name}")
                            if not(unit is target):
                                energy = unit.energy - unit.attack
                                if energy >= 0:
                                    unit.energy = energy
                                    if DEBUG:
                                        print(f"commit: {target.name} attack {unit.name}")
                                    target.incomingAttack(unit.attack)
                                    # populuate seen_by
                                    unit.seen_by.append(target)
                                    target.seen_by.append(unit)
                    for unit in self.board[self.x, self.y]:
                        if unit.destroyed:
                            unit_count = unit_count - 1
                for unit in self.board[self.x, self.y]:
                    if unit.destroyed == False:
                        self.board[self.x, self.y] = unit
                        if DEBUG:
                            print(f"{self.name} commit add unit to square [{self.x},{self.y}]")
                    else:
                        unit.on_board = False
                if unit_count == 0:
                    self.board[self.x, self.y] = Empty()
            else:
                if self.destroyed:
                    self.board[self.x, self.y] = Empty()
                    self.on_board = False
                    if DEBUG:
                        print(f"{self.name} commit removing unit from square [{self.x},{self.y}]")

    def dump(self):

        result = f"player: \"{self.player.number}\", type: \"{self.type_name}\", name: \"{self.name}\", symbol: \"{self.symbol}\", attack: \"{self.attack}\", health: \"{self.health}\", energy: \"{self.energy}\", x: {self.x}, y: {self.y}, state: {self.state}, direction: {self.direction}, destroyed: {self.destroyed}, on_board: {self.on_board}"
        if DEBUG:
            print(result)
        return(result)

    def __str__(self):
        return(self.symbol)

# Board
#   size_x: board size x
#   size_y: board size y
class Board:
    def __init__(self, size_x, size_y):
        self.size_x = size_x
        assert isinstance(size_x, int), "size_x must be an integer value"
        assert ((size_x >= 2) and (size_x <= 10)), "size_x must be a value from 2 to 10"

        self.size_y = size_y
        assert isinstance(size_y, int), "size_x must be an integer value"
        assert ((size_y >= 2) and (size_y <= 10)), "size_y must be a value from 2 to 10"

        self.board = board.Board((size_x, size_y))
        for x in range(0, size_x):
            for y in range(0, size_y):
                self.board[x, y] = Empty()

        self.units = []
        self.unit_dict = {}
        self.types = {}

    def add(self, player, x, y, name, unit_type, health = None, energy = None, destroyed = False, on_board = True):
        if DEBUG:
            print(type(unit_type))
            print(type(player))
        assert x >= 0 and x < self.size_x and y >= 0 and y < self.size_y, f"coordinates ({x}, {y}) are out of bounds for this board"
        # add the unit to a dictionary of types organised by player
        if not(player.number in self.types.keys()):
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
        if health != None:
            unit.setHealth(health)
        # if the energy value has been supplied, set it
        if energy != None:
            unit.setEnergy(energy)
        # mark the unit destroyed if required (needed when loading ongoing games)
        unit.setDestroyed(destroyed)
        # mark the unit on the board (needed when loading ongoing games)
        unit.setOnBoard(on_board)
        # set the coordinates
        unit.setCoords(x,y)
        # add it to the unit list
        self.units.append(unit)
        # add it to the unit dict
        if name in self.unit_dict:
            for instance in self.unit_dict[name]:
                assert instance.player != player, f"unit {name} already exists for {player.name}"
            self.unit_dict[name].append(unit)
        else:
            self.unit_dict[name] = [unit]
        # return the unit id
        return len(self.units)

    def print(self, player = None):
        def _render_unit(unit):
            if type(unit) is Empty:
                return unit.__str__()
            elif unit.player == player:
                return unit.__str__()
            else:
                return Empty().__str__()
        if player == None:
            self.board.draw()
        else:
            self.board.draw(callback=_render_unit)

    def listTypes(self, player = None):
        typesStr = "types:\n"
        for player in self.types.keys():
            for type_name in self.types[player].keys():
                unit_type = self.types[player][type_name]
                typesStr = typesStr + f"- { player: \"{player}\", name: \"{unit_type.name}\", symbol: \"{unit_type.symbol}\", attack: \"{unit_type.attack}\", health: \"{unit_type.health}\", energy: \"{unit_type.energy}\" }\n"
        return typesStr    

    def listUnits(self, player = None):
        # board information
        units_str = "board: {" + f" size_x: {self.size_x}, size_y: {self.size_y}" + "}\n"
        
        # player making request
        if player == None:
            units_str = units_str + f"player: {player}\n"
        else:
            units_str = units_str + f"player: {player.number}\n"

        # units seen by player
        i = 0
        tmp_str = ""
        while i < len(self.units):
            if player == None:
                tmp_str = tmp_str + "  - { " + f"id: {i}, " + self.units[i].dump() + " }\n"
            elif self.units[i].player == player:
                tmp_str = tmp_str + "  - { " + f"id: {i}, " + self.units[i].dump() + " }\n"
            else:
                for seen in self.units[i].seen_by:
                    #print(f"{player.name} {seen.player.number}")
                    if (player.number == seen.player.number):
                        tmp_str = tmp_str + "  - { " + f"id: {i}, " + self.units[i].dump() + " }\n"
            i = i + 1
        if tmp_str == "":    
            units_str = units_str + "units: None\n"
        else:
            units_str = units_str + "units:\n" + tmp_str

        return units_str    

    def getUnitByName(self, name, player = None):
        if player == None:
            assert name in self.unit_dict, f"Unit {name} does not exist"
            return self.unit_dict[name]
        else:
            assert name in self.unit_dict, f"Unit {name} does not exist"
            for unit in self.unit_dict[name]:
                if unit.player == player:
                    return [unit]
            assert True, f"unit {name} does not exist"    

    def getUnitById(self, index):
        assert isinstance(index, int) and index >= 0 and index < len(self.units), f"Unit {name} does not exist"
        return self.units[index]

    def getUnitByCoords(self, x, y):
        return self.board[x, y]

    def commit(self):
        # clear the seen_by list in each unit on the board
        for unit in self.units:
            if unit.on_board:
                unit.seen_by = []
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

    b = Board(4,4)
    b.print()

    w1_id= b.add(p1, 0, 0, "w1", white)
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
