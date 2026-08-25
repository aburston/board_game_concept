# Twenty games with rest and walls

The third series. Same board, same two hundred points, same split deployment as
`matches/RESULTS-FRONTIER.md`, with two more changes to the game itself:

1. **A unit that takes no action recovers 1 energy** at the end of the turn
   (**R3.9**). No order, and nothing paid for while the turn resolved — being
   attacked and unable to strike back still counts as doing nothing. It never
   recovers past the energy its type was designed with, and rest happens after
   combat and *before* the game is judged, so a unit that spends its last point
   acting is out before it can recover it.
2. **A type may have attack 0 and energy 0 together** (**R2.10**) — a **wall**.
   Health standing on a square: it can never move, never strikes, never rests,
   costs its health and nothing else, and blocks like anything else. Because it
   holds no energy it does not keep its owner in the game, so an army of walls
   has already lost.

Both are engine changes with the specs, the rules document and the tests moved
to match. Between them they answer **Q1**, which has been open since the rules
were first written down.

## What changed: nine decisions in twenty games

The previous series decided **two games in thirty**. This one decided **nine in
twenty**, and none of them were close-run: every winner finished with units
still in play, and six of the nine left the loser with nothing standing on
the board at all.

| # | player 1 | player 2 | result | in play, start → end | before |
|---|---|---|---|---|---|
| 61 | Swarm | Grinder | **player 2 wins, turn 59** | 18v6 → 0v5 | undecided |
| 62 | Assassin | Hunter | **player 1 wins, turn 18** | 6v4 → 2v0 | undecided |
| 63 | Mixed | Turtle | undecided | 6v10 → 6v10 | undecided |
| 64 | Phalanx | Swarm | **player 1 wins, turn 2** | 12v18 → 8v0 | won, turn 2 |
| 65 | Hunter | Grinder | undecided | 4v6 → 4v1 | undecided |
| 66 | Attrition | Tide | undecided | 6v16 → 4v3 | undecided |
| 67 | Duellist | Ambush | undecided | 6v10 → 6v10 | undecided |
| 68 | Sponge | Ambush | **player 2 wins, turn 12** | 12v10 → 0v8 | undecided |
| 69 | Sponge | Duellist | undecided | 12v6 → 6v2 | undecided |
| 70 | Attrition | Duellist | undecided | 6v6 → 3v1 | undecided |
| 71 | Drain | Ambush | **player 2 wins, turn 12** | 10v10 → 0v5 | undecided |
| 72 | Drain | Turtle | undecided | 10v10 → 1v7 | undecided |
| 73 | Reaper | Ambush | **player 1 wins, turn 30** | 2v10 → 2v0 | won, turn 30 |
| 74 | Reaper | Turtle | **player 1 wins, turn 43** | 2v10 → 1v0 | undecided at 140 |
| 75 | Bulwark | Reaper | undecided | 3v2 → 1v1 | new pairing |
| 76 | Bulwark | Swarm | undecided | 3v18 → 2v4 | new pairing |
| 77 | Bulwark | Drain | **player 1 wins, turn 2** | 3v10 → 3v0 | new pairing |
| 78 | Swarm | Bulwark | undecided | 18v3 → 4v2 | new pairing |
| 79 | Sharpshooter | Attrition | undecided | 6v6 → 2v3 | new pairing |
| 80 | Bulwark | Duellist | **player 2 wins, turn 14** | 3v6 → 0v3 | new pairing |

"In play" counts units on the board holding energy. A wall never holds any, so
Bulwark's ten walls are never in that count — its three fighting units are.

## Rest: armies stop freezing, so hunts finish

Every game in the two previous series ended the same way — both armies standing
still on a board they could no longer cross, holding energy they were saving for
a fight they could not reach. Rest ends that. A unit that stops for a turn gets
a point back, so a doctrine that keeps a reserve now marches at roughly half
speed *for ever* instead of stopping dead.

- **Game 74 is the clearest case.** Reaper against Turtle was undecided in the
  last series even when the cap was raised to 140 turns: the two champions
  killed eight of ten campers and then stood a few squares from the last two
  with eight and seven energy — enough to walk, never the ten they needed to
  strike. Under rest they wait, recover to ten, and finish it on turn 43.
- **Game 61** went the same way from the other side: Grinder's attack-1 tanks
  had frozen at their energy floor with four Swarm units alive. Now they keep
  grinding, and the last one falls on turn 59.
