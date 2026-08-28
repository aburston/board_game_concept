## Context

See `proposal.md` — Why.

The stall is one line. `service/turn.py`'s `has_started` answers "has the game
begun" with `bool(game.board.units)`, and the resolution that ends setup asks
it to avoid declaring every player out before anybody has deployed anything.
Contested deployments are refused in `_refused_deployments` *before* they reach
the board, so a first turn where every deployment collided leaves the board
empty, `has_started` false, nobody eliminated and nothing decided — while
`new_game` is already false for every player who committed, so no more units
can ever be added.

The interface keeps everything it draws in one `state` object and replaces the
whole screen on every change (`app.js` — "One state object, one render"). A
value held only in the DOM is therefore lost whenever anything else is done,
which is what happens to the deploy chooser and to the board-size fields.

## Goals / Non-Goals

**Goals:**

- A game can always be either played or finished, never neither.
- The armoury keeps a choice that is still being used across the redraw it
  causes.

**Non-Goals:**

- Changing the deployment rules. Two units deployed onto one square are still
  both refused, and that refusal is still only discovered at resolution.
- Reopening a committed setup. A player whose deployments were all refused is
  out; they do not get to place their army again knowing where the collisions
  were.
- Retroactively settling a game that is already stalled. The outcome is decided
  at resolution and stored, so a stalled game settles the next time its turn
  resolves.

## Decisions

**A game has begun once a player's committed setup has been resolved, not once
a unit has reached the board.** `has_started` becomes "any unit is on the
board, or any player has ever committed". The second half is durable and
already recorded: commit markers survive `clear_commits`, which is what tells a
player their setup is over, so there is nothing new to store and a game
restored from either backend answers what it answered before. At the
administrator's setup commit no player has committed yet, which is the case the
old guard existed for, so that resolution is still not a turn.

*Alternative considered:* pass "were there any orders this resolution" down
from `resolve`. It is not durable, so a stalled game would stay stalled even
after another resolution, and it says nothing at all when the turn is resolved
with no orders in it.

*Alternative considered:* let a player whose whole setup was refused deploy
again. It contradicts "a committed setup cannot be withdrawn or amended", and
the refusals name the contested squares, so a second attempt would be made
knowing where the opponent deployed.

**Elimination then follows the rule that is already there.** A player with
nothing standing is out; if that is everybody, `decide` records a draw. No new
outcome kind, and the existing "Draw — every player is eliminated" scenario is
what covers it.

**The two interface fixes go where the design already puts half-made work:**
`state.deployType` and `state.boardSize`, read when the form is built and
written on `change`/`input`, exactly as `state.design` and `state.unitName`
already are. The chooser falls back to the first type when what it held is
gone, and the size fields fall back to the board's own size when nothing has
been typed — so an accepted resize clears them rather than pinning a stale
number over the board.

**The armoury keys "nothing to set up here" on the seat's setup being closed**
(`new_game === false`) rather than on orders being in flight
(`unprocessed_moves`). Orders in flight is the narrower condition and stops
being true the moment the turn resolves, which is how a seat with a closed
setup was being offered forms whose every answer is a refusal.

## Risks / Trade-offs

- **A player whose army was entirely refused is eliminated without ever having
  played** → It is the only reading that ends the game, it matches the existing
  rule for a player who deployed nothing, and the refusals say exactly why.
- **The degenerate first turn is now numbered 1** → It is a resolved turn, and
  every record it publishes needs a turn to be attributed to. Nothing else
  changes: a normal first turn was already 1.
- **`has_started` now reads the repository as well as the board** → It is
  called from resolution and from the two judgements resolution makes, all of
  which already hold the game and read it.
- **A game already stalled is not settled by upgrading** → It settles at its
  next resolution. Nothing is lost, and the alternative is deciding games from
  a code path that only reads.
