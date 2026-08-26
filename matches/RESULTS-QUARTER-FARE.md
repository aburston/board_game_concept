# Twenty games at a quarter of the weight

The fifth series, and the third setting of the movement fare. Same board, same
two hundred points, same split deployment, same rest and walls as the two
series before it. One rule differs from `matches/RESULTS-MOVE-COSTS-HEALTH.md`:

> **R4.3** — a move costs the moving unit **a quarter of its type's maximum
> health, rounded up**. Health is 1–10, so the fare is **1** for health 1–4,
> **2** for health 5–8 and **3** for health 9–10 — never 0, because it rounds
> up.

Proposed, specified and implemented as the `move-costs-a-quarter-of-health`
change, on the evidence of the last series: at the full health the fare ran
1–10 against a rest rate of 1 a turn, and heavy units stopped being slow and
became furniture.

These are games **181–200**, the same twenty pairings as **81–100** and
**161–180**.

## Three fares, twenty pairings

| # | player 1 | player 2 | fare of 1 | fare = health | fare = health ÷ 4 |
|---|---|---|---|---|---|
| 181 | Swarm | Grinder | p2, t59 | p2, t7 | **p2, t37** |
| 182 | Assassin | Hunter | p1, t18 | p1, t9 | **p1, t11** |
| 183 | Mixed | Turtle | – | – | – |
| 184 | Phalanx | Swarm | p1, t2 | p1, t2 | **p1, t2** |
| 185 | Hunter | Grinder | – | – | – |
| 186 | Attrition | Tide | – | p1, t8 | – |
| 187 | Duellist | Ambush | – | – | – |
| 188 | Sponge | Ambush | p2, t21 | – | – |
| 189 | Sponge | Duellist | – | – | – |
| 190 | Attrition | Duellist | – | – | – |
| 191 | Drain | Ambush | p2, t12 | – | **p2, t9** |
| 192 | Drain | Turtle | – | – | **p2, t15** |
| 193 | Reaper | Ambush | p1, t30 | – | – |
| 194 | Reaper | Turtle | p1, t43 | – | – |
| 195 | Bulwark | Reaper | – | – | **p1, t48** |
| 196 | Bulwark | Swarm | – | – | – |
| 197 | Bulwark | Drain | – | – | – |
| 198 | Swarm | Bulwark | – | – | – |
| 199 | Sharpshooter | Attrition | – | – | – |
| 200 | Bulwark | Duellist | p2, t14 | p2, t49 | **p2, t14** |

**Eight decisions, then five, now seven.** The quarter fare recovers most of
what the full-health fare cost, and it does it without giving weight back its
free ride: nothing in this series behaves like the flat-fare series did.

| # | in play, start → end | walls left |
|---|---|---|
| 181 | 18v6 → 0v6 | – |
| 182 | 6v4 → 2v0 | – |
| 183 | 6v10 → 6v10 | – |
| 184 | 12v18 → 8v0 | – |
| 185 | 4v6 → 4v3 | – |
| 186 | 6v16 → 4v2 | – |
| 187 | 6v10 → 6v10 | – |
| 188 | 12v10 → 1v10 | – |
| 189 | 12v6 → 7v4 | – |
| 190 | 6v6 → 4v2 | – |
| 191 | 10v10 → 0v10 | – |
| 192 | 10v10 → 0v10 | – |
| 193 | 2v10 → 2v4 | – |
| 194 | 2v10 → 2v6 | – |
| 195 | 3v2 → 2v0 | 10 → 2 |
| 196 | 3v18 → 2v4 | 10 → 1 |
| 197 | 3v10 → 2v7 | 10 → 0 |
| 198 | 18v3 → 4v2 | 10 → 1 (p2) |
| 199 | 6v6 → 2v1 | – |
| 200 | 3v6 → 0v3 | 10 → 6 |

**A note on comparability.** Drain and Sponge are the armies they were at a
flat fare again. Both are cheap-heavy designs — ten health on almost no energy
— and the full-health fare made them *illegal by construction*, because a type
then had to hold at least its health in energy. The quarter fare's floor is the
movement cost, so Drain is back at its original ten units of (a1 h10 e9), and
Sponge at eleven of (a1 h10 e6) plus one nearly-empty unit, now (a1 h9 e3)
rather than (a1 h10 e2) — the floor's minimum. So games 188–192 and 197 compare
cleanly against 88–92 and 97, and it is the **middle** column that is the odd
one out.

## Heavy units move again, and are still slower

This is what the change was for, and it is legible in one number. Reaper is two
champions of attack 10, health 10, energy 80 — the heaviest thing anybody
fields.

| fare | orders it managed in 60 turns | result v Ambush |
|---|---|---|
| 1 | 29 of 29 — it moved every turn until it won | won, turn 30 |
| health (10 a square) | **11** | nothing found, undecided |
| health ÷ 4 (3 a square) | **26** | undecided, Ambush 10 → 4 |

