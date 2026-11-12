# Twenty games with an army that plays

> **Played under superseded rules.** Since these games were played the
> rest rule changed (`rest-for-everyone`): every unit standing on the board
> now recovers 2 energy at the end of every turn, whatever it did, where
> these games were played when a unit recovered 1, and only on a turn it
> was given no order, paid for nothing and was not charged by its meter.
> Every hunter's pauses to afford its next step, and every count of turns
> between blows below, belong to the old rule. The games have not been
> replayed.

The eighth series: the draw of the seventh played again, under the default
army the seventh showed was needed. Nobody ordered anything in these games
either. What differs is what a player who commits the army they are handed
fields, what a Scout does, what two units learn from meeting, how a tie is
settled, and how a settled board ends.

## What was played

**The code.** Commit `a027aa5` (8 November 2026), whose rules are
`GAME_RULES.md` at that commit. Nothing under `src/` was changed to play
these games.

**The board and the seats.** As in games 221-240: `bgcserver` registers
player 1 and player 2 and commits, and that is the whole of the
administrator's setup.

| | |
|---|---|
| board | 8 x 8, the default (**R2.1**) |
| budget | 320 points a seat, the default (**R2.3.1**) |
| placement | rows 0-3 for player 1, rows 4-7 for player 2 (**R2.6a**) |
| what a seat opens with | the catalogue of eight types with the programs the game gives them, and the sixteen-unit stock array, flag on `keep1`, 308 points spent (**R2.13**) |
| how a game ends | a flag falls and one player is left (**R7.1a**); or the whole state repeats (**R7.5**), nothing has happened for fifty turns (**R7.7**), or turn 500 is reached (**R7.6**), and the game is undecided |

**The rules that differ from games 221-240.** All of them came out of that
series' write-up, and all of them are archived changes or fixes made on the
way to this one:

| Then | Now | Rule |
|---|---|---|
| the array had the Walls in its front rank and the Lines behind them, and sent two Heavies out alone while twelve units stood boxed in | the Lines stand in front and the Walls beside the Keeps; the whole front rank goes and the back rank follows | **R2.13** |
| the Pawn was a sentry that never moved, compute 2, cost 9 | the Pawn is a vanguard that advances when it can afford a step and a strike, compute 3, cost 10; the array costs 308 | **R2.13**, **R2.4** |
| a hunter blocked both ways held, and paid for the thinking | it sleeps a turn for nothing | **R10** |
| the Scout ran the hunter at the nearest unknown square and walked into whatever was in the way | the Scout's explorer goes round its own, the enemies it knows of and the edge, and gives up on a square it cannot get nearer to in twenty turns | **R2.13** |
| two units that contested a square saw each other only if a blow was landed | units that contest a square have met, blow or no blow | **R6.2** |
| a tie for the nearest square went to the lower row | it goes to the row nearer the seat's own edge, then the lower column | **R10** |
| a static board ran to the cap of 500, because sleep countdowns and meters kept it from repeating | a game in which nothing happens for fifty turns stops | **R7.7** |

**The harness and the doctrines** are the seventh series' files unchanged,
but for the four doctrine hunters regenerated from the catalogue's - the
hunter that sleeps where it held. The six rebuilt doctrines are unaffected
by the array and the Pawn, since they take the array back; all ten are
affected by the contact rule, the tie-break and the quiet stop. Flag Hunt,
Advance and Screen, which keep the stock army, are the three that play a
different army now, and Flag Hunt is the only one whose programs changed,
being the catalogue's.

## The results

**Thirteen of twenty decided**, twelve by a flag falling and one a draw of
both flags in one exchange; of the seven undecided, three repeated a state
and four stopped for quiet, and none ran to the cap. The seventh series
decided eleven and ran four to the cap.

