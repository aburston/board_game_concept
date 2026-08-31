## Context

See `proposal.md` — Why. What shapes the approach is the interface's own
discipline, which these six changes have to fit inside:

- **One state object, one render.** `app.js` holds every piece of screen state
  and `render()` replaces the whole of `<main>`; nothing outside `render`
  touches the DOM. Half-made choices (a design being typed, the deploy
  chooser, a board size) live in `state` precisely because a redraw would
  otherwise throw them away.
- **The page is a client of the served contract and of nothing else.**
  `api.js` is the only file that speaks to the server, and
  `tests/test_web_flow.py` holds every `kind` it builds to a command the
  service can rebuild *and* the CLI grammar can type. A command kind added for
  the browser alone fails those tests by design.
- **What the interface does is asserted against its source.** There is no
  build step and no browser in the test suite: `tests/test_static_serving.py`
  reads the static files and asserts what they contain (the compass, the
  energy ring, the take-back key), and `tests/test_web_flow.py` drives the
  contract exactly as `api.js` does.
- **Responsive behaviour is CSS's, not JavaScript's.** `style.css` already
  decides by media query what a narrow screen and a coarse pointer get; there
  is no viewport measurement or resize listener anywhere in the page.

Relevant contract facts: there is no bulk-removal command and no
relocate-a-unit command — `add_unit`, `remove_unit`, `set_flag`, `move` and
`hold` are what setup and ordering are made of. `remove_unit` takes a unit
back only while the seat's setup is uncommitted, and taking back the flag
carrier drops that designation with it.

## Goals / Non-Goals

**Goals:**

- Add the six behaviours in `specs/web-interface/spec.md` without a new
  endpoint, a new command kind, or a change to any Python module.
- Keep every existing way of doing each thing working, so that the keyboard
  route and the pointer route are alternatives rather than replacements.
- Keep the state-and-render discipline intact, with one narrow, documented
  exception for the drag gesture.

**Non-Goals:**

- Reworking the play screen into real tabs on a wide screen: the toggle is for
  the width where the two panes do not fit, and a wide screen keeps the
  two-column layout it has.
- Dragging a unit more than one square to order a multi-square move: a move
  order is one square, and the drop rule follows the rules rather than
  softening them.
- Any change to how a turn resolves. Nothing here touches `domain/` or
  `service/`, and the determinism invariant is not in play.

## Decisions

### Pointer events for the drag, not HTML5 drag-and-drop

`dragstart`/`drop` does not fire for touch on any mobile browser, and its
behaviour over SVG children is uneven. Pointer events (`pointerdown`,
`pointermove`, `pointerup`, with `setPointerCapture` on the unit's group) are
one code path for mouse, pen and finger, and `touch-action: none` on the board
stops the page scrolling under a finger that is dragging a piece.

A drag is told from a click by distance: under a few pixels of movement the
gesture is a click and the existing select-or-order handler runs; past it, the
pointer-up resolves as a drop and the click is suppressed. Without that
threshold every tap on a unit would become a one-pixel drag, and selecting a
unit — the thing done most often — would break.

*Alternatives considered:* HTML5 drag-and-drop (rejected: no touch); a
long-press to "pick up" then a tap to "put down" (rejected: slower than the
tap-then-compass route that already exists, and it invents a gesture nobody
asked for).

### The drop square is worked out from the board's own geometry

`board.js` already draws on a fixed 44px grid inside a `viewBox`, and each
square and unit group carries its `data-x`/`data-y`. The drop square is the
pointer's position mapped through the SVG's screen CTM to board coordinates.
That is one calculation in the file that owns the grid, and it stays correct
if the board is ever scaled by CSS — which reading a bounding rectangle and
dividing by 44 would not.

`board.js` reports the gesture and decides nothing: it calls back an
`onDrop(unit, x, y)` the screen supplies, exactly as `onUnit` and `onSquare`
are supplied now. Whether a drop is a deployment, an order, or a refusal is
the screen's business, which keeps this file — the one that "draws what the
view gives it and never decides what to conceal" — free of rules.

### The dragged unit follows the pointer without a re-render

Moving a unit's `<g>` transform during `pointermove` is a deliberate exception
to "nothing outside `render` touches the DOM", and the only one. Re-rendering
per pointer move would rebuild the SVG under the pointer, discarding the
element that holds the pointer capture and ending the drag on the first move.
The exception is bounded: the transform is intermediate visual state, no state
object is written during the gesture, and the drop is followed by the usual
command-then-`loadSeat`-then-`set` path, so what is finally drawn comes from
the server as it always does. This is written down in `board.js` beside the
handler, since nothing enforces the rule but the reading of it.

### Re-placing a unit is `remove_unit` then `add_unit`, with the original put back on refusal

There is no relocate command, and adding one would mean a new node in
`service/commands.py`, a line in the CLI grammar, and a new verb in the
contract — for something that is exactly the two setup decisions the player
would otherwise make by hand.

The two calls are not atomic, so the order matters and so does the failure
path: the target square is checked against the seat's own view first (occupied,
or outside the rows `placement` publishes), so the common refusals never reach
the server; if `add_unit` is nonetheless refused, the unit is immediately
re-added at the square it came from and the refusal is what the player is
told. If the unit carried the flag, `set_flag` is re-sent after the successful
re-placement, because taking a unit back drops the designation with it.

