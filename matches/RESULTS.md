# Thirteen games on a ten by ten board

> **Played under the rules as they stood before this branch changed them.**
> Energy never came back, a unit at zero energy still kept its owner in the
> game, and there were no walls. These thirty-odd games are what argued for
> changing all three, and they would not play the same way today — the current
> rules are in `GAME_RULES.md`, and the series played against them is
> `matches/RESULTS-REST-AND-WALLS.md`. The series in between, at two hundred
> points across a split board, is `matches/RESULTS-FRONTIER.md`.

Thirteen two-player games, played through the real CLI roles — one
`bgcserver` resolving turns, one `bgcclient` session per player for the whole
game, an observer writing the log. Every order in every game was typed into a
player's own session, and every bot was handed its own player view and nothing
else: an enemy unit reached a bot only when the visibility rules (R6.2) put it
there, which is to say only when it had just been fought.

The five games the exercise asked for are games 1 to 5. Games 6 to 10 replay
the same question with the doctrines revised in light of what the first five
showed; games 11 to 13 are controls on the explanation.

## The results

| # | player 1 | player 2 | result | units, start → end | losses | last casualty |
|---|---|---|---|---|---|---|
| 1 | Swarm | Grinder | undecided | 9v3 → 5v3 | 4 v 0 | turn 6 |
| 2 | Assassin | Hunter | undecided | 3v2 → 3v2 | 0 v 0 | never met |
| 3 | Mixed | Turtle | undecided | 2v4 → 1v4 | 1 v 0 | turn 10 |
| 4 | Phalanx | Swarm | undecided | 6v9 → 6v4 | 0 v 5 | turn 6 |
| 5 | Hunter | Grinder | undecided | 2v3 → 2v1 | 0 v 2 | turn 17 |
| 6 | Attrition | Tide | undecided | 3v8 → 2v5 | 1 v 3 | turn 7 |
| 7 | Duellist | Ambush | undecided | 3v5 → 2v3 | 1 v 2 | turn 7 |
| 8 | Nomad | Attrition | undecided | 3v3 → 1v3 | 2 v 0 | turn 5 |
| 9 | Tide | Ambush | undecided | 8v5 → 1v5 | 7 v 0 | turn 10 |
| 10 | Attrition | Duellist | undecided | 3v3 → 2v2 | 1 v 1 | turn 6 |
| 11 | Marathon (400 pts) | Ambush | undecided | 3v5 → 1v3 | 2 v 2 | turn 22 |
| 12 | Sharpshooter | Attrition | undecided | 3v3 → 2v1 | 1 v 2 | turn 6 |
| 13 | Marksman (400 pts) | Ambush | **player 1 wins on turn 39** | 3v5 → 3v0 | 0 v 5 | turn 39 |

In game 3 both players lost a unit before the game began: the Mixed player and
the Turtle player both claimed (0,4) for a deployment, and both were refused
(R3.5). In game 2 the two armies never found each other at all.

Twelve of the thirteen ran to the sixty-turn cap undecided, and in nine of
them the last casualty fell by turn ten. The games did not end because
somebody was winning slowly; they ended because both armies had stopped being
able to do anything at all, usually by turn twenty, and then stood on the
board for forty turns.

## What the strategies were

Each is a fixed doctrine — what to buy, where to put it, where to walk —
written before any game was played and never changed inside a game.

| Strategy | The army, for 100 points | The bet |
|---|---|---|
| Swarm | 9 × (a1 h1 e9) | most bodies; every fight is a trade and I have more to trade |
| Grinder | 3 × (a1 h10 e20) | ten health absorbs ten attackers; attack 1 is the cheapest killer per point of energy |
| Assassin | 3 × (a10 h1 e21) | attack 10 destroys anything in one round, so trade up: 32 points kills a 50-point champion |
| Hunter | 2 × (a10 h10 e30) | one champion that wins every duel and can afford to look for one |
| Turtle | 4 × (a1 h10 e10) + 1 × (a1 h10 e5), never moves | invisible until stepped on, full pockets when it is |
| Phalanx | 5 × (a1 h5 e10) + reserve | a rank abreast sweeps without leaving a gap |
| Mixed | scout (a1 h1 e30) + assassin (a10 h1 e21) + tank (a1 h10 e20) | buy information with a cheap unit, spend the kill on something worth it |
| Tide | 8 × (a1 h1 e10) | the swarm with the legs it was missing |
| Attrition | 2 × (a1 h10 e30) + scout (a1 h1 e16) | buy energy, not statistics |
| Duellist | 2 × (a10 h10 e20) + scout (a1 h1 e18) | champions hold the centre; the scout brings them work |
| Ambush | 4 × (a1 h10 e10) + 1 × (a1 h5 e10), never moves | the turtle, on the squares a sweep has to cross |
| Nomad | 3 × (a1 h1 e30), never fights | a unit that survives is a veto on losing |
| Sharpshooter | 2 × (a2 h10 e28) + scout | attack 2 kills a ten-health unit in five rounds instead of ten |
| Marksman | 3 × (a5 h10 e100) on 400 points | the control: the same hunt with the arithmetic put right |