| # | player 1 | player 2 | result | in play, start → end | walls | was (games 221-240) |
|---|---|---|---|---|---|---|
| 251 | Garrison | Garrison | undecided, turn 2, repeated turn 1 | 14v14 → 14v14 | 2v2 → 2v2 | the same |
| 252 | Advance | Garrison | undecided, turn 29, repeated turn 28 | 14v14 → 8v14 | 2v2 → 2v2 | undecided, turn 45 |
| 253 | Flag Hunt | Garrison | **player 1 wins, turn 74** | 14v14 → 3v11 | 2v2 → 2v2 | undecided at the cap |
| 254 | Screen | Garrison | undecided, turn 73, quiet since 23 | 14v14 → 8v14 | 2v2 → 2v2 | undecided, turn 104 |
| 255 | Flag Hunt | Lancers | **player 1 wins, turn 38** | 14v12 → 12v2 | 2v0 → 2v0 | player 1 wins, turn 75 |
| 256 | Flag Hunt | Heavies | **player 2 wins, turn 89** | 14v9 → 3v4 | 2v0 → 2v0 | player 2 wins, turn 51 |
| 257 | Flag Hunt | Runners | **player 2 wins, turn 37** | 14v15 → 1v3 | 2v0 → 2v0 | a draw, turn 37 |
| 258 | Flag Hunt | Bulwark | **player 1 wins, turn 70** | 14v7 → 3v4 | 2v8 → 2v2 | undecided at the cap |
| 259 | Flag Hunt | Executioner | **player 2 wins, turn 30** | 14v10 → 10v5 | 2v0 → 2v0 | player 2 wins, turn 24 |
| 260 | Flag Hunt | Fugitive | **player 1 wins, turn 30** | 14v12 → 12v2 | 2v0 → 2v0 | player 1 wins, turn 30 |
| 261 | Lancers | Heavies | **player 2 wins, turn 25** | 12v9 → 0v8 | – | player 2 wins, turn 25 |
| 262 | Lancers | Runners | **player 2 wins, turn 20** | 12v15 → 2v7 | – | player 2 wins, turn 20 |
| 263 | Lancers | Bulwark | undecided, turn 99, quiet since 49 | 12v7 → 1v6 | 0v8 → 0v1 | player 1 wins, turn 50 |
| 264 | Heavies | Runners | **a draw, turn 25** | 9v15 → 7v1 | – | player 1 wins, turn 25 |
| 265 | Heavies | Bulwark | **player 1 wins, turn 38** | 9v7 → 5v1 | 0v8 → 0v2 | player 1 wins, turn 74 |
| 266 | Runners | Bulwark | **player 1 wins, turn 37** | 15v7 → 3v3 | 0v8 → 0v1 | player 1 wins, turn 37 |
| 267 | Executioner | Lancers | undecided, turn 74, quiet since 24 | 10v12 → 1v1 | – | undecided at the cap |
| 268 | Fugitive | Executioner | **player 1 wins, turn 20** | 12v10 → 4v1 | – | player 1 wins, turn 20 |
| 269 | Flag Hunt | Flag Hunt | undecided, turn 109, quiet since 59 | 14v14 → 4v4 | 2v2 → 2v2 | undecided at the cap |
| 270 | Advance | Advance | undecided, turn 60, repeated turn 59 | 14v14 → 8v8 | 2v2 → 2v2 | undecided, turn 21 |

"In play" counts units standing on the board whose type has energy, which is
what keeps a player in the game (**R7.1**); walls are counted beside them.
The judgement of who is in the game is the record's, read from each turn's
list of the eliminated.

## The stock army, played as it comes

**It takes a garrison now** (253). The seventh series' Flag Hunt ran five
hundred turns against a Garrison and struck its flag once; the replay of it
under the new array alone (game 243) lost twelve units for three and struck
the flag once. This one wins on turn 74. The difference is not the array
but the two rules that came after it: the army reached the Garrison's edge
on turn 10 as before, lost its Lines, Scouts, Pawns, one Runner and both
Heavies by turn 64 as before, and `heavy2` struck the carrier for five on
turn 40 as before - but this time `runner1`, which in 243 had walked
straight down its own column into the Garrison's Pawns and died there,
turned east on turn 8 at a square where two ways were equally near, came
down the middle behind the Heavies, struck the Keep for two on turns 67
and 68 and for the last two on turn 74, and died in the exchange that took
the flag. The turn-8 choice is the tie-break: the same squares, settled
towards the seat's own edge rather than the lower row. Three units left
against eleven, and the flag down.