Nothing published is at risk either way: this happens only while the seat's
setup is uncommitted, which is the only state `remove_unit` is accepted in.

*Alternative considered:* a `move_unit` command in the contract. Worth doing if
re-placement ever needs to be atomic or typeable at the CLI; not worth a new
verb in three layers for a browser convenience.

### Clearing the board is the same `remove_unit`, once per unit

Sequentially, over the seat's own deployed units, then one `loadSeat` and one
redraw — rather than a redraw per unit, which would flicker a board being
emptied. A budget-sized army is a handful of units, so the calls are few. If
one is refused the sequence stops and says what was refused, leaving the rest
deployed rather than continuing over an unexpected state.

`window.confirm` asks first, as the commit does. It is the page's existing
answer to "this cannot be undone by pressing it again", and a bespoke
confirmation card would be the second one on the screen.

### The toggle is state plus a media query, with no measuring

`state.pane` holds `'board'` or `'trays'`. The play screen always renders both
panes and the switch; `style.css` decides, at the breakpoint where the two
columns stop fitting, that the pane not chosen is hidden and the switch is
shown. Above that width the switch is hidden and both panes are visible
whatever `state.pane` says.

So there is no `matchMedia`, no resize listener, and no width in the state —
the page cannot get out of step with the layout, because the layout is the
only thing that knows the width. It also matches how the keyboard-help card is
already withheld from a device with no keyboard. The switch is an ordinary
button carrying `aria-pressed` and naming the view it shows, so the keyboard
route works with nothing extra.

### The commit control is one function called from two places

`renderCommit(game)` already exists in `play.js`; the board pane calls the same
function beneath the compass. One definition means the confirmation, the call,
the re-read of the seat and the "committed, waiting to resolve" state cannot
diverge between the two — which is the failure a second, hand-written commit
button would eventually become.

The `c` key clicks `button.primary`, and there will now be two. Both are the
same action, and the first in document order is the board's, which is where
the hand pressing `c` is looking. The key handler is left alone; a note beside
it records why it is still correct.

### The orders tray gains two columns and reuses `health()`'s shape

Energy becomes `now/full` drawn the way `health()` draws it, from
`designOf(game, unit)` — a helper shaped after `health()` rather than a second
copy of its logic. Attack comes off the unit as the Forces table already reads
it. The tray goes from six columns to eight; wide content already scrolls
inside its card on a narrow screen, which is what
`test_wide_content_scrolls_inside_its_card` holds.

## Risks / Trade-offs

- **A drag that is really a tap, or a tap that is really a drag** → the
  movement threshold, with a test of the gesture's two ends: a click still
  selects, and a drop past the threshold does not also fire the click handler.
- **`remove_unit` succeeds and `add_unit` fails** → the target is checked
  before either call, and the original placement is restored if the add is
  refused anyway. If the restore also fails (the server has gone), the player
  is told plainly which unit is no longer deployed rather than being left to
  find out from the board.
- **The flag designation lost in a re-placement** → re-sent after the move,
  and covered by a scenario in the spec and a test through the contract.
- **Two `button.primary` on the play screen** → both are the same commit; the
  first in document order is the board's. Should a third primary ever be added
  the `c` key would need a real selector, so the handler carries the note.
- **A toggle that hides something a player needs** → the choice is CSS-scoped
  to a width where only one pane fits anyway, and the switch names what it
  would show. Nothing is hidden at a width where both fit.
- **Source-level tests can assert only that the page says the words** → the
  behaviour behind each change is driven through the contract in
  `tests/test_web_flow.py` where it can be (clearing, re-placing, ordering);
  what remains browser-only (the gesture itself, the media query) is asserted
  against the source as the existing UI tests are.
