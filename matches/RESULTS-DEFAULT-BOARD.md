# Twenty games on the default board

The sixth series, and the first played on the game as it stands. Every
earlier series was played under rules the game no longer has; this one is
played on what a new two-player game is given when nobody sets it up further,
and the harness names nothing the game already decides.

## What was played

**The code.** Commit `7e1599b` (`master`, 18 September 2026), whose rules are
`GAME_RULES.md` at that commit. Nothing under `src/` was changed to play
these games.

**The board and the seats.** `bgcserver` registers player 1 and player 2 and
commits, and that is the whole of the administrator's setup:

| | |
|---|---|
| board | 8 x 8, the default (**R2.1**) |
| budget | 250 points a seat, the default (**R2.3.1**) |
| placement | rows 0-3 for player 1, rows 4-7 for player 2, as the game publishes them (**R2.6a**); no neutral row on an even board |
| what a seat opens with | the catalogue of eight types and the sixteen-unit stock array, flag on `keep1`, 242 points spent (**R2.13**) |
| turn cap | 60, as in every earlier series |

**The rules that differ from games 181-200.** The last series was played on
26 August. Since then:

| Then | Now | Rule |
|---|---|---|
| a fight was rounds until one side died or nobody could pay | one exchange a turn; a kill is the strikes landing in that exchange reaching the health | **R5.2**, **R5.11** |
| an undecided contest could leave units sharing a square | a survivor forced back crashes into whoever took its square, on down the column | **R5.8a** |
| no flag | one unit carries the flag; everybody sees its square; its fall puts its owner out | **R2.11**, **R6.5**, **R7.1a** |
| ten by ten, sized by the harness | eight by eight, the game's default | **R2.1** |
| 200 points named by the harness; a seat opened empty | 250 by default; a seat opens holding the stock army | **R2.3.1**, **R2.13** |
| halves refereed by the harness | halves enforced and published by the game | **R2.6a** |
| a setup clash refused both | the first commit keeps the square; a setup with no carrier is refused | **R3.5a**, **R2.11** |

**The harness.** As before: one `bgcserver` resolving turns, one `bgcclient`
per seat kept open for the whole game, an observer read only to write the
log after both seats have ordered. A bot is handed its own seat's view - the
board, units, types, players, flags and placement subjects, read by typing
`show ... json` at its own prompt - and nothing else. What it may deploy,
what it may afford and whether its setup carries a flag are the game's to
refuse, and no setup in this series was refused. The `match-series`
capability states what the harness keeps to, and `tests/test_match_harness.py`
holds it there.

**The doctrines.** Ten, in two families. Four keep the stock army as handed
and differ only in how they play it:

| | |
|---|---|
| **Garrison** | no unit is ever ordered. The control |
| **Advance** | the Pawns and Heavies step towards the enemy every turn they can afford to; the back rank holds |
| **Flag Hunt** | everything but the Keeps and Walls goes for the enemy flag square by the shortest route round its own units |
| **Screen** | the two Scouts stand on the frontier row in front of the Keeps; the rest play as Advance |

Six take the whole army back and deploy their own within the 250 points:

| | points | |
|---|---|---|
| **Lancers** | 236 | 11 x Lance (a8 h2 e10) + Keep with the flag; every Lance hunts the flag |
| **Heavies** | 242 | 7 x Heavy (a5 h10 e15) + Keep with the flag + Runner; the Heavies hunt |
| **Runners** | 240 | 14 x Runner (a2 h4 e10) + Keep with the flag; every Runner hunts |
| **Bulwark** | 246 | 8 x Wall across the frontier row + 4 x Heavy behind + Keep with the flag, Runner, Scout; nobody hunts |
| **Executioner** | 250 | 9 x Exec (a10 h4 e12, a type of its own) + Keep with the flag; every Exec hunts |
| **Fugitive** | 236 | the flag on a Runner that walks the back row every turn it can + 11 x Lance that hunt |

Every rebuilt doctrine deploys on the two rows nearest the frontier, which
on this board means the two armies' front rows are **adjacent** - row 3
faces row 4 with nothing between. The stock array stands two rows back from
that, on rows 0-1 and 6-7.

**Flag Hunt was revised once, and its games replayed.** The first version
sent only the Runners and Lines, with the Heavies following. In game 203
they never left the back rank: the stock array boxes its back row in until
the front row moves, and a step that merely shortens the distance is a step
into a unit of your own. The hunters were given a route search round their
own units and the Pawns and Scouts were sent as well, and the eight games
Flag Hunt is in were played again before anything was written up. The first
versions' logs were discarded, since a doctrine that could not do what its
docstring says is not evidence about that doctrine.

## The results

**Thirteen of twenty decided**, and every one of the thirteen was decided by
a flag falling (**R7.1a**). No game was decided by a player being wiped out
first; in game 206 the carrier was also the last unit.