**It beats the cheap rebuilt armies faster and loses to the dear ones more
slowly** (255-260). Against Lancers the win came on turn 38 rather than 75,
and against Fugitive on turn 30 as before, with twelve units standing at
the end of each: the Lances that die to a Pawn's fare in the front rank
now meet four advancing Pawns, two Lines and two Heavies at once. Against
Bulwark, which the seventh series could not touch in five hundred turns,
Flag Hunt broke six Walls and won on turn 70 with three units left, the
last Line taking the Keep with three into three. Against Heavies the loss
came on turn 89 rather than 51 and cost the Heavies four of seven; against
Executioner on turn 30 rather than 24, the one-blow units killing the
Scouts and taking the flag through a hole the Pawns had walked out of. The
one loss that got worse is Runners (257): a draw on turn 37 in the seventh
series, a defeat on turn 37 in this, eleven of fourteen Runners dead and the
stock army's `keep1` taken by the last two.

**Advance and Screen are shorter, and the same** (252, 254, 270). These
doctrines are the harness's and still send only Pawns and Heavies; the
Lines in their front rank run `HALT`. The games are the seventh series'
games with the stops that come sooner: the state repeats six turns after
the last casualty, or quiet takes it fifty turns after. Advance against
Advance is a mirror to the unit and now stops on turn 60, a turn after the
Pawns' six-turn cycle of step, strike, fall back and rest ended with all
eight dead on turn 59.

**The mirror is a battle, and a mirror** (269). This is game 247 again, to
the tick: 5,437 ticks a side, every casualty in pairs, two Scouts a side
left on reflected squares, stopped fifty turns after the last Pawns fell.

## What the other rules did to the rebuilt armies

Four games changed outcome or length; the rest are the seventh series'
games again, because a rebuilt army fights on turn 2 and a front row that
annihilates the one facing it leaves nothing for a tie or a contact rule to
reach. Three rules changed between the two series for a rebuilt army - the
hunter that sleeps where it held, contact without a blow, and the tie-break
- and the same doctrine files played both, so which rule moved which game
is not something twenty games can say; a controlled replay could. What the
logs show:

**The Bulwark holds its flag against the Lancers** (263). In the seventh
series the last Lance and the Keep it struck fell together on turn 50. Here
the Lances died a few turns sooner - `lance1` on turn 46 rather than 50,
the last on 49 - and the Keep stood with two health. Bulwark's Heavies came
out on turn 4 in both games. Fifty quiet turns later the game stopped with
a Keep a side.

**Heavies against Runners is a draw** (264). The seventh series' win on
turn 25 is a draw on turn 25. `runner9` walked the same seven squares to
the Heavies' Keep in both games and struck it on the same turn; what
differs is one blow of two that `runner1` landed on turn 23 in this game
and not in that one, before it died, so that `runner9`'s two on turn 25
were the Keep's last two, in the same exchange as `heavy5` took the
Runners'. Both flags fell together.

**Heavies against Bulwark is twice as quick** (265). Turn 38 rather than
74. The exchange on turn 14 is the same in both games - all four of
Bulwark's Heavies and four of the attackers' seven dead - and from there
the three Heavies left took the Keep in twenty-four turns where the
seventh series' three took sixty.

**Executioner against Lancers ends** (267). Two Keeps asleep at opposite
edges from turn 24, as before; the quiet stop takes the game on turn 74
instead of the cap on 500.

## What the tariff cost each doctrine

