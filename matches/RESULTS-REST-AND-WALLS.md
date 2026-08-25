# Twenty games with rest and walls

The third series. Same board, same two hundred points, same split deployment as
`matches/RESULTS-FRONTIER.md`, with three changes to the game itself — proposed,
specified and implemented as the `rest-walls-and-what-counts` change:

1. **A unit that takes no action recovers 1 energy** at the end of the turn
   (**R3.9**). No order, and nothing paid for while the turn resolved — being
   attacked and unable to strike back still counts as doing nothing, and rests.
   It never recovers past the energy its type was designed with.
2. **A type may have attack 0 and energy 0 together** (**R2.10**) — a **wall**.
   Health standing on a square: it can never move, never strikes, never rests,
   costs its health and nothing else, and blocks like anything else.
3. **Elimination asks whether a unit could ever act again** (**R7.1**). A unit
   at zero energy keeps its owner in the game, because resting will give it
   back. A wall never does, so a player left holding only walls is out.

The third followed from the first. This branch had earlier stopped counting
units at zero energy, which was right while energy never came back and wrong
the moment it did: with rest, zero is a state a unit passes through, and
judging a player on it decides games on the timing of a snapshot. The twenty
games below were played twice for that reason — once under the snapshot rule
and once under the rule that replaced it — and the differences are set out
under **What the snapshot rule had been deciding**.

## Nine decisions, then eight — and all eight are earned

The previous series decided **two games in thirty**. This one decides **eight in
twenty**, and every one of them is a player losing their last unit that could
play: seven by having nothing left on the board at all, and one — game 100 — by
being left holding nothing but walls.

| # | player 1 | player 2 | result | in play, start → end | walls left |
|---|---|---|---|---|---|
| 81 | Swarm | Grinder | **player 2 wins, turn 59** | 18v6 → 0v6 | – |
| 82 | Assassin | Hunter | **player 1 wins, turn 18** | 6v4 → 2v0 | – |
| 83 | Mixed | Turtle | undecided | 6v10 → 6v10 | – |
| 84 | Phalanx | Swarm | **player 1 wins, turn 2** | 12v18 → 8v0 | – |
| 85 | Hunter | Grinder | undecided | 4v6 → 4v1 | – |
| 86 | Attrition | Tide | undecided | 6v16 → 4v3 | – |
| 87 | Duellist | Ambush | undecided | 6v10 → 6v10 | – |
| 88 | Sponge | Ambush | **player 2 wins, turn 21** | 12v10 → 0v10 | – |
| 89 | Sponge | Duellist | undecided | 12v6 → 6v2 | – |
| 90 | Attrition | Duellist | undecided | 6v6 → 3v1 | – |
| 91 | Drain | Ambush | **player 2 wins, turn 12** | 10v10 → 0v6 | – |
| 92 | Drain | Turtle | undecided | 10v10 → 1v7 | – |
| 93 | Reaper | Ambush | **player 1 wins, turn 30** | 2v10 → 2v0 | – |
| 94 | Reaper | Turtle | **player 1 wins, turn 43** | 2v10 → 2v0 | – |
| 95 | Bulwark | Reaper | undecided | 3v2 → 1v1 | – |
| 96 | Bulwark | Swarm | undecided | 3v18 → 2v4 | 1 v 0 |
| 97 | Bulwark | Drain | undecided | 3v10 → 2v7 | – |
| 98 | Swarm | Bulwark | undecided | 18v3 → 4v2 | 0 v 1 |
| 99 | Sharpshooter | Attrition | undecided | 6v6 → 2v3 | – |
| 100 | Bulwark | Duellist | **player 2 wins, turn 14** | 3v6 → 0v3 | 7 v 0 |

"In play" counts units that could act again — every unit except a wall. A unit
out of energy is in that count, because it will rest its way back.

## Rest: armies stop freezing, so hunts finish

Every game in the two previous series ended the same way — both armies standing
still on a board they could no longer cross, holding energy they were saving for
a fight they could not reach. Rest ends that. A unit that stops for a turn gets
a point back, so a doctrine that keeps a reserve now marches at roughly half
speed *for ever* instead of stopping dead.

- **Game 94 is the clearest case.** Reaper against Turtle was undecided in the
  last series even when the cap was raised to 140 turns: the two champions
  killed eight of ten campers and then stood a few squares from the last two
  with eight and seven energy — enough to walk, never the ten they needed to
  strike. Under rest they wait, recover to ten, and finish it on turn 43.
- **Game 81** went the same way from the other side: Grinder's attack-1 tanks
  had frozen at their energy floor with four Swarm units alive. Now they keep
  grinding, and the last one falls on turn 59.
- **Game 82**, Assassin against Hunter, had never produced a casualty after
  turn 7. Now it resolves on turn 18.

What it does *not* fix is two armies that decline to engage. Games 83 and 87 —
a waiting attacker against a defender that never moves — are unchanged, and
under rest the defender is strictly better off than before: it recovers for
free while nobody comes.

