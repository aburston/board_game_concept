## Why

The energy arc is drawn at the same radius as the unit's ring — `r: RING`,
the ring's own radius — so it is painted directly over it. The ring is what
says whose the unit is: solid in your colour for yours, dashed in theirs for
an enemy, and by player number on a watched board. A four-pixel arc laid on
top of a two-pixel ring hides that, and worst at exactly the moment it matters
— a unit with most of its energy left covers most of its own ring.

The two things drawn round a unit also carry no reading of their own. Energy
and health are each drawn in the owner's colour with one warning state at a
quarter, so a unit at 90% and a unit at 30% are the same colour and only the
length differs. Length is the hardest thing to judge on a 44-pixel square, and
it is being asked to carry the whole message.

## What Changes

- The energy arc moves **outside** the ring, at a larger radius, so the ring
  is drawn whole and its colour is never covered. Nothing else on the unit
  moves, and the arc stays inside its square.
- The energy arc is coloured **red, amber or green by what is left**, not by
  whose the unit is: green above two thirds, amber between a third and two
  thirds, red at a third or below.
- The **health bar is coloured the same way**, by the same bands, replacing
  the owner's colour and the single `critical` state.
- This applies to **every unit** — yours and an enemy's alike — so a player
  can see which enemy is nearly finished. Whose a unit is is still said by
  the ring and the glyph, which keep the owner's colour and the dashed
  outline for an enemy.
- On a **watched** board, where units are coloured by player number, the arc
  and the bar read by level like everywhere else; the ring and the glyph go
  on carrying the player's colour.
- Three colour tokens are added for the bands, defined in both the light and
  the dark scheme.

Non-goals: no change to what energy or health *are*, to what a move costs, to
when a unit is inert, or to any number the server publishes. This is what the
board draws, and nothing below `http/static/`.

## Capabilities

### New Capabilities

None. Two existing requirements about what a unit shows are being sharpened.

### Modified Capabilities

- `web-interface`: the requirement on the energy ring gains where the arc is
  drawn — outside the ring, covering nothing — and both it and the health
  requirement gain the levels the colour has to distinguish. Today neither
  says anything about colour, so a board that drew every level alike
  satisfied both.

## Impact

- `src/board_game_concept/http/static/board.js`: the arc's radius and the
  class it is given; the health bar's class. Both come from one function that
  turns a share into a band, so the two cannot drift apart.
- `src/board_game_concept/http/static/style.css`: three colour tokens in both
  schemes, the rules for the three bands, and the removal of the
  owner-coloured `.energy` / `.health-left` rules and the `.spent` and
  `.critical` states they carried.
- `tests/test_static_serving.py` and `tests/test_board_selection.py`: whatever
  asserts on the current shapes.
- No change to `domain/`, `service/`, `storage/`, the CLI, or the HTTP
  contract, and none to the determinism invariant: this is a stylesheet and a
  radius.
