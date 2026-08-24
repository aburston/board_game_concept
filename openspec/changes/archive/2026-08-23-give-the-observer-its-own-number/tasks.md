## 1. Say what the numbers mean

Nothing asks these questions yet, so behaviour is unchanged and the suite must
be green at the end of the group with no test edited.

- [x] 1.1 Give `Player` the range: `FIRST = 1`, `LAST = 999`, asserted alongside
      the integer and non-negative checks it already makes (design.md —
      Decision 1). Verify `Player(1)` and `Player(999)` are built and
      `Player(0)`, `Player(1000)` and `Player(-1)` each raise, naming the range.
- [x] 1.2 Add `service/identity.py` naming `ADMINISTRATOR = 0` and
      `OBSERVER = 1000`, and answering the three questions the `== 0` tests were
      standing in for: `is_player`, `sees_everything`, `may_change`. Take the
      range from `Player` rather than restating it. Verify each answers
      correctly at the boundaries — 0, 1, 999, 1000 — and that a number outside
      them identifies nobody.

## 2. Ask the question instead of the number

- [x] 2.1 Replace the five tests in `service/game.py` that read `player_number
      == 0` or `!= 0` with the identity question each was standing for
      (design.md — Decision 2). Verify the whole suite passes with no test
      edited: the observer is still launched as 0 at this point, so nothing
      observable may change yet.
- [x] 2.2 Verify the two that are easy to get wrong: `new_game` must stay false
      for a session entitled to see everything, or the rules will think an
      observer is mid-setup; and a session entitled to see everything must still
      open a game with no board and be told `must create board - set size and
      commit` rather than be refused with `NoSuchGame`.

## 3. Refuse a bad number wherever it arrives

- [x] 3.1 Have `games.add_player` refuse a reserved or out-of-range number as a
      `GameError`, catching the domain's assertion the way `set_board_size`
      already catches the board's (design.md — Decision 5). Verify `add player
      0`, `add player 1000`, `add player -1` and `add player 1000000` are each
      reported at the prompt and leave the session taking commands.
- [x] 3.2 Have `games.load_player` refuse a file whose player number is not a
      player's, as the same `GameError`. Verify the server reports it and
      registers nobody.
- [x] 3.3 Have `Game.load` report a game whose registered players include a
      number out of range as a game that cannot be read, rather than letting an
      `AssertionError` escape. Verify a hand-written game directory holding
      player 0 or player 1000 is reported and the session exits, and that no
      game written by the commands is affected.

## 4. Give the observer its number

The step that changes what anyone can observe.

- [x] 4.1 Launch `bgcobserver` as `identity.OBSERVER` instead of 0. Verify
      `tests/test_cli_observer_surface.py` passes with no edit — the observer
      still sees every unit, still refuses every mutating command, and still
      shows `must create board` for a game with no board.
- [x] 4.2 Verify the leak the change exists for is closed: an administrator that
      sizes a board and registers players without committing, and an observer
      that then opens the same game, must leave the observer showing none of it
      and holding no draft. This is the behaviour demonstrated in proposal.md —
      Why, so it gets a test named for it.
- [x] 4.3 Have `bgcclient` refuse a player number outside 1 to 999 before it
      opens a session, alongside the non-integer it already refuses. Verify
      `bgcclient <game> 0`, `1000` and `-1` each report and exit with a failure
      status, and that `1` and `999` still open.

## 5. Refuse the observer below the CLI

- [x] 5.1 Have `games.perform` refuse a command from an identity that may not
      change the game (design.md — Decision 4). Verify a session opened as the
      observer is refused a command that would change the game even though no
      role table was consulted, and that the administrator's setup commands and
      a player's orders are unaffected.

## 6. Finish

- [x] 6.1 Update `MODULE_DESCRIPTION.md` and `README.md`, which both describe the
      observer as player 0. Verify neither names a number the code no longer
      uses.
- [x] 6.2 Record in `SPEC_COVERAGE.md` the defects this change closes — the
      observer sharing the administrator's identity and reading its draft,
      `add player 0` and `add player 1000` being accepted, and `add player -1`
      killing the server with an `AssertionError` that escaped the roles' error
      handling. Verify every entry names a test that now holds it.
- [x] 6.3 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does, and
      `pylint` against the configured `.pylintrc`. Verify the suite is green and
      lint reports no message kind in a file that it did not report before.
