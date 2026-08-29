## Context

See `proposal.md` — Why. And the determinism invariant: a rule must be
decidable from the board and the orders alone, never from the order a list
holds its members in.

Deployment is refused in two places today, and this rule joins them at both.
`service/games.py`'s `deploy_unit` refuses what the budget cannot pay for
before it places anything, so a refusal leaves the game untouched. And
`service/turn.py`'s `_refused_deployments` refuses again at resolution — a
contested square, or a budget a loaded file never passed through a client to
have checked. The budget is the model to follow: checked at the client and
again at resolution, from a single helper.

Views are built per seat: `read_view` loads the game as the acting number, so
a builder is handed a session that already knows who is asking. A new view must
also be shown by a command-line role, or `test_web_flow`'s one-contract test
fails: every view the browser reads, a role can show.

The board draws with `y` as the row and `x` as the column, `y = 0` at the top.
So "the top half" is the low-`y` rows.

## Goals / Non-Goals

**Goals:**

- One helper computes a seat's allowed area, and both the refusal and the
  published view read it, so the rule is stated once.
- The area is a pure function of the board size and the registered player
  numbers.
- A game that is not two-player is the null case of that one function, not a
  branch that skips it: the same helper, view and refusal run, and the answer
  they give is "the whole board". Behaviour for a non-two-player game is
  therefore identical to today's, reached by the same calls.

**Non-Goals:**

- Restricting anything but a two-player game. Every other count is the whole
  board, which is what the helper returns, so the callers carry no `if two
  players` of their own — they always compute the area and always honour it,
  and for a non-two-player game the area happens to be everything.
- Restricting columns, or movement. This is where a unit may be *deployed*
  during setup; once it is on the board it moves by the movement rules.
- Persisting anything. The area is derived from what is already stored.

## Decisions

**A `domain/placement.py` module, beside `budget.py`.** It exposes the area a
seat may deploy in, as a pure function of `(player_number, player_numbers,
size_x, size_y)`. The split for exactly two players:

- Sort the two numbers; the lower takes the top band, the higher the bottom.
- `m = size_y`. If `m` is even: top is rows `0 .. m/2 - 1`, bottom is rows `m/2
  .. m - 1`, no neutral row. If `m` is odd: `mid = m // 2` is neutral, top is
  rows `0 .. mid - 1`, bottom is rows `mid + 1 .. m - 1`.

For any other player count the area is every row — the null case, returned by
the same function rather than by a caller choosing to skip it. The module
answers two things from that: `allows(number, numbers, x, y, size_x, size_y)`
for the refusals, and `area(number, numbers, size_x, size_y)` for the view —
the same band expressed as the rows the seat may use, so the two can never
disagree. Because "the whole board" is a value the helper returns and not an
absence of a call, `deploy_unit`, the resolution and the view all run the same
code for every game; a non-two-player game simply has every square in its
area, and nothing downstream can tell it was ever a special case.

*Alternative considered:* put the rule in `board-model` beside occupancy. It is
a higher-level setup rule that depends on the player count, not a property of
the grid, so it sits better in its own module the way the budget does.

**The published area is the allowed rows and the board size.** Columns are
unrestricted, so the rows a seat may use are the whole of its area; the view
returns `{size_x, size_y, rows: [...], restricted: bool}`, where `rows` is the
list of `y` a seat may deploy in and `restricted` is false when it is the whole
board. The browser greys any square whose row is not in `rows`; `restricted`
drives the caption. A per-square list was considered and rejected as ten times
the payload for a rule that never varies along a row.

**Observer and administrator are told the whole board.** They do not deploy, so
their area is every row. This falls out of the helper: with player 1000 or 0
not among the two placing numbers, and their session reading every player, the
"exactly two players" branch still restricts *placing* seats — so the view
returns the whole board for a watcher rather than pretending they have a half.
The view builder passes the acting number, and a number that is not one of the
two placing players is given the whole board.

**Enforcement mirrors the budget, at both points.** `deploy_unit` refuses an
out-of-area placement before it places anything, with a message naming the
reason — outside your half, or the neutral middle row. `_refused_deployments`
adds the same check to what it already refuses, so a loaded player file is
bound too, and the player is told which units were refused and why, exactly as
for a contested square.

**The CLI shows it.** `placement` joins the roles' show subjects, printed as a
table and available as JSON like every other subject, so the one-contract test
holds and a prompt can see the limit the browser draws.

## Risks / Trade-offs

- **A half can be empty on a board too small to be meant** → For two players on
  an odd board of one row every row is neutral, and on any board the halves are
  non-empty at two rows or more. Setup offers 2–10, so a real game never hits
  the empty case; if a board is sized below that some other way, the seat is
  simply told it may place nowhere, which is a sizing mistake rather than this
  rule misbehaving.
- **The area depends on the full set of players, read at deploy time** → A seat
  registered or removed before setup is committed changes who the two players
  are, and the area moves with it. That is correct: the rule is about the game
  as it stands when the unit is placed, and setup is where players are still
  being added and removed.
- **A new view means a new CLI subject** → Wanted, not merely tolerated: the
  limit should be as visible to a prompt as to a browser.
