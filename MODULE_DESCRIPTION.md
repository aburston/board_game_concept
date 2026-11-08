# Board Game Concept - Module Description

## Overview

A strategy game played in the setup. Players design their own unit types,
write the program each type's units run, deploy them and commit; the server
waits for every player to commit and then resolves the whole game to its
end, every unit thinking and acting for itself, once a turn, and every turn
written into a record the players and the observer replay.

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
- **`player.py`** - `Player`, identified by an integer number, and holding the
  point budget they were registered with. A budget of `None` means the session
  is not entitled to know it - a player reads their own record and nobody
  else's.
- **`unit.py`** - `UnitType`, which is both a type and, once copied onto the
  board, a unit: name, symbol, attack, health, energy and compute, the
  program its units run, plus the direction and state constants. Holds
  movement, combat and contest resolution, the meter a unit pays its ticks
  through, the sleep that rests it, and `cost` - what deploying one unit of
  the design spends, compute included.
- **`program.py`** - the controller: `Program`, which parses a program and
  refuses one that will not run, and the register machine that runs it.
  Eight registers, a memory of words, sensors that read the army's map and
  the unit's own state, actuators that give the unit's order, speak on the
  radio or send it to sleep. `TICKS` is the tariff - every instruction's
  cost, stated once - and `cap` the ticks a point of compute buys a turn.
  Nothing here reads anything but the snapshot it is handed, so a turn stays
  a pure function of the board.
- **`army_map.py`** - `ArmyMap`, the board as one army knows it, shared by
  its units: the squares friendly units have stood on and the enemies they
  have fought where they fought them, each stamped with the turn. Filled by
  standing and fighting and by nothing else; what a program reads with `MAP`
  and `NEAREST`.
- **`army.py`** - what a new game and a newly registered player start with:
  the default board, the catalogue of eight types each with a program that
  fits its compute - the hunter, the vanguard, the explorer and the warden -
  and the sixteen-unit stock array, described by depth from the player's own
  edge: a front rank whose programs all leave it, and a back rank that
  follows, with the Walls beside the Keeps.
- **`placement.py`** - where a player may deploy during setup: the two
  halves of a two-player board, the neutral row of an odd one, and the whole
  board for any other count.
- **`budget.py`** - what a player has spent of their points, what they have
  left, and whether they can afford a type. Spend is summed off the board
  rather than counted, so no total can drift out of step with the army; there
  are no refunds for a destroyed unit. Both places a unit can reach the board
  - the client's `add unit` and the turn's resolution - ask this one module,
  so the refusal and the rejection cannot come to disagree.
- **`board.py`** - `Board`, the grid and the units on it. Placement, lookup,
  visibility bookkeeping, `settle`, which applies the deployments of a setup
  and nothing else, and `commit`, which resolves a turn: the radio is
  delivered, every controller thinks and gives its unit's order, every unit
  moves, combat is resolved in every contested square, the maps are brought
  up to date and the turn is recorded. It also answers who carries each
  player's flag and whose has fallen, read off the board rather than from a
  list that could disagree with it.
- **`events.py`** - what happened while a turn was resolved. `Board.commit`
  returns these in order; whoever called it decides whether to show them.
  `flag_fallen` is the one that ends somebody's game; `thought` is what a
  controller did, and is its owner's.

The engine performs no I/O. It does not print, does not write YAML, and does
not know how it is drawn.

### service - the use cases

- **`commands.py`** - one node per thing a caller can ask for. Parsing produces
  these and the service layer acts on them, so both are named for the same
  thing. They carry their children, ready for a grammar that nests.
- **`games.py`** - one function per command: sizing the board, registering
  players, loading configuration, defining types, setting a type's program,
  deploying units, designating the flag. Each carries the command out or
  refuses it by raising. The rules about *when* - only before the setup is
  committed, only your own types - are stated here, once. `perform` is the one way a caller changes
  a game: it carries the command out and writes it into the session's draft, so
  a caller cannot carry one out without recording it. A refused command is not
  recorded.
- **`game.py`** - `Game`, a game as one session sees it: the board, the
  players, what this player can see, what was refused last turn. Knows how to
  read a game through a repository, and to put back what this session had done
  and not committed - its own draft and never another's, replayed through the
  same rules that first accepted it.
