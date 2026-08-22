## Context

See `proposal.md` — Why. The constraints that shape the approach:

- **The characterisation suite is the proof of correctness.** The CLI surface
  tests added by task 1 assert observable behaviour — what each role prints in
  response to each command — rather than internal structure, so they hold across
  the whole refactor no matter how the modules move underneath. They, not the
  unit tests' import paths, are what says nothing observable changed.
- **Printed output is part of the contract.** `test_server_client_integration.py`
  drives the CLIs over stdin and matches their stdout — `'client.py> '`,
  `'waiting for turn to complete...'`, `'commit complete'`. Message wording is
  not free to drift during this change.
- **Games in progress are not a constraint.** No game outlives this change, so
  the on-disk format is free to move where the data model is better for it; see
  Decision 9.
- **The specs already characterise the CLIs.** `player-client`, `game-server`
  and `game-observer` carry roughly eighty scenarios between them, covering
  argument counts, invalid input, phase gating and role restrictions. They are
  written; they are largely untested.
- **The optional `board` package decides how the board is drawn, and CI installs
  it.** `BoardGameConcept.py` delegates drawing to `board` when the import
  succeeds and to `_FallbackBoard` when it does not, and the two render
  differently: `'+-+-+-+\n|X|#|#|\n...'` against `'X##\n###\n'`.
  `requirements.txt` lists `board` and the CI workflow installs it, while
  `pyproject.toml` does not, so `pip install .` gets the fallback. The same
  command prints a different board in the two environments today.

## Goals / Non-Goals

**Goals:**

- Four packages with one responsibility each, and an explicit interface between
  storage and everything above it.
- The engine computes and reports; it does not print, serialise, or read the
  filesystem.
- One grammar, parsed once, shared by all three roles.
- Every rule enforced in one place, reachable by callers that are not the CLI.
- The command surface each role presents, and what it prints, unchanged — except
  where the code diverges from its own spec, which is corrected (Decision 13).

**Non-Goals:**

- Loading a game written before this change, or keeping the current import
  paths. Neither has a user to protect: no game outlives the change, and the
  package has no consumer outside this repository.
- Changing what any role can do, or what any role may see. Correcting a
  divergence restores the specified behaviour; it does not add to it.
- Any new dependency, including a parser generator.
- Performance. The refactor may be slower; nothing here is hot.

## Decisions

### 1. Four packages, split by what would have to change together

```
src/board_game_concept/
    domain/     board, unit, player, events        the rules; no I/O, no yaml
    service/    commands, use cases, views, errors what a caller may ask for
    storage/    repository port, yaml repository   where a game lives
    cli/        grammar, parser, render, session   one REPL, three roles
```

The line between `service` and `domain` is that `domain` knows the rules of the
game and `service` knows the rules of a *session* — who is allowed to do what,
and when. The line between `service` and `storage` is that `service` never names
a file.

Alternative considered: two packages (`core` and `cli`), splitting storage out
later. Rejected — the storage interface is the seam the whole change exists to
create, and deferring it means `GameData` keeps its three jobs.

### 2. The import surface follows the packages

`board_game_concept/__init__.py` re-exports whatever the new layout makes
sensible rather than preserving today's five names, and the unit tests are
updated to import from where things now live.

This reverses an earlier decision to freeze the import surface so that
`tests/test_basic.py`, `tests/test_combat_stalemate.py` and
`tests/test_duplicate_seen_units.py` would never need editing. That was worth
doing while those three files were the only evidence the refactor preserved
behaviour. They no longer are: the characterisation suite from task 1 tests the
CLI surface end to end, which is both stronger evidence and evidence that
survives the modules moving. Holding the import surface still now buys a
weaker guarantee at the cost of a permanently misleading `__init__`.

The package has no consumer outside this repository, so nothing else breaks.

### 3. Rendering and serialisation move out completely

`Board.print` and `Board.listUnits` are called from the tests as well as the
CLIs — `test_combat_stalemate.py:365-379` asserts on captured `board.print`
output, and `test_combat_stalemate.py:394` with
`test_duplicate_seen_units.py:60,88,122` call `yaml.safe_load` on what
`listUnits` builds.

Both methods are removed rather than left as delegating shims, and those five
call sites move to `cli/render.py` and `storage/serialise.py` directly. The
shims were only ever there to keep those files unedited; with the
characterisation suite carrying that job (Decision 2), they would be debt
bought for nothing.

Reading a board's state in a test becomes a call against the serialiser, which
is what the storage layer does too — one path, not two.

### 4. The engine reports events; the caller decides whether to print them

