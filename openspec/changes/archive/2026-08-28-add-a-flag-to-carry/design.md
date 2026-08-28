## Context

See `proposal.md` — Why, and `specs/flag-carrier/spec.md` for what is being
built. What shapes the approach is what is already there:

- **Visibility is per-player and materialised.** Every resolution writes each
  player a view holding only the units that player may see, and every session
  is built from its own view rather than from the authoritative board. A flag
  has to be visible to somebody who has no view of the unit carrying it, so it
  cannot travel inside that view.
- **Elimination is derived, not recorded.** `eliminated_players` reads the
  board every turn and answers who has nothing that can act. Nothing durable
  says "out", which is what keeps the answer from drifting out of step with
  the board.
- **Resolution is deterministic.** Nothing may depend on a list's order, a
  clock, or an object's identity — `tests/test_determinism.py` holds the
  domain to it.
- **Two storage backends behind one port**, and a schema that is re-applied
  when a table it describes is missing, so an additive table reaches games
  that already exist.
- **Two clients of one contract.** Everything the browser can read, a prompt
  can read; `tests/test_web_flow.py` fails if a view exists for one and not
  the other.

## Goals / Non-Goals

**Goals:**

- One designation per player, stored on the unit, fixed by the setup commit.
- Every flag's square and owner readable by every seat, without leaking
  anything else about the unit carrying it.
- Elimination on flag loss, derived from the board like the rule beside it.
- The same feature at a prompt, in a browser, and in both storage backends.

**Non-Goals:**

- Passing, dropping or recapturing a flag. It is fixed for the game.
- A flag changing what a unit can do: no bonus, no penalty, no cost.
- Scoring by flags held, or any second victory condition.
- Re-entering a game after elimination.

## Decisions

### The flag is a property of the unit, not a list held by the player

A boolean on the unit, stored beside `destroyed` and `on_board`.

The alternative was a per-player `flag_unit: <name>` on the player record. It
duplicates a name that already exists, and it can disagree with the board — a
player record naming a unit the board does not hold has to be reconciled by
somebody, and the reconciliation is the bug. On the unit, "exactly one" is a
rule enforced where the designation is made, and a game restored from storage
cannot contradict itself.

`UnitType.__init__` does not gain a parameter: the flag is set after
construction, the way `state` and `direction` are, so nothing that builds a
unit today has to learn about it.

### Flags are published as their own record, not inside a player's view

A resolution already writes `units.yaml` (the whole board) and a view per
player (what that player may see). It writes a third thing: the flags, one
entry per player, holding the owner, the square and whether the carrier is
standing.

The alternative was to smuggle the carrier into each player's view with its
statistics blanked. That puts a half-hidden unit inside the one document whose
whole meaning is "these are units you may see", and every reader —
`units_view`, the board renderer, the CLI table, the browser — would have to
learn the difference between a unit and a rumour of one. A separate record
keeps the view meaning exactly what it means, and makes "position and owner,
nothing else" a property of the shape rather than of everybody's discipline.

It is on the repository port and implemented by both backends: a table in
SQLite, a file under `data/` in YAML.

### Elimination stays derived, and gains one clause

`eliminated_players` answers "nothing that can act" today. It gains "or their
flag carrier is destroyed", read from the same board. Nothing durable records
elimination, so it cannot drift, and a game restored from storage derives the
same answer it had.

A player eliminated by flag loss keeps units on the board — which is exactly
the state the existing wall clause already produces ("their walls stay on the
board, holding their squares"), so the rest of the engine has met this before.

### Inert units are enforced in the engine, not by asking clients not to order

`Board.commit` skips movement and attack for a unit whose owner is eliminated.
Refusing the order at the prompt as well is a courtesy, not the rule: a client
that publishes an order anyway must not be able to move a dead player's army.

This needs the engine to know which players are out, which today is a service
concern. The unit already carries its `Player`, so the flag-loss test is
answerable inside the domain: a player is out when the unit carrying their
flag is destroyed. `Board.commit` asks that question of the board it is
resolving, and consults nothing outside it — the determinism invariant holds.

### The setup refusal lives with the other setup refusals

A player's commit publishes their army. The check that exactly one of their
units carries the flag goes where "the board is too small to commit" already
is, so every client gets the same refusal from one place, and the HTTP tier
reports it rather than answering 200 the way it used to for the
administrator's boardless setup.

### Drawing it: a glyph on the square, and a legend row that names no type

The ASCII board and the browser both draw the flag on its square. Where the
seat cannot see the unit, the square draws the flag glyph alone; where it can,
the unit is drawn as it always was and marked as the carrier. The legend names
a flag as "player N's flag", never as a type, because the type is the thing
being withheld.

## Risks / Trade-offs

- **A flag tells an enemy where you are from turn one.** → That is the
  feature. What it does not tell them is what they will meet, which keeps the
  design decision — a cheap fast carrier hiding in a crowd, or a brute
  everybody can see coming — worth making.

- **A player who loses their flag early is out early, with an army still
  standing.** → Their units become terrain rather than vanishing, so the board
  they leave behind still matters to whoever is left. It is a shorter game,
  which is the point of the change.

- **The published flags are a new way to leak.** → They carry three fields —
  owner, square, standing — and a test asserts that no name, type, symbol or
  statistic can be read from them, beside the tests that already hold the
  per-player views to what contact allows.

- **Compulsory designation breaks an old habit.** → A setup that used to
  commit now refuses until a carrier is named. Games committed before the
  change keep playing under the old rule, so nothing in flight is invalidated;
  what changes is what a new setup must say.

- **A unit that carries the flag is a unit that cannot hide.** A player may
  designate a wall, which cannot move: a stationary flag is a target that
  never leaves. → Allowed deliberately. It is a real strategy (a fortress
  around the flag) and refusing it would be inventing a rule the game does not
  need.

## Migration Plan

Additive at every layer, with no data rewritten:

1. Storage gains a unit field and a flags record. `CREATE TABLE IF NOT EXISTS`
   plus the schema-repair already in place means an existing SQLite game gains
   the table on its next `ensure()`; a YAML game gains a file when it is next
   resolved. A unit record with no flag field reads back as carrying nothing.
2. A game whose setups were committed before the change has no carrier, so no
   flag is published and nobody can lose one. It plays under the rule it was
   set up under.
3. New setups are refused without a carrier from the moment the change lands.

Rolling back is deleting the code: the stored field and the flags record are
ignored by a build that does not know about them, and no existing field
changes meaning.

## Open Questions

None. The four decisions that would have changed the specs — whether a flag is
compulsory, what becomes of an eliminated player's units, whether the flag can
be reassigned, and how much a flag discloses — were settled before this was
written and are in the specs as requirements.
