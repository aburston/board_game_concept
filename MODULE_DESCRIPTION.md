# Board Game Concept - Module Description

## Overview

A turn-based, simultaneous-commit strategy game. Players design their own unit
types, deploy them, and order them each turn; the server waits for every player
to commit, then resolves all their orders at once.

`openspec/specs/` is the source of truth for what the game does.
`GAME_RULES.md` reads those specs and the code back as one set of rules, and
lists what is still unclear. `SPEC_COVERAGE.md` records where the code has
diverged from the specs and what was done about each. This file describes how
the code is arranged.

## Layout

```
src/board_game_concept/
    domain/     the rules of the game
    service/    what a caller may ask of a game, and when
    storage/    where a game is kept
    http/       the HTTP tier: `views.py` and the Flask app
    cli/        the three interactive roles
```

Each package depends only on the ones below it. Nothing in `domain` knows that
games are stored anywhere or that anyone is watching; nothing in `service`
names a file; nothing below `cli` reads a line of input or prints.

The split exists so that the pieces can be replaced one at a time - a database
in place of the YAML files, an HTTP API alongside the terminal - without
touching the parts that do not care.

### domain - the rules

- **`square.py`** - `Empty`, what a square holds when nothing else does.
- **`player.py`** - `Player`, identified by an integer number.
- **`unit.py`** - `UnitType`, which is both a type and, once copied onto the
  board, a unit: name, symbol, attack, health, energy, plus the direction and
  state constants. Holds movement, combat and contest resolution.
- **`board.py`** - `Board`, the grid and the units on it. Placement, lookup,
  visibility bookkeeping, and `commit`, which resolves a turn in two phases:
  every unit moves, and only then is combat resolved in every contested square.
- **`events.py`** - what happened while a turn was resolved. `Board.commit`
  returns these in order; whoever called it decides whether to show them.

The engine performs no I/O. It does not print, does not write YAML, and does
not know how it is drawn.

### service - the use cases

- **`commands.py`** - one node per thing a caller can ask for. Parsing produces
  these and the service layer acts on them, so both are named for the same
  thing. They carry their children, ready for a grammar that nests.
- **`games.py`** - one function per command: sizing the board, registering
  players, loading configuration, defining types, deploying units, ordering
  moves. Each carries the command out or refuses it by raising. The rules about
  *when* - only before the game starts, only after the first turn, only your
  own units - are stated here, once. `perform` is the one way a caller changes
  a game: it carries the command out and writes it into the session's draft, so
  a caller cannot carry one out without recording it. A refused command is not
  recorded.
- **`game.py`** - `Game`, a game as one session sees it: the board, the
  players, what this player can see, what was refused last turn. Knows how to
  read a game through a repository, and to put back what this session had done
  and not committed - its own draft and never another's, replayed through the
  same rules that first accepted it.
- **`turn.py`** - publishing orders, resolving a turn, and the commit barrier.
  The barrier lives here because "every player has committed" is a rule about
  the game, not a fact about files.
- **`identity.py`** - who a session is: the administrator, a player, or the
  observer, and what each is entitled to. The reserved numbers live here rather
  than in the domain because the engine resolves turns for players and has
  never heard of an administrator; what a *player's* number may be is `Player`'s
  and is taken from it.
- **`errors.py`** - what goes wrong, raised rather than printed, so a caller
  that is not a terminal can decide what to do about it.

### storage - where a game is kept

- **`repository.py`** - `GameRepository`, the operations a game's storage has
  to offer. Reads and writes, no rules; takes documents rather than text. The
  bus is not on it any more - a backend that does not know how to rendezvous
  is fine, and `Game` fits it with the notifier that does.
- **`yaml_repository.py`** - one of the two implementations of the port. The
  layout `game-persistence` describes: shared data under `data`, per-player
  files under `players`, one directory per game number. The only module that
  knows any of those names, and the only one that composes today's hand-
  crafted YAML text - the emitter turning a document into those bytes lives
  here.
- **`sqlite_repository.py`** - the other implementation. One SQLite database
  per game, at `games/_<gameno>/game.sqlite3`, with the schema in
  `schema.sql`. `held()` is a transaction (`BEGIN IMMEDIATE` for a writer,
  `BEGIN DEFERRED` for a reader, WAL on); `read_view` runs a visibility
  join against `sightings` rather than reading a materialised file; every
  turn's events are recorded to `turn_events`, ready for a caller to read.
  SQLite is the default backend.
- **`schema.sql`** - the DDL loaded on first `ensure()` of a SQLite backend.
  Each table maps nearly one-to-one to what a YAML file held; `sightings`
  and `turn_events` are the two the schema adds.
- **`serialise.py`** - the plain-data documents storage takes: `units_document`
  for the units file shape, `serialise_draft` and `restore_draft` for the
  commands a session has not committed yet.
- **`lock.py`** - holding a game while it is read or written on the YAML
  backend. An advisory lock on a file in the game's root: a caller holding
  it for writing excludes every other holder, and readers may hold it
  together. Where the platform has no such lock this does nothing and says
  so, as `notify.py` waits on the clock where there are no FIFOs. The
  SQLite backend uses a transaction for the same job.
- **`notify.py`** - the bus, on its own interface. `Notifier` (an ABC over
  `wake` and `waiter`), `FifoNotifier` around the FIFO helpers both
  backends use, and `NullNotifier` for a backend that carries no bus.
  `Game` picks the one that fits the repository it was handed.

### http - the HTTP tier

