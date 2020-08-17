#!/usr/bin/env python3

import board

# Unit
#   name: One or more character
#   symbol: One single character
#   speed: speed 10 is to move once per clock tick and 1 is to move once every 10th tick
#   attack: damage per attack
#   health: total amount of health
class UnitType:
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

    def move(self, direction):
        print("move")

    def commit(self):
        print("commit")

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
    
    def __str__(self):
        print("foo")

    def add(self, x, y, unit_type):
        self.board[x, y] = unit_type

    def print(self):
        self.board.draw()

    def __str__(self):
        return(self.symbol)
    

white = UnitType("White", "W", 1, 1, 1)
black = UnitType("Black", "B", 1, 1, 1)

b = Board(4,4)

b.add(0, 0, white)
b.add(0, 1, white)
b.add(0, 2, white)
b.add(0, 3, white)

b.add(3, 0, black)
b.add(3, 1, black)
b.add(3, 2, black)
b.add(3, 3, black)

b.print()
