# The toll booth

*A commentary on game 97 — Bulwark against Drain — and on game 100, where the
same wall line meets a different attacker.*

A hundred points of wall — ten units of ten health, laid across the whole width
of the board — stopped a hundred-and-ninety-eight-point army dead on turn 2. Not
"held it up". Stopped it: every attacker spent every point of energy it owned,
did not take a single square, and was thrown back to where it started.

Six turns later the line was gone and the army walked through it.

Both of those sentences are true, and the gap between them is what a wall is
actually worth.

## The armies

**Bulwark** — ten **walls** (attack 0, health 10, energy 0) along its own
frontier row, and behind them two swords of attack 2, health 10, energy 28, plus
a cheap scout. Half its points buy ground it denies; the other half buy the three
units that can actually play. A wall is the strangest thing in the game: it
cannot move, cannot strike, cannot be worn down by attrition and never recovers
anything, because its type was designed with no energy to recover to. It is
health standing on a square, for the price of its health.

**Drain** — ten units of attack 1, health 10, energy 9, one to a column, bought
on the theory that the way to beat a defender is to make it spend its pocket
killing you. Ten health each, and almost no energy: walk in, absorb, and let the
defender pay.

Drain is, in other words, the worst possible army to send at a wall. It is built
to take energy off an enemy, and a wall has none.

## Turn 2: the perfect repulse

All ten Drain units step forward into the wall line at once.

Each pays 1 energy for the move. Each then attacks — and attacking costs the
attacker its attack value per round, so at attack 1 each round costs 1 and deals
1. They keep going until they cannot pay: **eight rounds each, eight energy
each**, until every attacker stands at exactly **zero**.

Every wall ends the turn on **2 health**, undestroyed.

And then the rule that makes it a repulse rather than a stalemate: a contested
square with more than one survivor is **undecided** (R5.8), and every survivor
that moved in goes back where it came from. Both survived — the wall because it
had two health left, the attacker because a wall cannot hurt it. So all ten
attackers were returned to the squares they started from, with nothing in their
pockets.

```
row 4    W W W W W W W W W W     ten walls, 2 health each, untouched by anything
     ------------------------
row 5    d d d d d d d d d d     ten attackers, full health, zero energy,
                                 standing exactly where they began
```

A hundred points had emptied a hundred-and-ninety-eight-point army's pockets in
a single move, taken eighty points of damage doing it, and given up no ground at
all. If the game ended there it would be the most efficient defensive action in
any of the sixty-three games played.

The game did not end there.

## Turns 3 to 8: the toll is only a toll

A unit that takes no action recovers a point of energy (R3.9). Drain's units
were built with almost no energy, so they have almost nothing to lose by waiting
— and waiting is now a move.

| Turn | What happens | Walls | Attacker energy |
|---|---|---|---|
| 2 | First assault: 8 rounds each | 10 alive, 2 hp each | 90 → **0** |
| 3–4 | Rest | 10 alive, 2 hp each | 0 → **20** |
| 5 | Second assault: move and one round each | 10 alive, **1 hp** each | 20 → **0** |
| 6–7 | Rest | 10 alive, 1 hp each | 0 → **20** |
| 8 | Third assault | **0 alive** | 20 → **0** |

The line cost the attacker **130 energy over eight turns** — more than the 90 it
started the game with, the difference made up by four turns of standing still.
It cost Bulwark a hundred points and the whole width of its half of the board.

Then the walls were gone, the attackers stood on the line, and Bulwark's two
swords had to fight ten units on their own. They killed three over the next fifty
turns; the game reached the cap with seven attackers loose in Bulwark's half and
two swords still trying. Undecided.

**A wall is a toll booth, not a fortress.** It converts an attacker's energy into
time, at a fixed and knowable rate, and that is the whole of it. Against an
opponent who cannot afford the toll it is a wall. Against one who can — or one
who can simply sit down and wait until they can — it is a delay you have paid a
hundred points for.

## Game 100: the scout that killed a wall

The same Bulwark line, against **Duellist**: four champions of attack 10, health
10, energy 20, and two cheap scouts.

