# The battle nobody saw

*A commentary on game 84 — Phalanx (192 points) against Swarm (198 points),
decided on turn 2.*

Thirty units were destroyed in a single turn at the middle of the board. The
game was over before either player had given a second order. And here is the
part worth sitting with: **neither player ever saw an enemy unit.** Not one.
Both transcripts run from deployment to `game over` without a single opposing
unit appearing in either player's view, because no unit on either side ever
exchanged attacks with an enemy.

Every casualty in this game was self-inflicted.

## The armies

Both doctrines were written before any game was played, and neither knows
anything about the other.

**Phalanx** — 12 units of attack 1, health 5, energy 10. Its whole idea is a
rank abreast: a line that sweeps a corridor without leaving a gap. Ten of them
across its own frontier row, and two more tucked behind the middle at (4,3) and
(5,3), because twelve units do not divide evenly into ten columns.

**Swarm** — 18 units of attack 1, health 1, energy 9. The cheapest body that can
walk and hit, on the theory that the game is won by the last player with
*anything* standing, so more win-conditions per point is the buy. Two full ranks
of nine, on rows 5 and 6.

Nearly identical budgets. Wildly different armies: 60 points of health on one
side, 18 on the other.

They deploy into their own halves, four rows apart, blind to each other.

```
row 3    . . . . P P . . . .        P   Phalanx   a1 h5 e10
row 4    P P P P P P P P P P
     ------------------------ the frontier
row 5    s s s s s s s s s .        s   Swarm     a1 h1 e9
row 6    s s s s s s s s s .
```

## The orders

Turn 2. Phalanx orders all twelve units **south**. Swarm orders all eighteen
**north**. Both bots are doing exactly what they were built to do: advance in
step, sweep the board.

Neither order is a mistake in itself. What follows is three rules meeting.

## What actually happened, one column at a time

Take column 2. Three units, in a line: `p3` at (2,4), `s3` at (2,5), `s12` at
(2,6). `p3` is ordered south into `s3`'s square. `s3` is ordered north into
`p3`'s square. `s12` is ordered north into `s3`'s square.

**First, R4.9.** Two units ordered into each other's squares collide. They do
not pass through one another, and *neither completes its move* — both pay the
fare and stay where they stand. So `p3` is still on (2,4) and `s3` is still on
(2,5), each one energy poorer for a step it never took.

**Then R4.8, which is normally a kindness.** A unit that follows another out of
its square arrives cleanly: if the unit in front is leaving, you simply take the
square. `s12` was ordered into (2,5) on exactly that basis — `s3` had orders to
leave. But `s3` did not leave. It could not: it had just been stopped by a
collision that was decided at the same instant, against an enemy `s12` cannot
see and does not know exists.

**So R5.7 settles it.** Friendly fire is total. Two units on one square fight,
regardless of who owns them, on exactly the same terms as enemies. `s3` and
`s12` are both attack 1, health 1. One round. Both destroyed.

Nine columns. Eighteen Swarm units. Every one of them spent exactly one energy
moving and one energy attacking, and every one of them died — killed by the unit
standing directly behind it, which had been ordered to follow it forward.

## The Phalanx made the same mistake

This is the part that makes the game worth writing up. Phalanx did not win by
out-thinking anybody. It did **precisely the same thing** — and the record says
so plainly.

`p11` at (4,3) was ordered south into (4,4), where `p5` stood. `p5` was ordered
south into (4,5) and had been stopped head-on by `s5`. So `p11` arrived on top
of `p5`, and they fought each other. Same at column 5, with `p12` and `p6`.

Four Phalanx units destroyed, by their own side, for the same reason.

The difference is health. At health 5 with attack 1, a pair needs **five** rounds
to kill each other instead of one — but five rounds is what they got, and all
four died anyway. What saved the Phalanx was not toughness. It was **only having
two units in its second rank**. The Swarm had nine there, and lost all
eighteen.

The seven Phalanx units in columns 0–3 and 6–8 have nothing behind them, so
nothing walked into them. They end the turn at full health, having spent one
energy each on a move that never happened, without ever meeting an enemy.

And `p10`, on column 9? The Swarm deployed nine units per rank across ten
columns, so column 9 was empty. No collision, no follower, nothing in the way.
`p10` is the only unit on the board that carried out the order it was given.

## The ledger

| | Phalanx | Swarm |
|---|---|---|
| Deployed | 12 (192 pts) | 18 (198 pts) |
| Destroyed | 4 | 18 |
| Killed by the enemy | **0** | **0** |
| Killed by their own side | 4 | 18 |
| Units that saw an enemy | 0 | 0 |
| Units that completed their move | 1 | 0 |
| Standing at the end | 8 | 0 |

Player 1 wins on turn 2.

## What the losing player was looking at

The Swarm's last view before the result is eighteen units, every one of them
listed `moving north`, full health, nine energy, in two tidy ranks. The next
line in its transcript is:

```
commit complete
waiting for turn to complete...
game over: player 1 wins on turn 2
```

It never learned what killed its army, because nothing that killed its army was
an enemy. Under R6.2 you see an opponent by *fighting* one, and no Swarm unit
ever traded a blow with a Phalanx unit. The information that would have
explained the defeat does not exist anywhere in that player's view of the game.

## What this says about the rules

Three rules, each obviously right on its own:

- **R4.9** stops units teleporting through each other. Without it, two armies
  ordered at each other would swap places and end up behind each other's lines.
- **R4.8** stops a column of your own units jamming: if the one in front is
  leaving, you may step into the square it is vacating.
- **R5.7** stops stacking being a free action, and it is what makes a square a
  real piece of contested ground.

Put them together and you get a rule nobody wrote: **a rank that is stopped
head-on becomes a wall your own second rank walks into.** R4.8's promise — the
unit in front is leaving — is made when orders are given and broken when the
turn resolves, and the unit behind has already committed on the strength of it.

That is a genuinely good property for a wargame to have. It is exactly the sort
of thing that should punish a general, and it punishes this one severely. But it
has two edges worth noticing:

1. **It is invisible from inside.** A player cannot see the enemy rank they are
   about to collide with, cannot know their front rank will be stopped, and
   therefore cannot know their second rank is walking into a knife. Both bots
   here were reasoning correctly from everything they were allowed to know.
2. **It scales with the wrong statistic.** How badly this hurts depends entirely
   on the health of the units doing it to themselves — 18 dead at health 1, 4
   dead at health 5. The cheap-and-numerous doctrine is the one that suffers
   most, and it suffers most at exactly the moment it looks strongest: at the
   frontier, in formation, on the advance.

Whether that is a feature or a defect is a design decision rather than a bug —
nothing here breaks a stated rule, and the whole thing is perfectly
deterministic. If it is a feature, it wants documenting, because it is not
derivable from any single rule. If it is not, the lever is R4.8: a follower could
be told to check whether the unit in front actually vacated, and to stay put
rather than arrive on top of it.

## The practical advice

For anyone writing a doctrine for this game: **do not advance in two ranks into
ground you cannot see.** Move a rank, or move a column, but never order a unit
into a square that one of your own units has only *promised* to leave. The
promise is not binding, the enemy gets a vote, and the vote is counted before
yours is.
