# Twenty games at two energy a turn

The ninth series: the draw of the seventh and eighth played again, under
the rest rule the `rest-for-everyone` change gave the game. Nobody ordered
anything in these games. What differs from the eighth series is one rule
of the economy and one of the tariff: every unit standing on the board now
recovers 2 energy at the end of every turn whatever it did, where it
recovered 1 and only on a turn it did nothing; and a controller thinks a
hundred ticks a point with subroutines to hand, where it thought ten.

## What was played

**The code.** Commit `8cc6b2c` (12 November 2026), whose rules are
`GAME_RULES.md` at that commit. Nothing under `src/` was changed to play
these games; the only edits were the twenty new rows of the draw in
`matches/series.sh` and the range `matches/check_records.py` reads.

**The board and the seats.** As in games 251-270: `bgcserver` registers
player 1 and player 2 and commits, and that is the whole of the
administrator's setup.

| | |
|---|---|
| board | 8 x 8, the default (**R2.1**) |
| budget | 320 points a seat, the default (**R2.3.1**) |
| placement | rows 0-3 for player 1, rows 4-7 for player 2 (**R2.6a**) |
| what a seat opens with | the catalogue of eight types with the programs the game gives them, and the sixteen-unit stock array, flag on `keep1`, 308 points spent (**R2.13**) |
| how a game ends | a flag falls and one player is left (**R7.1a**); or the whole state repeats (**R7.5**), nothing has happened for fifty turns (**R7.7**), or turn 500 is reached (**R7.6**), and the game is undecided |

**The rules that differ from games 251-270.**

| Then | Now | Rule |
|---|---|---|
| a unit recovered 1 energy at the end of a turn it was given no order, paid for nothing and was not charged by its meter | every unit standing on the board recovers 2 energy at the end of every turn, whatever it did; never past the energy its type was designed with, and a Wall and a destroyed unit recover nothing | **R3.9** |
| a controller thought ten ticks a point, and a hundred ticks cost it one energy | a controller thinks a hundred ticks a point, every instruction costs ten times what it did, and a hundred ticks still cost one energy; a program may call a subroutine | **R10.2**, **R10.3** |

The second changes the tick counts in the tariff table below by a factor
of ten and the energy they cost by nothing; the catalogue's hunter and
explorer are restated with subroutines and give the same orders. Every
result in this write-up is the first rule's.

**The harness and the doctrines** are the eighth series' files unchanged.
Flag Hunt, Advance and Screen keep the stock army, and Flag Hunt runs the
catalogue's programs; the six rebuilt doctrines field their own types with
the harness's hunters. None of the ten was rewritten for the new economy,
and the sleeps in every hunter - a turn's pause where it cannot afford a
step and a strike - are still there. They are shorter now, not gone.

## The results

**Fourteen of twenty decided**, thirteen by a flag falling and one a draw
of both flags in one exchange; of the six undecided, three repeated a
state and three stopped for quiet, and none ran to the cap. The longest
game was 73 turns, against 109 in the eighth series and 500 in the
seventh. Every game between two rebuilt armies was decided, and none took
more than seventeen turns.

