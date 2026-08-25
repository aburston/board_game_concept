# Thirty games across a frontier

The same exercise as `matches/RESULTS.md`, played again under three changes:

1. **Two hundred points a player** instead of one hundred.
2. **The board is halved at deployment.** Player 1 may only deploy in rows 0–4,
   player 2 only in rows 5–9. Nothing stops a unit crossing once play starts.
3. **A unit at zero energy no longer counts.** It stays on the board and still
   holds its square, but it does not keep its owner in the game.

The third is a change to the game, not to the harness: `R7.1` used to say an
inert unit was spent but not lost. It now says a player is out once every unit
they own is destroyed **or** down to zero energy. That is one predicate in
`service/turn.py`, and the spec, the rules and the tests moved with it. The
second is a house rule with no place in the game's own rules (`R2.6` lets you
deploy anywhere), so the harness referees it: a deployment outside your half is
refused before it is typed, and the refusal is logged.

Everything else is as before — real `bgcserver` and `bgcclient` sessions, each
bot handed its own player view and nothing else.

## What the changes did

**The armies now actually fight.** In the open-board series, nine of thirteen
games saw their last casualty by turn ten and one pair never met at all. Across
these thirty games, 205 of the 506 units deployed were destroyed — 41% of
everything on the board — and only four games passed without a single
casualty. All four were the same shape: a passive attacker (Mixed, Duellist)
against a defender that never moves (Turtle, Ambush).

**Two of thirty were decided.** A frontier guarantees contact; it does not
guarantee a conclusion. What ends a game is still having to account for
*every* enemy unit, and two hundred points buys enough health to absorb what
two hundred points can pay to deal out.

## The results

Rounds 1 and 2 are the same ten pairings as the first exercise. Round 1 carried
two bot defects that the new setup exposed (see below), so round 2 is the fair
baseline. Rounds 3 and 4 are doctrines invented for the new win condition.

| # | player 1 | player 2 | result | in play, start → end | spent | last casualty |
|---|---|---|---|---|---|---|
| **Round 1** — the old doctrines, ported |||||||
| 21 | Swarm | Grinder | undecided | 18v6 → 1v6 | – | turn 11 |
| 22 | Assassin | Hunter | undecided | 6v4 → 3v1 | – | turn 7 |
| 23 | Mixed | Turtle | undecided | 6v10 → 6v10 | – | none |
| 24 | Phalanx | Swarm | undecided | 12v18 → 12v16 | – | turn 8 |
| 25 | Hunter | Grinder | undecided | 4v6 → 4v3 | – | turn 8 |
| 26 | Attrition | Tide | undecided | 6v16 → 4v3 | – | turn 13 |
| 27 | Duellist | Ambush | undecided | 6v10 → 6v10 | – | none |
| 28 | Nomad | Attrition | undecided | 6v6 → 1v4 | – | turn 12 |
| 29 | Tide | Ambush | undecided | 16v10 → 13v10 | – | turn 5 |
| 30 | Attrition | Duellist | undecided | 6v6 → 3v3 | – | turn 10 |
| **Round 2** — defects fixed, energy floors revised |||||||
| 31 | Swarm | Grinder | undecided | 18v6 → 4v6 | – | turn 6 |
| 32 | Assassin | Hunter | undecided | 6v4 → 3v1 | – | turn 7 |
| 33 | Mixed | Turtle | undecided | 6v10 → 6v10 | – | none |
| 34 | Phalanx | Swarm | **player 1 wins on turn 2** | 12v18 → 8v0 | – | turn 2 |
| 35 | Hunter | Grinder | undecided | 4v6 → 4v3 | – | turn 8 |
| 36 | Attrition | Tide | undecided | 6v16 → 4v7 | – | turn 7 |
| 37 | Duellist | Ambush | undecided | 6v10 → 6v10 | – | none |
| 38 | Sponge | Ambush | undecided | 12v10 → 2v5 | 5 v 5 | turn 4 |
| 39 | Sponge | Duellist | undecided | 12v6 → 4v2 | 6 v 0 | turn 4 |
| 40 | Attrition | Duellist | undecided | 6v6 → 3v3 | – | turn 10 |
| 41 | Swarm-100 | Grinder-100 | undecided | 9v3 → 4v3 | – | turn 4 |
| **Round 3** — draining, which the new win condition invented |||||||
| 42 | Drain | Ambush | undecided | 10v10 → 1v2 | 1 v 4 | turn 6 |
| 43 | Drain | Turtle | undecided | 10v10 → 3v3 | 1 v 4 | turn 9 |
| 44 | Drain | Duellist | undecided | 10v6 → 2v2 | 6 v 0 | turn 4 |
| 45 | Drain | Grinder | undecided | 10v6 → 4v6 | – | turn 5 |
| **Round 4** — clearing a half rather than searching a board |||||||
| 46 | Reaper | Ambush | **player 1 wins on turn 30** | 2v10 → 2v0 | – | turn 30 |
| 47 | Reaper | Turtle | undecided | 2v10 → 2v2 | – | turn 34 |
| 48 | Reaper | Grinder | undecided | 2v6 → 2v4 | – | turn 21 |
| 49 | Reaper | Swarm | undecided | 2v18 → 2v11 | – | turn 7 |
| 50 | Reaper | Turtle | undecided (140 turns) | 2v10 → 2v2 | – | turn 34 |

