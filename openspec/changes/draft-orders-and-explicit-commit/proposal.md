## Why

The RESTful API this project has wanted since the README was written cannot be
built on the storage as it stands, because **there is no such thing as an
uncommitted order**.

A session accumulates everything in memory. `games.define_type` and
`games.deploy_unit` mutate the loaded `Game` and write nothing;
`games.order_move` calls `unit.move()` on the in-memory board. Nothing reaches
disk until `turn.publish` writes `players/<n>_units.yaml` — and the existence of
that file *is* the commit. `committed_players()` is a directory listing.

That is fine for a REPL, which is a process that holds your working state for as
long as you are typing into it. It is fatal for HTTP, which has no such process.
`POST /games/{id}/orders` has nowhere to put an order that has not been
committed yet, and no way to say "committed" other than by publishing it.

Two consequences follow, and the second is the one worth acting on first:

1. **An API needs somewhere to accumulate.** Either a stateful session per
   token, or a durable draft. A durable draft is the honest answer for REST.
2. **The CLI needs one too, and always did.** A client that dies mid-setup
   loses its army — every type defined and every unit placed. The work is
   only in RAM. Nobody has minded because the REPL is usually short-lived,
   but the data loss is real and it is the same missing concept.

So this change is not API plumbing. It is a gap in the model that the API
happens to expose. Building it now, behind the CLI, means it can be proved
against `tests/test_server_client_integration.py` before any web framework is
chosen — and the API becomes a binding over something already known to work,
rather than two new things at once.

There is also a divergence to settle. `game-persistence` already says a commit
writes *both* the order file *and* a marker `players/commit_<number>` that
"records that they have committed". The code writes both, but the barrier reads
the order files and ignores the marker, while `has_committed` uses the marker to
mean something else entirely — "has ever committed", the flag that ends setup.
This change makes the code mean what the spec already says.

## What Changes

**A player's uncommitted work becomes durable, private, and separate from their
commit.**

- **Drafts.** What a player has done since their last commit — types defined,
  units deployed, moves ordered — is written down as they do it, and read back
  when they reopen the game. Reconnecting to a game shows you your own
  half-finished turn instead of an empty one.

- **A draft is private to its owner.** Nobody else may read it — not the
  administrator, not the observer. This matters more than it sounds: in a
  simultaneous-commit game, watching an opponent deliberate is information
  nobody can get today, and making orders durable is exactly the change that
  could leak it by accident. `show pending` continues to mean *committed*
  orders, which is what it means now.

- **A draft covers type definitions too, not just orders.** A drafted
  deployment names a type; if the type is not in the draft, replaying the draft
  after a restart fails on a type the game has never heard of. This also keeps
  unit designs out of the administrator's and observer's reach until their
  owner commits — today `write_player` publishes a player's types at commit,
  and reading them earlier would be a second leak of the same kind.

- **Committing becomes a recorded fact rather than an inference.** "Player *n*
  has committed for turn *t*" is stored, and the commit barrier reads that
  record instead of listing files. `mark_committed` / `commit_<n>` — currently
  a separate "has ever committed" flag propping up the `new_game` gate — is
  subsumed by it: having ever committed becomes "there is a commit record".

- **Committing stays irreversible.** `turn-commit` requires it, and the
  requirement survives — but it stops being free. Today the storage enforces
  finality, because committing *is* writing the file and there is nothing to
  withdraw. Once commit is its own record, un-committing is one line, and
  declining to write that line is now a decision. Withdrawing after others have
  committed leaks timing even when it leaks no orders.

Not in this change: HTTP, any web framework, accounts or bearer tokens, SQLite,
and any change to how a turn resolves. The engine is untouched. This is the
prerequisite that lets the API be written next without a stateful server.

### Deferred to design

How a draft is represented — as the resulting unit records, the shape
`serialise_orders` already writes, or as the list of command objects
`service/commands.py` already defines. The second re-validates through the
service layer on every load and maps directly onto both a REST body and a
parsed CLI line; the first reuses the existing code path. This is a design
question, not a scope question, and the constraint above — that a draft must
carry type definitions — bears on it.

## Capabilities

### New Capabilities
None. Drafting is the uncommitted half of committing, and belongs with it in
`turn-commit` rather than in a capability of its own.

### Modified Capabilities
- `turn-commit`: a player may draft orders privately before committing;
  committing is a recorded fact rather than the existence of an order file;
  the barrier and "orders are consumed once" are restated in those terms;
  finality is kept deliberately rather than by accident.
- `game-persistence`: drafts are stored per player and are readable only by
  their owner; the commit record replaces the `commit_<number>` marker;
  "Pending Order Detection" comes to mean *committed* orders rather than any
  order file.
- `player-client`: a client reopening a game is shown its own draft, and orders
  given before a disconnection are not lost.

## Impact

- **Storage**: `storage/repository.py` gains draft and commit operations and
  loses `mark_committed` / `has_committed` in their current form;
  `storage/yaml_repository.py` implements them. The port is where the API will
  later need a lock — this change does not add one, and the write race
  catalogued as divergence 10 in `SPEC_COVERAGE.md` is unchanged.
- **Service**: `service/game.py` — `load()` gains a fourth input and must
  replay the caller's own draft onto their published view; `unprocessed_moves`
  must come to mean *committed* orders, or a player editing a draft will be
  told they are waiting for the turn. `service/turn.py` — `publish` promotes a
  draft to a commit; `wait_for_all_commits` and `_published_orders` read
  committed orders. All four existing consumers of "the order file exists"
  already mean *committed*, so this is a rename in place plus one new concept,
  not a split of an existing one.
- **CLI**: `cli/bgcclient.py` writes its draft as it goes rather than holding it
  in memory. `cli/show.py` and `cli/views.py` are unaffected — `pending`
  keeps its current meaning.
- **Tests**: `tests/test_repository.py` for the new operations;
  `tests/test_server_client_integration.py` gains a client that is killed and
  restarted mid-turn, which is the behaviour this change exists to make
  possible. No engine test should need to change.
- **Docs**: `README.md`'s web-service TODO, and `ARCHITECTURE_OPTIONS.md`,
  which predates the layer split and describes a codebase that no longer
  exists.
