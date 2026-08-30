## 1. The catalogue as data

- [x] 1.1 Declare the eight catalogue types as data in `domain/`, with the
      statistics in `specs/default-army/spec.md`, and verify a new test builds
      every one through the ordinary `UnitType` constructor without an
      assertion firing
- [x] 1.2 Verify each catalogue cost and move fare against the table in the
      spec with a test, so a mistyped statistic fails rather than reaching a
      game

## 2. The default board

- [x] 2.1 Give a created game an 8x8 board in `service/registry.py:create`,
      and verify a created game is listed with that size
- [x] 2.2 Verify the administrator can still resize a created game's board
      until setup is committed, and that the default is not restored

## 3. The default budget

- [x] 3.1 Raise `Player.DEFAULT_BUDGET` from 100 to 250 and verify a player
      registered without a named budget holds 250
- [x] 3.2 Verify the permitted range, a named budget, and two players with
      different budgets are all unchanged by the new default

## 4. Seeding the catalogue

- [x] 4.1 Seed the catalogue when a player is registered in
      `service/games.py:add_player`, and verify a newly registered player
      holds the eight types and has spent nothing
- [x] 4.2 Verify a player can redefine a catalogue type under its own name and
      define types of their own alongside it, leaving the rest untouched
- [x] 4.3 Verify `load_player` - a player taken from a file - is not seeded on
      top of the types the file gave it

## 5. The array as data

- [x] 5.1 Declare the array as data in `domain/`: depth, column and type name
      per unit, and which unit carries the flag, per the table in the spec
- [x] 5.2 Add a function that resolves the array for a seat - depth to row for
      the lower and higher numbered player, columns unchanged - and verify
      against both seats of an 8x8 board
- [x] 5.3 Verify with a test that the array costs 232, uses only catalogue
      types, and holds fifteen units

## 6. Seeding the array

- [x] 6.1 Seed the array into a player's draft as ordinary deployment commands
      when their seat is opened and their draft is empty, setting the flag on
      the Keep, and verify the player holds fifteen units with a standing flag
- [x] 6.2 Verify the seeded setup commits as it stands, for both players, and
      the game reaches its first turn
- [x] 6.3 Verify seeding does not fire twice: opening the seat repeatedly
      leaves fifteen units, not thirty
- [x] 6.4 Verify an edited array is left alone - take a Heavy back, deploy a
      Line, reopen the seat, and find the Line and no restored Heavy
- [x] 6.5 Verify taking the whole array back leaves no units, and reopening
      the seat does not deploy it again
- [x] 6.6 Verify the seeded units are charged normally: 232 spent, 18
      remaining, and a Heavy taken back returns 30

## 7. Where the array is not given

- [x] 7.1 Refuse to seed the array in a game that is not of exactly two
      players, and verify a one-player and a three-player game get the
      catalogue and no units
- [x] 7.2 Refuse to seed where the array does not fit inside the seat's
      placement area, and verify a two-player game on a board too small gets
      the catalogue, no units, and can still be set up by hand
- [x] 7.3 Refuse to seed where the player's budget cannot pay for the array,
      and verify a player registered with a small budget gets the catalogue
      and no units
- [x] 7.4 Verify every unit of a seeded array falls inside the placement area
      `placement-zones` publishes for that seat

## 8. The tests that start from an empty game

- [x] 8.1 Fix the tests that assert a created game has no board (about 30
      files call `create`), and verify the suite passes on the YAML backend
- [x] 8.2 Fix the tests that assert a registered player holds no types (about
      22 files register players), preferring an explicit setup over an
      inherited default where the test is about something else
- [x] 8.3 Fix the tests that assert a default budget of 100 (about 11 files),
      and verify the point-budget suite passes
- [x] 8.4 Verify the whole suite passes on both the YAML and the SQLite
      backends, run one at a time so the CLI surface tests do not share
      `tests/games/`
- [x] 8.5 Verify `tests/test_determinism.py` still passes: the catalogue and
      the array are fixed data, so resolution must stay free of clock,
      randomness and object identity

## 9. Playing it

- [x] 9.1 Play a two-player game end to end from the defaults, in the browser,
      committing both seats unedited, and verify the first turn resolves
- [x] 9.2 Verify the browser armoury shows the eight catalogue types and the
      board shows the fifteen units without any front-end change

## 10. Rules and coverage

- [x] 10.1 Write the default board, the catalogue table and the array into
      `GAME_RULES.md`, including that a resize or a third player added after a
      seat is seeded is recovered by taking units back
- [x] 10.2 Add `default-army` to `SPEC_COVERAGE.md` and verify
      `openspec validate --specs --strict` still passes

## 11. What the browser found

- [x] 11.1 Make the SQLite lock wait for a held transaction as the file lock
      does, and verify a browser opening a screen - which asks for seven views
      at once - no longer has six of them fail with "database is locked"
- [x] 11.2 Seed inside one held transaction, re-reading the draft under the
      hold, and read the game again where another session seeded first, so
      that the first screen a player opens draws the army rather than an
      empty board
- [x] 11.3 Name each player's array units with their seat number, and verify a
      player's turn feed holds only their own army: the feed decides what a
      seat may read by matching unit names, so two seats given identically
      named armies read each other's deployments
