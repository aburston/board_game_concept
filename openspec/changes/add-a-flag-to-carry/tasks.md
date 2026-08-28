## 1. The flag, in the engine

- [x] 1.1 Give a unit a flag in `domain/unit.py`: a `flag` attribute set after
      construction the way `state` and `direction` are, defaulting to not
      carrying one, and never read by `move_cost`, `cost` or any combat
      arithmetic. Verify: a unit's cost and move cost are the same whether or
      not it carries the flag.
- [x] 1.2 Add `Board.flagOf(player_number)` — the unit carrying that player's
      flag, or None — and `Board.flagFallen(player_number)`, true when that
      player designated a carrier and it is destroyed. Both read the board and
      nothing else. Verify: a board with a designated, standing carrier
      answers the unit; one whose carrier is destroyed answers fallen; one
      where nobody designated answers neither.
- [x] 1.3 Report a flag falling from `Board.commit`: an event of its own,
      beside `destroyed`, naming the unit and the player it belonged to.
      Verify: `tests/test_turn_events.py` gains a case where destroying a
      carrier reports it, and destroying a unit that is not one does not.
- [x] 1.4 Make a unit belonging to a player whose flag has fallen inert in
      resolution: it plans no move and lands no attack, and is still attacked,
      damaged and destroyed like any other. Verify: a contest between a live
      unit and an eliminated player's unit ends with only the live one having
      struck.
- [x] 1.5 Hold the determinism invariant: nothing added consults a clock, a
      random source or an object's identity. Verify:
      `tests/test_determinism.py` passes unchanged.
- [x] 1.6 Add `tests/test_flag_carrier.py` covering 1.1 to 1.4 against a board
      directly, including a carrier that is a wall and a carrier destroyed in
      the same round as its killer.

## 2. Designating it, and refusing a setup without one

- [x] 2.1 Add the `SetFlag(unit)` command record to `service/commands.py`,
      kind `set_flag`. Verify: `as_record` and `from_record` round-trip it,
      alongside the existing records in `tests/test_draft_serialisation.py`.
- [x] 2.2 Add `set_flag` to `service/games.py` and its `ACTIONS`: it names one
      of the calling player's own units, moves the designation from whatever
      held it, and is refused after that player's setup is committed, for a
      unit that is not theirs, and for a name no unit has. Verify: each
      refusal is a `GameError` naming the reason, and the designation is
      unchanged after one.
- [x] 2.3 Refuse a player's setup commit unless exactly one of their units
      carries the flag, where "the board is too small to commit" is already
      refused. A commit for a later turn is not refused. Verify: the refusal
      names what is missing and publishes nothing.
- [x] 2.4 Add the flag-loss clause to `eliminated_players` in
      `service/turn.py`, derived from the board beside the existing one.
      Verify: a player whose carrier is destroyed is eliminated with units
      still standing; a player who designated nothing is judged as before.
- [x] 2.5 Extend `tests/test_setup_is_flexible.py` (or a sibling) with the
      designation being changeable until the commit and fixed after it.

## 3. Storing it and publishing it

- [x] 3.1 Carry the flag through `storage/serialise.py`: `_unit_record` writes
      it and a record without it reads back as carrying nothing. Verify: a
      units document written before this change loads with no carrier.
- [x] 3.2 Persist it in the YAML backend beside `destroyed` and `on_board`,
      and in the SQLite backend as a column on `units`. Verify: the byte-diff
      tests move by the one field and no more, and a SQLite game made by an
      older build gains the column on its next `ensure()`.
- [x] 3.3 Add `read_flags()` / `write_flags(entries)` to the repository port
      and both backends: one entry per player, holding the owner, the square
      and whether the carrier is standing, and nothing else. Verify: a
      round-trip on each backend, and a test asserting the entry has exactly
      those three fields.
- [x] 3.4 Publish the flags on every resolution in `service/turn.py`, written
      before anybody waiting on the turn is released, the way the views and
      the feed already are. Verify: after a resolution every player's flag is
      readable, and a fallen one is published as fallen with no square.

