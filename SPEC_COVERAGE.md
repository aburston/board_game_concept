# Spec Coverage

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for
spec-driven development. The specifications under `openspec/specs/` are the
source of truth for intended behaviour.

## Capabilities

| Capability | Covers |
|---|---|
| `unit-types` | Unit type definition, statistic ranges, state and direction constants |
| `board-model` | Board creation, unit placement, name uniqueness, lookup, rendering |
| `unit-movement` | Movement orders, edge handling, energy cost, entering occupied cells |
| `combat-resolution` | Contested cells, simultaneous attack rounds, damage, destruction |
| `turn-commit` | Two-phase turn resolution, the all-players commit barrier, setup vs play |
| `visibility` | Own units always visible, enemies revealed by contact, per-player views |
| `game-persistence` | On-disk game layout, YAML formats, orders as transport |
| `player-client` | The `board-game-client` command surface |
| `game-server` | The `board-game-server` command surface and unattended turn cycle |
| `game-observer` | The `board-game-observer` read-only command surface |

Validate them with:

```
openspec validate --specs --strict
```

The scenarios in `player-client`, `game-server` and `game-observer` are covered
one for one by `tests/test_cli_client_surface.py`,
`tests/test_cli_server_surface.py` and `tests/test_cli_observer_surface.py`,
which drive each role as a subprocess and assert what it prints. Run them with:

```
pytest tests/test_cli_client_surface.py tests/test_cli_server_surface.py tests/test_cli_observer_surface.py
```

They are what any change to the command surface is checked against.

## Known divergences

The specs describe intended behaviour. The following are places where the
implementation diverged from them. Each was reproduced against
`src/board_game_concept/` rather than inferred from reading, and all have since
been fixed, so the specs under `openspec/specs/` describe the behaviour the code
now has.

The first three were reported as issues and fixed by changes now archived under
`openspec/changes/archive/`. The rest were found by writing the scenarios in
`player-client`, `game-server` and `game-observer` out as tests — one per
scenario, driving each role as a subprocess — before the `split-into-layers`
change began moving anything. Each entry names the scenario that found it; every
one has a test in `tests/test_cli_*_surface.py`.

### 1. Deploying onto an occupied square crashes (issue #1) — fixed

`UnitType.preCommit` and `UnitType.commit` raised an uncaught `AssertionError`
(`can't add <name> to board at (x,y)`) when a unit was deployed onto a square
that already held one, which propagated out of turn resolution and terminated
the session rather than being reported.

Addressed by the `fix-combat-stalemate-hang` change. Deploying a brand new unit
onto a square that is already taken — or already claimed by a unit waiting to be
placed, which is the case the issue reports — is illegal, and `Board.add` now
refuses it before any state is mutated. The client reports the refusal and stays
usable; the server logs it and resolves the turn without that order. Moving onto
an occupied square is unaffected: that is combat, and stays legal.

The refusal is reported back to the player who gave the order. The server
publishes what it refused as `players/<number>_rejected.yaml` and the client
prints it before taking the next command, naming the unit, its square and the
reason. The refused unit is dropped rather than held, so the player is free to
place it somewhere else on a later turn.

### 2. A contest neither unit can win hangs the server (issue #2) — fixed

`UnitType.commit` looped `while unit_count > 1`, and `unit_count` only decreased
when a unit was destroyed. Two units that contested a cell but could not damage
each other — for example, both with energy below their attack value — never
reduced the count, and the loop never terminated. This was an unbounded spin,
not a slow turn: the server stopped making progress.

Reproduction: two units with energy below their attack value moved into the same
cell.

Addressed by the `fix-combat-stalemate-hang` change: combat ends when a round
lands no attacks, and an undecided contest returns every unit that moved in to
the square it came from, so nobody wins the square. The same change fixes a
survivor-count bug that emptied a contested square out from under a unit that
was still standing, and stops units destroyed in an earlier round from attacking in
later ones.

### 3. A unit seen more than once crashed the client (issue #3) — fixed

`visibility` requires contact to reveal an enemy unit to the player who made it.
Contact was recorded once per attack rather than once per unit, so two units
that fought over several rounds recorded each other many times; the per-player
view then named the enemy once per contact, and the client died restoring a unit
it had already restored. The report the player saw was misleading twice over:
`Board.add`'s duplicate-name assertion interpolated `player.name` while `Player`
defines only `number`, so evaluating the message raised
`AttributeError: 'Player' object has no attribute 'name'` over the top of it.

Reproduction: two units with more health than one round of attacks can spend
moved into the same cell, and a client for either player was then started.

Addressed by the `fix-duplicate-seen-units` change: contact is recorded once per
unit, a view names each unit it reveals once, restoring a unit the board already
holds puts the saved state back into it rather than failing, and the
duplicate-name error names the player by number.

### 4. A bare `add` or `load` kills the server — fixed

`game-server` requires the server to report that one argument is required when
`add player`, `load board` or `load player` is given the wrong number of them.
The arity guard on both verbs tested `len(tokens) == 2`, which is true of
`add player` but not of a bare `add`, so the shorter form fell past the guard to
`tokens[1]` and raised an uncaught `IndexError` that ended the session. The same
guard meant `add player` and `load player` — the case it was presumably written
for — reported a generic "invalid add command" instead of the arity message the
scenario asks for.

Reproduction: `add` or `load` alone at the server prompt.

Addressed by the `split-into-layers` change: the guard tests `len(tokens) < 2`,
so a bare verb is reported and each subcommand reaches its own arity check.

Found by: `game-server` — Registering Players / Wrong argument count, and
Loading Configuration From Files / Wrong argument count.