| # | player 1 | player 2 | result | in play, start → end | walls | flags at the end, p1 / p2 |
|---|---|---|---|---|---|---|
| 201 | Garrison | Garrison | undecided | 14v14 → 14v14 | 2v2 → 2v2 | standing / standing |
| 202 | Advance | Garrison | undecided | 14v14 → 10v8 | 2v2 → 2v0 | standing / standing |
| 203 | Flag Hunt | Garrison | **player 1 wins, turn 58** | 14v14 → 3v5 | 2v2 → 2v0 | standing / fallen |
| 204 | Screen | Garrison | undecided | 14v14 → 10v8 | 2v2 → 2v0 | standing / standing |
| 205 | Flag Hunt | Lancers | **player 1 wins, turn 27** | 14v12 → 6v1 | 2v0 → 2v0 | standing / fallen |
| 206 | Flag Hunt | Heavies | **player 2 wins, turn 34** | 14v9 → 0v6 | 2v0 → 0v0 | fallen / standing |
| 207 | Flag Hunt | Runners | **player 1 wins, turn 32** | 14v15 → 4v0 | 2v0 → 2v0 | standing / fallen |
| 208 | Flag Hunt | Bulwark | undecided | 14v7 → 2v6 | 2v8 → 2v1 | standing / standing |
| 209 | Flag Hunt | Executioner | **player 1 wins, turn 33** | 14v10 → 3v1 | 2v0 → 1v0 | standing / fallen |
| 210 | Flag Hunt | Fugitive | **player 1 wins, turn 26** | 14v12 → 7v2 | 2v0 → 2v0 | standing / fallen |
| 211 | Lancers | Heavies | **player 1 wins, turn 15** | 12v9 → 2v7 | – | standing / fallen |
| 212 | Lancers | Runners | **player 2 wins, turn 11** | 12v15 → 0v3 | – | fallen / standing |
| 213 | Lancers | Bulwark | **player 1 wins, turn 28** | 12v7 → 1v6 | 0v8 → 0v1 | standing / fallen |
| 214 | Heavies | Runners | **player 1 wins, turn 21** | 9v15 → 5v0 | – | standing / fallen |
| 215 | Heavies | Bulwark | **player 1 wins, turn 34** | 9v7 → 4v4 | 0v8 → 0v2 | standing / fallen |
| 216 | Runners | Bulwark | undecided | 15v7 → 1v7 | 0v8 → 0v6 | standing / standing |
| 217 | Executioner | Lancers | **player 1 wins, turn 13** | 10v12 → 2v1 | – | standing / fallen |
| 218 | Fugitive | Executioner | undecided | 12v10 → 1v2 | – | standing / standing |
| 219 | Flag Hunt | Flag Hunt | **player 1 wins, turn 38** | 14v14 → 5v3 | 2v2 → 2v2 | standing / fallen |
| 220 | Advance | Advance | undecided | 14v14 → 8v8 | 2v2 → 2v2 | standing / standing |

"In play" counts units standing on the board whose type has energy, which is
what keeps a player in the game (**R7.1**); walls are counted beside them.
The judgement of who is in the game is the game's own, read from the players
subject each turn, and the log says on which turn a seat became `eliminated`.

## What the stock army did when nobody played it

Games 201 to 204 put each stock doctrine against a Garrison that never gives
an order.

**Left alone, it is safe for ever** (201). Two stock armies four rows apart
with no orders lose nothing in sixty turns, which is what **R3.9** says: a
unit that does nothing rests.

**Walked at, it holds** (202). Advance's front rank reaches the Garrison on
turn 10 and spends fifty turns walking into it. Advance's Pawns die in pairs
(turns 16 and 34); the Garrison loses two Pawns (turn 18), both Walls and
both Scouts (turn 24) and both Lines (turn 34), and its Heavies and Keeps are
never struck. Advance's two Heavies end the game on the Garrison's back row
where its Lines stood, at (2,7) and (5,7), a square from a Keep each, and
never turn on them: Advance walks forward and fights what it walks into, and
forward from row 7 is off the board. Sixty turns, ten against eight, both
flags standing.

**A screen against a garrison is idle** (204). Game 204 is game 202 to the
unit and the turn: the same eleven casualties on the same turns. The Scouts
stood on the frontier row for fifty-eight turns and nobody came, because a
Garrison never comes. What a screen is worth is only answerable against a
doctrine that attacks, and none of the three other stock doctrines was drawn
against it.

