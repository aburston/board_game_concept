## Why

A move costs 1 energy whatever the unit is, so weight is free: a 10-health
brute crosses the board on the same fare as a 1-health scout, and health buys
durability without ever buying a penalty. The only thing separating a heavy
unit from a light one is how long it takes to kill, which leaves the design
space flat — the strongest type a budget can afford is simply the best type.
Charging a move the unit's **maximum health** makes weight cost mobility:
armour is paid for in the field, every turn, and a scout is genuinely quick
where a brute is genuinely ponderous.

## What Changes

- **BREAKING** A move costs the moving unit's **maximum health** in energy —
  the health its type was designed with, not the health it has left. A move by
  a 1-health unit costs 1 (as today); a move by a 10-health unit costs 10.
- The cost is read from the type's design, so damage never changes it: a
  wounded unit pays exactly what it paid when it was whole, and two units of
  the same type always pay the same to move.
- Every existing rule about paying stays as it is, with the flat 1 replaced by
  the unit's maximum health: a unit that cannot pay does not move and is
  refused for want of energy; a mover that enters a held square pays the fare
  and nothing more; both sides of a head-on collision pay it.
- **BREAKING** A non-wall type must be designed with **energy at least equal to
  its health**, and is refused at construction otherwise. Without this a type
  could be defined that can never afford a single move — resting gives back 1 a
  turn, so a health-10, energy-5 unit would be a wall that was charged for an
  attack it can never make. Walls (attack 0 and energy 0) are exempt and stay
  exactly as they are: 0 energy against a health cost, immobile by design.
- Rest is untouched: a unit that did nothing still recovers 1 energy a turn, so
  a heavy unit really does need several quiet turns to buy its next square.
- Attack cost is untouched: a round of fighting still costs the attacker its
  attack value.

## Capabilities

### New Capabilities

None — this changes what two existing capabilities require, not what the
system can do.

### Modified Capabilities

- `unit-movement`: the "Movement Costs Energy" requirement changes from a flat
  1 to the mover's maximum health, and the head-on collision requirement is
  restated so that each unit pays its own cost rather than a shared one.
- `unit-types`: adds the constraint that a non-wall type's energy is at least
  its health, and restates the wall rationale and the meaning of the health
  statistic in terms of the new cost.

## Impact

- Rules: `GAME_RULES.md` R4.3 (moving costs energy), R4.5, R2.10 (walls), R2.9
  and the energy/health statistic descriptions.
- Code: `domain/unit.py` — `UnitType.MOVE_COST` becomes a per-unit cost derived
  from `type_health`, the `planMove` affordability check, and the type
  validation asserts; `domain/board.py` — the single place moves are charged in
  `_move`.
- Tests: the movement, combat and determinism suites define types with energy
  below health that this change makes illegal, so their fixtures move with it.
- Existing saved games: a game stored before this change may hold a type whose
  energy is below its health. Loading one is addressed in design.md.
- Point budget: unchanged in formula (`attack + health + energy`), but health
  now buys a running cost as well as durability, which the budget change
  already in flight (`add-a-point-budget`) prices unchanged.
