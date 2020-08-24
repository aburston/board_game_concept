#!/usr/bin/python3

from BoardGameConcept import UnitType
from BoardGameConcept import Board

scout = UnitType("scout", "S", 1, 1, 50)
warrior = UnitType("warrior", "W", 2, 2, 100)

board = Board(8,8)
for i in range(0, 8):
    board.add(i, 0, f"White Scout {i}", warrior)
    board.add(i, 1, f"White Warrior {i}", scout)
    board.add(i, 6, f"Black Scout {i}", scout)
    board.add(i, 7, f"Black Warrior {i}", warrior)
board.commit()    

board.print()    
board.listUnits()    