On turn 2 something happens that says more about walls than the whole of game 97.
Duellist's scout `s1` — **one health, twenty points, attack 1** — walks into the
ten-health wall on column 0 and destroys it single-handed. Eleven energy: one for
the step, ten for ten rounds of attacking. It takes **no damage at all**, because
a wall never strikes back. It then takes the square.

That is the fact that governs everything about this unit type: **a wall cannot
hurt you, so there is no risk in attacking one — only cost.** Anything in the
game can kill a wall, given the energy. A one-health scout demolishes a ten-point
wall as safely as a champion does; the champion is merely faster, one round
instead of ten, for the same ten energy.

So Duellist did not batter the line down. It did not need to. It broke three
walls in fourteen turns and spent the rest of its attention on the three units
behind them:

| Turn | |
|---|---|
| 2 | a scout kills the wall on column 0 and takes the square |
| 4 | Bulwark's scout is destroyed |
| 7 | a second wall falls |
| 10 | Duellist loses a scout |
| 11 | a third wall falls; **Bulwark's first sword is killed** |
| 12 | Duellist loses a champion |
| 14 | **Bulwark's second sword is killed** — and Bulwark is out |

Bulwark finished that game with **seven walls standing**, at full health, holding
their squares — and lost, because none of them could act (R7.1). Seven-tenths of
its wall line survived the game and contributed nothing to the end of it. Half
the army's points were still on the board and none of them counted.

## What a wall is worth

Three numbers describe the unit completely.

- **It costs its health.** Attack 0 and energy 0 add nothing, so a wall of ten
  health costs ten points.
- **It costs its attacker about its health in energy**, whatever the attacker is:
  ten rounds at attack 1, one round at attack 10, ten energy either way.
- **It gives its owner nothing else.** No damage, no movement, no recovery, and —
  since R7.1 asks whether a unit could ever act again — no claim on the game
  staying alive.

So the wall's exchange rate is one point of your money for one point of their
energy, and the only variable is *time*. Against attack 1 the toll is paid ten
turns at a time, in one-round instalments if the attacker is poor. Against attack
10 it is paid instantly and the line is breached the moment somebody decides to
breach it.

The corollary, which game 97 and game 100 make from opposite directions: **a wall
line's real product is turns, and turns are only worth something if you have
something to do with them.** Bulwark bought six turns in game 97 and had two
swords to spend them with, which was not enough. It bought fourteen in game 100
and spent them losing the same two swords.

## What this says about the design

Walls work. They are coherent, they are cheap, they price cleanly, and they made
two of the most interesting games in the series. But three things are worth
deciding deliberately rather than by default:

1. **A wall is only a delay, and rest is what made it so.** Before energy
   regeneration, an attacker who emptied itself on a wall was finished — game 97
   under the old rules was a Bulwark win on turn 2, and that was the artefact
   that exposed the elimination rule. Now the same attacker rests and comes back.
   That is the right answer, but it means a wall's value depends entirely on a
   rule in a different part of the game, and halving `REST_GAIN` would double
   every wall's worth without touching walls at all.
2. **Nothing can be hurt by attacking a wall.** There is no bad trade available
   to the attacker and therefore no decision — only arithmetic. If a wall is
   supposed to be a *threat* as well as an obstacle, it needs something back; if
   it is supposed to be pure ground, it is exactly right as it is, and that is
   worth writing down as a choice.
3. **Half an army can be points that cannot lose the game for you and cannot win
   it either.** Bulwark's seven surviving walls in game 100 are the clearest
   picture of R7.1 in the whole series: a player eliminated with 70 points of
   perfectly healthy units standing on the board. That reads as correct — but it
   is the kind of correct that a new player will meet as a nasty surprise, and it
   belongs in the rules as prominently as it now is in R2.10.

## The practical advice

**Buying a wall is buying turns.** Count them before you buy: a wall of health
*h* buys you roughly *h* energy of somebody else's time, which is `h` turns
against an attack-1 army that must rest between blows, and one round against a
champion. Then ask what you will do with those turns, because the wall will not
do anything with them for you — and make sure that whatever you plan to do with
them is not so small that losing it loses you the game while your walls are still
standing.
