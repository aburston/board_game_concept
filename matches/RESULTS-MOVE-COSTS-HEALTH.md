# Twenty games where a step costs what the unit weighs

The fourth series, and the first played on `master` after PR #16 merged. Same
board, same two hundred points, same split deployment, same rest and walls as
`matches/RESULTS-REST-AND-WALLS.md`. One rule is different, and it is the only
rule that is different:

> **R4.3** — a move costs the moving unit **its type's maximum health** in
> energy, not a flat 1. Damage is not weight shed: a ten-health unit standing on
> two health still pays ten. A type must therefore be bought with at least its
> health in energy, or it could never move at all, and the engine refuses it.

These are games **161–180**, played against the same twenty pairings as games
**81–100**, so the two tables can be read side by side.

## The result: fewer decisions, and the ones that land land sooner

| # | player 1 | player 2 | under a flat fare of 1 (81–100) | under the health fare (161–180) |
|---|---|---|---|---|
| 161 | Swarm | Grinder | player 2, turn 59 | **player 2, turn 7** |
| 162 | Assassin | Hunter | player 1, turn 18 | **player 1, turn 9** |
| 163 | Mixed | Turtle | undecided | undecided |
| 164 | Phalanx | Swarm | player 1, turn 2 | **player 1, turn 2** |
| 165 | Hunter | Grinder | undecided | undecided |
| 166 | Attrition | Tide | undecided | **player 1, turn 8** |
| 167 | Duellist | Ambush | undecided | undecided |
| 168 | Sponge\* | Ambush | player 2, turn 21 | undecided |
| 169 | Sponge\* | Duellist | undecided | undecided |
| 170 | Attrition | Duellist | undecided | undecided |
| 171 | Drain\* | Ambush | player 2, turn 12 | undecided |
| 172 | Drain\* | Turtle | undecided | undecided |
| 173 | Reaper | Ambush | player 1, turn 30 | undecided |
| 174 | Reaper | Turtle | player 1, turn 43 | undecided |
| 175 | Bulwark | Reaper | undecided | undecided |
| 176 | Bulwark | Swarm | undecided | undecided |
| 177 | Bulwark | Drain\* | undecided | undecided |
| 178 | Swarm | Bulwark | undecided | undecided |
| 179 | Sharpshooter | Attrition | undecided | undecided |
| 180 | Bulwark | Duellist | player 2, turn 14 | **player 2, turn 49** |

**Eight decisions became five.** \*Drain and Sponge are not the same armies they
were — see *Two doctrines the rule deleted* below — so games 168, 169, 171, 172
and 177 are not clean comparisons. The other fifteen are.

| # | in play, start → end | walls left |
|---|---|---|
| 161 | 18v6 → 0v6 | – |
| 162 | 6v4 → 2v0 | – |
| 163 | 6v10 → 6v10 | – |
| 164 | 12v18 → 8v0 | – |
| 165 | 4v6 → 4v4 | – |
| 166 | 6v16 → 4v0 | – |
| 167 | 6v10 → 6v10 | – |
| 168 | 10v10 → 10v10 | – |
| 169 | 10v6 → 8v2 | – |
| 170 | 6v6 → 5v5 | – |
| 171 | 9v10 → 9v10 | – |
| 172 | 9v10 → 9v10 | – |
| 173 | 2v10 → 2v10 | – |
| 174 | 2v10 → 2v10 | – |
| 175 | 3v2 → 3v2 | 10 v 0 |
| 176 | 3v18 → 2v5 | 1 v 0 |
| 177 | 3v9 → 3v9 | 10 v 0 |
| 178 | 18v3 → 5v2 | 0 v 1 |
| 179 | 6v6 → 4v4 | – |
| 180 | 3v6 → 0v2 | 7 v 0 |

## Heavy units stopped being slow and started being furniture

This is the whole of it. Before, health bought staying power and cost nothing
else. Now health is also the price of every square you cross, and the two are
paid out of the same pocket that pays for attacking (R2.5).

Work the arithmetic for the standard heavy unit these doctrines keep buying —
attack 1, health 10, energy 20, a fifth of the budget for two of them:

- one step costs **10**, half of everything it owns;
- a second step costs the other 10 and leaves it unable to strike;
- resting recovers **1 a turn** (R3.9), so the third step is **ten turns** later.

A ten-health unit crosses at roughly **one square per ten turns** for ever. Over
a sixty-turn game that is six squares. The board is ten wide.

The logs show it as a flat line. In **game 171** — Drain against Ambush — player
1 gives the order `holds` on **fifty-nine of sixty turns**: its nine ten-health
units are bought at the legal floor of ten energy, a step costs ten, and no unit
will spend its last point and stand there unable to fight. Neither army moves a
single square in the entire game. In **game 173**, Reaper's two champions
(attack 10, health 10, **energy 80**) spend turns 2–8 walking seven squares,
then move again on turns 19, 30, 41 and 52 — one square every eleven turns,
exactly the rest rate. They never find anybody. Under the flat fare the same two
champions hunted down and killed all ten of Ambush's units by turn 30.

