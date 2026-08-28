## Why

A game ends when one player is the last with a unit standing, so ending one
means hunting down every unit an opponent has. On a 10x10 board with a hundred
points each that is a long, blind search: `visibility` hides an enemy until
contact, so most turns are spent looking rather than fighting, and a game
whose players stop before the search finishes has no outcome at all.

Give each army something it cannot hide and cannot afford to lose. One unit
carries the flag; every player can see which square each flag is on, whoever
owns it; and a player whose flag carrier is destroyed is out. There is
somewhere to go from the first turn, a reason to defend a square, and a way to
end a game in an afternoon.

## What Changes

- **One unit per player carries the flag.** A player designates it during
  setup with `set flag <unit>`, may change their mind until they commit, and
  cannot change it afterwards. Designating costs nothing: the flag is a
  standing, not a statistic.

- **A setup with no flag is refused.** **BREAKING** for setup: a player's
  commit is refused unless exactly one of their units carries the flag. A
  player who cannot be eliminated by flag loss would be playing a different
  game from everybody else at the table.

- **Every flag's square is visible to every player, always.** Position and
  owner only. The type, the symbol and the statistics of the unit carrying it
  stay hidden until contact discloses them the way it discloses any unit's -
  you know where to go, not what you will meet. This is the one exception to
  contact-based visibility, and it is deliberate.

- **Losing the flag carrier puts a player out.** When a flag carrier is
  destroyed its owner is eliminated at that resolution. Their remaining units
  are left standing where they are and go inert: they take no orders, they
  strike nothing, and they can still be attacked and destroyed. An army
  without its flag is terrain.

- **The outcome rule is unchanged and now gets used.** The last player not
  eliminated wins, as it always did; flag loss is a second way to be
  eliminated beside having nothing left standing.

- **Every client can see and do all of it.** `set flag` at a prompt and a
  designation in the armoury; `show flags` and a marker drawn on the board, in
  both the ASCII grid and the browser.

- A game set up before this change keeps playing under the old rule: no unit
  carries a flag, so nobody can lose one.

## Capabilities

### New Capabilities

- `flag-carrier`: which unit carries a player's flag, when it is designated
  and fixed, what a flag discloses to everyone, and what its destruction does
  to its owner and to their remaining units.

### Modified Capabilities

- `visibility`: the flag is the one thing shown without contact, and what is
  shown of it is the square and the owner and nothing else.
- `turn-commit`: a player's setup commit is refused without a flag; an
  eliminated player's units are resolved as inert.
- `game-outcome`: flag loss is a second way to be eliminated, and an
  eliminated player's standing units do not keep them in the game.
- `player-client`: `set flag <unit>` during setup, and `show flags`.
- `game-server`: the administrator and the observer read flags too.
- `game-observer`: `show flags` for a session that sees everything.
- `game-persistence`: which unit carries the flag is stored, and the flag
  positions are published for every player to read.
- `cli-output`: the `flags` table, the `FLAG` column on `units`, and the flag
  marked on the board grid.
- `web-interface`: designating in the armoury, the flag drawn on the board and
  named in the roster, and what an eliminated player is shown.

## Impact

- **domain**: `UnitType` gains a flag standing; `Board.commit` reports a flag
  destroyed; combat leaves an eliminated player's units unable to strike.
- **service**: `games.py` gains the `set_flag` command and the setup refusal;
  `turn.py` derives elimination from flag loss as well as from nothing
  standing, and publishes flag positions; `commands.py` gains the record.
- **storage**: a `flag` field on a unit in both backends, the published flag
  positions, and a schema table for them. Additive: a game stored before this
  reads back with no flags.
- **http**: a `flags` view, the flag in the units view, and the command on the
  existing `/commands` endpoint.
- **cli**: `set flag` in the grammar, parser, roles and completion; `show
  flags`; the flag on the board grid and in the units table.
- **web**: designation in the armoury, flag markers on the board, the flag in
  the Forces roster, and the account of a flag falling in the turn feed.
- **tests**: the rules in the domain and service suites, the contract in the
  HTTP suite, the surface in the three CLI suites, and the parity tests that
  hold the browser and the prompt to each other.
