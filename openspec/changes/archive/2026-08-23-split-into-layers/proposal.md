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
- The import surface SHALL follow the new packages rather than being frozen at
  today's names, and the unit tests SHALL be updated to import from where things
  now live. The characterisation tests added first, which drive each role and
  assert what it prints, are what shows behaviour is preserved.
- Player numbers and unit statistics SHALL be stored as the integers they are.
  Today `add player 1` records the string `'1'` while `load player` records the
  integer `1`, and statistics round-trip as quoted strings. Games written before
  this change will not load afterwards, and none needs to.
- The stale copies `src/BoardGameConcept.py` and `src/GameData.py`, left behind
  by an earlier restructure and since diverged from the package, SHALL be
  removed. Nothing imports them.

No change to what any role can do is intended. Where the code contradicts its
own spec, the code SHALL be corrected rather than the divergence carried through
the refactor. Writing the CLI scenarios out as tests found five:

- `show players` at the server prompt raised `KeyError` on an `email` field
  nothing ever sets, as soon as any player was registered.
- A bare `add` or `load` at the server prompt raised `IndexError`, from an arity
  guard that tested the wrong length.
- A board dimension below the minimum was reported as non-numeric, because the
  assertion raised by the board was caught alongside a bad integer, leaving the
  message about the minimum unreachable.
- A unit a player deployed during setup was neither drawn by `show board` nor
  listed by `show units`, because the view the server last published took
  precedence over the player's own board. It became visible only once a turn
  containing it had been resolved.

Each restores what `game-server` or `player-client` already requires, so none is
a requirement change and none needs a delta spec.

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
  `tests/test_duplicate_seen_units.py`: imports follow the new layout, and the
  five places that call `Board.print` or `Board.listUnits` move to the renderer
  and the serialiser.
- `tests/test_server_client_integration.py`: drives the CLIs over stdin and
  matches their output, so it covers the refactor end to end, but it exercises
  only part of the command surface and nothing of the observer.
- `tests/cli_harness.py`, `tests/test_cli_*_surface.py`: new, and written first.
  One test per scenario in the three CLI capabilities, driving each role as a
  subprocess. This is the safety net the rest of the change is checked against,
  which is why it comes before anything moves.
- `MODULE_DESCRIPTION.md`: describes the current module layout and needs
  rewriting to match the new one.
