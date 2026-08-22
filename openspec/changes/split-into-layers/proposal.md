## Why

The package has one layer. Game rules, persistence, the transport between
processes, turn synchronisation, authorisation and terminal I/O all live in the
same three files, so none of them can be replaced without touching all of them.

Two things the README has wanted for a long time — keeping game state somewhere
other than loose YAML files, and serving the game over HTTP — are blocked less by
the work itself than by there being nowhere to put it. `Board` prints to stdout
and builds YAML strings by hand, `GameData` is repository and message bus and
turn coordinator at once, and the rules about who may do what are `if` statements
inside three separate command loops.

This change cuts those seams and moves nothing through them. Behaviour, storage
format and the command surface all stay exactly as they are.

## What Changes

- The package SHALL be split into `domain` (the game engine), `service` (one
  function per use case), `storage` (game state persistence) and `cli`
  (parsing, rendering, the REPL), replacing the current flat module layout.
- The engine SHALL stop performing I/O. `Board.print` becomes a board view plus
  a renderer owned by the CLI; `Board.listUnits`, `Board.listTypes` and
  `UnitType.dump` return data with YAML serialisation moved out of them; the
  narration that combat resolution currently prints becomes a list of events the
  caller may render.
- The three hand-written command loops SHALL be replaced by one grammar, one
  recursive descent parser and a set of command objects. The parser SHALL be
  written as recursive descent even though today's grammar is flat, so that a
  nested grammar can be added later without rewriting it.
- The grammar SHALL be shared by all three roles, with a table naming which
  commands each role may run, replacing three separately maintained dispatch
  chains and three hand-written help strings.
- Rules currently enforced inside command loops — that only the game admin may
  set the board size, that players may not be added to an existing game, that
  types and units may only be defined before the first turn and movement only
  after it — SHALL move into the service layer, so that every caller is bound by
  them rather than only the CLI.
- Library code SHALL raise errors rather than calling `sys.exit`, so that a
  caller can report a failure and carry on.
- The path to a game's files SHALL be given to the storage layer rather than
  read from the process working directory.
- `GameData` SHALL be split behind a `GameRepository` interface, with today's
  YAML layout as its only implementation. File names, paths and contents are
  unchanged, and a game saved before this change loads after it.
- `board_game_concept` SHALL keep exporting `UnitType`, `Board`, `Player`,
  `Empty` and `GameData`, so existing imports keep working and the domain tests
  do not move.
- The stale copies `src/BoardGameConcept.py` and `src/GameData.py`, left behind
  by an earlier restructure and since diverged from the package, SHALL be
  removed. Nothing imports them.

No behaviour change is intended. Two current failures stop happening as a
consequence, because a grammar makes them impossible to express: `show players`
at the server prompt raises `KeyError` on an `email` key nothing ever sets, and a
bare `add` or `load` at the server prompt raises `IndexError` from an arity check
that tests the wrong length. Both bring the code into line with the `game-server`
capability as it is already written, so neither is a requirement change.

Explicitly out of scope, each its own later change: SQLite or any other store;
an HTTP API; a web interface; accounts, logins or any identity beyond the
current player number; unit programming and its cost model. Nor is this change
an attempt to support a larger game, more players or more concurrent games than
the current one does.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is a structural refactor: every requirement in
`openspec/specs/` describes behaviour that this change preserves, so no delta
spec is written and `.openspec.yaml` sets `skip_specs: true`.

## Impact

- `src/board_game_concept/BoardGameConcept.py`: rendering and YAML string
  building move out; combat narration becomes events. The rules themselves —
  movement, contest resolution, visibility, placement — are untouched.
- `src/board_game_concept/GameData.py`: split into a repository holding the YAML
  layout and a coordinator holding the commit barrier.
- `src/board_game_concept/server.py`, `client.py`, `observer.py`: reduced to
  entry points over a shared session loop, a shared grammar and a per-role
  command table.
- `src/BoardGameConcept.py`, `src/GameData.py`: deleted.
- `pyproject.toml`: console script targets follow the moved entry points. No new
  dependency is added.
- `requirements.txt`: the `board` entry is removed. Rendering stops being
  delegated to that package, so nothing imports it, and the fallback grid it
  was optional against goes with it. Every environment then draws the board the
  same way — the bordered grid `board` produces today, which is what CI and the
  README's setup already give.
- `tests/test_basic.py`, `tests/test_combat_stalemate.py`,
  `tests/test_duplicate_seen_units.py`: import from `board_game_concept` and
  keep working unchanged, except where they assert on printed output.
- `tests/test_server_client_integration.py`: the safety net for the whole
  change, and it should need no edits. It drives the CLIs over stdin and matches
  their output, so it covers the refactor end to end — but it exercises only
  part of the command surface, and nothing of the observer. Characterisation
  tests pinning the current output of every command, for every role, are
  needed before the command loops are touched.
- `MODULE_DESCRIPTION.md`: describes the current module layout and needs
  rewriting to match the new one.
