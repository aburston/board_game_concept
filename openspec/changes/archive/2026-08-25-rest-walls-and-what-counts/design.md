## Context

See `proposal.md`. Q1 has been open since the rules were first written down,
and sixty-three played games are what closed it: forty-three of them ended with
both armies alive, immobile and holding energy they could not spend where it
was needed. The interesting design work is not "should energy come back" — the
games answer that — but the three decisions underneath it: what counts as doing
nothing, what a unit bought with no energy at all is, and what a player must
hold to still be in the game once zero energy is survivable.

## Goals / Non-Goals

**Goals:**
- An army that has won a fight can finish it, rather than stalling one energy
  short of the last enemy.
- Resting is a decision with a price — a turn — rather than a free tick.
- A unit deliberately bought as an obstacle is expressible, and is honestly
  priced.
- What ends a game is stated in terms of what a unit *is*, so it does not have
  to be restated every time energy rules change.

**Non-Goals:**
- Healing. Health does not come back; only energy does.
- Changing what a move or an attack costs.
- Removing a spent unit or a wall from the board. Both still block, and both
  are still killable; a square is only cleared by destroying what is on it.
- The draw by mutual refusal. Two armies that decline to engage still play out
  the whole game undecided (R7.2 covers only a mutual wipe-out), and that is
  left as it is.

## Decisions

### 1. Doing nothing is "no order **and** nothing paid for"

The obvious rule — "recover if you did not move" — is exploitable: a unit
ordered off the board pays nothing (R4.6), so it could be walked into the edge
every turn and refuel while pretending to march. The obvious repair — "recover
if your energy did not change" — has the same hole from the other side.

Requiring both closes it. A unit that was given an order has acted, whatever
the turn did with the order; a unit that paid for something has acted, whatever
it was ordered to do. What is left is a unit that was told to do nothing and
did nothing, which is the thing being paid for.

It also decides the case worth deciding deliberately: a unit that was attacked
and could not afford to strike back **rests**. Being hit is not an action. That
is what makes a defender's position recoverable, and it is what killed draining
as a tactic — a cost inflicted once cannot outrun a point a turn.

The snapshot is taken at the top of `Board.commit`, before `_move` consumes the
order it is read from (R3.3), and compared with what each unit holds after
`_fight`.

### 2. Rest is a phase of the turn, not a property of a unit

`Board.commit` grows a fourth phase, `_rest`, after `_deploy`, `_move` and
`_fight`. Putting it there rather than in `Unit` keeps the whole of a turn
readable in one place and keeps the ordering explicit, which the next decision
depends on. It emits a `rested` event like every other phase, so a turn still
narrates itself.

### 3. Rest happens before the game is judged

`service/turn.py` resolves the board and then asks who is eliminated. Rest is
part of resolving the board, so a unit that stood still is already back on one
energy when elimination is judged.

The alternative — judge first, then rest — makes the outcome depend on which
side of a boundary a unit's quiet turn fell, which is exactly the kind of rule
`R1.2` exists to keep out of the game.

### 4. A wall is attack 0 and energy 0, and each only with the other

The two zeroes are what make the unit coherent. Energy 0 with an attack above 0
is a unit that was charged points for an attack it can never pay for; attack 0
with energy above it is a unit that can walk about being harmless, which the
rules already allow at attack 1 and which would then also *rest*, making an
un-killable wanderer that keeps its owner in the game for ever. Requiring both
gives one thing with one meaning: health on a square.

Cost falls out of the existing rule — a type costs `attack + health + energy`
— so a wall costs its health, 1 to 10 points, and nothing has to be special
cased.

### 5. A wall lands no attacks, explicitly

`exchangeAttacks` skips a unit that cannot pay for its attack, and a wall pays
0 for an attack of 0, so it passes that check. It would then "attack" every
opponent for no damage, and a round that lands an attack is a round that
repeats (R5.6): the fight would never terminate. The skip is therefore on
`attack <= 0` rather than on affordability, and it is the first check in the
loop.

### 6. Elimination asks what a unit is, not what it holds

Earlier on this branch, elimination stopped counting units at zero energy. That
was right while energy never came back — a unit at zero was finished, and
counting it was counting a corpse. With rest it is wrong: zero is a state a
unit passes through, and three of the twenty replayed games were decided on
which turn the snapshot was taken rather than on the play.

So the test becomes whether a unit could ever act again, which is a property of
its **type**: `type_energy > 0`. Every ordinary unit qualifies however spent it
is; a wall never does. This states the wall rule and the rest rule in one
sentence and does not have to be revisited if the energy numbers change again.

The cost is that draining an opponent to zero is no longer a way to win. That
tactic was already dead — a defender that recovers a point a turn cannot be
drained by an attacker who spends its life getting there — so the rule is
following the play rather than leading it.

## Risks / Trade-offs

- **A defender nobody reaches now recovers for free**, while an attacker spends
  everything crossing the board. Holding still was already strong and is now
  stronger. If that proves too strong the lever is decision 1: require the
  quiet turn to be out of contact.
- **A wall is permanent ground.** It cannot be moved, cannot be worn down and
  never expires, so a line of them denies a corridor for the whole game to
  anyone who cannot afford to break it. The lever is price: a wall currently
  pays for its health and nothing else.
- **Games can now run longer.** Nothing exhausts itself into a stop, so a
  passive pairing plays out to the turn cap with both armies intact rather than
  grinding down. Eleven of the twenty replayed games ended that way.
