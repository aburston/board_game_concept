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

## Known divergences

The specs describe intended behaviour. The following are places where the
implementation diverged from them. Each was reproduced against
`src/board_game_concept/` rather than inferred from reading. Two have since been
fixed; the spec deltas describing the behaviour they now have live in
`openspec/changes/fix-combat-stalemate-hang/` until that change is archived.

### 1. Deploying onto an occupied square crashes (issue #1) — crash fixed

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

Still open: the refusal reaches the server's error stream, not the player who
ordered it. From that player's side the unit simply never appears. Carrying the
rejection back to the client needs a channel that does not exist yet.

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

### 3. Duplicate unit name raises the wrong error (issue #3)

`board-model` requires that reusing a unit name within one player's forces fails
with a duplicate-name error. `Board.add` does detect the duplicate, but its
assertion message interpolates `player.name`, and `Player` defines only
`number`. Evaluating the message raises
`AttributeError: 'Player' object has no attribute 'name'`, so the real cause is
never reported to the player.

This is the most likely source of the confusing "already exists" report in
issue #3, though the issue describes it arising when units are *encountered*
rather than added; the enemy-type lookup on the seen-board load path in
`GameData.load` is a second candidate and has not been ruled out.

## Documented but not implemented

- **Win condition.** `README.md` and `MODULE_DESCRIPTION.md` both describe the
  game ending when one player is the last with a functional unit. No win, loss,
  or game-over logic exists in the source. The server's turn cycle runs
  indefinitely. No capability specifies it, because there is nothing to specify
  yet — it is a feature to propose, not behaviour to document.
- **Web service.** The Flask/REST API and SQLite backend in `README.md` are
  aspirational; no such code exists.

## Housekeeping

`src/BoardGameConcept.py` and `src/GameData.py` are byte-identical copies of the
modules inside `src/board_game_concept/`. Only the package copies are importable
via `pyproject.toml`, which packages `board_game_concept` from `src/`. The
top-level copies are stale duplicates and are not covered by these specs.