### 5. `show players` dies on a field nothing sets — fixed

`game-server` requires `show players` to list the registered players. It printed
an `email` field instead, which nothing anywhere sets: not `add player`, not
`load player`, not `GameData.load`. The only other trace of the idea was an empty
`add_player(name, email)` stub. With no players registered the loop body never
ran and the command appeared to work, so the `KeyError` surfaced only once the
game had a player in it — which is to say, always in a real game and never in a
smoke test.

Reproduction: `add player 1`, then `show players`.

Addressed by the `split-into-layers` change: the command prints the player
number, as the client and observer already did, and the stub is removed.

### 6. A board dimension below the minimum is reported as non-numeric — fixed

`game-server` requires a dimension below 2 to be reported as needing to be
greater than 1. `Board` asserts its own limits, and the constructor call sat
inside a `try` whose `except BaseException` reported "x and y must be a
numbers", so an out-of-range dimension was reported as though it were not a
number at all. The two checks written for the case, below that block, were
unreachable.

Reproduction: `set board 1 1`.

Addressed by the `split-into-layers` change: the dimensions are parsed, then
range checked, then used to construct the board, and the board is left to report
its own upper limit.

### 7. A unit a player has just deployed is invisible to them — fixed

`player-client` requires `show units` to list the player's own units and
`add unit` to place one. The client draws the view the server last published in
preference to its own board, so a unit deployed during setup appeared in neither
`show board` nor `show units` until a turn containing it had been resolved. Its
owner had no way to see what they had placed.

That precedence is deliberate and could not simply be reversed: the published
view is what limits a player's visibility, while the client holds the whole board
in memory, so drawing the local board instead would have shown every player every
enemy position.

Reproduction: deploy a unit in a game the server has already committed, then
`show board`.

Addressed by the `split-into-layers` change: a unit the player deploys is added
to the published view as well as to the local board. Only the player's own unit
is mirrored, so nothing the server has not already revealed becomes visible.

### 8. A game set up with `load player` cannot be reopened — fixed

`game-observer` requires the observer to open a game and display it. A player
file records its number as an integer, while `UnitType.dump` writes that number
back into `data/units.yaml` as a quoted string. A game set up through
`load player` was therefore keyed by integers but described by unit records
naming strings, and rebuilding the board looked each unit's player up under a key
that was not there, raising `KeyError`.

The observer died on startup. The server would have died the same way on its next
load, one commit barrier past the point any test had reached, so the crash lived
behind a passing suite.

Reproduction: `load player player_1.yaml`, `commit`, then start the observer
against that game.

Addressed by the `split-into-layers` change: player numbers are converted to
integers at every point they are read — the server prompt, a loaded player file,
a unit dump and the client's argument — and `Player` asserts that it holds one,
so the two ways of creating a game can no longer disagree about what a player is
called.

### 9. The packaged console scripts cannot start anything — fixed

`player-client`, `game-server` and `game-observer` each require their role to
start when invoked with its arguments. `pyproject.toml` declares
`board-game-server`, `board-game-client` and `board-game-observer` as the way to
invoke them, and every one of those raised
`TypeError: main() missing 1 required positional argument: 'argv'` and stopped.
Each role's `main` took `argv`, while the console script setuptools generates
calls it with nothing. Only launching the module files directly, as the tests
did, ever worked.

Reproduction: `pip install .`, then run `board-game-server`.

Addressed by the `split-into-layers` change: `main` defaults its argument to
`sys.argv`. Each role now has a test that calls `main()` with no arguments the
way the generated wrapper does.

### 10. Loading a game races the server deleting orders — fixed

`game-persistence` requires the server to remove each player's pending order
file once it has resolved a turn, and requires a client loading a game to
notice its own orders are still pending. Loading opened every file in the
players directory and then decided what it was by searching the repr of the
open file object for a substring of its name — so it opened files it only
meant to skip, including the order files the server deletes as it resolves.
A file listed a moment earlier could be gone by the time it was opened, and
the load died of `FileNotFoundError`.

The window is small, which is why this never showed while both sides waited
whole seconds for each other. Signalling closed those gaps and the race began
to fire.

Reproduction: run a client through a commit while the server resolves the turn,
repeatedly.

Addressed by the `split-into-layers` change: a file is classified by its name,
so the files that are only skipped are never opened, and the two that are read
tolerate having been removed since the directory was listed. Matching on the
name also made the match exact, where searching for a substring meant
`commit_1` matched `commit_11` and one player could be mistaken for another.

## Documented but not implemented

- **Win condition.** `README.md` and `MODULE_DESCRIPTION.md` both describe the
  game ending when one player is the last with a functional unit. No win, loss,
  or game-over logic exists in the source. The server's turn cycle runs
  indefinitely. No capability specifies it, because there is nothing to specify
  yet — it is a feature to propose, not behaviour to document.
- **Web service.** The Flask/REST API and SQLite backend in `README.md` are
  aspirational; no such code exists.

## Housekeeping

The specs call a board position a **cell**; the source calls it a **square**
(`Board.squareIsFree`, and comments predating these specs). Both terms mean the
same thing. Aligning them is a terminology sweep across all ten capabilities,
which no behavioural change should carry, so it is left as its own job.


`src/board_game_concept/test_suite.py`, run by the `board-game-test-suite`
console script, is a hand-rolled harness covering the same ground as
`tests/test_basic.py`. It was not updated when `fix-combat-stalemate-hang` made
combat multi-round attrition, so its attack test still expected one round of
damage and had been failing 9/10 since. The expectation has been corrected.
Whether the harness is worth keeping alongside pytest at all is open.
