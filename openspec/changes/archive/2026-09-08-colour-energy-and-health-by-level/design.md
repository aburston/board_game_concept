## Context

See `proposal.md` — Why. The geometry is what matters here, in the board's own
coordinates where a square is 44 units:

- `SQUARE = 44`, `RING = SQUARE / 2 - 11 = 11`, so a unit's ring is a circle of
  radius 11 about the centre of its square at (22, 22).
- The ring is stroked at width 2, so it occupies **10 to 12** from the centre.
- The energy arc is a second circle at `r: RING` stroked at width 4, so it
  occupies **9 to 13** — straddling the ring and painting over all of it. That
  is the defect.
- The health bar sits above the ring, not around it: `x: 8, y: 3`, 28 wide and
  3 high, so it occupies **y 3 to 6**.
- The order arrow starts at `RING + 2` = **13** from the centre and reaches to
  `SQUARE * REACH` = 34.3, past the edge of the square on purpose.
- Half a square is 22, so anything drawn about the centre has to stay inside
  that to remain in its own square.

## Goals / Non-Goals

**Goals:**

- The ring drawn whole and uncovered at every level of energy.
- One band function, used by both the arc and the bar, so the two cannot
  drift apart as thresholds are tuned.
- Colours that work in both schemes and never carry the meaning alone.

**Non-Goals:**

- Any change to what energy or health are, what a move costs, or what the
  server publishes.
- Re-laying-out the unit. The glyph, the health bar's position and the ring
  all stay where they are; only the arc's radius, the arrow's start and the
  colours change.
- Colour-blind-safe hue choice beyond red/amber/green. The user asked for RAG
  and the length of the arc and bar carries the same information, so hue is a
  second channel rather than the only one.

## Decisions

### Where the arc goes: `RING + 3`, stroked at 3

The arc becomes a circle at `r: RING + 3` = 14, stroked at width 3, so it
occupies **12.5 to 15.5** from the centre. That gives:

- the ring's outer edge at 12 and the arc's inner edge at 12.5 — clear, with
  half a unit between them;
- the arc's outer edge at 15.5, so the top of the arc is at `y = 6.5`, half a
  unit clear of the health bar which ends at `y = 6`;
- 6.5 units of slack to the edge of the square.

Alternatives: `RING + 4` at width 4 was tried on paper first and puts the top
of the arc at 4.5, which runs under the health bar. Growing `RING` itself was
rejected — it moves every unit's ring and the glyph inside it, to fix
something that is not the ring's fault.

### The order arrow starts outside the arc

The arrow's shaft starts at `RING + 2` = 13, which is now inside the arc. Left
alone, an ordered unit would have its arrow drawn across its own energy — the
same defect one ring further out. The start moves to `RING + 6` = 17, just
clear of the arc's outer edge at 15.5. The arrow keeps its length and its
head: it reaches to 34.3 either way, and only its tail is trimmed.

### One function turns a share into a band

`band(share)` returns `'full'`, `'low'` or `'spent'`, and both the arc and the
bar take their class from it. Two call sites, one rule. The alternative —
each computing its own comparison — is how the existing code came to have
`share <= 0.25` written twice, once for energy and once for health, which is
also why the boundaries could have drifted and nobody would have noticed.

Boundaries: green above two thirds, amber from a third to two thirds, red at a
third or below. `> 2/3` and `> 1/3` as strict comparisons, so a unit at
exactly a third is red and a unit at exactly two thirds is amber — a boundary
belongs to the worse band, because a player deciding whether to commit a unit
should not be told it is fine when it is on the line.

### Colour lives in tokens, not in the rules

Three tokens — `--level-full`, `--level-low`, `--level-spent` — defined on
`:root` and again in the dark-scheme block, beside the tokens already there.
The band classes reference them and nothing else.

They are **not** `--mine` / `--warn` / `--theirs`. Those three mean whose a
thing is and whether it needs attention, and reusing them would make a healthy
enemy's bar the same green as "yours", which is the confusion this change is
trying to remove from the ring. Separate names also say plainly, to whoever
reads the stylesheet next, that a level is not an owner.

Light: a light green, an amber, and a red that all hold up at 3 units wide on
a light ground. Dark: the same three lifted, as the existing dark tokens are.

### Ownership is left to the ring and the glyph

Removing the owner's colour from the arc and the bar takes two of the four
things that said whose a unit is. What remains is the ring — solid in your
colour, dashed in an enemy's — and the glyph, which is drawn in the owner's
colour. Both are now more legible than they were: the ring is no longer
painted over, which is the whole point of the change.

On a watched board the player-numbered rules colour the ring, the glyph and
`health-left`. The `health-left` rules there are dropped, so a watched board
reads levels the same way as a seat's own and identity still comes from the
ring and the glyph, which those rules keep.

## Risks / Trade-offs

- **A healthy enemy is now green** → It could read as "yours" for a moment.
  The ring is dashed for an enemy and its glyph is in the enemy's colour, and
  both are now unobscured. The alternative — RAG on your own units only —
  was offered and rejected: seeing which enemy is nearly finished is worth
  more than a fourth redundant signal of ownership.
- **Red/amber/green is the worst pairing for the commonest colour blindness**
  → Length carries the same information on both the arc and the bar, the
  figures are in the tray and in every unit's description, and the bands
  differ in lightness as well as hue. This is a second channel added to
  existing ones, not a channel replaced.
- **The arc is thinner (3 rather than 4)** → It is also longer, being at a
  bigger radius, so the area is close to unchanged; and it no longer competes
  with the ring underneath it.
- **Two more things to keep inside a 44-unit square** → The arithmetic is
  written down above and asserted in the tests, so the next thing drawn round
  a unit has the numbers to check itself against.

## Migration Plan

None. No stored state, no contract change, no schema; a radius and a
stylesheet, served as files. Rolling back is reverting the commit.
