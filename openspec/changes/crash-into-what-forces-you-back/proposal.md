## Why

A contest nobody won sends its survivors back to the square they came from.
That square is often gone - the unit behind stepped into it as the column
advanced - and the survivor stayed where it stood, sharing the contested
square with whoever it had failed to shift.

Found in a played game. One square held a Heavy and a Pawn for four turns, the
Heavy too spent to strike back and too spent to leave. Another held two units
of the **same player**, both at no energy, unable to fight their way apart or
step apart - though `unit-movement` already says there is no way to stack with
your own units.

A square holds one unit. What was missing was what happens instead.

## What Changes

- A survivor that falls back into an occupied square SHALL **crash into**
  whoever took it: one exchange, on the ordinary terms, so a unit that is hit
  hits back even when the blow destroys it.
- The unit in the way SHALL then give ground and fall back itself, crashing
  into whoever is behind it, down the column.
- **BREAKING**: no square ends a turn holding more than one unit. The
  `shared` outcome is gone, and with it the event that reported it.
- A unit SHALL strike each other unit **at most once a turn**, however many
  exchanges the turn holds - a turn now holds more than one.

## Capabilities

### Modified Capabilities

- `combat-resolution`: what becomes of a survivor with nowhere to fall back,
  and one strike per pair per turn.

## Impact

- `domain/unit.py` - `_fall_back`, `exchangeAttacks`, `resolveContest`.
- `domain/board.py` - the record of who has struck whom, kept for the turn.
- No client change: a square that can only hold one unit is simpler to draw
  than one that could hold two.
