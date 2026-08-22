## Why

A client crashes as soon as one of its units meets an enemy unit (issue #3).
Combat records a contact for every attack, so a unit that fought over several
rounds is recorded as seen many times over, is written into the player's view
that many times, and the client then dies trying to restore the same unit
twice — reporting that the unit already exists.

## What Changes

- Contact records SHALL hold each unit at most once, however many attacks two
  units exchange in a turn.
- A per-player view SHALL list each unit it reveals once, even when several of
  the player's units made contact with it.
- Restoring a unit a board already holds for that player SHALL put the saved
  state back into that unit rather than failing: a view that names the same
  unit twice is loaded, not refused.
- The error raised when a player really does reuse a unit name SHALL name the
  player by number, instead of failing on a player attribute that does not
  exist and masking the original error.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `visibility`: contact is recorded once per pair of units, and a per-player
  view lists each revealed unit once.
- `board-model`: restoring a unit the board already holds for that player
  updates it instead of failing; the duplicate-name error names the player
  correctly.

## Impact

- `src/board_game_concept/BoardGameConcept.py`: `UnitType.resolveContest`
  (contact recording), `Board.listUnits` (per-player view), `Board.add`
  (restoring a known unit, error text), plus a `Board.findUnit` lookup that
  answers rather than asserting.
- No change to the on-disk format, so games in progress keep working: a view
  written by an older server that names a unit twice now loads.
- `tests/`: a regression test covering a client reading a view of a unit it
  fought over more than one round.
