#!/usr/bin/env python3

import board
import copy

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

    def incomingAttack(self, attack):
        print(f"{self.name} being attacked")
        self.health = self.health - attack
        if self.health <= 0:
            self.destroyed = True

    # calculates attacks and marks units as DESTROYED, creates arrays of units in squares where multiple units are
    # trying to move simultaneously into the same square
    def preCommit(self):
        if self.state == UnitType.INITIAL:
            # make sure that location on the board is empty
            assert self.board[self.x, self.y] is board.Empty, f"can't add {self.name} to board at ({self.x},{self.y})"
        elif self.state == UnitType.MOVING:
            dest_x = self.x
            dest_y = self.y
            if self.direction == UnitType.NORTH:
                dest_y = self.y - 1
                if dest_y < 0:
                    self.y = 0
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.EAST:
                dest_x = self.x + 1
                if dest_x > self.board_max_x - 1:
                    self.x = self.board_max_x - 1
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.SOUTH:
                dest_y = self.y + 1
                if dest_y > self.board_max_y - 1:
                    self.y = self.board_max_y - 1
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.WEST:
                dest_x = self.x - 1
                if dest_x < 0:
                    self.x = 0
                    self.state = UnitType.NOP
                    return
            else:
                self.state = UnitType.NOP
                return

            if self.board[dest_x, dest_y] is board.Empty:
                energy = self.energy - (self.energy // 100 + 1)
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    self.board[self.x, self.y] = board.Empty
                    self.setCoords(dest_x, dest_y)
                    self.board[self.x, self.y] = [ self ]
                    print(f"preCommit: {self.name} move to [{self.x},{self.y}]")
            elif type(self.board[dest_x, dest_y]) is list:
                energy = self.energy - (self.energy // 100 + 1)
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    self.board[self.x, self.y] = board.Empty
                    self.setCoords(dest_x, dest_y)
                    self.board[dest_x, dest_y].append(self)
                    print(f"preCommit: {self.name} added to list in [{self.x},{self.y}]")
            elif type(self.board[dest_x, dest_y]) is UnitType:
                energy = self.energy - self.attack
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    target = self.board[dest_x, dest_y]
                    target.incomingAttack(self.attack)
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
            assert self.board[self.x, self.y] is board.Empty, f"can't add {name} to board at ({x},{y})"
            # add the unit to the board
            self.board[self.x, self.y] = self
            self.state = UnitType.NOP
        elif self.state == UnitType.MOVING:
            assert not(self.state == UnitType.MOVING), "During commit, no unit should be in the MOVING state" 
        else:
            if type(self.board[self.x, self.y]) is list:
                unit_count = len(self.board[self.x, self.y])
                print(f"{self.name} commit process list in [{self.x},{self.y}]: {self.board[self.x, self.y]}")
                while unit_count > 1:
                    print(f"{self.name} commit process {unit_count} units in square [{self.x},{self.y}]")
                    for unit in self.board[self.x, self.y]:
                        for target in self.board[self.x, self.y]:
                            print(f"{self.name} commit processing {unit.name} -> {target.name}")
                            if not(unit is target):
                                energy = unit.energy - unit.attack
                                if energy >= 0:
                                    unit.energy = energy
                                    print(f"commit: {target.name} attack {unit.name}")
                                    target.incomingAttack(unit.attack)
                    for unit in self.board[self.x, self.y]:
                        if unit.destroyed:
                            unit_count = unit_count - 1             
                for unit in self.board[self.x, self.y]:
                    if unit.destroyed == False:
                        self.board[self.x, self.y] = unit
                        print(f"{self.name} commit add unit to square [{self.x},{self.y}]")
                    else:
                        unit.on_board = False
                if unit_count == 0:
                    self.board[self.x, self.y] = board.Empty
            else:
                if self.destroyed:
                    self.board[self.x, self.y] = board.Empty
                    self.on_board = False
                    print(f"{self.name} commit removing unit from square [{self.x},{self.y}]")

    def dump(self):
        print(f"{self.name}, {self.symbol}, {self.attack}, {self.health}, {self.energy}, [{self.x},{self.y}], {self.state}, d={self.destroyed}, ob={self.on_board}")

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
        self.units = []
        self.unit_dict = {}
    
    def add(self, x, y, name, unit_type):
        # make a shallow copy of the unit type to create a new unit instance
        unit = copy.copy(unit_type)
        # reset the unit name
        unit.setName(name)
        # add a ref to the board into the unit + the size
        unit.setBoard(self.board, self.size_x, self.size_y)
        # keep a copy of the unit coords in the unit
        unit.setCoords(x,y)
        # add it to the unit list
        self.units.append(unit)
        # add it to the unit dict
        self.unit_dict[name] = unit

    def print(self):
        self.board.draw()

    def listUnits(self):
        for unit in self.units:
            unit.dump()

    def getUnit(self, name):
        assert name in self.unit_dict, f"Unit {name} does not exist"
        return self.unit_dict[name]

    def commit(self):
        for unit in self.units:
            if unit.on_board:
                unit.preCommit()
        for unit in self.units:
            if unit.on_board:
                unit.commit()

white = UnitType("White", "W", 1, 1, 100)
black = UnitType("Black", "B", 1, 1, 100)

b = Board(4,4)

b.add(0, 0, "w1", white)
b.add(0, 1, "w2", white)
b.add(0, 2, "w3", white)
b.add(0, 3, "w4", white)

b.add(3, 0, "b1", black)
b.add(3, 1, "b2", black)
b.add(3, 2, "b3", black)
b.add(3, 3, "b4", black)

b.commit()
b.print()
b.listUnits()

w1 = b.getUnit("w1")
b1 = b.getUnit("b1")
w2 = b.getUnit("w2")
b2 = b.getUnit("b2")
b3 = b.getUnit("b3")
b4 = b.getUnit("b4")
w4 = b.getUnit("w4")

w1.move(UnitType.EAST)
b1.move(UnitType.WEST)
w2.move(UnitType.EAST)
b.commit()

b.print()

w1.move(UnitType.EAST)
w2.move(UnitType.EAST)
b2.move(UnitType.WEST)

b.commit()
b.print()
b.listUnits()

w1.move(UnitType.NORTH)
w4.move(UnitType.WEST)
b3.move(UnitType.EAST)
b4.move(UnitType.SOUTH)

b.commit()
b.print()
b.listUnits()

w2.dump()
b2.dump()