## 4. The contract

- [x] 4.1 Add a `flags` view to `http/views.py` and register it in
      `VIEW_BUILDERS`, reading the published flags rather than the session's
      own board, so a seat is given every flag whatever its visibility.
      Verify: a seat out of contact reads an enemy flag's square.
- [x] 4.2 Add the flag to `units_view` as a field of the unit, so a seat can
      see which of the units it can see is a carrier. Verify: a seat's own
      carrier reads as one, and a seat is never given the flag field of a unit
      it cannot see - because it is not given that unit at all.
- [x] 4.3 Extend `tests/test_web_flow.py`: designating through `/commands`,
      the setup commit refused without a carrier, the `flags` view read by a
      seat with no contact, and the proof that it carries no name, type or
      statistics.
- [x] 4.4 Check the parity tests still pass, and that they cover the new view
      and command: every view the page reads is a subject some role shows, and
      every command it sends is a line the grammar takes.

## 5. The command line

- [x] 5.1 Add `set flag <unit>` to `cli/grammar.py` and `cli/parser.py` as a
      second `set` production, and to the client role in `cli/roles.py`.
      Verify: the pinned usage lines in `tests/test_grammar.py` gain the line,
      and every role that may not use it refuses it.
- [x] 5.2 Add `show flags` as a subject in the grammar, the parser and all
      three roles, answered by `cli/backend.py` from the published flags.
      Verify: a player, the administrator and the observer each get the same
      table.
- [x] 5.3 Render it in `cli/render.py`: the `flags` table, and the `FLAG`
      column on `units`. Verify: `tests/test_cli_tables.py` covers the columns
      and the fallen case.
- [x] 5.4 Draw a flag on the ASCII board for a square whose unit the session
      cannot see, with a legend row naming the player rather than a type.
      Verify: a player out of contact renders the enemy flag's square as a
      flag, and the legend does not name a type.
- [x] 5.5 Extend the three CLI surface suites: designating, the refusal after
      committing, `show flags`, and the setup commit refused without a
      carrier.
- [x] 5.6 Regenerate or extend the shell completions so `set` offers `flag`
      and `show` offers `flags`. Verify: `tests/test_completion.py` and
      `tests/test_shell_completion.py`.

## 6. The browser

- [ ] 6.1 Read the `flags` view in `loadSeat` beside the others, and hold it
      in state. Verify: the seat's state holds every flag in the game.
- [ ] 6.2 Designate in the armoury: mark which deployed unit carries the flag,
      let another be chosen while setup is open, and say a carrier is needed
      before offering to commit. Verify: in a browser, choosing, changing, and
      the commit button refusing to be offered without one.
- [ ] 6.3 Draw every flag on the board: on the seat's own carrier as a mark
      beside the unit, and on an enemy square with no unit drawn, naming the
      player it belongs to and nothing else. Verify: in a browser, from a seat
      that has made no contact.
- [ ] 6.4 Name the carrier in the Forces roster, and say in the feed when a
      flag falls. Verify: the turn that destroys a carrier reads as one.
- [ ] 6.5 Tell an eliminated player they are out and why, stop offering orders
      and commits, and keep the board and the feed arriving. Verify: in a
      browser, playing a game to a flag falling.

## 7. Finishing

- [ ] 7.1 Run both suites - `pytest` and `BOARD_GAME_BACKEND=sqlite pytest` -
      and the flake8 gate CI runs. Verify: green on both backends.
- [ ] 7.2 Play a whole game in a browser, from designating to a flag falling,
      with two seats and a watching observer. Verify: the loser is told, the
      winner is told, and the observer sees both.
- [ ] 7.3 Update `README.md`, `GAME_RULES.md` and `MODULE_DESCRIPTION.md` for
      the rule and the commands. Verify: the rules file states the flag rule
      where the other rules are stated.
- [ ] 7.4 Run `openspec validate --all --strict`, then sync and archive this
      change. Verify: the specs carry the capability and `openspec list` shows
      no active change.
