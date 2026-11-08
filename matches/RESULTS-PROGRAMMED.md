# Twenty games nobody ordered

The seventh series, and the first played under the rules the project is
named for: a type carries a program, every unit runs its type's program
once a turn, and a player's whole game is the setup. Nobody gave an order
in any of these games. Each seat typed its types, its programs, its
squares and its flag, committed, and the game played itself to its end
the moment the second seat had.

## What was played

**The code.** Commit `d49a170` and the two that follow it on the
`programmable-units` change (8 November 2026), whose rules are
`GAME_RULES.md` at that commit. Nothing under `src/` was changed to play
these games; one thing under `src/` was changed *because* of a game played
while the harness was being built, and is said below.

**The board and the seats.** `bgcserver` registers player 1 and player 2 and
commits, and that is the whole of the administrator's setup:

| | |
|---|---|
| board | 8 x 8, the default (**R2.1**) |
| budget | 320 points a seat, the default (**R2.3.1**) |
| placement | rows 0-3 for player 1, rows 4-7 for player 2, as the game publishes them (**R2.6a**); no neutral row on an even board |
| what a seat opens with | the catalogue of eight types, each with the program the game gives it, and the sixteen-unit stock array, flag on `keep1`, 304 points spent (**R2.13**) |
| how a game ends | a flag falls and one player is left (**R7.1a**); or the whole state repeats, or turn 500 is reached, and the game is undecided (**R7.5**, **R7.6**) |

**The rules that differ from games 201-220.** The last series was played on
18 September, and its doctrines ordered their units by hand each turn.
Since then:

| Then | Now | Rule |
|---|---|---|
| a player ordered each unit every turn and committed every turn | a player writes a program per type and commits once; the last commit resolves the game to its end | **R3.1**, **R3.3**, **R10.1** |
| three statistics | four: compute, 0 to 10, is what a controller has, and is priced into the cost like the others | **R2.4**, **R2.9** |
| 250 points, and a stock army of 242 | 320 points, and the same army at 304 - every thinking type pays for its compute | **R2.3.1**, **R2.13** |
| thinking was free, because a person did it | every instruction costs ticks from a published tariff; ten ticks a point of compute cost one energy, and a turn's thinking is capped at the same | **R10.3**, **R10.4**, **R10.5** |
| a unit saw what it fought and nothing else | the same, plus a map the whole army shares of where it has stood and what it has fought there | **R6.9**, **R10.7** |
| the series stopped at a cap of 60 turns | the game stops itself: a repeated state, or turn 500 | **R7.5**, **R7.6** |
| a bot read its seat's view each turn | a doctrine is a file read once; nothing reads anything during play | `match-series` |

**The harness.** One `bgcserver` registers the seats and commits; one
`bgcclient` per seat types its doctrine's setup - `remove unit`, `add type`
with the fourth statistic, `set program` naming a file the client reads,
`add unit`, `set flag` - and commits. The second commit resolves the game.
The record is then read back, turn by turn, at a `bgcobserver` prompt with
`show turn <n> json`, which is what writes the log and the history: the
board after each turn, what every controller decided and what it spent,
every event, every refusal, and who was eliminated when. Nothing reads
anything while the game is being resolved, because nothing could act on it
if it did. The `match-series` capability states what the harness keeps to,
and `tests/test_match_harness.py` holds it there - and holds every doctrine
to the game before a game is played: every type through `UnitType`, every
program through `Program`, every army inside its half and its budget, and
every doctrine played against the Garrison in process with its traces read
for a controller stopped at its cap.

**The doctrines.** Ten, in two families, each a file under `matches/bots/`
and each a translation of the doctrine of the same name in the last series
into programs. Four keep the stock army as handed and differ only in what
they tell it to think:

| | |
|---|---|
| **Garrison** | every type's program is `HALT`: no unit ever thinks or moves. The control |
| **Advance** | the Pawns and Heavies step towards the enemy's edge every turn they can afford the step and a strike; the back rank's program is `HALT` |
| **Flag Hunt** | the stock army with the programs the game gives it: Runners, Lines and Heavies hunt the enemy flag round their own units, Scouts walk at the nearest unknown square, Pawns strike back at what struck them, Keeps sleep until struck |
| **Screen** | the Scouts walk to the frontier row in front of the Keeps and stand there; the rest play as Advance |

Six take the whole army back and deploy their own within the 320 points:

| | points | |
|---|---|---|
| **Lancers** | 288 | 11 x Lance (a8 h2 e10 c4) + Keep with the flag; every Lance runs the game's hunter |
| **Heavies** | 283 | 7 x Heavy (a5 h10 e15 c4) + Keep with the flag + Runner that holds; the Heavies hunt |
| **Runners** | 318 | 14 x Runner (a2 h4 e10 c5) + Keep with the flag; every Runner hunts |
| **Bulwark** | 281 | 8 x Wall across the frontier row + 4 x Heavy behind that go at an enemy their map shows within two squares + Keep with the flag, Runner, Scout; nobody hunts |
| **Executioner** | 294 | 9 x Exec (a10 h4 e12 c4, a type of its own) + Keep with the flag; every Exec hunts |
| **Fugitive** | 285 | the flag on a Runner whose program walks it along the back row, turning at the edge and away from an enemy its map shows near + 11 x Lance that hunt |

The programs are eleven files under `matches/bots/programs/`, and four of
them are the game's own hunter written out for a given fare and attack.
Every rebuilt doctrine deploys on the two rows nearest the frontier, as
before, so the two armies' front rows are adjacent; the stock array stands
two rows back from that.

**One rule of the game was changed on the way, before any game in the
series was played.** The catalogue's hunter checked that the square it
preferred to step into held none of its own, and when it did, stepped the
other way without checking - onto one of its own, which is a contest with
friendly fire (**R5.7**). In the first Flag Hunt against Lancers played
while the harness was being built, a Line walked onto its own Keep on turn
2 and the two fought. The hunter now checks both ways and holds when both
are its own, which takes its longest path from twenty-eight ticks to
thirty-three, and the Lance's compute went from three to four to afford
it - the one change to `src/` this series made, recorded in the
`programmable-units` change rather than hidden in a match log. The Lancers,
Fugitive and Executioner doctrines above pay for that fourth point.

## The results

**Eleven of twenty decided**, ten by a flag falling and one a draw in which
both flags fell in the same exchange (**R7.1a**). Of the nine undecided,
four ran to the cap of 500 turns and five stopped on a repeated state -
one of them on turn 2, which is the control doing what a control should.

| # | player 1 | player 2 | result | in play, start → end | walls | flags at the end, p1 / p2 |
|---|---|---|---|---|---|---|
| 221 | Garrison | Garrison | undecided, turn 2, repeated turn 1 | 14v14 → 14v14 | 2v2 → 2v2 | standing / standing |
| 222 | Advance | Garrison | undecided, turn 45, repeated turn 44 | 14v14 → 8v14 | 2v2 → 2v2 | standing / standing |
| 223 | Flag Hunt | Garrison | undecided, turn 500, the cap | 14v14 → 12v14 | 2v2 → 2v2 | standing / standing |
| 224 | Screen | Garrison | undecided, turn 104, repeated turn 44 | 14v14 → 8v14 | 2v2 → 2v2 | standing / standing |
| 225 | Flag Hunt | Lancers | **player 1 wins, turn 75** | 14v12 → 14v0 | 2v0 → 1v0 | standing / fallen |
| 226 | Flag Hunt | Heavies | **player 2 wins, turn 51** | 14v9 → 10v6 | 2v0 → 1v0 | fallen / standing |
| 227 | Flag Hunt | Runners | **a draw, turn 37** | 14v15 → 6v1 | 2v0 → 1v0 | fallen / fallen |
| 228 | Flag Hunt | Bulwark | undecided, turn 500, the cap | 14v7 → 12v7 | 2v8 → 2v6 | standing / standing |
| 229 | Flag Hunt | Executioner | **player 2 wins, turn 24** | 14v10 → 10v4 | 2v0 → 1v0 | fallen / standing |
| 230 | Flag Hunt | Fugitive | **player 1 wins, turn 30** | 14v12 → 14v2 | 2v0 → 1v0 | standing / fallen |
| 231 | Lancers | Heavies | **player 2 wins, turn 25** | 12v9 → 0v9 | – | fallen / standing |
| 232 | Lancers | Runners | **player 2 wins, turn 20** | 12v15 → 1v4 | – | fallen / standing |
| 233 | Lancers | Bulwark | **player 1 wins, turn 50** | 12v7 → 1v4 | 0v8 → 0v1 | standing / fallen |
| 234 | Heavies | Runners | **player 1 wins, turn 25** | 9v15 → 8v1 | – | standing / fallen |
| 235 | Heavies | Bulwark | **player 1 wins, turn 74** | 9v7 → 4v1 | 0v8 → 0v2 | standing / fallen |
| 236 | Runners | Bulwark | **player 1 wins, turn 37** | 15v7 → 3v3 | 0v8 → 0v1 | standing / fallen |
| 237 | Executioner | Lancers | undecided, turn 500, the cap | 10v12 → 1v1 | – | standing / standing |
| 238 | Fugitive | Executioner | **player 1 wins, turn 20** | 12v10 → 4v1 | – | standing / fallen |
| 239 | Flag Hunt | Flag Hunt | undecided, turn 500, the cap | 14v14 → 12v12 | 2v2 → 2v2 | standing / standing |
| 240 | Advance | Advance | undecided, turn 21, repeated turn 15 | 14v14 → 12v12 | 2v2 → 2v2 | standing / standing |