Turn resolution currently narrates to stdout from inside `UnitType.preCommit`,
`resolveContest` and `commit` — 28 `print` calls, some behind `DEBUG`. Resolution
returns a list of events instead, and the CLI renders them.

The events are the same facts the prints carry today (unit attacked unit, unit
destroyed, unit retreated, contest undecided), so the rendered text can be
reproduced exactly where it is currently unconditional. `DEBUG`-guarded prints
are diagnostics rather than behaviour and are dropped at the point they become
events.

This is what later makes a stored turn log possible, but nothing in this change
stores one.

### 5. Hand-written recursive descent, shaped for a grammar it does not yet have

The grammar today is flat — `verb noun args`, LL(2), no nesting — so recursive
descent buys nothing structurally right now. It is chosen anyway because the
destination is unit programs with conditionals, and a flat dispatch table would
have to be thrown away to get there. Structuring it as a descent now costs
almost nothing; retrofitting recursion onto a table costs a rewrite.

No parser generator: no new dependency, better control of error text (which is
contract, per Context), and the grammar is small enough that a generator would
be the larger of the two artefacts.

### 6. Command objects are the service layer's signature

Parsing produces a command object per grammar production, and each one
corresponds to exactly one service function:

```
   "add unit Cross x1 0 0"  ─parse─▶  DeployUnit(type, name, x, y)
                                            │
                                            ▼
                                    service.deploy_unit(session, cmd)
```

Designing the two separately would produce two vocabularies for one set of
operations. One set of names, defined once. The nodes are a uniform tree with a
visitor, not ad-hoc records handled by `isinstance` chains, because the later
interpreter and cost calculator are both visitors over the same shape.

### 7. The parser sees no game state

Split by what each layer can know:

- **Parser**: arity, literal types, keyword validity. Rejects
  `move x1 northeast` and `add unit Cross x1 0` without consulting anything.
- **Service**: phase gating, ownership, occupancy, role. Rejects
  `move x1 north` before the first turn resolves, or a player moving another
  player's unit.

Today both live in the same `if` chain. Separating them is what lets the parser
be tested with no game and no filesystem, and it is what makes the same parser
usable by a caller that is not a terminal.

### 8. Errors replace `sys.exit`, and their text is fixed

`GameData.load` calls `sys.exit(1)` at four points. Those become a small
exception hierarchy under `service/errors.py`. The CLI catches them at the
session loop and prints — reproducing today's messages verbatim, because the
integration tests match on them.

The role table (`game-server:90` "only the administrator may size the board",
`game-observer:30` "no mutating commands") moves out of the REPLs and becomes
data the session consults before dispatching. Its refusal messages are equally
fixed.

### 9. The data model is normalised

Player numbers are integers everywhere, and unit statistics are stored as the
integers they are.

Today they are neither. `add player 1` at the server prompt stores the *string*
`'1'` (`server.py:229`), which is written out as `number: '1'`, while
`load player player_1.yaml` reads the *integer* `1`; `client.py:49` takes its
player number from `argv` as a string and so only matches games created the
first way. Unit statistics are written as quoted strings and re-cast with
`int()` on every load.

Normalising this changes the bytes on disk, which is why an earlier version of
this design ruled it out. Since no game outlives the change, there is nothing
to migrate, and carrying the inconsistency through a refactor whose whole point
is to make the data layer replaceable would be perverse — the parser and the
service layer would both have to reproduce it deliberately.

Parsing therefore converts, once, at the edge, and everything below it sees
typed values.

### 10. The repository holds files; the coordinator holds the barrier

`GameData` splits along its two unrelated jobs:

- `storage/yaml_repository.py` — the `games/_<gameno>/{data,players}` layout,
  reading and writing exactly the files it writes today.
- `service/turn.py` — `waitForPlayerCommit`, the commit barrier, the
  order-consumption cycle. It asks the repository what exists; it does not know
  that "exists" means a file.

The base path becomes a constructor argument defaulting to `os.getcwd()`, so
`GameData(gameno, player_number)` behaves as it does now while a caller that is
not a CLI can pass a path.

### 12. The renderer draws the bordered grid, and the `board` dependency goes

Drawing is currently delegated to whichever of two renderers is installed, so
`show board` prints one thing under CI and another under `pip install .`. Once
rendering moves into `cli/render.py` there is one renderer, and it has to pick
one of the two outputs.

It draws the bordered grid the `board` package produces:

```
+-+-+-+
|X|#|#|
+-+-+-+
|#|#|#|
+-+-+-+
```

That is what CI produces, what `requirements.txt` asks for and what the README's
setup instructions give you, so it is the output most runs see today. With
nothing left calling `board.draw`, the optional import, `_FallbackBoard` and the
`board` entry in `requirements.txt` all go, and every environment prints the
same board.