- **`views.py`** - one function per `show` subject, each returning plain data.
  Also what the HTTP tier hands over the wire, so the two are the same JSON
  and cannot come to disagree. `cli/views.py` is a re-export shim for callers
  the seam has not yet stopped naming directly.
- **`app.py`** - `create_app(base_path, backend)` returns a Flask app that
  serves the read side: `/games/<gameno>/players/<n>/state`,
  `/games/<gameno>/players/<n>/views/<subject>`, and `/games/<gameno>/players`.
  Each request opens a fresh `Game` and calls `load()`; no cache to disagree
  with the game. Writes and long-poll are later steps.
- **`bgcapiserver.py`** - the console-script entry point that runs the
  Flask dev server. `--host`, `--port`, `--base-path`, `--backend`; local by
  default, and a real deployment binds where its operator wants.

### cli - the three roles

- **`grammar.py`** - the language all three roles share, described once.
- **`parser.py`** - a recursive descent parser over it. Answers questions about
  shape - how many arguments, which are numbers, which words are directions -
  and never about the game.
- **`roles.py`** - which part of the grammar each role may use. The observer is
  read-only because it is not given the commands that write.
- **`help.py`** - generated from the grammar and the role's table, so it lists
  what the role will actually accept.
- **`render.py`** - the board as a grid of squares between rules.
- **`session.py`** - what all three sessions share: turning a line into a
  command, reporting a refusal, and failing when the game cannot be read.
- **`backend.py`** - the seam between a role and the game it drives. Every
  role holds a `Session` and talks to it, rather than reaching into a `Game`;
  `LocalSession` is the in-process implementation (the in-process `Game`,
  `service.games` and turn functions the roles used to call directly),
  `HttpSession` speaks HTTP against `bgcapiserver`. The read half is served
  today; the write half raises `NotImplementedError` and lands in step 3.
- **`bgcserver.py`**, **`bgcclient.py`**, **`bgcobserver.py`** - the roles
  themselves, reduced to what is genuinely theirs. Each file is named for the
  command it is installed as, so a role has one name and not two.

## The three roles

| | Who | Does |
|---|---|---|
| `bgcserver` | 0, the administrator | sets the board size, registers players, then runs unattended as the commit authority |
| `bgcclient` | one player, 1 to 999 | defines types, deploys units, orders moves, commits |
| `bgcobserver` | 1000, the observer | watches, and can reload |

The three numbers are three identities, and `service/identity.py` is where they
are named. The administrator and the observer are both entitled to the whole
game and only one of them may change it, which is a distinction nothing below
the command line could make while they shared a number.

Installing the package puts those three on the path and nothing else. Each names
itself in its prompt and its usage from a `PROGRAM` constant rather than from
`argv[0]`, so a role is called the same thing however it was started.

`src/board_game_concept/test_suite.py` runs a standalone harness covering the
same ground as `tests/test_basic.py`. It has no command of its own - it is
developer tooling, so it is run as `python -m board_game_concept.test_suite`.

## How a turn goes

1. The administrator sizes the board and registers the players, then commits.
   That first commit ends setup.
2. Each player defines their unit types and deploys their units, then commits.
   Committing publishes their orders and signals the server.
3. The server waits until every player still in the game has committed, then
   applies all their orders together, works out every destination against the
   board as the turn began, applies all the moves at once, resolves combat in
   every contested square, and publishes the result: the board, the turn
   number, and what each player is entitled to see.
4. Anything it will not carry out - an order it refused, a move nobody could
   pay for, a contest that decided nothing - is reported back to the player who
   gave it, rather than taking the turn down.
5. Players are woken, and order the next turn. When a turn leaves one player
   standing, the game is decided, the outcome is published, and the server
   reports it and stops.

## Storage

Games live under `games/_<gameno>/`, split into `data` for what is shared and
`players` for what is per-player. The filesystem is also the transport between
the processes: a player publishes orders by writing a file, and the server
publishes results the same way.

Where that root is, is given to the repository rather than read from the
process working directory.

A game is held while it is used: a turn being resolved and a commit being
published hold it for writing, and reading it holds it for reading. Waiting
never holds it - a barrier waits for as long as a player takes to decide, and a
game held across that would be stopped rather than protected. Every write
replaces its file rather than emptying and refilling it, so a reader sees the
old contents or the new ones and a crash leaves the old ones.

What a session has done and not committed is kept too, as the commands that did
it, stamped with the turn they belong to. A draft is private to the session
that made it and is discarded when that session commits, its work having become
the published orders. Committing is recorded against a player and a turn, and
is spent when that turn is resolved - the way the orders it published are.

## Testing

```
pytest
```

- `tests/test_basic.py`, `test_combat_stalemate.py`,
  `test_duplicate_seen_units.py`, `test_turn_events.py` - the engine.
- `tests/test_parser.py` - the grammar, with no game behind it.
- `tests/test_repository.py` - the storage seam.
- `tests/test_turn_notification.py` - waking rather than polling.
- `tests/test_cli_server_surface.py`, `test_cli_client_surface.py`,
  `test_cli_observer_surface.py` - one test per scenario in the three CLI
  capabilities, driving each role as a subprocess. These are what any change to
  the command surface is checked against.
- `tests/test_server_client_integration.py` - two roles against one game.

## Dependencies

Python 3.10 or later and PyYAML. Nothing else.

## Not built yet

An HTTP API, a web interface, accounts, and the unit programming the concept is
named for. See `SPEC_COVERAGE.md` for what is documented but absent.
