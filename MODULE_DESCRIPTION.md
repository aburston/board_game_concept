# Board Game Concept - Module Description

## Overview

A turn-based, simultaneous-commit strategy game. Players design their own unit
types, deploy them, and order them each turn; the server waits for every player
to commit, then resolves all their orders at once.

`openspec/specs/` is the source of truth for what the game does.
`SPEC_COVERAGE.md` records where the code has diverged from it and what was
done about each. This file describes how the code is arranged.

## Layout

```
src/board_game_concept/
    domain/     the rules of the game
    service/    what a caller may ask of a game, and when
    storage/    where a game is kept
    cli/        the three interactive roles
```

Each package depends only on the ones below it. Nothing in `domain` knows that
games are stored anywhere or that anyone is watching; nothing in `service`
names a file; nothing below `cli` reads a line of input or prints.

The split exists so that the pieces can be replaced one at a time - a database
in place of the YAML files, an HTTP API alongside the terminal - without
touching the parts that do not care.

### domain - the rules

- **`cell.py`** - `Empty`, what a square holds when nothing else does.
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
  own units - are stated here, once.
- **`game.py`** - `Game`, a game as one session sees it: the board, the
  players, what this player can see, what was refused last turn. Knows how to
  read a game through a repository.
- **`turn.py`** - publishing orders, resolving a turn, and the commit barrier.
  The barrier lives here because "every player has committed" is a rule about
  the game, not a fact about files.
- **`errors.py`** - what goes wrong, raised rather than printed, so a caller
  that is not a terminal can decide what to do about it.

### storage - where a game is kept

- **`repository.py`** - `GameRepository`, the operations a game's storage has
  to offer. Reads and writes, no rules. Everything above is written against
  this rather than against a directory of YAML.
- **`yaml_repository.py`** - the layout `game-persistence` describes: shared
  data under `data`, per-player files under `players`, one directory per game
  number. The only module that knows any of those names.
- **`serialise.py`** - units as YAML. The on-disk format, which the roles also
  print verbatim for `show units`.
- **`notify.py`** - waking the other side of the file transport. Each side
  blocks on a FIFO until the other signals; the signal is a hint over a
  re-checked condition, so losing one costs latency and not correctness.

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
- **`server.py`**, **`client.py`**, **`observer.py`** - the roles themselves,
  reduced to what is genuinely theirs.

## The three roles

| | Who | Does |
|---|---|---|
| `board-game-server` | player 0, the administrator | sets the board size, registers players, then runs unattended as the commit authority |
| `board-game-client` | one player | defines types, deploys units, orders moves, commits |
| `board-game-observer` | nobody | watches, and can reload |

`board-game-test-suite` runs a standalone harness covering the same ground as
`tests/test_basic.py`.

## How a turn goes

1. The administrator sizes the board and registers the players, then commits.
   That first commit ends setup.
2. Each player defines their unit types and deploys their units, then commits.
   Committing publishes their orders and signals the server.
3. The server waits until every player has committed, then applies all their
   orders together, resolves movement, resolves combat in every contested
   square, and publishes the result: the board, and what each player is
   entitled to see.
4. An order it will not carry out is refused and reported back to the player
   who gave it, rather than taking the turn down.
5. Players are woken, and order the next turn.

## Storage

Games live under `games/_<gameno>/`, split into `data` for what is shared and
`players` for what is per-player. The filesystem is also the transport between
the processes: a player publishes orders by writing a file, and the server
publishes results the same way.

Where that root is, is given to the repository rather than read from the
process working directory.

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

The win condition, an HTTP API, a web interface, accounts, and the unit
programming the README describes. See `SPEC_COVERAGE.md` for what is documented
but absent.