Alternative considered: reproduce `_FallbackBoard`'s plain rows, which is what a
bare `pip install .` prints. Rejected — it changes output for CI and for anyone
who followed the README, which is the larger population.

### 11. The spec scenarios become the characterisation suite

The riskiest step is replacing the command loops, and it is the thinnest-covered:
nine integration tests, none of them touching the observer, none touching `show
types`, `show players`, `load board` or `reload`.

The characterisation is not missing, though — it is written as ~80 scenarios
across the three CLI specs, and simply untested. Turning those into tests is
therefore not invention: it is closing the gap between `openspec/specs/` and the
suite, which the project already treats as the source of truth, and it produces
exactly the safety net this refactor needs. It happens **first**, against the
current code, before any command loop is touched.

Any scenario that fails against today's code has found a divergence rather than
a regression. Two are already known (`proposal.md` — What Changes), and belong in
`SPEC_COVERAGE.md` alongside the existing entries.

### 13. Divergences are corrected where they are found

The characterisation suite turns spec scenarios into tests, so it finds the
places where the code contradicts its own spec. Those are fixed as they are
found rather than being carried through the refactor and fixed afterwards: a
divergence preserved deliberately is one more thing every later step has to
reproduce, and the parser and service layer would have to be written to keep
bugs alive.

Each fix restores what the spec already requires. None of them changes what a
role can do, and none needs a spec delta.

## Risks / Trade-offs

- **Message wording drifts during the refactor and the integration tests fail
  obscurely** → Treat every user-visible string as fixed. Move strings verbatim
  rather than retyping them; do the characterisation suite (Decision 11) first
  so drift is caught at the command that caused it.

- **Editing the unit tests alongside the code they test removes a control**
  (Decisions 2 and 3) → The CLI characterisation suite is the control instead,
  and it is a better one: it asserts what each role prints rather than how the
  package is arranged, so it cannot be quietly adjusted to match a mistake in
  the code. It is written first, before anything moves, for exactly this reason.

- **A divergence fix changes behaviour someone was relying on** (Decision 13) →
  Each fix is checked against the spec scenario that found it, and restores what
  that scenario already required. A correction that would go beyond restoring
  specified behaviour is raised rather than made.

- **Dropping `_FallbackBoard` changes what a bare `pip install .` prints**
  (Decision 12) → The bordered grid is what CI, `requirements.txt` and the
  README's setup all produce today, so the environment whose output changes is
  the one that was already the odd one out. Called out rather than hidden, and
  the characterisation tests pin the chosen output so the divergence cannot
  reappear.

- **A refactor this size is unreviewable as one diff** → Sequenced as the
  Migration Plan below, one commit per step, suite green at each. Any step can
  be reviewed and reverted alone.

- **A mechanical move quietly changes behaviour in a path no test covers** →
  This is what Decision 11 is for, and it is the reason the characterisation
  suite is the first step rather than the last.

## Migration Plan

Each step is a commit; the suite is green at every one. There is no data
migration and no on-disk format change, so reverting any step is a plain
`git revert`.

1. **Characterisation tests** from the CLI spec scenarios, against the current
   code. No source changes. Divergences recorded, not fixed.
2. **Delete `src/BoardGameConcept.py` and `src/GameData.py`.** Stale copies from
   the restructure in `7a26b26`; nothing imports them.
3. **Move modules into the four packages** with no logic change. Imports
   updated, `__init__.py` exports unchanged, `pyproject.toml` script targets
   follow.
4. **Purify the engine**: rendering and serialisation out, events in, shims left
   behind (Decisions 3 and 4).
5. **Grammar, parser and command objects.** The CLIs parse to commands and then
   run the existing code paths unchanged, so only the front half of each REPL
   moves.
6. **Service layer.** The rules move down out of the command loops; the CLIs
   become parse → service → render.
7. **Repository port**, with the YAML implementation behind it and `GameData`
   reduced to a facade (Decisions 2 and 10).

Steps 5–7 are the ones that need step 1 to have happened.

## Open Questions

None of these change the approach, the sequence, or the interfaces above; all
can be answered while the work is in flight.

- `Board.listTypes` (`BoardGameConcept.py:515`) is called from nowhere, and
  shadows its own `player` parameter in its loop. Delete it during step 4 or
  leave it for a cleanup change?
- `src/board_game_concept/test_suite.py` and its `board-game-test-suite` console
  script duplicate `tests/test_basic.py` in a hand-rolled harness. It keeps
  working under Decision 2 either way. Retire it, or keep it?
- When do the Decision 3 shims come out — immediately after this change, or
  bundled into whichever later change first needs the engine free of them?
