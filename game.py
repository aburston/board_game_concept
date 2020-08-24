#!/usr/bin/python3

from BoardGameConcept import UnitType
from BoardGameConcept import Board

white = UnitType("White", "W", 1, 2, 100)
black = UnitType("Black", "B", 1, 1, 100)

b = Board(4,4)
b.print()

w1_id= b.add(0, 0, "w1", white)
b.add(0, 1, "w2", white)
b.add(0, 2, "w3", white)
b.add(0, 3, "w4", white)

b.add(3, 0, "b1", black)
b.add(3, 1, "b2", black)
b.add(3, 2, "b3", black)
b.add(3, 3, "b4", black)
b.add(2, 2, "b5", black)
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
b.listUnits()

w1.move(UnitType.EAST)
b1.move(UnitType.WEST)
w2.move(UnitType.EAST)
b.commit()

b.print()
b.listUnits()

w1.move(UnitType.EAST)
w2.move(UnitType.EAST)
b2.move(UnitType.WEST)
b5.move(UnitType.NORTH)

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