| # | player 1 | ticks | energy | player 2 | ticks | energy | turns |
|---|---|---|---|---|---|---|---|
| 251 | Garrison | 0 | 0 | Garrison | 0 | 0 | 2 |
| 252 | Advance | 1,188 | 32 | Garrison | 0 | 0 | 29 |
| 253 | Flag Hunt | 5,069 | 106 | Garrison | 0 | 0 | 74 |
| 254 | Screen | 4,048 | 79 | Garrison | 0 | 0 | 73 |
| 255 | Flag Hunt | 5,012 | 106 | Lancers | 1,702 | 39 | 38 |
| 256 | Flag Hunt | 3,255 | 70 | Heavies | 3,062 | 72 | 89 |
| 257 | Flag Hunt | 1,543 | 25 | Runners | 2,950 | 53 | 37 |
| 258 | Flag Hunt | 5,311 | 114 | Bulwark | 1,403 | 34 | 70 |
| 259 | Flag Hunt | 4,058 | 87 | Executioner | 1,679 | 38 | 30 |
| 260 | Flag Hunt | 3,945 | 84 | Fugitive | 1,821 | 39 | 30 |
| 261 | Lancers | 805 | 14 | Heavies | 1,545 | 36 | 25 |
| 262 | Lancers | 744 | 11 | Runners | 2,093 | 32 | 20 |
| 263 | Lancers | 2,370 | 57 | Bulwark | 2,094 | 51 | 99 |
| 264 | Heavies | 1,366 | 31 | Runners | 1,406 | 21 | 25 |
| 265 | Heavies | 1,306 | 30 | Bulwark | 350 | 8 | 38 |
| 266 | Runners | 2,589 | 43 | Bulwark | 738 | 15 | 37 |
| 267 | Executioner | 374 | 3 | Lancers | 912 | 16 | 74 |
| 268 | Fugitive | 1,152 | 20 | Executioner | 442 | 5 | 20 |
| 269 | Flag Hunt | 5,437 | 122 | Flag Hunt | 5,437 | 122 | 109 |
| 270 | Advance | 2,140 | 64 | Advance | 2,140 | 64 | 60 |

The stock army's thinking is a twentieth of what it was: 5,069 ticks over
74 turns to take the Garrison against 81,902 over 500 to fail to, because
nothing in it pays to stand still any more - a blocked hunter sleeps, a
Scout with nowhere to go sleeps, and a unit in a fight is doing something.
No controller was stopped at its cap in any of the twenty games; the halts
in the record are units with no energy left after a fight.

## What this series says

**The default is a game now.** A player who commits what they are handed
sends sixteen units, wins against a garrison, beats the cheap rebuilt
armies and loses to the dear ones, and a game between two of them is a
battle that ends inside 110 turns with every unit having fought. The
seventh series' stock seat sent two units and finished nothing.

**The quiet stop is doing what the repeat rule could not.** Four games
stopped for quiet, between 50 and 110 turns in, where the seventh series
ran the same boards to the cap; three repeated a state and the rest were
decided. Fifty turns was never close: the longest gap between two
happenings in a game that then went on was the Advance mirror's six-turn
Pawn cycle.

**The small rules moved three results, and one of them is traceable.** The
tie-break turned the Garrison's defeat (253): a Runner that had walked into
the same Heavies as everybody else went the other way at a tie on turn 8
and took the flag from behind. A Bulwark kept its flag (263) and Heavies
against Runners became a draw (264) under the same three rule changes, and
the logs show where each game diverged from its predecessor without saying
which rule did it. None of the three is a doctrine's doing: the same files
played the same armies.

**Heavies are still the thing to beat.** Three of their four games won and
the fourth a draw with seven Heavies standing; what beats them was not in
the draw.

## What this series does not show

- **Whether a screen is worth anything**, or what Advance does against
  anything but a Garrison: both were drawn against the control only, and
  both still run the harness's programs rather than the catalogue's.
- **What beats Heavies.** Heavies against Heavies, and Lancers arriving in
  pairs, were not played.
- **What the radio is for.** No doctrine says anything.
- **Anything about three players.**

The logs are `matches/logs/game_251.log` to `game_270.log`; each names
each seat's setup, what every controller decided and what it spent every
turn, the board after it, every event and every refusal, the outcome and
the final units. `matches/check_records.py` reads them with the seventh
series' and reports each complete.
