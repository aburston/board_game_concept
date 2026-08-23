## Context

See `proposal.md` — Why. What matters here is the shape of the code the change
lands in.

A session's uncommitted work is held in three places at once: `Game.board`
(deployments and move orders, as unit state), `Game.players[n]['types']` (type
definitions), and nothing else. `turn.publish` turns the first into
`players/<n>_units.yaml` via `serialise_orders`, and the second into
`players/<n>.yaml` via `write_player`. Both happen at commit and never before.

Two facts about that code shaped every decision below.

**`serialise_orders` cannot represent a type definition.** It walks
`board.units` and writes unit records. A design that stores the draft in that
format needs a second, parallel structure for types — and the proposal
establishes that a draft must carry types, because a drafted deployment names
one and replay fails without it.

**The service functions already are the operations a draft records.**
`games.define_type`, `games.deploy_unit` and `games.order_move` each take a
command object and either carry it out against the loaded `Game` or raise
`GameError`. `service/commands.py` already gives those commands `fields`,
`__eq__` and `__repr__`. Nothing new has to be invented to describe what a
player did — it is already described.

## Goals / Non-Goals

**Goals:**
- A draft that survives the process that made it, for every role including the
  administrator.
- One code path that records a draft, so no caller — CLI today, HTTP later —
  can carry out a command without recording it.
- No change to the format the server consumes, so turn resolution is untouched.

**Non-Goals:**
- Locking. The write race catalogued as divergence 10 in `SPEC_COVERAGE.md` is
  neither fixed nor worsened here. The API will need a lock; this is not it.
- Any change to `turn.resolve`, the engine, or the commit barrier's rule.
- Making the draft visible to anyone but its owner, now or by extension later.

## Decisions

### 1. A draft is a list of commands, not a board snapshot

`players/<n>_draft.yaml` holds the commands issued since the last commit, in
order, each as its kind and fields:

```yaml
turn: 3
commands:
  - {kind: add_type, name: Cross, symbol: X, attack: 1, health: 1, energy: 10}
  - {kind: add_unit, type_name: Cross, name: x1, x: 0, y: 0}
  - {kind: move, unit: x1, direction: 1}
```

Serialising is a walk over `Node.fields`; reading back is a lookup from `kind`
to class and `cls(**values)`. Both are small enough to live in
`storage/serialise.py` beside the existing writers.

*Why not a board snapshot*, reusing `serialise_orders`: it cannot hold a type
definition, as above. It also stores the *result* of an order rather than the
order, so a draft restored after the world moved on is restored unexamined —
whereas replaying commands runs them back through `games.py` and refuses what
has become illegal, with the same `GameError` the player would have seen had
they typed it now.

The command form is also what the HTTP layer will want as a request body, and
what `parser.py` already produces from a line. One representation serves the
draft file, the REST body and the CLI — which is the argument `commands.py`
makes for itself in its own docstring.

The cost is replay on every load, proportional to the commands issued this
turn. That is a handful of commands against a board of tens of squares.

### 2. Recording happens in the service layer, behind one entry point

`games.perform(data, command)` carries a command out and, if it does not raise,
appends it to the draft. Callers use `perform`; the individual functions stay
public for replay, which must not re-record what it is replaying.

```
   caller ──▶ games.perform ──┬──▶ games.deploy_unit(data, command)   apply
                              └──▶ repository.write_draft(...)        record

   replay ──▶ games.deploy_unit(data, command)                        apply only
```

This is deliberately not a flag on `Game`. A `replaying` boolean would be a
mode the service layer has to remember to be in, and forgetting it duplicates
every command in the draft on every load.

`perform` also absorbs the command dispatch that `bgcclient.py` and
`bgcserver.py` currently hand-roll as two `if` ladders. That duplication is the
last of the §2.5 problem in `ARCHITECTURE_OPTIONS.md` — rules in CLI branches —
and it is exactly what an HTTP layer would otherwise have written a third copy
of.

### 3. Replay happens in `Game.load()`, after players are loaded

The draft is applied last, onto the view the player was published:

```
   ensure ─▶ board ─▶ progress ─▶ players ─▶ view|units ─▶ rejections ─▶ DRAFT
                                     │                                    │
                                     └── sets new_game ───────────────────┘
                                         (deploy_unit and order_move
                                          both gate on it)
```

Order is forced: `games.deploy_unit` refuses unless `new_game`, and
`games.order_move` refuses unless not `new_game`, and `_load_players` is what
sets it. Replaying earlier would refuse every command in the draft.

A command that raises during replay is dropped and reported to its owner, not
fatal. The alternative — refusing to open a game because one drafted order went
stale — makes a draft a way to lock yourself out.

### 4. The committed order format does not change

`publish` still writes `serialise_orders(board, player)` to
`players/<n>_units.yaml`, because by the time it runs the draft has already
been replayed into the board. Committing is therefore: serialise as today,
record the commit, delete the draft.