- **Game 62**, Assassin against Hunter, had never produced a casualty after
  turn 7. Now it resolves on turn 18.

What it does *not* fix is two armies that decline to engage. Games 63 and 67 —
a waiting attacker against a defender that never moves — are unchanged, and
under rest the defender is strictly better off than before: it recovers for
free while nobody comes.

## Rest kills draining

Draining was the tactic the zero-energy win condition invented: walk a
ten-health, low-energy unit into a defender and make it spend its whole pocket
killing you. It does not survive regeneration. A camper that spends ten energy
in a fight now gets it back a point a turn while the next sponge is still
walking over, so the drainer runs out of bodies before the defender runs out of
pocket.

Both drain matchups reversed outright: **games 68 and 71 are wins for Ambush on
turn 12**, having been the drainer's best results in the previous series. The
lesson is that a cost you inflict once is worthless against an opponent who
recovers, unless you can inflict it faster than they heal.

## Walls: a hundred points that ends a two-hundred-point army

Bulwark lays ten walls of ten health across its own frontier row — a hundred
points, the whole width of the board — and keeps two attack-2 fighters and a
scout behind them.

**Game 77 is the shortest decisive game in three series.** Drain's ten units
each stepped into a wall on turn 2. Each spent 1 energy on the move and then
attacked, and attacking costs a point a round: nine rounds later every attacker
stood at **zero energy** and every wall stood at **two health**, undestroyed.
All ten attackers were out of the count at the end of the turn they first
moved, and the walls that beat them cost half what they did.

```
s.........        s  Bulwark's scout
..........        K  Bulwark's fighters, untouched
...K..K...        w  ten walls: 2 health left, and they never had energy
..........        d  ten attackers: full health, no energy, out of the game
wwwwwwwwww
dddddddddd        game 77, end of turn 2
..........
```

That is the wall's whole argument: **it converts an attacker's energy into
nothing at all.** It has no energy to lose, so it cannot be drained; it has no
attack, so it never spends; and every point of damage it absorbs was paid for
out of somebody else's pocket.

The counter is attack, and specifically attack 10. In **game 80** Duellist's
champions broke through in one round a wall — ten energy for ten health, the
same price anyone pays, but paid in a single round rather than ten — and were
through the line and onto the fighters by turn 14. Against attack 1 a wall is
worth roughly its own weight in enemy energy; against attack 10 it is worth
exactly its cost and no more.

## What plays well under these rules

- **Retreat and rest is now a real move.** A champion below its attack value is
  not finished, it is out of position. Walking two squares back, waiting three
  turns, and coming again is a better plan than any of these bots had.
- **Never spend your last point in a fight you started.** Rest happens before
  the game is judged but a unit that acted does not rest, so the turn you go to
  zero is the turn you can be eliminated.
- **Draining is dead; killing is not.** Anything that works by imposing a
  one-off cost has to out-race a point a turn.
- **Walls stop attack-1 armies and inconvenience attack-10 ones.** Ten points
  of wall costs an attack-1 attacker ten energy and an attack-10 attacker ten
  energy — but the first spends ten turns' worth of pocket and the second
  spends one round.
- **A wall line still needs an army behind it.** Walls hold no energy, so they
  keep nobody in the game. Bulwark spends half its points on ground it denies
  and half on the three units that are actually playing.

## What this asks of the design

1. **Rest makes a defender who is never reached strictly stronger.** It
   recovers for free while an attacker spends everything crossing the board.
   Worth deciding whether rest should require a turn *out of contact*, or
   whether a unit that was attacked should recover at all.
2. **A wall is unkillable ground for anyone who cannot afford to break it.** Ten
   of them across a corridor, at ten points each, cannot be moved, cannot be
   worn down, and never expire. If that is too strong, the lever is the cost:
   a wall currently costs its health and nothing else.
3. **The draw by mutual refusal is now the only undecided ending left** — and
   with rest it is permanent rather than exhausted. Eleven of these twenty games
   ended that way, most of them with both armies intact. `R7.2` still gives a
   draw only for a mutual wipe-out.

## How the games were run

```
python matches/arena.py --game 77 --p1 matches/bots/bulwark.py \
       --p2 matches/bots/drain.py --budget 200 --max-turns 60
```

Unchanged from the previous series: real `bgcserver` and `bgcclient` sessions,
each bot handed its own player view and nothing else, the half-board rule
refereed by the harness because the game does not have it. The rest rule and
walls are in the game itself. `matches/logs/game_N.log` is the record of each.
