## 1. Which games exist

- [ ] 1.1 Add `service/registry.py`: `games(base_path, backend)` returning one
      record per game under the games tree — number, state (being set up,
      being played, decided), board size or `None`, turn number, registered
      player numbers, and outcome where there is one. Derived by opening each
      game, with nothing written down (design.md — "The registry is derived,
      not tracked").
- [ ] 1.2 `create(base_path, backend, gameno)` making a new empty game through
      the repository's own `ensure()`, refusing where a game of that number
      exists. No board, no players, nothing played.
- [ ] 1.3 A game whose storage is unreadable is reported as unreadable rather
      than failing the whole listing — one bad game directory must not make
      the lobby unusable.
- [ ] 1.4 Add `tests/test_game_registry.py`: an empty tree lists nothing; a
      game made by a command-line role is listed without registration; a game
      with no board reports no board size; a decided game reports its outcome;
      a removed game stops being listed; an unreadable game does not stop the
      others being listed.

## 2. The registry over HTTP

- [ ] 2.1 Add `http/registry.py`: `GET /games` and `POST /games`, mounted by
      `create_app`. Both behind the guard `accounts-and-membership` adds —
      any authenticated account may list, only the administrator may create.
- [ ] 2.2 `GET /games` reports what `service/registry.py` gives, plus each
      game's seats and who holds them, read from the account store. A game is
      listed whether or not the caller holds a seat in it.
- [ ] 2.3 `POST /games` refuses an identity that is not the administrator with
      403, and a game number already in use with 409.
- [ ] 2.4 Extend `tests/test_game_registry.py` over HTTP: listing needs a
      token; a player may list and may not create; the administrator may
      create; creating a number that exists is refused and the existing game
      is untouched.

## 3. Serving the interface

- [ ] 3.1 Add `http/static/` and serve it from `create_app`. Everything under
      it is a plain file: no build step, no package manager, nothing generated
      (design.md — "No build step").
- [ ] 3.2 `index.html` — one page, loading `app.js` as a module. No markup that
      the page does not need to start.
- [ ] 3.3 `style.css` — layout and theme in custom properties, a dark and a
      light scheme, and no colour carrying meaning on its own.
- [ ] 3.4 Add `tests/test_static_serving.py`: the page is served, the modules
      are served with a JavaScript content type, and a path outside the static
      directory is refused.

## 4. State and routing

- [ ] 4.1 `app.js` — **one state object and one `render()`**, with no code
      outside `render` touching the DOM. State this in the file's own comment,
      because nothing else will enforce it (design.md — "No build step").
- [ ] 4.2 Routing on the address: `/` the lobby, `/play/<gameno>/<number>` a
      seat, `/setup/<gameno>/<number>` the armoury. The seat is read from the
      address every time and never held as shared state (design.md — "The seat
      is in the path").
- [ ] 4.3 One `api.js` holding every call the page makes, each named for the
      contract endpoint it calls, so the whole surface the interface depends on
      can be read in one file.
- [ ] 4.4 A 401 sends the person to log in; a 403 is reported as the refusal it
      is rather than as a failure to load.

## 5. The lobby

- [ ] 5.1 `lobby.js` — the games, each with its state, turn number and seats;
      seats show taken with the username or open; the games this person holds
      a seat in are marked as theirs.
- [ ] 5.2 Taking an open seat, and reporting the refusal where it was taken
      first — then re-reading the listing so it shows what is now true.
- [ ] 5.3 A game being set up says how many seats are still open.
- [ ] 5.4 The administrator gets creating a game, and reaching any game as the
      administrator; the observer gets watching any game.

## 6. The armoury

- [ ] 6.1 `armoury.js` — designing a type with attack, health and energy, and
      the cost shown as their sum **as they are chosen** rather than when the
      type is defined.
- [ ] 6.2 The budget, the spend and the remainder from the `players` view, and
      each type marked affordable or not against the remainder.
- [ ] 6.3 Deploying by choosing a type and a square, with the refusal shown
      against the deployment and the board unchanged when it is refused.
- [ ] 6.4 Committing setup, with what it means said before it is done.
- [ ] 6.5 Verify a type costing more than the whole budget is still defined —
      defining is free — and is shown unaffordable rather than deployable.

## 7. The board

- [ ] 7.1 `board.js` — one `<svg>`, squares drawn from `board_view`'s
      dimensions, one `<g>` per unit positioned by `transform`, keyed by owner
      and name.
- [ ] 7.2 Movement between turns is a change of `transform` with a CSS
      transition. No timeline, no frame loop, no library.
- [ ] 7.3 Draw only what the view holds, and **never** decide what to conceal:
      everything the view gives has already been filtered where `visibility`
      filters it (design.md — "The board is one SVG").
- [ ] 7.4 Compare the previous view with the new one to mark units that moved
      and units that are gone, and to notice an enemy that has dropped out.
- [ ] 7.5 Contact lost is said in words, and nothing is drawn on the square the
      enemy was last seen on — a remembered position would give a player what
      the rules withhold.
- [ ] 7.6 The legend from `board_view`, so a symbol drawn is a symbol
      explained.

## 8. Orders and committing

- [ ] 8.1 `orders.js` — the tray: one row per unit, what it is ordered to do,
      what that will cost, and the unit's energy beside it.
- [ ] 8.2 The fare is `ceil(max_health / 4)`, read from the unit's type rather
      than computed in the page from a rule the page has restated. Verify it
      against `show types` for the same unit.
- [ ] 8.3 A unit under no order is shown resting and recovering a point, not as
      an empty row.
- [ ] 8.4 An order the unit cannot pay for is marked and still committable —
      the turn decides what happens, not the interface.
- [ ] 8.5 Re-ordering a unit replaces its order in the tray, so one unit shows
      one order.
- [ ] 8.6 Uncommitted orders come back after a reload, from the draft the
      contract already keeps. Verify by reloading mid-turn and finding the
      tray as it was.
- [ ] 8.7 Committing asks for confirmation, saying it cannot be withdrawn or
      amended, and afterwards no order can be given, changed or withdrawn.

## 9. Waiting and what the turn did

- [ ] 9.1 The wait uses `wait/commit` and `wait/turn`, re-issued when they
      return unmet, and names who has not committed. Eliminated players are
      not named.
- [ ] 9.2 The interface moves on by itself when the turn resolves — no reload.
- [ ] 9.3 After a resolution: the units that moved shown moving, and every
      refused order of this player's from `rejected` and `dropped`, each
      naming the unit, its square and the reason.
- [ ] 9.4 What is shown describes the turn just resolved and does not
      accumulate.
- [ ] 9.5 The outcome when the game is decided — the winner or a draw — with
      orders and commits withdrawn and the final board still shown. An
      eliminated player is told they are out and may still watch.

## 10. The keyboard

- [ ] 10.1 Every unit selectable, every direction orderable and the commit
      reachable from the keyboard alone.
- [ ] 10.2 Moving about the board square by square, with what is reached shown.
- [ ] 10.3 The selection shown by more than colour — an outline as well as a
      fill — and focus visible wherever it goes.
- [ ] 10.4 Verify a whole turn can be played with no pointer at all.

## 11. The whole flow

- [ ] 11.1 Add `tests/test_web_flow.py` driving a whole game through exactly
      the calls `api.js` makes: the administrator creates a game and sets it
      up, two accounts claim a seat each, both design a type, deploy within
      budget, commit setup, order a move, commit, and the turn resolves. This
      is what keeps the interface from needing a private back channel
      (design.md — "The interface is a client of the served contract").
- [ ] 11.2 Verify in that test that each seat's view holds only what
      `visibility` entitles it to.
- [ ] 11.3 Verify a game played partly through those calls and partly through a
      command-line role leaves neither in a state the other cannot read.
- [ ] 11.4 Run the whole suite against both storage backends, since the
      registry reads both.
- [ ] 11.5 `pylint` clean to `.pylintrc`. Confirm no Python change outside
      `http/` and `service/registry.py`, and no change to `domain/`,
      `storage/` or `cli/`.

## 12. Documentation

- [ ] 12.1 `README.md`: how to reach the interface, what it offers, and that it
      needs no build step and no package manager.
- [ ] 12.2 `README.md`: the deployment note — each waiting player holds a
      server thread for the length of the long-poll budget, so a host serving
      more than a few players wants gunicorn or uwsgi rather than Flask's
      development server.
- [ ] 12.3 `MODULE_DESCRIPTION.md`: `service/registry.py`, `http/registry.py`
      and the static directory, with what each file in it is for.
- [ ] 12.4 `ARCHITECTURE_OPTIONS.md`: mark step 5 done, and record that §6's
      P2 was taken without its toolchain — a client of the JSON contract, but
      built from ES modules rather than a framework — with the reasoning in
      `design.md`.
- [ ] 12.5 `GAME_RULES.md` is **not** touched. Verify by diff.