"In play" counts units that are on the board **and** hold energy — which under
the new rule is what keeps a player in. "Spent" counts units still standing on
their squares at zero energy, which no longer do.

Game 41 is the control: the same pairing and the same frontier at the old
hundred points. It finished 4v3 with both sides down to their last few points
of energy — the same shape as game 31 at two hundred. Doubling the budget did
not change the ending; it doubled how long the fighting lasted.

Games 47 and 50 are the same match played twice, the second with the turn cap
raised from 60 to 140. They are identical move for move — the determinism the
rules require (**R1.2**), seen from outside.

## The two decisive games

**Game 34 — both armies destroy themselves, and one of them survives it.**
Both sides were deployed in two ranks on their own side of the frontier, and
both ordered every unit forward on turn 2. Every unit in the two front ranks
collided head-on with its opposite number (**R4.9**), which means *neither
completes its move*: the whole front line stayed where it stood. The second
ranks, which had been ordered into the squares their own front ranks were
supposed to vacate, arrived on top of them — and friendly fire is total
(**R5.7**), so each pair fought.

What that cost depended entirely on health. The Swarm's units have one health,
so every pair killed each other outright: all eighteen were destroyed on the
turn they first moved, each having spent exactly one round of attacks, and
seven of the twelve Phalanx units finished the turn untouched at full health,
having paid nothing but the fare. The Phalanx's own second rank did the same
thing to itself — p11 and p12 walked into p5 and p6 — but at five health it
took five rounds to settle, and it cost four units rather than twelve.

Neither bot could have seen this coming from its own view. It is two rules
interacting, and a frontier is what makes both sides do it on the same turn.

**Game 46 — the arithmetic of clearing a half.** Reaper is two units of attack
10, health 10 and eighty energy. Attack 10 kills any unit in one round, which
costs ten energy and takes one point of damage back, so a champion is worth ten
kills and eighty energy is five of them plus thirty squares of walking. Two of
them cleared Ambush's ten campers by turn 30 and finished with both units
alive. This is what the split board actually buys the attacker: an enemy is
somewhere in fifty squares rather than a hundred, and none of them are behind
you.

## What the new win condition changed

**It invented draining.** A defender pays its attack value in energy every
round of every fight, and rounds go on until one side is destroyed. So a unit
bought with ten health and almost no energy — seventeen points — walks into a
camper, absorbs ten rounds, dies, and leaves the camper on **zero energy**.
Under the old rule that camper still kept its owner in the game. Under the new
one it is out of the count. Game 38 left five of Ambush's ten units in
that state and game 42 left four, without killing any of them.