## Rest kills draining

Draining was the tactic the zero-energy win condition invented: walk a
ten-health, low-energy unit into a defender and make it spend its whole pocket
killing you. It does not survive regeneration, twice over. The defender now
heals a point a turn while the next sponge is still walking across — and since
a defender at zero is no longer out of the count anyway, emptying its pocket
buys nothing at all.

Both drain matchups are losses now: **games 88 and 91 are wins for Ambush**,
having been the drainer's best results in the previous series, and in both the
drainers finish destroyed rather than merely spent. A cost you inflict once is
worthless against an opponent who recovers.

## Walls: they stop an army, and they cannot finish one

Bulwark lays ten walls of ten health across its own frontier row — a hundred
points, the whole width of the board — and keeps two attack-2 fighters and a
scout behind them.

Against an attack-1 army the line does what it is for. In **game 97** Drain's
ten units each stepped into a wall on turn 2 and spent everything they had:
each spent 1 energy on the move and 8 attacking, and every one of them stood at
zero at the end of the turn it first moved, with every wall still up on 2
health. A hundred points of wall had emptied a two-hundred-point army's pockets
in a single move.

And then, under R7.1, nothing happened. The attackers rest, recover, and come
back — they spend the next fifty turns chewing through the line, and the game
ends undecided with the walls gone and seven attackers inside Bulwark's half.
That is the right answer and it is worth being clear about why: **a wall
converts an attacker's energy into nothing, and energy is no longer something
you can take away for good.**

The other edge of it is **game 100**, and it is the wall clause doing exactly
the work it was written for. Duellist's attack-10 champions break a wall in one
round — ten energy for ten health, the same price anybody pays, but paid in one
round rather than ten — and were through the line and onto Bulwark's two
fighters by turn 14. Bulwark ends the game with seven walls standing and
nothing that can play, and is out. Walls hold ground; they are not an army.

## What the snapshot rule had been deciding

Played under the superseded rule — a unit at zero energy stops counting — the
same twenty games gave nine decisions rather than eight. Three of those nine
turned on the snapshot, and the two that changed are the two worth reading:

- **Game 97** was a **win for Bulwark on turn 2**. Every attacker was at zero
  energy at the end of the turn it first moved, so every attacker stopped
  counting and the game was over before the wall line had lost a single point
  of health. Under the current rule that same position is a stalled attack that
  recovers and eventually breaks through.
- **Game 88** was a win for Ambush on turn 12 rather than 21: the sponges hit
  zero and were counted out, rather than resting and being killed properly over
  the following nine turns.

Both old results were the same artefact — a player judged on what they were
holding mid-fight rather than on what they had left. The rule now asks what a
unit *is*, and every one of the eight decisions is a player who ran out of
units rather than out of pocket.

## What plays well under these rules

- **Retreat and rest is now a real move.** A champion below its attack value is
  not finished, it is out of position. Walking two squares back, waiting three
  turns, and coming again is a better plan than any of these bots had.
- **Draining is dead twice over.** It cannot out-race a point a turn, and even
  when it lands there is no longer a prize for emptying somebody's pocket.
- **Walls stop attack-1 armies and delay attack-10 ones.** Ten points of wall
  costs either attacker about ten energy — but the first spends ten turns'
  worth of pocket and the second spends one round.
- **A wall line needs an army behind it, and the army is what you can lose.**
  Bulwark spends half its points on ground it denies and half on the three
  units that are actually playing; game 100 is what happens when those three
  die.
- **Passivity is still a guaranteed draw**, and now a comfortable one: a
  defender nobody reaches recovers for free while the attacker spends
  everything crossing the board.

## What this asks of the design

1. **Rest makes an unreached defender strictly stronger.** It recovers for
   nothing while an attacker spends everything getting there. Worth deciding
   whether resting should require a turn *out of contact*, or whether a unit
   that was attacked should recover at all.
2. **A wall is permanent ground for anyone who cannot afford to break it.** It
   cannot be moved, cannot be worn down and never expires. If ten points for
   ten health is too cheap, cost is the lever — a wall currently pays for its
   health and nothing else.
3. **The draw by mutual refusal is the only undecided ending left**, and with
   rest it is permanent rather than exhausted. Twelve of these twenty games
   ended that way, most of them with both armies intact. `R7.2` still gives a
   draw only for a mutual wipe-out.

## How the games were run

```
python matches/arena.py --game 100 --p1 matches/bots/bulwark.py \
       --p2 matches/bots/duellist.py --budget 200 --max-turns 60
```

Unchanged from the previous series: real `bgcserver` and `bgcclient` sessions,
each bot handed its own player view and nothing else, the half-board rule
refereed by the harness because the game does not have it. Rest, walls and the
elimination test are in the game itself. `matches/logs/game_N.log` is the record
of each game, and every game there is one the current rules would play the same
way again.