| # | player 1 | player 2 | result | in play, start → end | walls | was (games 251-270) |
|---|---|---|---|---|---|---|
| 271 | Garrison | Garrison | undecided, turn 2, repeated turn 1 | 14v14 → 14v14 | 2v2 → 2v2 | the same |
| 272 | Advance | Garrison | undecided, turn 10, repeated turn 9 | 14v14 → 8v8 | 2v2 → 2v2 | undecided, turn 29 |
| 273 | Flag Hunt | Garrison | undecided, turn 73, quiet since 23 | 14v14 → 3v6 | 2v2 → 2v2 | player 1 wins, turn 74 |
| 274 | Screen | Garrison | undecided, turn 59, quiet since 9 | 14v14 → 8v8 | 2v2 → 2v2 | undecided, turn 73 |
| 275 | Flag Hunt | Lancers | **a draw, turn 14** | 14v12 → 4v2 | 2v0 → 2v0 | player 1 wins, turn 38 |
| 276 | Flag Hunt | Heavies | **player 2 wins, turn 12** | 14v9 → 6v7 | 2v0 → 2v0 | player 2 wins, turn 89 |
| 277 | Flag Hunt | Runners | **player 1 wins, turn 13** | 14v15 → 5v1 | 2v0 → 1v0 | player 2 wins, turn 37 |
| 278 | Flag Hunt | Bulwark | **player 1 wins, turn 19** | 14v7 → 5v2 | 2v8 → 2v0 | player 1 wins, turn 70 |
| 279 | Flag Hunt | Executioner | **player 2 wins, turn 7** | 14v10 → 5v6 | 2v0 → 2v0 | player 2 wins, turn 30 |
| 280 | Flag Hunt | Fugitive | **player 2 wins, turn 14** | 14v12 → 4v2 | 2v0 → 2v0 | player 1 wins, turn 30 |
| 281 | Lancers | Heavies | **player 2 wins, turn 8** | 12v9 → 1v5 | – | player 2 wins, turn 25 |
| 282 | Lancers | Runners | **player 1 wins, turn 9** | 12v15 → 3v5 | – | player 2 wins, turn 20 |
| 283 | Lancers | Bulwark | **player 1 wins, turn 17** | 12v7 → 3v3 | 0v8 → 0v1 | undecided, turn 99 |
| 284 | Heavies | Runners | **player 1 wins, turn 9** | 9v15 → 8v3 | – | a draw, turn 25 |
| 285 | Heavies | Bulwark | **player 1 wins, turn 16** | 9v7 → 5v5 | 0v8 → 0v2 | player 1 wins, turn 38 |
| 286 | Runners | Bulwark | **player 1 wins, turn 15** | 15v7 → 2v4 | 0v8 → 0v1 | player 1 wins, turn 37 |
| 287 | Executioner | Lancers | **player 2 wins, turn 9** | 10v12 → 0v3 | – | undecided, turn 74 |
| 288 | Fugitive | Executioner | **player 1 wins, turn 9** | 12v10 → 3v0 | – | player 1 wins, turn 20 |
| 289 | Flag Hunt | Flag Hunt | undecided, turn 73, quiet since 23 | 14v14 → 3v3 | 2v2 → 2v2 | undecided, turn 109 |
| 290 | Advance | Advance | undecided, turn 8, repeated turn 7 | 14v14 → 8v8 | 2v2 → 2v2 | undecided, turn 60 |

"In play" counts units standing on the board whose type has energy, which is
what keeps a player in the game (**R7.1**); walls are counted beside them.
The judgement of who is in the game is the record's, read from each turn's
list of the eliminated.

## What two a turn does

**A unit that has arrived fights every turn.** Under the old rule a unit
that struck did not recover, so a fight was a series of blows with turns of
rest between them, and a unit forced back out of a contested square walked
in again on what it had left. Now a Pawn - fare 1, attack 1 - pays two to
walk in and strike and gets two back, so it walks in and strikes every
turn until one side is dead; a Line, fare 2 and attack 3, pays five and
gets two, and once its reserve is spent strikes two turns in three; a
Heavy, fare 3 and attack 5, pays eight and gets two, and once its reserve
is spent lands a blow every fourth turn. Identical units facing
each other now do what **Q2** always said they would, only without the
pauses: two Pawns at four health kill each other on the fourth exchange,
two Lines on the second, two Heavies on the second. The eighth series'
Advance mirror took 59 turns to kill eight Pawns; this one took seven.

**The march costs a net one a square, and a unit arrives short.** A Heavy
walking five squares pays three a square and gets two back, so it reaches
the enemy's line with ten of its fifteen and strikes once; then it waits
two turns for the next eight. The sleep in the hunter that guards against
stepping into a fight it cannot pay for is what the Heavies did on turns 7
and 8 of game 273, between the blows that killed them on 6 and 9.

**Fourteen games were over by turn 19.** Every rebuilt army fights on turn
2 or 3 and its front row and the row facing it annihilate each other in
one or two exchanges; what is left walks at a Keep and takes it, or does
not, inside another ten turns. Nothing is left to wait for, so there is
nothing for the quiet stop to do in a decided game, and the three games it
stopped are ones in which nothing was going to happen.

## The stock army, played as it comes

**It does not take a garrison any more** (273). The eighth series' win on
turn 74 came from one Runner going round the Heavies and reaching the Keep
from behind, over sixty turns in which the Garrison's front rank and the
stock army's traded blows between rests. Here the two front ranks are the
same eight units facing each other, and at two a turn they kill each other
in pairs: the Lines on turn 7, the Pawns and the Heavies on turn 9, the
stock army's units falling back into their own squares after every
undecided exchange and walking in again the next turn. The Runners reached
the Keeps on turn 15, struck them for two on four turns running, and died
on the fourth to a Keep that strikes back for one and recovers two: the
Keeps were left with two health each, and the stock army with two Keeps,
two Walls and a Scout that paced between two squares until its explorer
gave up on turn 24. Nothing happened for fifty turns after that. Three
units against six, both flags standing.

