## Context

See `proposal.md` — Why. `UnitType.preCommit` resolves a move down one of three
branches, chosen by what is standing on the destination: empty, a square
already claimed by other movers this turn, or a standing unit. The first two
charge the movement cost and refuse the move when the unit cannot pay it. The
third did neither.

## Goals / Non-Goals

**Goals:**

- One rule about paying for a move, applied to every move.

**Non-Goals:**

- Changing what combat costs. An attack still costs the attacker its attack
  value per round, and that is charged where it always was, in
  `resolveContest`.
- The order in which movement is resolved. Two units approaching each other
  along a row still pass through one another rather than meeting, because a
  unit placed in contention can still move out of it when its own order is
  resolved afterwards. That is a rule nobody has written down, and deciding it
  is its own change; this one only makes the cost of a move the same for both
  of them.

## Decisions

### 1. Both tests, then charge

Engaging now requires two things: enough energy to attack, which is the
existing rule, and enough to pay for the move, which is the rule every other
move already followed. Both are tested against the energy the unit has before
it moves, and the cost is taken only if it engages.

Testing the attack against energy the move has already reduced was the
alternative. Rejected: `unit-movement` says the engagement test is about a unit
"with energy at least equal to its attack" moving in, which is the energy it
sets out with, and combat re-tests what it can afford each round anyway, so the
second test would have been the same one twice with a worse reading.

### 2. A unit that can attack but not arrive stays put

A unit whose energy covers its attack but not the movement cost no longer
engages. It cannot move, and engaging is moving.

This is a behaviour change at the margin, and the only one this change makes
beyond the charge itself. It follows from the existing rule that a move is
refused when it cannot be paid for; the alternative would be a standing
exception nobody asked for.

## Risks / Trade-offs

- **A unit reaches a fight with one less energy than it used to, so a contest
  that was winnable may now be lost** → That is the point: arriving cost
  something it was not being charged for. The change is small — one point at
  the energy levels the game uses — and it applies to both sides of any
  exchange, which is what makes an even fight even.

- **Existing games in progress have units holding energy they were never
  charged** → Nothing migrates, and nothing needs to: the difference is in what
  the next move costs, not in what is stored.