**It did not, by itself, end games.** A competent player never spends their
last point: all these bots hold at least one energy back, and one point of
energy is a whole veto on losing. What the rule really does is make
*spendthrift* strategies lose and give an attacker a second way to win. Notably
it broke Nomad, whose entire premise was to keep something alive at any cost —
it now has to keep something alive *with energy in it*.

**It made attack 10 brittle at the end.** A Reaper below ten energy cannot
attack at all, even a one-health straggler. Game 50 ran 140 turns: the reapers
killed eight of ten campers and then stood four squares from the last two with
eight and seven energy — enough to walk, never enough to strike. An attack-1
unit is never in that position, which is the compensation for losing every
duel it fights.

## What plays well under these rules

- **Never advance in two ranks.** A front rank that collides head-on does not
  move, and the rank behind walks onto it. Both armies did this in game 34 on
  the same turn; the one with five health survived it and the one with one
  health did not.
- **Buy attack 10 or attack 1, and know which endgame you are buying.** Attack
  10 wins every duel and cannot finish a game once its pocket falls below ten.
  Attack 1 can always land a blow and never wins a duel against equal health.
  Attack 2 (Sharpshooter, in the first series) remains the honest compromise.
- **Ten health and no energy is a weapon now.** It costs seventeen points and
  takes ten off whatever kills it.
- **Passivity is a guaranteed draw.** Every game with no casualties at all was
  a waiting attacker against a defender that never moves. Two armies that both
  decline to cross the frontier produce nothing, for sixty turns or a hundred
  and forty.
- **Deploying on your own frontier row is aggressive and often wrong.** It puts
  your whole army in contact on turn 2, before you know anything about what you
  are facing.

## Two bot defects the new setup exposed

Round 1 was played before these were found, and its results should be read with
them in mind. Both were in the bots, not the game:

- **Phalanx advanced away from the enemy.** Its advance direction was a
  constant from the open-board series, where it deployed on the south edge.
  Given the north half it marched to row 0 and stood there (game 24). Fixed to
  advance across the frontier from whichever side it holds — and it then won
  game 34 on turn 2.
- **An army with more units than columns got empty search lanes.** The lane
  splitter divided ten columns between eighteen units and handed eight of them
  nothing to sweep, so most of the Swarm never received an order (games 21, 24,
  29). Units now sweep the column they are standing in when they outnumber the
  columns.

## What this asks of the design

1. **The win condition now has teeth, and needs a partner rule.** Draining an
   opponent to zero is a real way to win, but a player who keeps one point in
   hand can never be finished off by exhaustion alone. If the intent is that
   spent armies lose, the rule wants either energy regeneration (so the
   condition is recoverable) or a threshold above zero.
2. **Zero-energy units are now permanent, unkillable terrain.** They cannot
   act, cannot be removed except by being destroyed, and no longer count for
   anybody. Ten of them in a corridor block it forever. Worth deciding whether
   a spent unit should be removed from the board rather than left on it.
3. **A draw by mutual refusal still has no name.** Four of these games had no
   casualties at all and ran the full sixty turns. `R7.2` gives a draw only for
   a mutual wipe-out; two armies staring at each other across a frontier is not
   covered.

## How the games were run

```
python matches/arena.py --game 34 --p1 matches/bots/phalanx.py \
       --p2 matches/bots/swarm.py --budget 200 --max-turns 60
```

`--budget` sets both players' point budgets. Deployment is split by default;
`--no-split` restores the open board. Each bot's army is written in own-half
coordinates — `(x, depth)`, where depth 0 is your own back row and depth 4 is
the row against the frontier — so one army definition deploys correctly from
either side. `matches/logs/game_N.log` is the turn-by-turn record.