## Why every hundred-point game was undecided

Three rules multiply together, and the product is a stalemate.

**Finding somebody costs a point of energy a square, and there is no other
way to look.** An enemy is revealed by being fought (R6.2), not by being
adjacent, so searching the board means walking onto every square that might
hold something. A hundred points buys at most about 94 energy — every unit
also has to pay at least 1 for attack and 1 for health — and a ten by ten
board is 100 squares. An army cannot walk over the board it is playing on
even once, let alone find five things dispersed on it.

**Energy never comes back (Q1), so an army has exactly one march in it.**
Every doctrine here froze: Tide at turn 10, Attrition's tanks at turn 21,
Marathon's survivor with 41 energy it had nothing left to spend on because
its two partners were dead. Twelve games ended with both sides standing still
on a board they could no longer cross.

**Two equal units kill each other (R5.11), so attrition never nets anything.**
A fight is decided by `ceil(health ÷ attack)`, and attack 1 against health 10
is ten rounds in both directions: two corpses. Six of the strategies here were
attack 1 against health 10, and every fight between them was a mutual funeral.
That is what makes the defensive builds unbeatable rather than merely
expensive: killing a camper with an identical unit costs you the unit.

Game 11 is the control on the second and third of those. Marathon had **four
times the budget** — 300 energy against Ambush's 50 — and still could not
clear five stationary campers, because at attack 1 against health 10 it killed
them by dying on them. It traded two of its three units for two of their five
and its survivor walked away with 41 unspendable energy.

Game 13 is the control with the arithmetic corrected. The same 400 points and
the same doctrine, but at attack 5: two rounds to kill a ten-health defender,
ten energy a kill, two damage taken. It cleared the whole camp and won on turn
39 with all three units alive, 21 health and 141 energy still in hand.

So the stalemate is not the bots being timid. At a hundred points a side, on
this board, **wiping out an opponent who spreads out and holds still is not
affordable**, and the win condition (R7.2) is the only way a game ends.

## What actually plays well, on this evidence

- **Attack 1 is a trap against health 10.** One extra point of attack halves
  the rounds you need and is the difference between killing and dying. In game
  12 the attack-2 champions killed a tank and a scout for the loss of their
  own scout, and both walked away — the same doctrine at attack 1 (game 10)
  traded evenly.
- **Buy energy.** Statistics decide fights you have found; energy decides how
  many you find. Round one's armies averaged 10 energy a unit and stopped
  moving on turn 10.
- **Standing still is strong, and boring.** Across the three hundred-point
  games they played, Turtle and Ambush lost two units between them and killed
  nine — Ambush took nothing at all off eight Tide units and destroyed seven of
  them. A unit that never moves keeps every point of energy for the one fight
  it is walked into, and an attacker that has walked ten squares to reach it
  does not. It is also a strategy that cannot win: neither ever killed a unit
  that had not come to it.
- **Deploying is blind, and collisions are real.** In game 3 the Mixed player
  and the Turtle player both claimed (0,4); both deployments were refused
  (R3.5) and both started a unit down.
- **Do not stack your own units.** Friendly fire is total (R5.7), so two of
  your units on one square kill each other on the same terms as enemies. Every
  bot here checks its own orders for that before committing them.

## Suggestions this raises for the design

These are the two open questions in `GAME_RULES.md`, met from the playing
side rather than the design side.

1. **Q1 (energy never returns) decides more of the game than the statistics
   do.** Regenerating even 1 energy a turn for a unit that took no action
   would keep armies mobile and let a game reach a conclusion instead of a
   freeze. Alternatively, a hundred points is simply too small an army for a
   hundred-square board: the same doctrines on a 6 × 6 board, or at a
   400-point budget, do reach a result.
2. **Q2 (identical units annihilate) makes low attack strictly worse than it
   looks.** Because a fight costs the attacker `attack` energy per round and
   takes `ceil(health ÷ attack)` rounds, the energy spent per kill is about
   the victim's health *whatever* your attack is — so a higher attack is
   nearly free, and there is little reason to ever buy attack 1. The
   statistics are less of a choice than they appear.
3. **A draw by exhaustion has no name.** R7.2 gives a draw only when the last
   players are wiped out together; a game where nobody can move is simply
   never decided, and both clients sit at a prompt forever. Something that
   ends a game in which no unit can act — or an agreed draw — would close it.

## How the games were run

```
python matches/arena.py --game 1 --p1 matches/bots/swarm.py \
                       --p2 matches/bots/grinder.py --max-turns 60
```

`matches/arena.py` starts a real `bgcserver`, opens one real `bgcclient` per
player and leaves it open for the whole game, and types into it: `show ...
json` to read that player's view, `move ...` and `commit` to give orders.
Nothing touches the game's storage or its domain objects, so every rule in the
game — visibility, budgets, simultaneous resolution, combat — was enforced by
the game and not by the harness. `matches/logs/game_N.log` is the turn-by-turn
record of each game; the raw session transcripts are written alongside it.

The one liberty taken: the observer role, which sees everything (R6.5), is
read once a turn to write the log. It is read after both players have already
given their orders, and its output never reaches a bot.