This matters more than it looks. `turn.resolve`, `_published_orders`,
`has_orders`, `clear_orders` and `Game.unprocessed_moves` all read committed
orders and **none of them change**. The draft is a new file that nothing
existing reads. The change is additive at the storage layer, which is what
keeps `tests/test_server_client_integration.py` meaningful throughout.

### 5. A draft is stamped with the turn it was drafted for

Replay discards a draft whose `turn` is not the game's current turn. A draft
belongs to one turn; one left behind by a crash during resolution, or written
into the window while the server was clearing orders, is stale rather than
dangerous.

This is the whole mitigation for the resolution race, and it is deliberately
cheap: it cannot prevent the race, only ensure that losing it discards work
rather than replaying last turn's orders into this one.

### 6. Privacy is enforced by not reading, not by the repository

`storage/repository.py` says of itself that a repository "holds no rules". So
`read_draft(number)` will read any player's draft, and `Game.load` calls it
only for `self.player_number` — the same way `_load_players` already reads
`players/<n>.yaml` only when `mine`, and a client is built from `read_view`
rather than `read_units`.

`views.pending_view` is fed from `player['moves']`, which is committed orders.
It is not touched, so `show pending` keeps meaning what it means today and the
observer gains nothing.

### 7. `commit_<number>` gains the turn it was for

The marker file stays where `game-persistence` already says it is and gains a
body: `{turn: N}`. `has_committed` remains "the file exists". `committed_players`
reads the markers and returns those whose turn is the current one, instead of
listing order files.

**This is not load-bearing for the CLI, and the proposal implies more than the
code justifies.** With the draft in a separate file, "committed" is still
exactly "`<n>_units.yaml` exists", and the barrier would keep working
untouched. What is wrong today is subtler: that file means *committed for the
current turn* only because `clear_orders` deletes it at resolution. The commit
fact is encoded in the absence of a deletion.

It is in scope anyway, for three reasons. It makes true a scenario
`game-persistence` already asserts — that the marker "records that they have
committed" — which today it does not, since the barrier ignores the marker
and `has_committed` uses it to mean "has ever committed". It lets an
idempotent `POST /commit` ask whether this player has committed *for this
turn*, which is the question it needs answered and which no file's existence
answers directly. And it is one file and one method, where splitting it out
means editing `game-persistence` twice.

If it is cut, nothing else in this design moves.

### 8. The administrator drafts too

`set_board`, `add_player`, `load_board` and `load_player` record like any other
command. Setup is the most laborious part of a game and the most expensive to
lose, and `POST /games/{id}/players` needs to be durable before a commit for
the same reason a player's deployments do.

`load_board` and `load_player` are recorded as the command, so replay re-reads
the path. A file that has changed or moved since produces a `GameError` on
replay and is dropped per decision 3. Expanding them into primitive commands at
record time would avoid it, but `load_player` sets `players[n]['units']`
directly and has no equivalent in the grammar to expand into.

## Risks / Trade-offs

- **A draft written while the server clears orders is lost** → the turn stamp
  (decision 5) makes it discarded rather than misapplied. Not fixed, because
  fixing it means locking, which is out of scope and belongs with the API.

- **Replay depends on the published view being stable within a turn** → it is:
  views are written only by `turn.resolve`, and the draft is cleared at commit
  and discarded when the turn advances. If turn resolution ever republishes a
  view mid-turn, this assumption breaks and replay produces a board the player
  did not build.

- **`perform` becomes a chokepoint every caller must use** → a caller that
  reaches past it to `games.deploy_unit` silently loses drafting. Mitigated by
  making replay the only in-tree caller that does so, and by a test that drives
  every write command through the CLI and asserts the draft holds it.

- **A stale `load_player` path fails on replay** → reported and dropped, as
  decision 8 describes. The administrator sees which command was dropped and
  can reissue it.

- **Replay cost grows with commands per turn** → bounded by what a person types
  between commits. If drafting is ever driven by a bot issuing thousands of
  orders a turn, a snapshot alongside the command list is the answer, and
  decision 1 does not preclude adding one.

## Migration Plan

No data migration. A game whose players directory holds no `_draft.yaml` loads
exactly as it does now — an absent draft is an empty one — so an in-progress
game keeps playing across the change, and a rollback leaves at most an unread
file behind.

The order of work follows the dependency, not the value:

1. `write_draft` / `read_draft` / `clear_draft` on the port and the YAML
   implementation, plus command serialisation. Nothing calls them yet.
2. `games.perform`, recording. Still nothing reads the draft, so behaviour is
   unchanged and the suite must stay green on its own.
3. Replay in `Game.load`. This is the step that changes observable behaviour,
   and the step the restart test is written against.
4. The CLI ladders collapse into `perform`.
5. The commit record (decision 7), which is independent of 1–4.

Steps 1 and 2 are separately revertable. Step 3 is the one to review hardest.

## Open Questions

- **What a client says when replay drops a command.** The rejection channel
  (`players/<n>_rejected.yaml`) is written by the server about the last resolved
  turn, and a dropped draft command is neither. It may want its own line at load
  rather than a share of that. This changes no requirement and no task — only
  the wording of one message.
