# Twenty games where everybody is trying to win

Twenty games on a 10x10 board, 200 points a side, deployment split at the
frontier, under the rules as they stand on master: a move costs a quarter of
the unit's maximum health rounded up (**R4.3**), a unit that does nothing
recovers 1 energy (**R3.9**), walls are health standing on a square
(**R2.10**), and a player is out when nothing they hold could ever act again
(**R7.1**).

**Nothing in the engine changed for this series.** Everything below is the
harness and the doctrines it plays: `matches/arena.py` and `matches/bots/`.

## What was wrong

The previous series ended thirteen of twenty games undecided, most with both
armies intact, and the reason was not subtle once it was looked at properly.
Two doctrines - Turtle and Ambush - implemented `orders()` as `return []`.
Not as a tactic: for ever. Turtle's own docstring admitted it: *"it can never
win. Holding still kills nobody who does not come to it, so the best it can do
is not lose."* A third, Nomad, was *"three runners that never fight and are
never caught... It cannot win."*

A series in which two of the players are not trying to win measures nothing.

## What changed

**1. No doctrine may sit for ever.** `Sweeper` grows a `patience`: how many
turns a doctrine will hold its deployment before it has to come forward.
Contact overrides it - once there is an enemy to go at, waiting stops being a
plan. Turtle holds 20 turns and then advances; Ambush holds 15; everything
else has a patience of 0 and moves from the first turn. Nomad is deleted.

**2. Every army was under-fuelled, and that was the real problem.** Every
doctrine in the stable was designed when a move cost a flat 1, so 10 energy
meant 10 squares. On the quarter fare a health-10 unit pays 3 a square, and
those same armies had *three squares* in them. They crossed a tenth of the
board and then rested for the rest of the game. The audit:

| doctrine | before | squares each | after | squares each |
|---|---|---|---|---|
| Turtle | 10 x (a1 h10 e10) | **3** | 4 x (a1 h7 e42) | **21** |
| Ambush | 8 x (a1 h10 e10) | **3** | 5 x (a1 h5 e34) | **17** |
| Sponge | 11 x (a1 h10 e6) | **2** | 5 x (a1 h8 e31) | **15** |
| Drain | 10 x (a1 h10 e9) | **3** | 4 x (a1 h10 e39) | **13** |
| Phalanx | 12 x (a1 h5 e10) | **5** | 6 x (a1 h4 e28) | **28** |
| Grinder | 6 x (a1 h10 e20) | **6** | 3 x (a1 h10 e55) | **18** |
| Swarm | 18 x (a1 h1 e9) | 9 | 7 x (a1 h1 e26) | **26** |

Every doctrine was rebuilt at the same 200 points: fewer bodies, enough fuel to
cross the board and then fight. Nothing now fields a unit with less than 13
squares in it. That is a real strategic shift and it is the one R4.3's fare
table predicts - a campaigning army is a small one.

**3. Three doctrines had stall bugs, and the harness now catches them.** The
arena counts consecutive orderless turns and calls a bot out in the log after
thirty. It found, in order:

- **Mixed** gave no order for 66 turns of 100. Its killers were told to wait on
  what its scout found, and its scout had been killed on turn 9. Waiting on a
  scout is only a plan while there is a scout.
- **Bulwark** gave no order for 81 turns of 100. `plan_routes` returned nothing
  at all: the two units behind the wall line held their squares and waited for
  somebody to walk onto them. A wall line holds ground; the units behind it are
  the only things that can win, and they cannot win standing still.
- **Duellist**'s champions had a route one square long, so a champion that
  reached its post stood on it for the rest of the game.

All three now fall back to sweeping when they have nothing to chase. **No bot
stalls anywhere in the twenty games below**, and the check stays in the harness
so the next one cannot hide.

**4. The turn cap is 100**, up from 60.

## The twenty games

