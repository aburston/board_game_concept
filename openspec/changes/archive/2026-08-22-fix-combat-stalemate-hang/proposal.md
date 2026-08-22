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
into it goes back to the square it came from, and the board is left as it was. A defender
that was already standing there never moved, so it has nowhere to fall back to and keeps the
square.

Moving into a square another unit holds stays legal — that is combat. Deploying a **brand new
unit** onto a square that is already taken is a different thing, and is now **illegal**:
it is refused when the unit is created, which is what issue #1 asks for.

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
- Deploying a brand new unit onto a square that is already held, or already claimed by a
  unit waiting to be placed, is refused with a clear error instead of raising an uncaught
  assertion out of turn resolution. The server rejects such an order and resolves the turn
  without it. Restoring a saved game is not a deployment and is exempt.
- A refused order is published back to the player who gave it, as
  `players/<number>_rejected.yaml`, and the client reports it before taking their next
  command. The file is written for every player on every resolved turn, so it always
  describes the turn just resolved.
- An order the server cannot make sense of — an unknown state, or a move naming a unit the
  player does not own — is refused through the same channel rather than asserting and taking
  the turn down.
- A player holding no units can commit without killing the server. `listUnits` writes
  `units: None`, which YAML reads back as the string `"None"`; the load path already knew
  that and the turn resolver did not.
- **BREAKING (state model)**: a board square may hold more than one unit beyond turn
  resolution, in the residual case where a survivor of an undecided contest cannot fall back
  because another unit took the square it came from during the same turn. Board rendering
  and game load tolerate such a square instead of raising.
- The server resolves a player's move order against the named unit rather than against
  whatever `getUnitByCoords` returns, which is a list for a shared square.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `combat-resolution`: combat now ends on a round that deals no damage; the requirement that
  it runs until at most one unit remains is replaced by an explicit undecided outcome in
  which the movers retreat, and exhaustion is stated never to destroy a unit. Friendly fire
  is stated explicitly: a contestant attacks every other unit in the cell whoever owns it.
- `board-model`: placement requires a free square and says so as a rule rather than an
  assertion, while restoring a saved game is exempt; a square may hold multiple units;
  rendering defines what a shared square displays; leaving a square does not disturb the
  units still in it.
- `turn-commit`: deploying onto an occupied square is illegal and refused, and the turn
  resolves without the refused order rather than failing.
- `player-client`: the client refuses a deployment onto a square it knows is taken, and
  reports any order the server refused on the last resolved turn.
- `game-persistence`: a saved game containing a shared square reloads faithfully, and the
  server applies move orders by unit identity rather than by square contents.

## Impact

- `src/board_game_concept/BoardGameConcept.py` — `UnitType.commit`, `UnitType.preCommit`,
  new `UnitType.resolveContest`, `UnitType.retreat` and `UnitType.vacate`, `Board.add`,
  new `Board.squareIsFree`, `Board.print`, `Board.commit`.
- `src/board_game_concept/GameData.py` — order application, order rejection and the load
  path in `serverSave` and `load`.
- `src/board_game_concept/client.py` — reporting refused orders at the start of a session.
- `tests/test_combat_stalemate.py` — regression coverage for the hang, the retreat, the
  survivor count, rendering and a shared-cell save/load round trip.
- Fixes issue #1: the assertion that killed the session is replaced by a rule enforced where
  the unit is created, and a rejected order is now reported to the player who gave it.
- `src/BoardGameConcept.py` and `src/GameData.py` are stale duplicates outside the package
  and are deliberately left untouched; see `SPEC_COVERAGE.md`.