"In play" counts units standing on the board whose type has energy, which is
what keeps a player in the game (**R7.1**); walls are counted beside them.
"Repeated turn *n*" is the game's own finding that the board after the
final turn is the board after turn *n*, controllers' memories, meters and
sleep included (**R7.5**). The judgement of who is in the game is the
record's, read from each turn's list of the eliminated, and the log says on
which turn a seat became `eliminated`.

## What the stock army did when nobody played it

Games 221 to 224 put each stock doctrine against a Garrison whose every
controller is one `HALT`.

**Left alone, it is a repeated state on turn 2** (221). Two stock armies
whose controllers do nothing cost nothing - `HALT` is the one instruction
with no price - so the board after turn 2 is the board after turn 1 to the
last register, and the game says so and stops. The last series ran this
pairing for sixty turns to find out nothing had happened; this one needed
one.

**Walked at, it holds, and the walkers run out of board** (222). Advance's
front rank reaches the Garrison on turn 14 - later than before, because a
Pawn that has to afford a step and a strike before stepping walks every
other turn and sleeps between. Both Heavies die on turn 23 to the Garrison's
Heavies, which strike back for five without being told to; all four Pawns
die on turn 43 to the Pawns they walked into. The state repeats on turn 45:
what is left of Advance is its back rank, whose program is `HALT`, and a
Garrison that never came. Eight against fourteen, both flags standing.

**A screen against a garrison is Advance with two Scouts out of the way**
(224). The Scouts reach their posts at (3,3) and (4,3) on turn 11, walking
round the Pawns in front of them, and stand there for ninety-three turns.
The rest is game 222 to the unit and the turn - the Heavies fall on turn 23
and the Pawns on turn 43 - and the game stops on turn 104, the state repeating from
turn 44: the two Scouts, whose program still looks for a post it is
standing on, cost one energy every so many turns and rest it back, and the
meter takes sixty turns to come round. What a screen is worth is only
answerable against a doctrine that attacks, and none was drawn against it.

**Hunted, it is not taken** (223). This is the series' clearest finding
about the default army. Flag Hunt against the Garrison ran to the cap with
the Garrison's flag never struck. Only the two Heavies ever left the stock
array: the Runners, Lines and Scouts on the back row are boxed in by the
Pawns and Walls in front of them and the Keeps and each other beside, and
the hunter, which will not step onto one of its own, holds. The Pawns are
sentries that strike back and otherwise sleep, so they never move out of
the way, and the Walls cannot. The two Heavies walked out alone on turn 2,
met the Garrison's Heavies on turn 16, traded fives, and died on turn 25
with the Garrison's Heavies at half health. From turn 25 to turn 500 twelve
units stood where they were seeded, and the game did not repeat because
every one of them was thinking: a boxed-in Line runs the hunter's whole
longest path - thirty-two ticks against a cap of forty - every turn it is
awake, pays an energy for it nearly every turn, falls below what a step
and a strike need, sleeps a turn, rests the energy back, and thinks again.
Over 500 turns the Flag Hunt seat paid 1,792 energy for 81,902 ticks of
thinking and moved two units. The last series' Flag Hunt took the Garrison's
flag on turn 58, because a person had sent the Pawns and Scouts as well and
the back rank followed them out; the catalogue's programs do not.

## What decided the decided games

**The rebuilt armies fight on turn 2, as before.** A doctrine that deploys
on its frontier row stands adjacent to an enemy that does the same, and
every hunter steps out on the first turn of play. In 231, 232, 234, 237 and
238 both front rows stepped into each other on turn 2:

