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

    def __init__(self, name, symbol, speed, attack, health):
        self.name = name
        assert (len(str(name)) >= 1), "name must be one or more character"

        self.symbol = symbol
        assert (len(str(symbol)) == 1), "symbol must be only one character"

        self.speed = speed
        assert isinstance(speed, int), "speed must be an integer value"
        assert ((speed >= 1) and (speed <= 10)), "speed must be a value from 1 to 10"

        self.attack = attack
        assert isinstance(attack, int), "attack must be an integer value"
        assert ((attack >= 1) and (attack <= 10)), "attack must be a value from 1 to 10"

        self.health = health
        assert isinstance(health, int), "health must be an integer value"
        assert ((health >= 1) and (health <= 10)), "health must be a value from 1 to 10"

        self.state = UnitType.INITIAL
        self.direction = UnitType.NONE
        self.destroyed = False

    def move(self, direction):
        self.state = UnitType.MOVING
        self.direction = direction

    def setName(self, name):
        self.name = name

    def setBoard(self, board, board_max_x, board_max_y):
        self.board = board
        self.board_max_x = board_max_x
        self.board_max_y = board_max_y

    def setCoords(self, x, y):
        self.x = x
        self.y = y

    def incomingAttack(self, attack):
        self.health = self.health - attack
        if self.health <= 0:
            destroyed = True

    # calculates attacks and marks units as DESTROYED, creates arrays of units in squares where multiple units are
    # trying to move simultaneously into the same square
    def preCommit(self):
        if self.state == UnitType.INITIAL:
            # make sure that location on the board is empty
            assert self.board[self.x, self.y] is board.Empty, f"can't add {name} to board at ({x},{y})"
        elif self.state == UnitType.MOVING:
            if self.direction == UnitType.NORTH:
                dest_y = self.y - 1
                if self.y < 0:
                    self.y = 0
                    self.STATE = UnitType.NOP
                    return
            elif self.direction == UnitType.EAST:
                dest_x = self.x + 1
                if self.x > self.board_max_x:
                    self.x = self.board_max_x
                    self.STATE = UnitType.NOP
                    return
            elif self.direction == UnitType.SOUTH:
                dest_y = self.y + 1
                if self.y > self.board_max_y:
                    self.y = self.board_max_y
                    self.STATE = UnitType.NOP
                    return
            elif self.direction == UnitType.WEST:
                dest_x = self.x - 1
                if self.x < 0:
                    self.x = 0
                    self.STATE = UnitType.NOP
                    return
            else:
                self.STATE = UnitType.NOP
                return

            if self.board[dest_x, dest_y] is board.Empty:
                setCoords(dest_x, dest_y)
                board[self.x, self.y] = [ self ]
            elif type(self.board[dest_x, dest_y]) is list:
                self.board[dest_x, dest_y].append(self)
            elif self.board[dest_x, dest_y] is UnitType:
                self.board[dest_x, dest_y].incomingAttack(self.attack)
            self.STATE = UnitType.NOP
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
        elif self.state == UnitType.MOVING:
            assert self.state == UnitType.MOVING, "During commit, no unit should be in the MOVING state" 
        else:
            if type(self.board[self.x, self.y]) is list:
                units = len(self.board[self.x, self.y])
                while units >= 1:
                    for unit in self.board[self.x, self.y]:
                        for target in self.board[self.x, self.y]:
                            if unit != target:
                                target.incomingAttack(unit.attack)
                    for unit in self.board[self.x, self.y]:
                        if unit.destroyed:
                            units = units - 1 
                for unit in self.board[self.x, self.y]:
                    if unit.destroyed == False:
                        self.board[self.x, self.y] = unit
            else:
                if self.destroyed:
                    self.board[self.x, self.y] = board.Empty

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
    
    def add(self, x, y, name, unit_type):
        # make a shallow copy of the unit type to create a new unit instance
        unit = copy.copy(unit_type)
        # reset the unit name
        unit.setName(name)
        # add a ref to the board into the unit + the size
        unit.setBoard(self.board, self.size_x, self.size_y)
        # keep a copy of the unit coords in the unit
        unit.setCoords(x,y)
        # add it to the board
        unit.preCommit()
        unit.commit()
        self.units.append(unit)

    def print(self):
        self.board.draw()

white = UnitType("White", "W", 1, 1, 1)
black = UnitType("Black", "B", 1, 1, 1)

b = Board(4,4)

b.add(0, 0, "w1", white)
b.add(0, 1, "w2", white)
b.add(0, 2, "w3", white)
b.add(0, 3, "w4", white)

b.add(3, 0, "b1", black)
b.add(3, 1, "b2", black)
b.add(3, 2, "b3", black)
b.add(3, 3, "b4", black)

b.print()