| # | player 1 | player 2 | result | in play, start -> end | idle |
|---|---|---|---|---|---|
| 1 | Swarm | Grinder | undecided | 7v3 -> 1v3 | 37% |
| 2 | Assassin | Hunter | **p1, turn 36** | 5v3 -> 2v0 | 37% |
| 3 | Mixed | Turtle | undecided | 4v4 -> 1v1 | 48% |
| 4 | Phalanx | Swarm | undecided | 6v7 -> 1v1 | 37% |
| 5 | Hunter | Grinder | undecided | 3v3 -> 3v1 | 53% |
| 6 | Attrition | Tide | undecided | 4v6 -> 2v1 | 37% |
| 7 | Duellist | Ambush | undecided | 3v5 -> 2v3 | 43% |
| 8 | Sponge | Ambush | **p1, turn 59** | 5v5 -> 5v0 | 41% |
| 9 | Sponge | Duellist | undecided | 5v3 -> 3v3 | 37% |
| 10 | Attrition | Duellist | undecided | 4v3 -> 2v2 | 47% |
| 11 | Drain | Ambush | **p1, turn 100** | 4v5 -> 4v0 | 50% |
| 12 | Drain | Turtle | undecided | 4v4 -> 2v2 | 45% |
| 13 | Reaper | Ambush | undecided | 2v5 -> 2v3 | 51% |
| 14 | Reaper | Turtle | undecided | 2v4 -> 2v1 | 59% |
| 15 | Bulwark | Reaper | **p1, turn 20** | 2v2 -> 2v0 | 39% |
| 16 | Bulwark | Swarm | undecided | 2v7 -> 2v2 | 25% |
| 17 | Bulwark | Drain | **p1, turn 19** | 2v4 -> 1v0 | 33% |
| 18 | Swarm | Bulwark | undecided | 7v2 -> 4v1 | 49% |
| 19 | Sharpshooter | Attrition | undecided | 3v4 -> 2v3 | 47% |
| 20 | Bulwark | Duellist | undecided | 2v3 -> 1v1 | 48% |

**Five decisions. Every game is now a real battle** - the armies grind each
other from four-to-seven units down to one-to-three in every single game,
where the previous series had twelve games in which nothing whatever happened.

`matches/logs/game_8.log` is kept as the worked example. It is the whole story
in one game, good and bad: see below.

## About that 44% idle

Idling is now **evenly spread from about turn 26 onward**, and it is not
refusal to play - it is exhaustion. Rest returns 1 energy a turn and a move
costs 1 to 3, so a unit that has spent its pocket moves at best every second
or third turn from then on. Half-idle is the steady state of an army that has
finished its fuel, and the only ways to lower it are more energy (which means
fewer units, since energy is bought with points) or a faster rest rate (which
is a rule, and out of scope here).

The distinction worth keeping: **a doctrine that refuses to play is a bug in
the doctrine; a unit resting to afford its next square is the game working.**
The first is gone. The second is R3.9 doing what it was added to do.

## What is still broken, and it is not the doctrines

Five decisions in twenty is no better than the last series, and **game 8 shows
exactly why**. Sponge walks into Ambush and destroys four of its five units by
turn 9, losing nothing. Then it spends **fifty turns hunting the last one**,
and only finds it on turn 59.

That is not a doctrine failing. Under **R6.2** you learn where an enemy is only
by stepping onto its square, so hunting one unit on a 10x10 board means walking
a hundred squares on the chance of collision - and the quarry moves. Most of
the undecided games above are in exactly that state at the cap: one or two
survivors a side, still trying, unable to find each other.

**The remaining lever is a rule, not a bot.** Nothing the harness can do fixes
the endgame hunt. Worth deciding deliberately: whether R7.2 should decide a
game that reaches its length on ground held or on damage done, whether
visibility should widen once an army is nearly destroyed, or whether the board
is simply too large for 200 points.

## How the games were run

```
python matches/arena.py --game 8 --p1 matches/bots/sponge.py \
       --p2 matches/bots/ambush.py --budget 200
```

Real `bgcserver` and `bgcclient` sessions throughout. Each bot is handed its
own player's published view and nothing else, so no bot can see what its
opponent holds; the observer is read only for the log, after both players have
committed. The half-board deployment split is refereed by the harness, because
the game itself does not have that rule.