| game | turn 2 |
|---|---|
| 231 Lancers v Heavies | six of eleven Lances destroyed, no Heavy; three more Lances on turn 3 |
| 232 Lancers v Runners | all eight front-row Lances and all eight front-row Runners destroyed, each pair killing the other |
| 234 Heavies v Runners | six Runners on turn 2, four more on turn 3, no Heavy until turn 8 |
| 237 Executioner v Lancers | all eight front-row Executioners and all eight front-row Lances destroyed, each pair killing the other |
| 238 Fugitive v Executioner | the same sixteen |

The stock array, standing two rows back, makes first contact on turn 3 or
4 against a rebuilt army and on turn 14 to 16 against another stock army.

**A Lance is a strike and a corpse, and it needs company.** Against
Heavies (231) the Lances struck for eight into ten health and died to five,
and this time none of them arrived in pairs: nine dead by turn 3, the last
two on turns 18 and 21, and the Heavies took the Keep on turn 25 having lost
nobody. Against Runners (232) the two front rows annihilated each other on
turn 2, and the Runners' second row walked through and took the Keep on
turn 20 with three left. Against Bulwark (233) the Lances broke four Walls
on turn 4 and three more on turn 16, lost four to the Heavies that came out
to meet them, and the last Lance and the Keep it struck fell together on
turn 50 - and the Lancers won, with one unit left, because the Keep that
fell was Bulwark's. Three Lancers games, one win, eleven Lances lost in
each.

**Two armies of one-blow units leave two Keeps, and two sleeping Keeps
never repeat** (237). Executioner against Lancers killed sixteen units on
turn 2, two more on turn 12 and the last two Lances on turns 21 and 24, and
from turn 24 to turn 500 the board held one Keep at each edge, both
running the warden's `SLEEP 100`. The game did not stop, because a sleeping
unit's countdown is part of the state the repeat is judged on: a Keep that
is 60 turns into its sleep is not a Keep that is 61 turns in, and when it
wakes on turn 125 it pays a tick to sleep again, which moves its meter, so
the state would come round only after eighty wakings. Four hundred and
seventy-six turns in which nothing could ever happen were resolved and
recorded. The repeat rule is doing what it says; whether a sleep counter
*should* count as a change of state is a question for the rules.

**A column walking into a wall still destroys itself, and this time the
wall falls anyway** (236). Runners against Bulwark: on turn 4 the front row
of Runners stepped into four Walls - the hunter goes at the flag square, so
only the columns between it and the flag are struck - and four Runners died
with the four Walls, each Runner having been struck twice by its own second
row crashing in behind it (**R5.8a**). Four more died on turn 6 the same
way and three on turns 11 to 13. What is different from the last series is
that the Runners this time broke three more Walls on turn 14 and, with two
Runners left, walked through the hole, killed the two Heavies that came out
on turn 29, and took the Keep on turn 37. Heavies against Bulwark (235)
broke six Walls on turns 4 and 5, met Bulwark's four Heavies on turn 14 in
one exchange that killed all four of them and four of its own seven, and
took the Keep on turn 74 with two Heavies left.

**The Bulwark comes out now, and that is what kills it.** Last series the
Bulwark's Heavies held unless an enemy was already adjacent. This series
their program goes at anything the army's map shows within two squares,
and a Wall that is struck puts the striker on the map. In 233, 235 and 236
the Heavies stepped through their own line to meet what had broken it,
traded blows on open ground, and were killed there; in each case the Keep
was then taken by the one or two units that remained. Against Flag Hunt
(228) it worked the other way: Bulwark's Heavies came out, killed Flag
Hunt's two Heavies on turn 21, and then had nothing within two squares for
479 turns, while Flag Hunt's back rank stood boxed in at its own edge. Two
flags standing at the cap.

**Heavies beat the stock army again, and so did Executioner** (226, 229).
Flag Hunt's two Heavies are the only units it sends, so a rebuilt army that
can kill two Heavies has the stock array's flag for the taking - once it
has walked there. The Heavies lost three of seven to Flag Hunt's two and the
Pawns, and took `keep1` on turn 51 with one blow of five into a Keep worn
to five. Executioner lost six of nine and took it on turn 24, the one
blow of ten being enough from full health. Lancers (225) and Fugitive (230)
lost to Flag Hunt because a Lance that strikes a Pawn or a Wall and does
not kill it falls back onto its own second row (**R5.8a**), and because
Flag Hunt's Heavies kill a Lance a blow; in both the stock army lost one
Wall and nothing else. Runners (227) is the draw: on turn 37 Flag Hunt's
surviving Runner struck the Runners' Keep for two into two health left as
the Runners' last Runner struck Flag Hunt's `keep1` for two into two, both
flags fell in the same exchange, and the game declared a draw.

