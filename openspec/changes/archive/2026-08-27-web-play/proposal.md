## Why

The game can only be played by people willing to run a terminal. `bgcclient`
is a good REPL and it is the whole of the presentation tier: to play, you
install a Python package, open a shell, and type `add type Cross X 1 10 10`
from memory. `design.md` has described a website since before the layer split
— "a player wants to see their pieces", "a player wants to place pieces on the
board" — and none of it exists.

The API is ready for one. `http/app.py` serves the read side as JSON,
`http/views.py` returns render-agnostic data, commands serialise through
`as_record`/`from_record`, drafts survive a session, and `wait/turn` and
`wait/commit` are already long-poll endpoints. Once `accounts-and-membership`
lands, the API also knows who is asking. What is missing above it is a
browser.

Two things are missing beside it. There is no way to ask **which games exist**
— the API is per-game, and a game is a directory somebody knew the number of —
so a lobby has nothing to list and "join a game" has nothing to join. And
there is no way to **create** a game except by running `bgcserver` in the right
directory. Both are small, both are server-side, and neither is worth a change
of its own.

## What Changes

- **A game registry over HTTP.** `GET /games` lists the games with their
  status, board size and turn number; `POST /games` creates one. The listing
  is **derived** from the games tree rather than tracked in a table, the way
  elimination is derived from the board and a player's spend from their units:
  a registry that is written down is a registry that can disagree with what is
  on disk.

- **A web interface, served by the same Flask app.** One page, five screens:
  the lobby, the armoury, the board, the wait, and the outcome. It is a client
  of the JSON API and of nothing else — no server-rendered HTML, no template
  layer — so that anything it cannot do is a gap in the API rather than a gap
  in a private back channel.

- **No build step.** Vanilla ES modules and one SVG board component, served as
  static files. The board is at most 10x10, so the diffing a framework is for
  buys nothing here, and the animation a framework is also for is a CSS
  transition on an SVG transform. The repository stays one language with one
  toolchain and CI is unchanged.

- **The armoury shows the trade the budget exists to make.** A type's cost is
  the sum of its statistics, so the cost moves as the statistics are chosen,
  and the budget meter says what is left before a unit is deployed rather than
  after it is refused.

- **The orders tray shows what an order costs before it is final.** A move
  costs a quarter of the unit's maximum health, rounded up, and today that
  number is invisible until the energy is gone. The tray names the fare beside
  each order and the unit's reserve beside that. A unit given no order is shown
  as resting for a point, because under `turn-commit` that is a choice and not
  an empty row.

- **Committing is final, and the interface says so before it is done, not
  after.** `turn-commit` allows no withdrawal and no amendment. Then the wait
  names who is still to commit, through the long-poll endpoints that exist.

- **What the last turn did is shown as a change, not as a log.** Units that
  moved, units destroyed, and every order the turn would not carry out — which
  `/state` already returns as `rejected` and `dropped`. The board's own
  transition from the previous view to this one is the animation.

- **A contact that drops off the board says why.** `visibility` wipes every
  sighting at the start of each resolution, so an enemy fought last turn simply
  vanishes. Unexplained, that reads as a defect; the interface marks it as lost
  contact rather than letting a unit blink out.

- **A seat is in the URL, so two tabs are two seats.** `accounts-and-membership`
  lets one account hold several seats in a game. The interface follows the
  path rather than holding a current seat, which is what makes playing both
  sides work at all.

- **Playable from the keyboard.** Select a unit, order it with the arrow keys,
  commit. A grid of squares that can only be clicked is a grid half the people
  who would play it cannot use.

Not in this change: an animated, event-by-event replay of a resolution.
`turn_events` is written on every resolution and read by nothing, it exists in
the SQLite backend only, and it is unfiltered — serving it to a player as it
stands would hand them every unit on the board and undo `visibility`. Filtering
it is real work and it is worth its own change; what this one shows is the
board changing and the orders that were refused, which is what a player needs
to take the next turn.

Also not in this change: SSE or WebSocket push, a spectator interface beyond
the observer account watching a game, a chat, a game history or archive
browser, ratings, accounts for the bots in `matches/`, and mobile-specific
layout beyond the interface being usable at a small width.

## Capabilities

### New Capabilities

- `game-registry`: which games exist and what state each is in, that the
  listing is derived rather than tracked, and creating a game over HTTP.
- `web-interface`: the five screens, what each must show and let a person do,
  that it is a client of the JSON API only, that the seat is carried in the
  path, that the costs a player decides by are shown before the decision, that
  lost contact is explained, and that the game is playable from the keyboard.

### Modified Capabilities

None. The web interface is a new surface over an unchanged API, and the
registry is behaviour the HTTP tier did not have rather than behaviour it had
differently. No rule of the game changes and no existing role changes.

## Impact

- **HTTP**: `http/registry.py` — new; `GET /games` and `POST /games`.
  `http/app.py` — serves the static directory, and mounts the registry.
  `http/views.py` — unchanged; the interface consumes the views that exist.
- **Static**: `http/static/` — new. `index.html`, `app.js` (state and
  routing), `board.js` (the SVG board), `lobby.js`, `armoury.js`,
  `orders.js`, `style.css`. Served by Flask, no build step, no package
  manager.
- **Service**: `service/registry.py` — new; what games exist and what state
  each is in, derived by opening each game. No change to `service/games.py`,
  `service/turn.py` or `service/identity.py`.
- **Storage**: no change. The registry reads the games tree through the
  repositories that exist and writes nothing of its own.
- **Domain**: no change.
- **CLI**: no change. The roles keep working exactly as they do.
- **Tests**: `tests/test_game_registry.py`, `tests/test_static_serving.py`,
  and `tests/test_web_flow.py` — a whole game driven through the same JSON
  calls the page makes, which is what keeps the interface from needing a
  private back channel.
- **Docs**: `README.md` — how to reach the interface and what it offers.
  `MODULE_DESCRIPTION.md` — the new modules and the static directory.
  `ARCHITECTURE_OPTIONS.md` — step 5 done, and which of §6's options was
  taken and why. `GAME_RULES.md` is **not** touched.

## Dependencies

This change depends on `accounts-and-membership`. Without it there is nothing
for the lobby to know a person by, no seat to join, and no guard — a browser
would be able to ask for any player's view by editing the address bar, which
is the defect that change exists to close.
