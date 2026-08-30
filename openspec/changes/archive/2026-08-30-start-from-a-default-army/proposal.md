## Why

A new game starts empty: no board, no unit types, no units. Before anybody can
play, an administrator sizes the board and every player invents a set of unit
designs from nothing and places them one at a time. That is a lot of work
before the first turn, and it is work a newcomer cannot do well because the
costs, the move fare and the reach of a unit are not obvious until you have
played a few games.

A game should come ready to play. Press commit and the game begins; then edit
what you were given, because the pieces you start with are a starting point
rather than a fixture.

## What Changes

- A created game SHALL have an **8x8 board** instead of no board. The
  administrator can still resize it until setup is committed.
- Every registered player SHALL be given a **default catalogue of eight unit
  types** - Wall, Scout, Pawn, Runner, Line, Lance, Heavy and Keep - drawn up
  so that the set demonstrates each kind of design the rules allow.
- Every player of a two-player game SHALL be given a **default deployment**: a
  fifteen-unit array built from that catalogue, placed in their own half, with
  the flag on the Keep. The array is a copy from the catalogue - it introduces
  no design the catalogue does not hold.
- **BREAKING**: the default point budget rises from **100 to 250**, because the
  default array costs 232 and a player must be able to edit it without first
  taking something back.
- The catalogue and the array are ordinary setup decisions. A player edits
  them with the commands they already have: redefine a type, take a unit back,
  deploy it somewhere better.
- **BREAKING**: no migration. Games created before this change keep the board,
  budget and empty catalogue they were created with.

## Capabilities

### New Capabilities

- `default-army`: what a new game and a newly registered player start with -
  the default board size, the default unit catalogue, the default deployment
  and its flag, when each is seeded, and what happens when the array does not
  fit.

### Modified Capabilities

- `point-budget`: the default budget where the administrator names none
  changes from 100 to 250.
- `game-registry`: a created game has an 8x8 board rather than no board.

## Impact

- `service/registry.py` - `create` writes a board instead of leaving it unset.
- `service/games.py` - `add_player` seeds the catalogue; a player session with
  an empty draft seeds the deployment.
- `domain/player.py` - `DEFAULT_BUDGET`.
- `domain/` gains the catalogue and the array as data, run through the
  ordinary `UnitType` constructor and the ordinary deployment commands.
- No client change. Both the CLI and the browser read types and units through
  the views they already read, so a backend default appears in both.
- Tests that register players or create games inherit a board, a catalogue and
  a larger budget; those that assert on an empty game need adjusting.