**The mirrors are mirrors.** Advance against Advance (240) is exactly
symmetric and stops on turn 21: both pairs of Heavies die on turn 15, and
the four pairs of Pawns facing each other across rows 3 and 4 then step
into each other, strike for one into four health, fall back, run out of
energy, sleep, rest and step in again on a cycle of six turns, which the
repeat rule catches on its second round. Flag Hunt against Flag Hunt (239)
is symmetric to the tick - 81,752 ticks of thinking a side, 1,788 energy a
side - which the last series' mirror was not: a program is the same
program from either edge, where the old Python route search tried the
compass in a fixed order. Both sides' Heavies met on turn 16 and killed
each other, and the two boxed-in back ranks thought about the enemy flag
for 484 turns.

## What the tariff cost each doctrine

Every controller's ticks and the energy they cost are in the record, so the
price of thinking can be read off for each seat. The table gives, per game,
the ticks a seat's controllers ran and the energy they paid for them, over
the turns the game lasted.

| # | player 1 | ticks | energy | player 2 | ticks | energy | turns |
|---|---|---|---|---|---|---|---|
| 221 | Garrison | 0 | 0 | Garrison | 0 | 0 | 2 |
| 222 | Advance | 1,532 | 64 | Garrison | 0 | 0 | 45 |
| 223 | Flag Hunt | 81,902 | 1,792 | Garrison | 0 | 0 | 500 |
| 224 | Screen | 5,603 | 131 | Garrison | 0 | 0 | 104 |
| 225 | Flag Hunt | 14,131 | 306 | Lancers | 1,829 | 42 | 75 |
| 226 | Flag Hunt | 8,649 | 181 | Heavies | 2,796 | 68 | 51 |
| 227 | Flag Hunt | 4,173 | 85 | Runners | 3,886 | 70 | 37 |
| 228 | Flag Hunt | 81,788 | 1,788 | Bulwark | 11,057 | 274 | 500 |
| 229 | Flag Hunt | 4,496 | 95 | Executioner | 1,846 | 42 | 24 |
| 230 | Flag Hunt | 5,846 | 126 | Fugitive | 2,131 | 47 | 30 |
| 231 | Lancers | 805 | 14 | Heavies | 1,720 | 40 | 25 |
| 232 | Lancers | 575 | 7 | Runners | 2,060 | 34 | 20 |
| 233 | Lancers | 2,448 | 57 | Bulwark | 910 | 21 | 50 |
| 234 | Heavies | 1,514 | 35 | Runners | 1,464 | 23 | 25 |
| 235 | Heavies | 2,729 | 66 | Bulwark | 356 | 8 | 74 |
| 236 | Runners | 2,665 | 43 | Bulwark | 734 | 16 | 37 |
| 237 | Executioner | 378 | 3 | Lancers | 916 | 16 | 500 |
| 238 | Fugitive | 1,152 | 20 | Executioner | 442 | 5 | 20 |
| 239 | Flag Hunt | 81,752 | 1,788 | Flag Hunt | 81,752 | 1,788 | 500 |
| 240 | Advance | 820 | 32 | Advance | 820 | 32 | 21 |

Three things stand out.

**Thinking is cheap when it ends in a step and dear when it does not.** A
hunter that finds its way costs twenty-six ticks and moves; one that is
blocked both ways runs thirty-two or thirty-three and holds, every turn,
for ever. The stock army's back rank is blocked both ways from turn 1, so
Flag Hunt pays about 3.6 energy a turn for nothing in every long game - a
Line's twelve energy is gone in fifteen turns of this, and comes back only
by sleeping. The per-turn cap (**R10.5**) never bit: no controller in the
series was stopped at its cap, and the halts in the record are all a unit
with no energy left being refused another tick (**R10.4**). What the tariff
punished was not a long program but a program with nowhere to go.

**The doctrines that won spent least.** Heavies paid 40 and 35 energy to
win 231 and 234; Executioner 42 to win 229; Fugitive 20 to win 238. A
rebuilt army of hunters on the frontier row is in contact on turn 2 and
either dead or walking a clear board by turn 3, and a hunter with a clear
board thinks for twenty-six ticks and moves. The stock army paid 306 to
beat the Lancers in 225, because twelve of its fourteen units were paying
to stand still.

