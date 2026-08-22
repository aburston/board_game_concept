## Context

See `proposal.md` — Why. Two rules from the owner shape everything below:

1. **Energy exhaustion makes a unit inert, never dead. Only health destroys a unit.** An
   inert unit stays on the board and holds its square until an opponent kills it.
2. **When units contest a square and exhaust themselves, they all retreat and nobody wins.**
   The move is undone rather than settled.
3. **Moving onto an occupied square is combat, but deploying a brand new unit onto one is
   illegal.** The two are different acts and are ruled on differently.

There is also **friendly fire**: units do not tell their own side from anyone else's. Every
unit in a contested square attacks every other unit in it. The engine already behaves this
way; the specs now say so.

Three properties of the current engine were verified against the code rather than assumed:

- Movement costs `energy // 100 + 1`, which is `1` even at zero energy. A unit needs at
  least 1 energy to move, but a unit too spent to *attack* can usually still *move*. So an
  inert unit is not permanently stuck: it can walk away next turn.
- A square holds an `Empty`, a single unit, or a list. The list was only ever meant to exist
  transiently during turn resolution.
- Combat is the only thing that reduces health, and it only happens between units sharing a
  square.

## Goals / Non-Goals

**Goals:**

- Turn resolution terminates in a bounded number of rounds, always.
- No unit is destroyed by running out of energy.
- An undecided contest leaves the board as it was, with the movers back where they started.

**Non-Goals:**

- Energy regeneration. Energy remains non-renewable.
- A win condition. Still unimplemented; see `SPEC_COVERAGE.md`.
- A rejection channel richer than "what was refused last turn". Anything else the server might
  want to tell a player — combat reports, a win notice — would want a general notices file;
  this carries refused orders only.
- Deduplicating the stale `src/BoardGameConcept.py` and `src/GameData.py` copies.

## Decisions

### Terminate combat on a round that deals no damage

Track whether any attack landed during a round. If none did, combat for that square ends. This
is the narrowest possible termination condition: it fires exactly when the loop would
otherwise spin, and never when combat is still progressing. Because the loop only exits with
more than one survivor when *no* contestant could pay for an attack, the outcome is
unambiguous — nobody could win.

*Alternative considered:* a fixed round cap. Rejected — it would truncate long but legitimate
attrition between high-health units, and the cap would be arbitrary.

### Count survivors afresh each round

Replace the running `unit_count` decrement with a recount of undestroyed contestants at the
top of each round. The old code subtracts one for every destroyed unit it finds, every round,
so a unit destroyed in round 1 is counted again in round 2. With three contestants and two
rounds the count reaches zero while a unit is still standing, and the square is then wrongly
emptied — a live unit vanishes from the board.

### Attacks in a round are drawn from the units standing at the start of that round

A unit destroyed mid-round still lands its own attack that round, preserving the
simultaneous-exchange semantics the existing tests pin down. A unit destroyed in an *earlier*
round no longer attacks at all, which the old code got wrong: it iterated every unit in the
square each round, so corpses kept fighting.

### An undecided contest retreats the movers

Each unit records the square it vacated during `preCommit`. When combat ends with more than one
survivor, every survivor that has such a record is put back there and the contested square is
handed to whoever is left — the defender who never moved, or `Empty` if nobody stayed.

The retreat is the move being undone, so it costs no further energy. The energy already spent
moving in and attacking is *not* refunded: the unit made the attempt.

Two units cannot collide while retreating, because distinct units left distinct squares. If a
unit's origin was taken by a third unit during the same turn, there is nowhere to go back to
and it stays in the contested square.

*Alternatives considered:*

- *Destroy the exhausted units.* Kills by energy, which rule 1 forbids.
- *Leave the survivors stacked in the contested square.* Rejected under rule 2, and it created
  a permanent obstacle no one could clear: stacked inert units can neither die nor separate.

### Deployment onto a taken square is refused where the unit is created