At a quarter it crosses the board, finds people and fights them: games 193 and
194 take Ambush from ten to four and Turtle from ten to six. It no longer wins
either, where at a flat fare it won both. That middle is the whole intent —
armour costs mobility, and a heavy unit is now genuinely ponderous rather than
genuinely stationary.

The same thing from the other side, in **game 181** (Swarm v Grinder). Grinder's
six health-10 tanks pay 3 a square. Under the full fare they moved once and
then held for the whole game while the Swarm walked onto them and died on turn
7. Now they grind forward, and the same eighteen Swarm units take **thirty-seven
turns** to run out — 18 → 4 by turn 6, then a slow attrition to 0. Same winner,
five times the game.

## A wall line's life, measured three times

Game 197 is the same position each time: Bulwark's hundred points of wall — ten
units of ten health across the whole frontier — against Drain's ten health-10
units at attack 1.

| fare | when the line fell |
|---|---|
| 1 | turn 8 |
| health | never — Drain could not take a step, all ten walls untouched at turn 60 |
| health ÷ 4 | **turn 22** |

A wall converts an attacker's energy into time, and the fare sets the exchange
rate. Under the quarter, Drain's ten attackers spend 3 to arrive, empty their
pockets on the line, rest, and come again — and the whole line goes down at
once on turn 22, fourteen turns later than it did when walking was free. The
game then runs out with seven attackers loose in Bulwark's half and two swords
trying to hold them. Undecided, as it was before.

**Game 195 is new, and it is the first win a wall doctrine has taken in any
series.** Bulwark against Reaper, decided on turn 48. Reaper's two champions
broke **eight of the ten walls** — attack 10 breaks a ten-health wall in one
round, at ten energy, whoever is swinging — killed Bulwark's scout, and then
died to the two attack-2 swords behind the line. Bulwark finished with both
swords at full health, 22 and 12 energy left, and two walls standing.

That is what a wall line is supposed to buy. It bought forty-eight turns and
two champions' worth of energy, and this time there was something behind it
still able to spend them.

## Draining is dead, conclusively

Restoring the original Drain settles the question the last two series left open.
It is the real cheap-heavy army again, and it loses both matchups without
killing anything at all:

- **Game 191** (v Ambush): 10 v 10 → **0 v 10** by turn 9. Every drainer
  destroyed; Ambush loses nothing.
- **Game 192** (v Turtle): 10 v 10 → **0 v 10** by turn 15. The same.

At a flat fare the same army at least made Ambush pay — game 91 ended 0 v **6**.
Now the fare takes three energy a square out of a nine-energy pocket before the
fight even starts, so a drainer arrives with too little left to make anyone pay,
and rest gives the defender back whatever it does spend. **A cost you inflict
once is worthless against an opponent who recovers**, and a fare that scales
with health makes the cheap-heavy body pay for its own delivery.

## What plays well at this fare

- **Health 4 is the best value on the board.** It is four times the durability
  of health 1 for the same fare of 1 a square. Health 5 is the worst buy in the
  game: one more point of durability, and double the running cost for ever.
  Nothing in this series was designed around that, because every doctrine here
  predates the rule — and that is the most interesting thing the series does
  *not* show.
- **The passive draw is still the only guaranteed result.** Thirteen of twenty
  ended undecided, most of them with both armies intact, and games 183 and 187 —
  a waiting attacker against a defender that never moves — have now been
  identical under three different fares. Movement cost is not the lever on that.
- **A wall line finally has an argument for it**, in game 195: it works when
  what stands behind it can still fight after the line goes down.

## What this asks of the design

1. **The dial has been moved three times and each setting invalidated a
   series.** Flat 1 gave 8 decisions, health gave 5, health ÷ 4 gives 7. On this
   evidence the fare is not what decides games — armies that refuse to engage
   are. It may be worth stopping here and pointing the next change at R7.2
   instead.
2. **Rest is the binding constraint, not the fare.** A heavy unit's speed is
   `REST_GAIN ÷ fare`, and only one of those two numbers has been tuned. The
   quarter fare made a health-10 unit three times as mobile; halving the rest
   rate would undo it exactly.
3. **The step is invisible to every bot here.** Health 4 and health 5 are one
   point apart on the type sheet and a factor of two apart in running cost, and
   nothing in this series notices. R4.3 now prints the whole fare table for that
   reason — but a rule a player has to be told about in a table is worth
   checking is the rule you wanted.

## How the games were run

```
python matches/arena.py --game 200 --p1 matches/bots/bulwark.py \
       --p2 matches/bots/duellist.py --budget 200 --max-turns 60
```

Unchanged: real `bgcserver` and `bgcclient` sessions, each bot handed its own
player view and nothing else, the half-board rule refereed by the harness
because the game does not have it. `matches/logs/game_N.log` is the record of
each game.