- **`turn.py`** - publishing a setup, the commit barrier, and the resolution
  that follows the last commit: the game is played to its end in one sitting,
  turn after turn, until a flag falls and one player is left, the board
  repeats a state it has been in before, or the turn cap is reached. The
  barrier lives here because "every player has committed" is a rule about
  the game, not a fact about files.
- **`replay.py`** - reading the record back: one turn as a seat may see it
  (the board after it, drawn whole or as one army knew it, what it did, what
  it would not do for the player, and the player's own traces) and a type's
  program listed with the ticks each line costs. Entitlement is decided here
  and nowhere else.
- **`turn_feed.py`** - what each seat is told the turn did. The engine's
  events, turned into records and filtered per seat: a seat reads anything one
  of its own units did or had done to it, and other people's units only where
  it could see every unit involved. The filtering happens at resolution
  because a sighting lasts one turn, so there is nothing left later to decide
  it with. It also puts the square of a contest onto the attacks thrown inside
  it, which is what lets a board draw where a fight was.
- **`registry.py`** - which games exist and what state each is in - setting
  up, decided, undecided - derived by reading the games tree.
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
  turn's events are recorded to `turn_events` and each seat's share of them to
  `player_events`; `known_types` holds the designs each seat has met, which
  outlive the sighting that taught them - `show events` and `show designs`
  read those, at a command line and in a browser alike. The schema is
  re-applied whenever a table it describes is missing, so a game made by an
  older build gains the tables added since. SQLite is the default backend.
- **`schema.sql`** - the DDL loaded when a SQLite backend finds a table it
  describes missing. Each table maps nearly one-to-one to what a YAML file
  held; `sightings`, `turn_events`, `player_events` and `known_types` are the
  four the schema adds. Every statement is `IF NOT EXISTS`, which is what makes
  re-applying it to an existing game safe.
- **`serialise.py`** - the plain-data documents storage takes: `units_document`
  for the units file shape, `serialise_draft` and `restore_draft` for the
  commands a session has not committed yet.
- **`lock.py`** - holding a game while it is read or written on the YAML
  backend. An advisory lock on a file in the game's root: a caller holding
  it for writing excludes every other holder, and readers may hold it
  together. Where the platform has no such lock this does nothing and says
  so. The SQLite backend uses a transaction for the same job.
- **`notify.py`** - the `Notifier` interface a `Game` waits through, with
  `NullNotifier` as its one implementation. Local waits poll at
  `POLL_INTERVAL` (0.2s); the outer loops in `service/turn.py` re-check
  the condition on every return. HTTP-side waiting is long-poll served
  by `http/app.py` and never goes through this interface. The ABC stays
  as the seam a future push notifier (SSE, WebSocket, Redis pub/sub)
  hangs off.

### http - the HTTP tier

- **`views.py`** - one function per `show` subject, each returning plain data.
  Also what the HTTP tier hands over the wire, so the two are the same JSON
  and cannot come to disagree. `cli/views.py` is a re-export shim for callers
  the seam has not yet stopped naming directly.
- **`app.py`** - `create_app(base_path, backend)` returns a Flask app that
  serves both halves of the seam. Reads:
  `/games/<gameno>/players/<n>/state`,
  `/games/<gameno>/players/<n>/views/<subject>`,
  `/games/<gameno>/players`; each opens a fresh `Game`, calls `load()`,
  and returns the JSON. The record: `.../players/<n>/turns` lists the
  turns, `.../turns/<t>` is one of them as `replay.turn_view` draws it for
  that seat (`?known=1` for the board as the seat's army knew it, `&seat=`
  for a session that sees everything to say whose), and
  `.../programs/<type>` lists a program. `GET /_/program` is the tariff
  and `POST /_/program/check` prices a program before it is set; both are
  what the browser's editor runs on, so it cannot disagree with the
  server. Writes: `POST /games/<gameno>/players/<n>/commands` takes the
  record `commands.as_record` produces, decodes with `from_record`, holds
  the game for writing, and runs `games.perform`. Commit: `POST
  /games/<gameno>/players/<n>/commit` publishes and, when the barrier is
  met, resolves the whole game inline - 200 with `resolved: true` when the
  request itself resolved it, 202 with `waiting_on: [n, ...]` when it left
  the barrier open. Long-poll: `GET /wait/turn` and `GET /wait/commit`
  hold the request up to `WAIT_BUDGET` seconds, either the condition is
  met and the server answers, or the budget runs out and the client's loop
  asks again.
- **`bgcapiserver.py`** - the console-script entry point that runs the
  Flask dev server. `--host`, `--port`, `--base-path`, `--backend`; local by
  default, and a real deployment binds where its operator wants. Its banner
  says where the server can be reached: bound to `0.0.0.0` it finds the
  machine's network address rather than printing the wildcard, and draws
  that address as a QR code on the terminal (via `segno`) so a phone across
  the room scans the host's screen instead of typing an IP. Loopback gets
  no code, since nothing else could reach it.

### cli - the three roles

- **`grammar.py`** - the language all three roles share, described once.
- **`parser.py`** - a recursive descent parser over it. Answers questions about
  shape - how many arguments, which are numbers, which words are directions -
  and never about the game.
- **`roles.py`** - which part of the grammar each role may use. The observer is
  read-only because it is not given the commands that write.
- **`help.py`** - generated from the grammar and the role's table, so it lists
  what the role will actually accept.
- **`render.py`** - the board as a grid of squares between rules, a
  program's listing, and a turn of the record.
- **`show.py`** - answering `show`, and `Replay`, which keeps the turn a
  session is looking at so that `next` and `prev` know where they are.
- **`session.py`** - what all three sessions share: turning a line into a
  command, reporting a refusal, and failing when the game cannot be read.
- **`backend.py`** - the seam between a role and the game it drives. Every
  role holds a `Session` and talks to it, rather than reaching into a `Game`;
  `LocalSession` is the in-process implementation (the in-process `Game`,
  `service.games` and turn functions the roles used to call directly),
  `HttpSession` speaks HTTP against `bgcapiserver`. Every method the
  seam names is served: read, perform, commit, wait, who is being waited
  for, and the record - the turn numbers, one turn, a program.
- **`bgcserver.py`**, **`bgcclient.py`**, **`bgcobserver.py`** - the roles
  themselves, reduced to what is genuinely theirs. Each file is named for the
  command it is installed as, so a role has one name and not two. All three
  honour `--server URL` (or `BOARD_GAME_SERVER`) and construct an
  `HttpSession` against `bgcapiserver` when set; without it they open the
  game directory themselves and run the local flow. `bgcserver` sets the
  board, registers the players, commits and waits for the players' setups;
  `bgcserver --replay` opens a resolved game at the prompt to read its
  record. `bgcclient` sets a seat up, commits, waits for the rest and then
  shows the outcome and the record; `bgcobserver` opens a resolved game at
  its final turn.

## The three roles

| | Who | Does |
|---|---|---|
| `bgcserver` | 0, the administrator | sets the board size, registers players, commits, and reads the record back with `--replay` |
| `bgcclient` | one player, 1 to 999 | defines types, writes their programs, deploys units, designates the flag, commits, and replays the record |
| `bgcobserver` | 1000, the observer | watches the whole board and replays the record |

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

## How a game goes

1. The administrator sizes the board and registers the players, then commits.
   That commit ends the administrator's setup.
2. Each player defines their unit types, gives each type with compute the
   program its units run, deploys their units, designates the flag carrier,
   and commits once. A program is checked as it is set and refused with the
   line that is wrong; the setup is refused without a carrier.
3. The last commit resolves the game. Turn after turn, until it ends: the
   radio delivers what was said last turn; every awake controller runs its
   type's program against what its army knows, paying its ticks in energy
   through a meter sized by its compute and halting at the per-turn cap;
   every move is worked out against the board as the turn began and applied
   at once; combat is resolved in every contested square; each army's map
   learns where its units stood and what they fought; and the turn is
   written into the record - the board after it, the events, each army's
   map and each controller's trace.
4. Anything a turn will not do - an order a controller gave that its unit
   could not pay for or that would leave the board, a contest that decided
   nothing - is in the record against the unit that gave it, rather than
   taking the turn down.
5. The game ends when a flag falls and one player is left standing, which
   decides it; or when the board repeats a state it has been in before,
   nothing has happened for fifty turns, or the turn cap is reached, which
   leaves it undecided. The outcome is
   published and every role shows it and the record.

## Storage

Games live under `games/_<gameno>/`, split into `data` for what is shared and
`players` for what is per-player. The filesystem is also the transport between
the processes: a player publishes a setup by writing a file, and the server
publishes the record the same way, one entry per turn.

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
the published setup. Committing is recorded against a player, and is spent when
the game is resolved.

## Testing

```
pytest
```

- `tests/test_basic.py`, `test_combat_stalemate.py`,
  `test_duplicate_seen_units.py`, `test_turn_events.py` - the engine.
- `tests/test_program_parser.py`, `test_program_executor.py` - the
  controller: what parses, what each instruction does and costs, the meter,
  the cap, sleep and the radio.
- `tests/test_army_map.py` - what an army learns by standing and fighting,
  and nothing else.
- `tests/test_default_army.py` - the catalogue's programs fit their types'
  caps on every turn; `test_full_game.py` plays the stock armies to an end.
- `tests/test_turn_reporting.py`, `test_commit_record.py` - the record:
  what each seat is told, and that every turn is written.
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

## Accounts

Who is asking, as opposed to what they are entitled to. The player numbers and
what each may do are unchanged; these modules decide which numbers an account
may act as, over HTTP.

  * `domain/account.py` - what an account is: its three kinds, the reserved
    names, and the rules a username and a password must satisfy. Hashes
    nothing and stores nothing.
  * `service/accounts.py` - one function per use case (register, authenticate,
    change and reset a password, mint and end a token, claim and release a
    seat), and `may_act_as`, which is the one rule about which numbers an
    account may be. `service/identity.py` still answers what a *number* is
    entitled to and is untouched.
  * `storage/account_store.py` - the port, in the shape of
    `storage/repository.py`, and `make_account_store`, which is the only way
    one is built.
  * `storage/sqlite_account_store.py`, `storage/accounts.sql` - the SQLite
    implementation, one file at `accounts.sqlite3`.
  * `storage/yaml_account_store.py` - the YAML implementation, three files
    under `accounts/`, created private to the user running the server because
    they carry password hashes.
  * `http/auth.py` - the guard in front of every route that names a number,
    and where a token is read from.
  * `http/sessions.py` - registering, signing in and out, passwords, tokens.
  * `http/seats.py` - which seats a game holds, and taking or giving up one.

The store is one per server, beside the `games/` tree rather than inside any
game — the only state in this project that is not scoped to one game, because
a person outlives every game they play in. Which backend keeps it is the
backend the games use: one choice drives both, and a deployment is never a
SQLite store beside YAML games. It is opened per request, for the same reason
a game repository is: a SQLite connection belongs to the thread that opened
it.

## The web interface

  * `service/registry.py` - which games exist and what state each is in,
    derived by reading the games tree rather than kept in a record, so it
    cannot drift out of step with what is on disk. Also making a game.
  * `http/registry.py` - `GET /games` and `POST /games`, the two things a
    lobby needs that the per-game API could not answer.
  * `http/static/` - the interface, as plain files with no build step:
    `index.html` (one page), `app.js` (one state object, one `render`, and
    the routing), `api.js` (every call the page makes, in one file),
    `board.js` (the SVG board), `lobby.js`, `armoury.js` (designing types
    and writing their programs), `program.js` (the listing that prices a
    program line by line, from the tariff the server publishes), `play.js`
    (the replay: stepping and playing through the record, the known board,
    the traces), `style.css`.

The interface reaches the game only through the contract every other client
uses. That is the cheapest test that the contract is complete: anything the
page cannot do is a gap in the API rather than a reason for a private route,
and `tests/test_web_flow.py` drives exactly the calls `api.js` makes.

## Built, at last

The unit programming the concept is named for is built: `domain/program.py`
is the controller, `domain/army_map.py` what it reads, `service/replay.py`
how what it did is read back, and the `unit-program` capability under
`openspec/specs/` what all three are held to. Nothing documented is absent;
`SPEC_COVERAGE.md` records where each requirement is held.