**Hunted, it falls - slowly** (203). Flag Hunt takes the Garrison's flag on
turn 58, two turns from the cap, and it takes it with one Line. By turn 40
the hunt had spent ten units to kill ten, and `line1` stood at (3,6) above
the carrier at (3,7) and struck it for the first time. A Line strikes for
three, a Keep has ten health and strikes back for one, and the contest is
undecided each time (**R5.8**), so the Line falls back, rests, and steps in
again: four strikes, on turns 40, 46, 52 and 58, one every six turns, and the
fourth is lethal. A garrisoned flag is taken by
whatever is left standing next to it with the patience to rest between
blows, because a garrison never counter-attacks the unit resting one square
away.

## What decided the decided games

**On this board, the rebuilt armies fight on turn 2.** A doctrine that
deploys on its frontier row stands adjacent to an enemy that does the same:
row 3 and row 4 touch. In games 211, 212, 214, 217 and 218 both sides
ordered their front rows forward on the first turn of play, the two rows
met in one exchange on turn 2, and that exchange did most of the killing the
game would see:

| game | turn 2 |
|---|---|
| 211 Lancers v Heavies | nine of eleven Lances destroyed, no Heavy |
| 212 Lancers v Runners | all eleven Lances destroyed, and five Runners |
| 214 Heavies v Runners | six Runners on turn 2, six more on turn 3, no Heavy until turn 5 |
| 217 Executioner v Lancers | eight of nine Executioners and ten of eleven Lances destroyed |
| 218 Fugitive v Executioner | ten of eleven Lances and eight of nine Executioners destroyed |

The stock array, standing two rows further back, makes first contact on
turn 3 against a rebuilt army and on turn 9 or 10 against another stock army.

**A Lance is a strike and a corpse.** Eight attack reaches everything in the
stock army but a Keep or a Heavy in one blow, and two health dies to any
strike of two. Against Heavies (211) the front row of Lances struck for eight
into ten health and died to five; the two that survived turn 2 took a Heavy
on turn 12, lost one of themselves on turn 13, and took the Keep on turn 15,
and won. Against Runners (212) every
Lance died on turn 2 taking five Runners with it, and the Runners walked the
length of the board and took the Lancers' Keep with three left. Against
Bulwark (213) the Lances broke seven Walls in eleven turns - a Wall is ten
health, a Lance strikes eight, so two blows - and the last Lance and the Keep
it struck fell together on turn 28. Three Lancers games, two wins, and eleven
Lances lost in each.

**A column walking into a wall destroys itself** (216). Runners against
Bulwark is the clearest single result in the series. On turn 2 the front
row of eight Runners stepped into the eight Walls, struck for two, and were
forced back undecided - into the squares the second row of Runners had just
stepped into behind them. **R5.8a** says what happens next: the unit forced
back crashes into whoever took its square, one exchange on the ordinary
terms, and friendly fire is total (**R5.7**). Two Runners strike each other
for two. On turn 3 the same thing happened again, and a Runner with four
health had now been struck twice by its own side: twelve of fourteen
Runners were destroyed by turn 3, and **not one Wall had fallen**. The last
two Runners broke two Walls on turn 11 and died on turn 12, and from then to
turn 60 the Runners' Keep stood alone at its edge, which Bulwark, which
cannot hunt, could not come for. The rule was written so that no square
holds two units at the end of a turn, and it does that; what it also does is
make a two-deep advance into anything that cannot be shifted in one exchange
cost the advancing side its second rank. Heavies against Bulwark (215) shows
the other way to do it: a Heavy's five breaks a Wall in two blows, six Walls
fell on turn 4, and the Heavies took the Keep on turn 34 having lost five of
seven.

**One strike a turn is what makes numbers on one square the only quick
kill.** Runners against Heavies (214) and against Flag Hunt (207) is fourteen
units of attack two against health ten and health six, and a lone Runner's
two kills nothing that matters. Runners won only game 212, against the one
army whose every unit dies to a strike of two.

**Attack ten kills anything and is then spent for ten turns.** An
Executioner strikes for ten, which is a Keep or a Heavy in one blow, and
holds twelve energy - two squares and a strike, then ten quiet turns to
afford the next. In 217 the one Executioner that survived turn 2 took the
Lancers' Keep on turn 13. In 218 the one that survived met a flag that
moves: Fugitive's carrier is a Runner walking its back row, and the
Executioner, which can step once and must then rest before it can afford to
strike, spent forty-four turns one square behind it and never landed a blow.
The game ended with the two of them at (6,0) and (7,1) and both flags
standing. A flag that runs is not easier to take than one that stands still;
against a hunter that has to rest between steps it cannot be taken at all.
Against Flag Hunt (210) the same carrier was caught on turn 26, by Runners
and Lines that do not have to rest between steps.

