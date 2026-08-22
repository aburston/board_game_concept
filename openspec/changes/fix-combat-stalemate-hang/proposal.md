## Why

The server hangs permanently when a contested cell cannot be decided. `UnitType.commit`
loops `while unit_count > 1`, and the count only falls when a unit is destroyed. If every
surviving contestant has less energy than its attack value, no damage is dealt, no unit is
destroyed, and the loop never exits. This is an unbounded spin, not a slow turn: the server
stops making progress and every player in the game is blocked. Reported as issue #2.

The obvious fix — destroy the exhausted units to break the tie — contradicts the game's
design rule that **energy exhaustion makes a unit inert, never dead**. An inert unit stays
on the board, blocks the cell it holds, and can only be removed by an opponent reducing its
health to zero. Honouring that rule forces stalemated units to remain co-located, which the
rest of the engine does not currently tolerate.

## What Changes

- Combat terminates when a round deals no damage. No unit is ever destroyed by running out
  of energy.
- Fix the survivor bookkeeping in `UnitType.commit`, which re-counts every already-destroyed
  unit on each round rather than counting the survivors afresh. With three or more
  contestants this can drive the count to zero while a unit is still standing, and the cell
  is then wrongly emptied.
- **BREAKING (state model)**: a board cell may now hold more than one unit indefinitely, not
  only transiently during turn resolution. A stalemated cell keeps its contestants stacked
  until an opponent with energy destroys them.
- Board rendering handles a stacked cell instead of raising or printing raw object reprs.
- Unit placement and game load tolerate a cell that already holds units, rather than
  asserting the cell is empty.
- The server resolves a player's move order against the named unit rather than against
  whatever `getUnitByCoords` returns, which is a list for a stacked cell.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `combat-resolution`: combat now ends on a round that deals no damage; the requirement that
  it runs until at most one unit remains is replaced by an explicit stalemate outcome, and
  exhaustion is stated never to destroy a unit.
- `board-model`: a cell may hold multiple units; placement no longer requires an empty cell;
  rendering defines what a stacked cell displays.
- `turn-commit`: deploying onto an occupied cell no longer fails.
- `game-persistence`: a saved game containing a stacked cell reloads faithfully, and the
  server applies move orders by unit identity rather than by cell contents.

## Impact

- `src/board_game_concept/BoardGameConcept.py` — `UnitType.commit`, `UnitType.preCommit`,
  `Board.print`, `Board.add`.
- `src/board_game_concept/server.py` — move-order application in `serverSave`.
- `src/board_game_concept/GameData.py` — unit reload path.
- `tests/` — regression coverage for the stalemate, the survivor count, and a stacked-cell
  save/load round trip.
- Overlaps issue #1: the placement assertion this change has to relax is the same assertion
  that makes issue #1 crash. Issue #1 is not otherwise in scope here.
- `src/BoardGameConcept.py` and `src/GameData.py` are stale duplicates outside the package
  and are deliberately left untouched; see `SPEC_COVERAGE.md`.
