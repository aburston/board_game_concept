## Context

See `proposal.md` — Why.

`service/turn_feed.py` decides what each seat reads. `for_seat` keeps an entry
where `named & owned` — one of the seat's own units is in it — **or** where
`named <= visible`, every unit named is one the seat's published view holds.
The second clause is the one being withdrawn.

The board is drawn by `http/static/board.js` from the units a seat is given.
Each unit is a group holding a ring, its symbol, a health bar and — where it
is under orders — an arrow. The direction buttons are built by `play.js`'s
`renderDirections`, which the orders tray appends.

## Goals / Non-Goals

**Goals:**

- What another player's units did to each other never reaches a third seat.
- Ordering happens in one place, where the board is.
- A unit's energy is legible from the board.

**Non-Goals:**

- Changing what a seat is told about **its own** units, which is unchanged.
- Changing the observer, which reads the whole log by right.
- Hiding that a square this seat fought in was contested. It was in the
  fight; the square-level entry stays, and is what the marks on the board are
  drawn from.
- Moving the orders table. What moves is the direction controls; the table of
  units and their costs stays where it is.

## Decisions

**`for_seat` keeps an entry only where the seat owns a unit named in it.** One
clause deleted, and `visible` with it: the parameter goes, because nothing
left in the function reads it. Callers pass the seat's own unit names, which
resolution already has in hand. Square-only entries keep the rule they have —
kept where the seat was told about something else at that square — which now
means "a square this seat had a unit in", exactly what the marks want.

*Alternative considered:* keep the clause and filter only `attacked` entries.
It would leave `engaged`, `destroyed` and `retreated` disclosing the same
fight in different words, which is the sort of half-rule that reads as a bug.

**The directions move into the board card, under the board.** `renderDirections`
stays where it is and is appended by `renderBoardCard` instead of by the
orders tray. The tray keeps the table, the spend line, the barrier and the
commit button; where it used to hold the directions it now says nothing,
because the board says it.

**The ring is drawn as a proportion of its circumference.** A second circle
over the first, using `stroke-dasharray` against the ring's circumference and
`stroke-dashoffset` to start it at the top, so the drawn share is the share of
energy left. `board.js` is given `energyOf(unit)` the way it is already given
`healthOf`, returning `{now, full}`; where `full` is not known — a seat that
has not met the type — the plain ring is drawn and nothing is claimed.

*Alternative considered:* colour the whole ring on a scale from green to red.
It says "low" without saying how low, and the board already uses colour for
whose unit it is; a proportion says the number.

## Risks / Trade-offs

- **A seat sees less than it did** → That is the change. What it sees of its
  own units is untouched, and a fight it was in still reads in full from its
  side.
- **The ring now carries two things: ownership by colour, energy by extent** →
  The health bar is a separate mark above the unit and stays, so nothing that
  was legible becomes ambiguous.
- **An enemy unit's energy is drawn from what contact disclosed** → `energyOf`
  reads the type from what this seat has met. A seat that has not met the
  design gets a plain ring rather than a proportion computed from a maximum it
  is not entitled to know.