**Heavies beat the stock army, and nothing else in the series did** (206).
A Heavy's five destroys a Pawn, a Runner, a Scout or a Lance in one blow and
nothing in the stock array destroys a Heavy in one exchange short of two
Lances arriving together. Flag Hunt's whole army walked into seven Heavies
and lost all sixteen units; the Heavies lost two of their own and their
Runner, and took the Keep on turn 34. Runners (214) and Lancers (211) lost to Heavies as well; only the
Lancers, striking eight, took Heavies down at all. The counter the series
found is Heavies against Heavies, which nobody was drawn to play.

**The stock army, played as a hunt, beat five of the six rebuilt armies and
drew the sixth.** Games 205, 207, 209 and 210 are Flag Hunt over Lancers,
Runners, Executioner and Fugitive, decided between turns 26 and 33; 208 is
sixty turns against Bulwark with seven Walls broken and both flags standing;
206 is the loss to Heavies. In every one of the four wins the pattern was
the same: the rebuilt army's front row met Flag Hunt's Pawns on turn 3 or 4
and killed all four, and then met the Heavies and Lines behind, which the cheap or
fragile rebuilt units could not kill in one exchange and could not afford to
press. What the stock array turned out to be is a screen of four cheap
Pawns in front of the two units that decide fights.

**The mirrors.** Advance against Advance (220) is exactly symmetric - both
Heavies die on turn 12 on each side, all four Pawns on turn 15, sixty turns,
eight against eight - which is what a deterministic game and a deterministic
doctrine should give. Flag Hunt against Flag Hunt (219) is not: player 1
wins on turn 38. The doctrine, not the game, breaks the symmetry: its route
search tries the four directions in one fixed compass order, so a seat
walking south and a seat walking north do not make mirror-image choices at a
tie. Nothing in 219's log shows the game favouring either seat, but it is
the one game in the series where the harness could not have told a rules
asymmetry from a doctrine's, and a mirror that is made mirror-symmetric in
its tie-breaking is the control the next series should carry.

## What the series says about the open questions

**Q2 - identical units.** Under one strike a turn, two identical units of
any real health stand off rather than annihilate, and this series is full of
it: every undecided contest in 202, 203 and 220 is a pair of like units
striking once and falling back. What it did *not* produce is a game decided
by which of two identical units went first - 220, the purest mirror, is
symmetric to the unit. The series gives no reason to add an initiative
statistic; it gives one reason to keep simultaneous resolution, which is
that the mirror came out even.

**The flag.** Every decision in the series was a flag falling. The earlier
series decided two of thirty and eight of twenty by wiping an army out; this
one decided thirteen of twenty, on turns 11 to 58, and in only one of them
was the carrier also the last unit. A visible flag gives every army somewhere
to go from turn 1, and the games that went undecided are the ones where
nobody could get there: two Garrisons that never move, a Bulwark that cannot
hunt, and a hunter that cannot catch a carrier that runs.

**The frontier.** Halving an eight-row board gives each seat four rows, and
a doctrine that uses its two forward rows is in contact on the first move.
Nothing in the rules is wrong with that, but it means the choice of
deployment row is the largest single decision a rebuilt army makes, and the
stock array's choice - the two rows at the edge - is the one that survived
first contact best.

## Two things the game got wrong, found on the way

Neither is fixed by this change, which plays games and changes no rule.
Both are recorded as open divergences in `SPEC_COVERAGE.md`.

**A game started at the command line has no board.** `bgcserver -g <n>` on a
new number opens an unsized game and refuses to commit with "the board size
is too small (0, 0)"; the 8 x 8 default is given only where a game is created
through the registry, which the lobby does. The harness creates its games
through that same call so as not to type `set board 8 8`.

**The rejected-orders list is matched by unit name, not by owner.** Both
players hold the sixteen stock names, and a player whose `pawn1` walked into
the other's `pawn1` is told twice, at their own unit's square both times; a
player whose Lance left the enemy `keep1` standing is told "keep1 at (3,0):
the contest at (3, 7) was undecided" - their own Keep's square, which took no
part. Every game in the series with a stock army on both sides shows it from
the first undecided contest.

## What this series does not show

- **Whether a screen is worth anything.** Screen was drawn only against a
  Garrison, which never came.
- **What beats Heavies.** Nothing in the draw did; Heavies against Heavies,
  and Lancers arriving in pairs, were not played.
- **What a doctrine that deploys at the edge rather than the frontier does
  with a rebuilt army.** Every rebuilt doctrine stood on rows 2-3 or 4-5 and
  fought on turn 2; whether the same armies two rows back would survive first
  contact the way the stock array did is the obvious next question.
- **Whether the mirror in 219 hides a rules asymmetry.** See above.
- **Anything about three players.** Every game was two seats on the default
  halves.

The logs are `matches/logs/game_201.log` to `game_220.log`; each names the
orders every turn, the board after it, every refusal each client printed,
the outcome and the final units. `matches/check_records.py` reads all twenty
and reports each complete.
