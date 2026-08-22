## Why

The server hangs permanently when a contested cell cannot be decided. `UnitType.commit`
loops `while unit_count > 1`, and the count only falls when a unit is destroyed. If every
surviving contestant has less energy than its attack value, no damage is dealt, no unit is
destroyed, and the loop never exits. This is an unbounded spin, not a slow turn: the server
stops making progress and every player in the game is blocked. Reported as issue #2.

The obvious fix — destroy the exhausted units to break the tie — contradicts the game's
design rule that **energy exhaustion makes a unit inert, never dead**. An inert unit stays
on the board, blocks the cell it holds, and can only be removed by an opponent reducing its
health to zero.

The rule for an undecided contest is that **nobody wins the square**: every unit that moved
into it goes back to the cell it came from, and the board is left as it was. Units that were
not moving — the defender already standing there, or a unit deployed onto the cell this turn
— have nowhere to fall back to and stay put.

## What Changes

- Combat terminates when a round deals no damage. No unit is ever destroyed by running out
  of energy.
- An undecided contest sends every contestant that moved in back to the cell it left. The
  contested cell is left to whoever was already holding it, or empty if nobody was.
- Fix the survivor bookkeeping in `UnitType.commit`, which re-counts every already-destroyed
  unit on each round rather than counting the survivors afresh. With three or more
  contestants this drives the count to zero while a unit is still standing, and the cell is
  then wrongly emptied.
- A unit destroyed in an earlier round no longer attacks in later ones. Attackers are the
  units standing at the start of each round, so a unit destroyed mid-round still lands its
  own attack that round.
- Leaving a cell removes only the departing unit, rather than clearing the cell outright and
  taking any unit sharing it off the board with it.
- **BREAKING (state model)**: a board cell may hold more than one unit beyond turn
  resolution, in the residual case where no contestant can fall back — every survivor was
  either already standing there or was deployed onto the cell. Board rendering, unit
  placement and game load all tolerate such a cell instead of raising.
- The server resolves a player's move order against the named unit rather than against
  whatever `getUnitByCoords` returns, which is a list for a shared cell.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `combat-resolution`: combat now ends on a round that deals no damage; the requirement that
  it runs until at most one unit remains is replaced by an explicit undecided outcome in
  which the movers retreat, and exhaustion is stated never to destroy a unit. Friendly fire
  is stated explicitly: a contestant attacks every other unit in the cell whoever owns it.
- `board-model`: a cell may hold multiple units; placement no longer requires an empty cell;
  rendering defines what a shared cell displays; leaving a cell does not disturb the units
  still in it.
- `turn-commit`: deploying onto an occupied cell no longer fails.
- `game-persistence`: a saved game containing a shared cell reloads faithfully, and the
  server applies move orders by unit identity rather than by cell contents.

## Impact

- `src/board_game_concept/BoardGameConcept.py` — `UnitType.commit`, `UnitType.preCommit`,
  new `UnitType.resolveContest`, `UnitType.retreat` and `UnitType.vacate`, `Board.print`,
  `Board.commit`.
- `src/board_game_concept/GameData.py` — move-order application in `serverSave`.
- `tests/test_combat_stalemate.py` — regression coverage for the hang, the retreat, the
  survivor count, rendering and a shared-cell save/load round trip.
- Overlaps issue #1: the placement assertion this change has to relax is the same assertion
  that makes issue #1 crash, so deploying onto an occupied cell now resolves as a contest
  instead of killing the session.
- `src/BoardGameConcept.py` and `src/GameData.py` are stale duplicates outside the package
  and are deliberately left untouched; see `SPEC_COVERAGE.md`.