**Sleep is the only rest a thinking unit gets, and the stock programs use
it as a brake, not a plan.** A hunter sleeps for one turn when it cannot
afford a step and a strike, and wakes to think again. The Keep's warden
sleeps a hundred and wakes only when struck, which is why two Keeps alone
cost 3 and 16 energy over 476 turns (237) and why they never repeated a
state. A program that slept until its map changed would cost nothing while
boxed in; none of these does.

## What the series says about the open questions

**The default army plays itself badly.** The catalogue's programs send two
Heavies and nothing else, because the back rank cannot get past the front
rank and the front rank's sentries do not move. A player who commits what
they are handed fields twelve units that pay to stand still. Whether the
remedy is a Pawn that advances, a hunter that waits for the square in
front to clear rather than giving up on the axis, or a stock array that
leaves the back rank a way out, is the rules' to decide; what the series
shows is that the stock army as programmed cannot take a flag from
anything that does not come to it.

**A repeated state is the right stop, and sleep counters make it rare.**
Five games stopped on a repeat, and in each the repeat was real: nothing
could ever have happened again. Four ran to the cap, and in each the board
had been static for hundreds of turns - 475, 479, 476 and 484 - while
sleep countdowns and thinking meters kept the state technically new. The
cap is doing the work the repeat rule was meant to do. Excluding a sleeping
unit's countdown and a controller's meter from the state, or declaring a
game undecided when no unit has moved or struck for some number of turns,
would have stopped those four in a tenth of the time with the same result.

**Q2 - identical units.** Under one strike a turn, two identical units
still stand off rather than annihilate, and the Advance mirror (240) shows
it with a cycle: step in, strike for one, fall back, rest, step in again.
Nothing in the series produced a game decided by which of two identical
units went first; both mirrors came out even to the tick.

**The flag.** Every decision was a flag falling, and the draw was two flags
falling at once. A visible flag gives every hunter somewhere to go from
turn 1, and the games that went undecided are the ones where nobody could
get there: a Garrison that never moves, a back rank that cannot, two Keeps
alone, and a Bulwark that only comes out two squares.

**Compute as a price.** Every type in the series that thinks pays between
two and eight points for it, and the dearest controller, the Keep's, does
the least. The cost of compute showed up nowhere in the results - no
doctrine was constrained by its cap, and no doctrine ran out of points
because of compute - which says the tariff's prices are low enough to be
ignored at these program sizes. A compute of two bought a Pawn a
twenty-tick program that fits with one tick to spare, and that was the one
place the cap was felt, in the writing rather than the playing.

## Found on the way

Two defects in the game were found by building this harness and are fixed
in the `programmable-units` change rather than recorded as divergences:

- **The hunter stepped onto its own units on the second axis**, said above.
- **A unit woken by a blow had no words for it.** The `woken` event the
  engine emits when a sleeping unit is struck had no description, so a feed
  printed its raw fields (`players: 1, unit: keep1`). Games 221 to 232 were
  played before the words were added and their logs show the raw form;
  games 233 to 240 say `keep1 is woken by the blow`. The record is the same
  event either way.

One thing was found in the harness itself: a role's transcript was
accumulated a character at a time, which was quadratic in its size and made
reading a 500-turn record back take an hour. It takes thirty seconds now,
and the first eight games of the series were read back the slow way, with
the same result.

## What this series does not show

- **Whether a screen is worth anything.** Screen was drawn only against a
  Garrison, which never came.
- **What a stock army does when its programs let it out.** Every stock
  game is two Heavies and twelve bystanders; a Pawn program that advances,
  or a hunter that waits for the way to clear, would make the four stock
  games a different series.
- **What the radio is for.** No doctrine says anything: `SAY`, `RECV` and
  the inbox were not exercised, and nothing here says whether a
  coordinated army beats an uncoordinated one.
- **What a program that sleeps until something changes does to the
  tariff.** Every program here thinks every turn it can; one that slept
  while its map was unchanged would pay nothing to stand still, and would
  also stop the four capped games on a repeat.
- **Anything about three players.** Every game was two seats on the default
  halves.

The logs are `matches/logs/game_221.log` to `game_240.log`; each names
each seat's setup, what every controller decided and what it spent every
turn, the board after it, every event and every refusal, the outcome and
the final units. `matches/check_records.py` reads all twenty and reports
each complete.
