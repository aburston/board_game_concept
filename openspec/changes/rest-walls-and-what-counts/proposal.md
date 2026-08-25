## Why

`GAME_RULES.md` has carried Q1 since it was written: energy is spent by moving
and by attacking and never comes back, so a unit that spends down below its
attack value can never fight again, and one at zero can do nothing at all while
still holding its square. Q1 asked whether to regenerate energy, and left it
open because changing it changes how every game plays.

Sixty-three games were played to find out (`matches/RESULTS.md`,
`matches/RESULTS-FRONTIER.md`). They answered it. Every one of the first
forty-three ended the same way: both armies standing still on a board they
could no longer cross, holding energy they were saving for a fight they could
not reach. Two of thirty were decided in the second series, and the two that
were not decided by destruction were decided by the turn cap. The endgame was
always an army one energy short of finishing a hunt it had already won.

Three rules follow from fixing that, and they only make sense together:

1. **Rest.** A unit that takes no action recovers a point of energy. That alone
   turned nine of twenty replayed games into decisions
   (`matches/RESULTS-REST-AND-WALLS.md`), because a hunt that stalls can now
   wait and finish.

2. **Walls.** With rest in the game, a unit deliberately bought with *no*
   energy becomes a coherent thing to own: health standing on a square that can
   never act and never recover. It costs its health and nothing else, and it is
   the one unit rest can never help.

3. **What counts at the end.** Elimination was changed earlier on this branch to
   ignore units at zero energy, which was right while zero was permanent. With
   rest it is not: zero is a bad afternoon, and judging a player on it decides
   games on the timing of a snapshot — three of the nine decisions above turned
   on exactly that. Elimination has to ask whether a unit **could ever act
   again**, which is every unit except a wall.

Taken separately the third rule reads as a reversal of the second series and
the second rule reads as an oddity. Taken together they are one rule: a player
is out when they hold nothing that can play, and what can play is decided by
what a unit is, not by what it happens to be holding this turn.

## What Changes

**A unit that does nothing gets a point of energy back.** No order given, and
nothing paid for while the turn resolved. Being attacked and unable to strike
back is doing nothing, and rests; being ordered to move is acting whether or
not the move happened, so walking a unit into the board edge — which costs
nothing — is not a way to refuel. Nothing recovers past the energy its type was
designed with. Rest is a fourth phase of the turn, after combat and before the
game is judged.

**A type may be defined with attack 0 and energy 0, and only with both.** A
wall. It can never be ordered to move, it lands no attacks, it never rests, it
blocks a square like anything else and it can be destroyed like anything else.
Combat skips it explicitly: paying nothing and dealing nothing would otherwise
count as an attack landed, and a round that lands an attack repeats — a fight
with a wall in it would never end.

**Elimination is judged on whether a unit could ever act again.** A unit whose
type was designed with energy keeps its owner in the game whatever it holds
now, because resting will give it back. A wall does not.

**BREAKING**: a game saved before this change is unaffected — no stored field
changes — but the rules it plays by do. An army worn down to zero is no longer
out, and an army of walls is.

## Capabilities

### Modified Capabilities
- `turn-commit`: a new requirement states that a unit which took no action
  during a turn recovers `REST_GAIN` energy at the end of it, never past the
  energy its type was designed with, and that this happens after combat and
  before elimination is judged.
- `unit-types`: a new requirement admits walls — attack 0 with energy 0, and
  each only with the other — and states what a wall may and may not do. The
  validation requirement's attack and energy ranges widen to include 0.
- `game-outcome`: the elimination requirement is restated. A player is out once
  no unit they own could ever act again, which is every unit destroyed or a
  wall; a unit at zero energy keeps its owner in.

## Impact

- **Domain**: `domain/unit.py` — `REST_GAIN`, the widened ranges and the
  paired-zero assertion, and the `attack <= 0` skip in `exchangeAttacks`.
  `domain/board.py` — `commit` takes a snapshot of what every unordered unit
  held and calls a new `_rest` phase after `_fight`. `domain/events.py` — a
  `rested` event.
- **Service**: `service/turn.py` — `eliminated_players` tests `type_energy`
  rather than the energy a unit is holding.
- **Tests**: `tests/test_energy_regeneration.py` and `tests/test_walls.py` are
  new. `tests/test_game_outcome.py` covers the restated elimination rule,
  `tests/test_cli_client_surface.py` covers defining a wall and the refusal of
  a half one, and two fixtures that walked a lone unit down to nothing were
  given something in reserve.
- **Docs**: `GAME_RULES.md` gains R2.10 and R3.9, restates R5.10, R7.1 and
  R7.2, and closes Q1 as answered rather than open. `SPEC_COVERAGE.md` records
  that divergence 21's settled question was reopened and settled again.
- **Play**: `matches/RESULTS-REST-AND-WALLS.md` is the twenty games played
  against these rules, and `matches/bots/bulwark.py` is the doctrine that
  buys walls.