**Games 173, 174 and 180 are the price of this in decisions.** Reaper won both
its games before by crossing the board; now it cannot cross the board. Duellist
still beat the Bulwark line, but took **turn 49 instead of turn 14** — the same
breach, executed by champions that could afford one step in two.

## The light armies are the only things still moving — and they die faster

The flip side, and the reason three games got *shorter*:

- **Game 161** (Swarm v Grinder, turn 7 instead of turn 59). Grinder's six
  ten-health tanks move once, on turn 2, and then hold for the rest of the game
  at ten energy — one short of the eleven a step-plus-a-blow needs. Swarm's
  eighteen one-health units pay a fare of **1** and are free to march. So they
  march into stationary tanks and are annihilated a rank at a time: 18 → 17 → 12
  → 6 → 3 → 1 → 0. Player 2 wins by standing still.
- **Game 166** (Attrition v Tide, turn 8 instead of undecided). Identical shape.
  Attrition's four ten-health grinders take two steps and stop; Tide's sixteen
  one-health units keep coming, and all sixteen are gone by turn 8.
- **Game 164** is unchanged at turn 2, because it was never about movement — it
  is the friendly-fire collision written up in `COMMENTARY-GAME-84.md`.

So the rule did not slow the game down uniformly. It **separated the army into
things that move and things that do not**, and every decisive game in this
series is a mobile army walking into an immobile one. Nothing chased anything.

## Two doctrines the rule deleted

Two of the twenty bots became **illegal army lists** and had to be rebuilt before
the series could be played at all:

- **Drain** was ten units of attack 1, health 10, **energy 9** — bought
  deliberately poor, because its whole idea was to make a defender spend its
  pocket killing you. Energy below health is now refused outright: the unit
  could never take a step. Rebuilt at the floor as nine of (1, 10, **10**), 189
  points.
- **Sponge** was eleven of (1, 10, 6) plus one of (1, 10, 2). Rebuilt as nine of
  (1, 10, 10) plus one of (1, 5, 5), 200 points.

Both had to buy the energy they were designed not to have, and both are now the
same immobile block: Drain never moved in games 171 or 172, and Sponge never
moved in 168. **The cheap-heavy archetype is gone** — not beaten, forbidden.
Game 168 flipped from a loss to a draw purely because the army that used to lose
it can no longer walk far enough to lose it.

The bots themselves also needed a fix that is worth recording, because it was
the same mistake a human player would make: every doctrine's energy arithmetic
was written against a fare of 1 and had to be taught to read its own type list
and pay the real fare (`matches/bots/common.py::fares`). A doctrine that budgets
energy at all has to know the number.

## Walls got cheaper to hold and no harder to break

A wall never moves, so a wall pays nothing new. Everything that was true of the
line in `COMMENTARY-GAME-97.md` is still true — and one thing is sharper:

**breaking a wall is priced by attack, but *reaching* it is priced by health.**
In **game 176** Swarm's one-health units cross the board for 1 a square and have
nine of Bulwark's ten walls down by turn 9. In **game 177** Drain's ten-health
units never take a step, so all ten walls are still standing at turn 60 without
a scratch. The same wall line, against the same attack value of 1, beaten
comprehensively by the army that weighs less.

That inverts the advice in the wall commentary. A wall line used to cost its
attacker roughly its health in energy whoever the attacker was. Now it costs
them that **plus the health of everything they walked over with**, and the
cheapest bodies in the game are the ones that can afford the trip.

## What this asks of the design

1. **Rest is now the binding constraint, not the fare.** One energy a turn
   against a fare of ten means a heavy unit's speed is `REST_GAIN / health`.
   That single ratio decides whether an army is an army or a fortification, and
   it is currently set in two different rules that were never designed together.
2. **`energy ≥ health` is a floor that guarantees exactly one step.** A type
   bought at the floor is legal, deployable, and can move once in its life. If
   that is meant to be a real option it is fine; if a unit is meant to be able to
   *campaign*, the floor wants to be something like `health × 3`, and the engine
   should say so at purchase rather than let a player discover it on turn 2.
3. **Health now costs three times** — points to buy it, energy every step, and
   the fare comes out of the attack pocket. The cost table in `GAME_RULES.md`
   §R9 says this; the games say it is the dominant fact about the game, not a
   footnote. Two hundred points of ten-health units is a wall you paid movement
   prices for.
4. **The draw by immobility is a new ending.** The previous series' draws were
   armies that declined to engage. Five of these — 171, 172, 173, 174, 177 — are
   armies that *wanted* to engage and could not afford to arrive. Nothing in R7
   distinguishes them, and both look like `undecided after 60 turns` in the log.

## How the games were run

```
python matches/arena.py --game 180 --p1 matches/bots/bulwark.py \
       --p2 matches/bots/duellist.py --budget 200 --max-turns 60
```

Unchanged: real `bgcserver` and `bgcclient` sessions, each bot handed its own
player view and nothing else, the half-board rule refereed by the harness
because the game does not have it. `matches/logs/game_N.log` is the record of
each game.
