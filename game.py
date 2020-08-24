#!/usr/bin/python3

from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player

p1 = Player("test1", "ashley_burston@hotmail.com")
p2 = Player("test2", "ashley_burston@hotmail.com")

scout = UnitType("scout", "S", 1, 1, 50)
warrior = UnitType("warrior", "W", 2, 2, 100)

board = Board(8,8)
for i in range(0, 8):
    board.add(p1, i, 0, f"Scout {i}", warrior)
    board.add(p1, i, 1, f"Warrior {i}", scout)
    board.add(p2, i, 6, f"Scout {i}", scout)
    board.add(p2, i, 7, f"Warrior {i}", warrior)
board.commit()    

board.print()    
board.print(p1)    
board.print(p2)    
board.listUnits()    
board.listUnits(p1)    
board.listUnits(p2)    