**Against the rebuilt armies it wins two, draws one and loses three, and
every game is short** (275-280). The stock army's front rank meets a
rebuilt army's on turn 3, and the first exchange costs it most of that
rank: all eight against Executioner on turn 3 (279), six on turn 3 and a
Heavy on turn 4 against Lancers and Fugitive (275, 280), six over turns 3
and 4 against Heavies (276), the four Pawns on turn 4 against Runners
(277). What decides the game is whether what is left - a Heavy or two, the
Runners, the Lines where they survived - reaches the rebuilt army's flag
before the rebuilt army's survivors reach `keep1`. Against Lancers both
got there on turn 14: `lance11` took `keep1` with one blow of eight and
died to the Keep's one, and in the same turn the stock army's two Runners
walked into the Lancers' Keep together, struck it for the last four
between them and, two units of one side in one square, struck each other
too; both flags fell, and the game is a draw. Against Fugitive, whose flag
rides a Runner that walks the back row, the same `lance11` took `keep1` on
the same turn 14, and the two stock Runners walked into the square the
flag Runner had stood on the turn before and found only each other there:
the moving flag was not taken, and the stock army lost on turn 14 the
game it had won on turn 30. Against Executioner the one-blow units killed
`keep1` on turn 7, against Heavies `heavy7` did on turn 12. Against Runners
the stock army won on turn 13 the game it had lost on turn 37: its front
rank killed six Runners for the four Pawns, and the two Lines, striking the
Runners' Keep for three on turns 12 and 13 and each dying to it, took it
with the second blow while the Heavies stood behind them. Against Bulwark
it broke all eight Walls by turn 13 and took the Keep on turn 19 with seven
units standing, where the eighth series' win took 70 turns and left three.

**Advance and Screen are shorter still, and the same** (272, 274, 290).
These doctrines still send only Pawns and Heavies and still run `HALT` on
their Lines. Their Pawns and Heavies now die with the Garrison's on turn 9,
and the game stops as soon as the rules allow: a repeat the next turn for
Advance, whose survivors never move again, and the quiet stop fifty turns
later for Screen, whose Scouts wander. The Advance mirror is over on turn 8.

**The mirror is a mirror, and nobody wins it** (289). Every casualty in
pairs: the Lines on turn 5, the Pawns and Heavies on 7, a Scout and a
Runner a side on 10, the other Runners on 11. Two Keeps, two Walls and a
Scout a side, on reflected squares, from turn 11 until the quiet stop on
73. The eighth series' mirror ran to the same end over 109 turns; this one
has nothing left to fight with by turn 11.

## The rebuilt armies

Every one of the eight games between rebuilt doctrines was decided, five
of them with a different result from the eighth series. In each the front
rows annihilate each other on turn 2 and the game is decided by what each
side has in its second rank and how fast it can walk.

**Lancers win three** (282, 283, 287). The Lance - attack 8, health 2,
fare 1 - pays nine to walk in and strike, and used to sleep four turns
between blows; now it pays a net seven and is back in three, and a Lance
that is not struck first kills whatever it reaches. Against Runners the
eight front pairs killed each other on turn 2 as before, and this time
`lance9` and `lance11` reached the Runners' Keep on turn 9 where in the
eighth series the Runners' second rank reached the Lancers' on turn 20
while the Lances slept; a Runner reached the Lancers' Keep on the same
turn 9 and struck it for two, and the Lance's eight settled it. Against
Bulwark the Lances broke seven of the eight Walls
by turn 7, killed three of the four Heavies on turn 10, and took the Keep
on turn 17 - the game the eighth series stopped for quiet on turn 99 with
a Keep a side. Against Executioner, a mutual annihilation of the front
rows on turn 2 and of one more unit a side on turn 4, and then the two
Lances left took the Executioner's Keep on turn 9, where the eighth series
left both Keeps asleep.

**Heavies win all four** (276, 281, 284, 285), each faster than before and
Heavies against Runners a win on turn 9 instead of a draw on turn 25: the
Runners' front six died on turn 2 and four more on turn 3, and seven
Heavies walked at the Keep and `heavy5` took it on turn 9, the Heavies
having lost their Runner and no Heavy. Seven
Heavies standing at the end against Runners, five against Lancers, five
against Flag Hunt, three against Bulwark.

**Bulwark loses all four** (278, 283, 285, 286), and faster: six or seven
of its eight Walls are broken in the first week and its Heavies killed in
the second, and the Keep falls between turns 15 and 19. Under the old rule
a Wall held an attacker that had to rest between blows; now a Runner
strikes it for two every turn.

**Fugitive beats Executioner on turn 9 as before** (288), and Executioner
beats Flag Hunt (279), as before, in a quarter of the turns.