`Board.add` is the single choke point every deployment goes through — the client's
`add unit`, and the server applying a player's order — so the rule lives there. It refuses a
square that is already held, or that another unit is already waiting to be placed on, which
is the case issue #1 actually reports: two units created in the same turn, neither on the
board yet, both claiming one square. `Board.squareIsFree` checks both.

The refusal has to be recoverable, not fatal. The client already reports an error from
`add unit` and carries on. The server catches the refusal, logs it, and resolves the turn
without that order, so one player's bad order cannot stall the game for everyone.

Restoring a saved game goes through the same `Board.add` but is not a deployment: it puts
back whatever the save held, including a shared square. `restoring=True` marks that path.

*Alternative considered:* checking in the client and the server separately, leaving the engine
permissive. Rejected — two copies of the rule, and the engine would still accept a state it
considers illegal.

### A refused order is published back to the player who gave it

A refusal the player never sees is barely better than a silent drop: their unit simply does not
appear and nothing says why. The server writes `players/<number>_rejected.yaml` naming the
unit, its square and the reason, and the client reports it before taking the next command.

The file travels the same way every other server-to-player message already does, and is written
for **every** player on **every** resolved turn — empty when nothing was refused. That is what
makes it describe the turn just resolved rather than accumulating, and it means neither side
has to delete it. The client's player-file scan skips it, the way it already skips
`_units_seen.yaml`.

A refused deployment is dropped, not held: no unit of that name exists on the server, and the
player is free to place it elsewhere on a later turn. Holding it pending would need a unit that
exists but is on no square, which the save format has no room for.

*Alternative considered:* a general notices file for any server-to-player message. Rejected for
now — nothing else needs one yet, and the shape a win notice or a combat report wants is not
yet known.

### Nothing a single player does may stop the turn

Refusing an order is only useful if the refusal is survivable, so every path that reads a
player's published orders now refuses rather than asserts: an unknown order state, and a move
naming a unit the player does not own. Both used to abort turn resolution for everyone.

The same rule turned up a bug that predates this change. `listUnits` writes `units: None` for a
player holding no units, and YAML reads that back as the *string* `"None"`, not as null. The
load path knew this and compared against the string; the turn resolver tested `is None`, so it
fell through and iterated the characters of `"None"`. Any player with no units killed the
server on commit — and a player whose only deployment was refused is exactly such a player.

### Shared squares remain legal, as a residual case

Retreat empties the contested square in the ordinary case, but not always. A unit whose origin
was taken by a third unit during the same turn has nowhere to go back to. Those survivors
share the square, so every path that reads a square must still cope with one:

- `Board.print` renders a shared square via a representative unit — the player's own unit under
  a player view, otherwise any occupant — instead of raising or printing an object repr.
- The load path is exempt from the placement rule, so a save holding a shared square reloads
  as it was.
- The server applies a move order to the unit it names, looked up by name and owning player,
  rather than to `getUnitByCoords(x, y)`, which returns a list for a shared square and has no
  `move` method.
- Leaving a square removes only the departing unit. The old code assigned `Empty()` over the
  whole square, which took any unit sharing it off the board.

## Risks / Trade-offs

- **Retreating hands the square back to a defender that could not fight either.** → Intended:
  nobody wins, and the status quo is the defender's. An attacker that wants the square must
  come back with enough energy.
- **A refused deployment is reported to the server's error stream, not to the player who
  ordered it.** → The player's unit simply does not appear after the turn. Better than the
  crash it replaces, but the reporting gap keeps issue #1 open; see `SPEC_COVERAGE.md`.
- **Two players can still race for the same empty square on the first turn**, since neither
  can see the other's units when ordering. → One deployment wins and the other is refused.
  Which one wins depends on the order the server reads the player files in.
- **A shared square is still possible**, when a survivor of an undecided contest finds the
  square it came from taken. → Rare, and no longer a deadlock: a unit with any energy at all
  can move away next turn. Rendering, the load path and move orders all handle it.
- **Existing saved games are unaffected**, since no file format changes. A save written before
  this change loads identically after it.
