# Design

## Context

See proposal.md - Why. The facts the approach rests on, all from the
programmed series and the engine as it stands:

- The hunter (`domain/army.py`, `HUNTER`) will not step onto a square one of
  its own stands on, on either axis, and holds when both are blocked. Its
  longest path is 33 ticks. Nothing that runs it has less than compute 4.
- The Pawn has compute 2, a cap of 20 ticks a turn, and the sentry program.
  The `advance2.asm` written for the match harness - step towards the
  enemy's edge when a step and a strike are affordable, never onto a friend
  - is 19 ticks on its longest path, which fits a cap of 20 with one tick
  to spare and costs a Pawn nearly one energy for every turn it thinks.
- `SELF` writes r0 to r5, every other sensor r0 to r3; r6 and r7 are the
  only registers a program can keep across a sensor.
- The repeated-state stop (`service/turn.py`, `state_record`) compares every
  unit's square, health, energy, memory, meter, sleep and inbox, and the
  maps. A sleeping Keep's countdown and a thinking unit's meter make a static
  board a new state every turn.
- The array is seeded by `domain/army.py`'s `ARRAY` and read by
  `tests/test_default_army.py`, `tests/test_match_harness.py`'s canned
  views, and `GAME_RULES.md` R2.13, which draws it.

## Goals / Non-Goals

**Goals:**

- A player who commits what they are handed sends the whole army, not two
  units of it, and a game between two such players is a battle that ends.
- Nothing a player has to learn changes: the same eight types, the same
  sixteen units, the same budget. The Pawn costs one point more.
- The quiet stop is a stop, not a rule change to combat or movement: it
  judges what happened, from the events the turn already emits.

**Non-Goals:**

- Making the default *good*. It should fight and finish; whether it beats
  the doctrines is what the series is for.
- Changing the repeated-state comparison. Excluding sleep countdowns from
  it would stop a game a sleeper was about to change; the quiet stop makes
  the question moot without touching R7.5.
- Teaching the default programs the radio, or a Pawn that falls back. One
  change at a time.

## Decisions

**Swap the Lines and the Walls between the ranks; move nothing else.** The
boxed-in rank is the problem, and the two units that box it in forever are
the Walls. Putting them beside the Keeps makes them do the one thing a wall
is for - guard a flank that is not going anywhere - and puts the Lines,
which hunt, where the hunters are. Every other unit keeps its column, so the
array is still symmetric, still fills both rows, still shows seven of the
eight types, and `GAME_RULES.md`'s drawing changes two letters a row.
Alternatives: a three-rank array (breaks the "two rows at the edge" rule
and the placement tests); Walls at the corners (leaves a Runner behind
each, boxed in again); no Walls (changes the composition the write-ups
describe).

**The Pawn becomes the vanguard, at compute 3.** The sentry never moves, and
a unit that never moves in the front rank boxes in whatever is behind it.
The vanguard is the match harness's `advance2.asm`, already written and
played: step towards the enemy's edge when a step and a strike are
affordable, not onto a friend, fight what you meet, sleep otherwise. At
compute 2 it fits with one tick to spare and costs a Pawn an energy nearly
every time it thinks, which with two energy is a Pawn that walks every third
or fourth turn; at compute 3 the cap is 30, the meter 30 ticks an energy,
and a Pawn walks every other turn, which is what Advance did in the series.
One point a Pawn, four points the array. Alternatives: keep the sentry and
move the Pawns to the back rank (then four of sixteen units never move, and
the Runners and Scouts are behind them); give the Pawn energy 3 instead
(changes a statistic rather than a controller, and R4.3's reasoning for
the front rank); write a cheaper vanguard (17 ticks is the floor with the
friend check, and the friend check is not negotiable).

**The hunter sleeps where it held.** `stay: HOLD` becomes `stay: SLEEP 1`.
A unit blocked both ways has run the hunter's whole longest path to find
out, and holding pays for that thinking on the meter; sleeping a turn rests
instead, and the unit looks again next turn. A sleeping unit struck is
woken, so nothing is lost. The program text changes one word; the per-type
caps are unaffected.

**The quiet stop counts events, not state.** `resolve_game` keeps the turn
on which anything last happened, read from the turn's events: a `moved`,
`attacked`, `destroyed` or `flag_fallen` kind resets it. Fifty quiet turns
stop the game as `undecided` with `reason: 'quiet'` and `since` the last
eventful turn, through `_stop_undecided` as the other reasons do. Fifty is
a round number comfortably above the longest rest-and-return cycle the
series saw (six turns, in the Advance mirror) and far below the 470-odd
turns the capped games wasted. Alternatives: excluding sleep and meter from
`state_record` (wrong when a sleeper will wake and act); a shorter cap
(hides a slow game); counting only moves (a garrison struck every ten turns
by a unit that cannot move is still a game).

**The default is held by playing it.** Two in-process games in
`tests/test_default_army.py`: the mirror, in which every unit with a
controller but the Keeps must have left its square inside twenty turns of
play, and the default against an army of the same units whose programs are
`HALT`, which must be decided for the default within a hundred turns. Both
are the series' findings turned into requirements, and both run in under a
second on SQLite.

## Risks / Trade-offs

- [The mirror may still not finish inside the quiet cap if the two fronts
  cycle - step in, fall back, rest - the way the Advance mirror did] → that
  cycle repeats its whole state and the repeated-state stop catches it, as
  it did on turn 21 of game 240; the quiet stop is for the boards that do
  not repeat.
- [A Pawn vanguard walking into a Heavy dies for nothing] → it does, and
  that is a game: the series showed the stock Pawns as a screen the
  Heavies behind them needed. What changes is that the Pawn chooses it.
- [Runners and Scouts following the front rank out leave the Keeps with two
  Walls and nothing else] → by design; the flag is meant to be takeable.
  Whether it is too takeable is what the replayed stock games will say.
- [The quiet stop ends a game a long sleeper would have changed] → a Keep's
  hundred-turn sleep is the longest in the catalogue, and a Keep alone with
  nothing to wake it will never move; a player's own program that sleeps
  fifty-one turns and then acts is a program that has chosen not to play.
  The write-up of the first series under this rule should say whether that
  ever bit.
- [Games 221-240 become evidence about a default that no longer exists] →
  `RESULTS-PROGRAMMED.md` gains an addendum replaying the five stock games
  under the new default, and a note at its head saying which games it
  affects; nothing else in the write-up depends on the array.

## Migration Plan

A game set up before this change holds its own types and array in its own
files and is unaffected; the catalogue and the array are given at
registration. No stored data changes. The `undecided` outcome's `reason`
gains the value `quiet`, which every reader already treats as "it could not
go on" when it does not know the word.

## Open Questions

None that change the specs or the tasks. Whether fifty is the right cap, and
whether a Pawn at compute 3 is still the cheap unit it was meant to be, are
what the replayed games are for.
