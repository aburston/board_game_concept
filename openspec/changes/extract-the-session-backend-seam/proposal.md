## Why

`put-a-rest-api-under-the-cli` sets out a staircase whose every later step —
SQLite, the HTTP endpoints, inline resolution, retiring the file transport —
stands on one thing: a seam between the CLI REPLs and the game, with two
implementations the migration can flip between. This is step 0, the seam
itself, with only the in-process implementation. It moves no behaviour; it makes
the later moves possible.

Today each role builds a `Game` and reaches into it directly — `data.getBoard()`,
`data.clientSave()`, `data.waitForTurn()`, `games.perform(data, command)`, and
the view built from `data.getBoard()` inside `show`. The REPL and the game are
soldered together. An HTTP client cannot slot in there, because it holds no
`Game` and no board — it holds a view it fetched. So before any of that, the
soldering has to become a seam: one interface the REPLs talk to, and one
implementation behind it that is exactly today's in-process stack.

Doing it first, alone, is what keeps the rest safe. The seam is covered
end-to-end by the existing suite — the integration test drives the real
`bgcserver`/`bgcclient`/`bgcobserver` binaries as subprocesses — so "the CLI
still behaves identically" is checkable at the moment the seam goes in, before
anything harder depends on it.

## What Changes

- **A session interface** captures the narrow surface the REPLs use: open the
  game, read the view for a `show` subject as plain data, read the scalar state
  a loop needs (outcome, turn number, setup-or-play, orders-pending, refusals,
  dropped draft commands, elimination), perform a command, commit, wait for the
  turn, and offer the names completion needs.

- **One implementation, `LocalSession`**, wraps today's `Game`, `service.games`,
  and the turn waits — the same calls the REPLs make now, behind the interface
  instead of in front of it.

- **The three roles are rewritten against the interface.** They construct a
  session rather than a `Game`, and never touch a `Game`, a repository, or a
  board object directly again. Parsing, the role table, rendering, the shared
  session loop and completion are untouched in what they do.

- **`show` is split at the seam it already half-has.** `cli/views.py` builds view
  data and `cli/render.py` turns it into text; today `cli/show.py` calls both.
  Building moves behind the session (it is "my view", which the HTTP
  implementation will one day fetch); rendering stays in the CLI, where it
  belongs. Neither `views.py` nor `render.py` changes.

**No behaviour changes**, which is the point: same commands, same prompts, same
output, same refusals, same waiting. `skip_specs` is set — there is no
spec-level behaviour to delta, and the specs describe behaviour. The proof is
that no test is edited and the suite stays green, the integration suite included.

Not in this change: the HTTP implementation of the interface, SQLite, any
endpoint, and any change to what the roles do. Those are the treads above this
one.

## Capabilities

None. This is an internal restructuring — a pure refactor introducing an
architectural seam — with no change to any capability's behaviour, so it
declares no spec deltas and sets `skip_specs`. The capabilities the later steps
will touch are named in `put-a-rest-api-under-the-cli`.

## Impact

- **New**: a session interface and `LocalSession` in `cli/` (the consumer side)
  — the seam the roles are written against.
- **Reshaped, behaviour preserved**: `cli/bgcserver.py`, `cli/bgcclient.py`,
  `cli/bgcobserver.py` construct and use a session rather than a `Game`;
  `cli/session.py` (the shared loop) and `cli/complete.py` take their game
  facts from the session; `cli/show.py` calls the session for view data and
  keeps rendering.
- **Unchanged**: `cli/views.py`, `cli/render.py`, `cli/parser.py`,
  `cli/grammar.py`, `cli/roles.py`; the whole of `service/`, `storage/` and
  `domain/`. The seam is a consumer-side abstraction; nothing below it moves.
- **Tests**: none edited. The suite — the CLI surface suites and the 542-line
  integration suite driving the real binaries — is the proof the behaviour is
  preserved. If any of it needs a change, the refactor was not pure and the
  change is wrong.
- **Docs**: `MODULE_DESCRIPTION.md`'s account of `cli/` gains the seam.
