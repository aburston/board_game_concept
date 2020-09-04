#!/usr/bin/python3

from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player

p1 = Player("test1", "")
p2 = Player("test2", "")

scout = UnitType("scout", "S", 1, 1, 50)
warrior = UnitType("warrior", "W", 2, 2, 100)

board = Board(8,8)

for i in range(0, 8):
    board.add(p1, i, 0, f"Scout {i}", warrior)
    board.add(p1, i, 1, f"Warrior {i}", scout)
    board.add(p2, i, 6, f"Scout {i}", scout)
    board.add(p2, i, 7, f"Warrior {i}", warrior)

board.commit()    

board.print(p1)    
board.print(p2)    
print(board.listUnits(p1))
print(board.listUnits(p2))
print(board.listUnits())
