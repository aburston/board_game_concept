## Why

A two-player game today lets either player deploy anywhere on the board,
including right on top of where the other will start. There is nowhere that is
safely theirs to form up in, and the first turn can begin with the armies
already interleaved. A setup wants a side of the board that is yours to deploy
into, and a strip between the two sides that belongs to neither.

## What Changes

- During setup, when a game has **exactly two players**, the board is divided
  into a top half and a bottom half by rows. The player with the **lower
  number** may deploy only in the top half; the higher-numbered player only in
  the bottom half.
- When the number of rows is **odd**, the middle row is **neutral**: neither
  player may deploy in it. When it is even, there is no neutral row and the two
  halves meet.
- For any player count that is **not two** — one player, three, or more — there
  is no restriction: the whole board is open for placement.
- A deployment outside the placing player's allowed area is **refused**, at the
  client and again when the turn resolves, the same way a deployment the budget
  cannot pay for is.
- The allowed area is **published through the API**, per seat, so a client can
  show it without knowing the rule. The browser **greys out** the squares a
  seat may not deploy in while it is placing units, so the limit guides the
  hand rather than only refusing after the fact.
- Separately, and asked for alongside: a type with **no attack** may now have
  energy. With none it is still a wall; with energy it is a **scout** that
  moves like anything else and strikes nothing. What is still refused is
  energy 0 with an attack above it, and a type with any energy must still hold
  at least its movement cost in it.

## Capabilities

### New Capabilities

- `placement-zones`: which squares a player may deploy in during setup, as a
  function of how many players there are and how the board is sized, and that
  this area is published per seat and enforced when units are placed.

### Modified Capabilities

- `unit-types`: a type with no attack may hold energy - a scout - where the
  two zeroes previously had to go together.
- `web-interface`: the deploy board greys out the squares this seat may not
  place in, and says why, while it is deploying.
- `cli-output`: a `show placement` subject, so the placement area the browser
  reads is readable from a command line too — the one-contract rule every view
  is held to.

## Impact

- A new `domain/placement.py` computing a seat's allowed area from the board
  size and the registered player numbers, used both to refuse a placement and
  to publish the area, so the rule lives in one place.
- `service/games.py` (`deploy_unit`) and the turn resolution refuse a
  deployment outside the area, mirroring the budget refusal.
- `http/views.py` and `http/app.py`: a new `placement` view.
- `cli/*`: `show placement` for the roles, for parity.
- `http/static/*`: the deploy board greys out the disallowed squares.
- No storage format change: the area is derived from what is already stored
  (board size and the registered players), so nothing new is persisted and a
  game reloads to the same limits.
