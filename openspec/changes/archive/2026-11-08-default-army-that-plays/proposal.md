# Proposal

## Why

A player who commits the default army as handed fields two Heavies and
twelve bystanders. The programmed series (`matches/RESULTS-PROGRAMMED.md`,
games 221-224 and 239) showed it in every game with a stock seat: the back
rank of Runners, Lines and Scouts is boxed in by the Pawns and Walls in front
of it and the Keeps beside it, the Pawns are sentries that never move and the
Walls cannot, and the hunter will not step onto one of its own - so the two
Heavies walk out alone and die, and the other twelve stand where they were
seeded for the rest of the game, paying energy every turn to think about a
route they cannot take. Flag Hunt against a Garrison ran 500 turns without
touching the flag; the mirror of two default armies killed four units on
turn 16 and then nothing for 484 turns. The default is the first game anybody
plays, and the first thing it should be is a game.

## What Changes

- **The array is rearranged so that its front rank goes and its back rank
  can follow.** The Lines move to the front rank beside the Heavies and the
  Walls move to the back rank beside the Keeps: a front rank of eight units
  that all advance, and a back rank in which the Walls guard the flag's
  flanks and the Runners and Scouts stand behind Pawns that will get out of
  their way. The composition of the army is unchanged.
- **The Pawn becomes a vanguard rather than a sentry.** Its default program
  steps towards the enemy's edge every turn it can afford a step and a
  strike, never onto one of its own, and fights whatever it walks into. To
  afford that program it gets a third point of compute, so a Pawn costs 10
  and the array 308 of the 320. **BREAKING** for anybody reading the
  catalogue's numbers: the Pawn's compute, cost, and the array's cost change.
- **A blocked hunter sleeps instead of paying to hold.** The catalogue's
  hunter, when both ways round are its own units, sleeps a turn rather than
  holding, so a unit waiting for the way to clear costs its owner nothing.
- **A game in which nothing happens stops.** A game in which no unit has
  changed square, landed a blow, been destroyed or lost a flag for fifty
  consecutive turns is undecided, saying so and naming the last turn anything
  happened. The repeated-state and 500-turn stops stay; this one catches the
  static boards that sleep countdowns and thinking meters keep from ever
  repeating, which were four of the twenty games in the series. Separable
  from the rest if wanted, but without it the mirror of two default armies
  still ends in hundreds of empty turns.
- The default's play is held by a test that plays it: in the mirror of two
  unchanged defaults every unit with legs leaves its square. A second test,
  that the default takes the flag of an army whose programs all halt, was
  proposed and dropped: a halted army still strikes back, rests for free
  and keeps two Heavies in front of its Keeps, and the default loses twelve
  units for three with the carrier struck to half its health. Taking a
  garrison needs hunters that arrive together, which is another change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `default-army`: the catalogue's Pawn (compute, cost, program), the hunter's
  behaviour when blocked, the array's layout and cost, and what a seat that
  changes nothing is required to do when it plays.
- `game-outcome`: a game in which nothing happens for fifty turns stops
  undecided.
- `point-budget`: the default budget's stated reason names the array's new
  cost.

## Impact

- `domain/army.py`: `CATALOGUE` (the Pawn), `ARRAY`, the `HUNTER` and a new
  vanguard program.
- `service/turn.py`: the quiet stop beside the repeated-state stop; the
  `undecided` outcome gains a reason.
- `cli/session.py` (`describe_outcome`), `http/static/play.js`
  (`outcomeText`): the new reason's words.
- `GAME_RULES.md` R2.13, R3.10, R7.5; `README.md`; `SPEC_COVERAGE.md`'s open
  questions; `MODULE_DESCRIPTION.md`.
- `tests/test_default_army.py`, `test_resolve_game.py`, `test_game_outcome.py`,
  `test_match_harness.py`'s canned views, `test_seeding_the_default_army.py`,
  and the doctrine comments under `matches/bots/` that describe the stock
  array.
- The five stock games of the series replayed under the new default, written
  up as an addendum to `matches/RESULTS-PROGRAMMED.md`.
