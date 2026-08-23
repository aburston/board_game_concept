## Why

`GAME_RULES.md` states the rules the game actually plays by, read back from
both `openspec/specs/` and the source. Part 2 of that document catalogues 17
places where the rules are broken, unstated, or contradicted between documents.
Three of them stop the game being playable at all:

- A destroyed unit is republished as a deployment order every turn and comes
  back at full health once the cell it died on is empty (`Q1`). Nothing works
  past the first casualty.
- Turn resolution follows the order units were registered, not the order they
  were committed, so identical orders give different outcomes and enemy units
  walk through each other unseen (`Q3`).
- There is no win condition, and a wiped-out player still gates the commit
  barrier, so a finished game can neither be won nor left (`Q7`).

The rest are smaller but of the same kind: rules the code has and the specs do
not, or specs the code does not honour. All 227 tests pass today, because none
of them plays a game on past a unit's death.

## What Changes

**Death is permanent** (`Q1`, `Q2`). A client stops republishing destroyed units
as orders, a restored unit is never put back in the `INITIAL` (deploy) state,
and `Board.add` validates completely before it registers anything, so a refused
deployment leaves nothing behind. This also stops the rejection channel filling
with a message about a unit that died ten turns ago.

**Movement resolves simultaneously** (`Q3`). Every destination is computed
against the board as it stood at the start of the turn, then all moves are
applied together, so registration order stops deciding outcomes. **BREAKING**:
two units ordered into each other's cells now collide and fight instead of
passing through, and both record having seen the other. **BREAKING**: the rule
that a unit needs energy at least equal to its attack value before it may enter
an occupied cell is removed — under simultaneous resolution there is no
order-independent moment at which "occupied" can be evaluated, and a unit that
cannot afford to attack is already covered: it is inert in the fight it walked
into.

**A game can be won** (`Q7`, `Q16`). New `game-outcome` capability: a player is
eliminated when every unit they own is destroyed; the last player left with an
undestroyed unit wins; simultaneous elimination is a draw. An inert unit — one
whose energy is spent — still counts as alive, which is what
`combat-resolution` has always said and what `design.md` contradicted.
Eliminated players drop out of the commit barrier so a finished game does not
freeze. Turns are numbered and the number is persisted.

**Hidden information is enforced, not just displayed** (`Q5`, `Q6`).
**BREAKING**: a client no longer reads `data/units.yaml`. It loads only its own
published view, and enemy unit types reach it through contact rather than by
reading every player's file. Fixing the client's board also fixes the unit
lookup that today refuses a player's own order when an opponent registered the
same unit name first.

**Every order that does nothing says so** (`Q9`, `Q11`, `Q12`). Rejections
currently cover only orders refused while being applied. They are extended to
the movement phase: a move nobody can pay for, a move off the board edge, an
engagement refused for want of energy, and a contest that ended undecided are
all reported to the player who ordered them. The deployment-collision tiebreak
is stated rather than left to player-number ordering.

**Rules that were true but unwritten are written down** (`Q4`, `Q13`, `Q14`).
Movement costs a flat 1 energy — the `energy // 100 + 1` formula never varies
under the 1–100 energy cap and only misleads. `(0, 0)` is the north-west cell
and north decreases `y`. Destroyed units stay in the record as a casualty list,
marked, rather than reading as though they are still on the board.

**Documentation is made to agree with itself** (`Q17`). `README.md` stops
advertising unit programming, a REST API and a resolved winner as though they
exist. `openspec/config.yaml` still describes `BoardGameConcept.py` and
`GameData.py`, which the `split-into-layers` change removed. `GAME_RULES.md` is
brought up to the rules this change lands.

### Not in scope

`Q8` (energy never regenerates, so an exhausted unit is a permanent obstacle)
and `Q10` (identical units always destroy each other) are design choices, not
defects. Both are recorded as deliberate in `design.md` and left alone. Changing
either alters how every game plays and belongs in its own proposal.

`Q15` (the specs say "cell", the source says "square") is a mechanical rename
across every capability with no behavioural content. Carrying it here would mean
renaming requirement headers this change is also rewriting, making both harder
to review — which is the reasoning `SPEC_COVERAGE.md` already gave for leaving
it as its own job. It stays its own change, and these deltas keep saying "cell".

## Capabilities

### New Capabilities
- `game-outcome`: player elimination, victory, draw, how a finished game stops,
  and the turn number the rest of the game is recorded against.

### Modified Capabilities
- `board-model`: the coordinate system and board orientation stated; placement
  validates before it registers a unit; unit lookup by name scoped to a player.
- `unit-movement`: destinations computed against the starting board; two units
  trading cells collide; movement costs a flat 1 energy.
- `combat-resolution`: a destroyed unit can never return to play.
- `turn-commit`: the movement phase is two passes; eliminated players leave the
  commit barrier; turns are numbered; the deployment-collision tiebreak stated.
- `visibility`: a session is never given state it may not see; destroyed units
  are a marked casualty record.
- `game-persistence`: destroyed units are not republished as orders; a client
  loads its view rather than the shared board; rejections cover movement-phase
  failures; the turn number and the game's outcome are persisted.
- `player-client`: `show types` lists only own and contacted types; move orders
  resolve against the player's own units; the outcome is reported.
- `game-server`: the unattended turn cycle stops when the game is decided.
- `game-observer`: the outcome is reported.

## Impact

- **Engine**: `domain/unit.py` (`preCommit`, `commit`, `resolveContest`),
  `domain/board.py` (`add`, `commit`), `domain/events.py`.
- **Service**: `service/turn.py` (`_apply_orders`, `resolve`, the barrier),
  `service/game.py` (`load`, `_restore`), `service/games.py` (`order_move`).
- **Storage**: `storage/serialise.py`, `storage/yaml_repository.py` — a new
  outcome file, a turn number, and a client that no longer reads
  `data/units.yaml`. **BREAKING** on-disk format: existing saved games will not
  load.
- **CLI**: `cli/client.py`, `cli/server.py`, `cli/observer.py`,
  `cli/render.py`.
- **Tests**: the CLI surface suites gain the new scenarios; a new suite plays a
  game through to a decided outcome, which is the gap that let `Q1` survive.
- **Docs**: `README.md`, `MODULE_DESCRIPTION.md`, `SPEC_COVERAGE.md`,
  `GAME_RULES.md`, `openspec/config.yaml`.
