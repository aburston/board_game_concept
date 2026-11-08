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