## What the tariff cost each doctrine

Ticks are in the new tariff, ten times the eighth series' for the same
instruction; the energy they cost is on the same scale as before.

| # | player 1 | ticks | energy | player 2 | ticks | energy | turns |
|---|---|---|---|---|---|---|---|
| 271 | Garrison | 0 | 0 | Garrison | 0 | 0 | 2 |
| 272 | Advance | 852 | 0 | Garrison | 0 | 0 | 10 |
| 273 | Flag Hunt | 4,186 | 3 | Garrison | 0 | 0 | 73 |
| 274 | Screen | 3,114 | 2 | Garrison | 0 | 0 | 59 |
| 275 | Flag Hunt | 2,130 | 0 | Lancers | 1,503 | 0 | 14 |
| 276 | Flag Hunt | 2,320 | 0 | Heavies | 1,315 | 0 | 12 |
| 277 | Flag Hunt | 2,322 | 0 | Runners | 2,626 | 0 | 13 |
| 278 | Flag Hunt | 3,721 | 3 | Bulwark | 554 | 0 | 19 |
| 279 | Flag Hunt | 1,230 | 0 | Executioner | 787 | 0 | 7 |
| 280 | Flag Hunt | 2,219 | 0 | Fugitive | 1,674 | 0 | 14 |
| 281 | Lancers | 840 | 0 | Heavies | 882 | 0 | 8 |
| 282 | Lancers | 843 | 0 | Runners | 1,563 | 0 | 9 |
| 283 | Lancers | 1,513 | 0 | Bulwark | 447 | 0 | 17 |
| 284 | Heavies | 1,102 | 0 | Runners | 1,362 | 0 | 9 |
| 285 | Heavies | 1,061 | 0 | Bulwark | 518 | 0 | 16 |
| 286 | Runners | 2,632 | 0 | Bulwark | 507 | 0 | 15 |
| 287 | Executioner | 353 | 0 | Lancers | 842 | 0 | 9 |
| 288 | Fugitive | 1,015 | 0 | Executioner | 353 | 0 | 9 |
| 289 | Flag Hunt | 3,249 | 2 | Flag Hunt | 3,249 | 2 | 73 |
| 290 | Advance | 624 | 0 | Advance | 624 | 0 | 8 |

Thinking is nearly free at this length: a game of nine turns never fills a
meter, and the two 73-turn games charged two or three energy a side, to a
Scout pacing for fifty of them. No controller was stopped at its cap in
any game. The ticks the stock army spent against the Garrison, 4,186 over
73 turns, are a tenth of the eighth series' 5,069 over 74 once the tariff
is allowed for, because the units that did the thinking were dead by turn
18.

## What this series says

**Two a turn makes the game short and makes it the first exchange's.**
Half the games were over inside thirteen turns. A fight is no longer decided by which side
ran dry first but by what each side's front row does to the other's in
one or two exchanges, and then by what is left and how fast it walks. The
eighth series' long games - 74, 89, 99, 109 turns - were units resting
between blows; there is no resting between blows now.

**The stock army no longer beats a garrison, and the mirror is a
stalemate.** Identical units that meet kill each other, so the stock army
against itself, standing or advancing, ends with two Keeps and two Walls a
side and nothing that can take a Keep. The eighth series' win over the
Garrison came from a Runner that had sixty turns to go round; this one is
over by turn 18. A default that plays an interesting game against a copy
of itself is the open question this series leaves.

**The dear units got dearer.** Heavies won all four of their games and
Lancers three of five; Bulwark lost all four and Runners all three. What
two a turn buys is proportionally most for the unit whose fare and strike
together are nearest to two - a Lance pays nine for a blow that kills
anything - and least for a Wall, which gets nothing, and a Runner, whose
two attack now takes five turns to do what a Lance does in one.

**The quiet stop and the repeat still end what needs ending.** Six games
undecided, the longest 73 turns; none ran to the cap.

## What this series does not show

- **Whether the catalogue should change for this economy.** The Pawn at
  fare 1 and attack 1 is the one unit that never waits, and the Heavy
  waits two turns in three; whether the prices should follow is a question
  for a change, not a series.
- **Whether a screen is worth anything**, or what Advance does against
  anything but a Garrison: both were drawn against the control only, and
  both still run the harness's programs rather than the catalogue's.
- **What the radio is for.** No doctrine says anything.
- **Anything about three players.**

The logs are `matches/logs/game_271.log` to `game_290.log`; each names
each seat's setup, what every controller decided and what it spent every
turn, the board after it, every event and every refusal, the outcome and
the final units. `matches/check_records.py` reads them with the seventh
and eighth series' and reports each complete.
