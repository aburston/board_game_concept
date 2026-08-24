## 1. Say what the barrier is, once

- [ ] 1.1 Take the barrier condition out of `wait_for_all_commits` into
      `barrier_met(game)`, and have the wait ask it (design.md — Decision 3).
      No behaviour change: verify the whole suite passes with no test edited.

## 2. Ask it where the turn is resolved

- [ ] 2.1 Add `resolve_when_ready(game)`: hold the game for writing, read it,
      ask `barrier_met`, and resolve only if it is met (design.md — Decision 1).
      Verify the read, the question and the resolution all happen inside one
      hold, with the recorder shape `tests/test_turn_publication.py` uses.
- [ ] 2.2 Give it three answers, not two: `None` for a barrier that is not met,
      and `resolve`'s own `True`/`False` otherwise (design.md — Decision 2).
      Verify each of the three separately, because folding the first into
      `False` sends the server to its fatal branch on the one case that is not
      a failure.
- [ ] 2.3 Add the session operation beside `serverSave`, and verify
      `serverSave` still resolves without asking the barrier — it is what the
      administrator's `commit` calls to end setup, where nobody has committed
      (design.md — Decision 4).

## 3. Two callers, one turn

- [ ] 3.1 Verify the case the change exists for: two callers each find the
      barrier met and each ask for the turn to be resolved; one resolves it and
      the other is told the barrier is no longer met. Driven by asking from
      inside the first resolution's hold rather than by timing, so it fails
      deterministically.
- [ ] 3.2 Verify the turn resolved once — the turn number advanced by one, and
      each player's orders consumed once rather than twice.

## 4. The server asks instead of acting

- [ ] 4.1 Have the unattended half of `cli/bgcserver.py` call it and handle all
      three answers: say so on `True`, report and exit on `False`, and wait
      again on `None` (design.md — Decision 5). Waiting before looping, or a
      barrier that is never met again becomes a spin.
- [ ] 4.2 Verify the server still plays a game end to end and still reports an
      outcome:  `tests/test_server_client_integration.py`,
      `tests/test_cli_server_surface.py` and `tests/test_cli_outcome_surface.py`
      pass unedited.
- [ ] 4.3 Verify a server woken for a turn somebody else resolved waits again
      rather than exiting, and says nothing about it.

## 5. Finish

- [ ] 5.1 Record in `SPEC_COVERAGE.md` that the gap the previous entry left open
      is closed, naming the tests. Say what is still not one act: a player's
      commit does not resolve the turn.
- [ ] 5.2 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does, and
      `pylint` against the configured `.pylintrc`. Verify the suite is green and
      lint reports no message kind in a file that it did not report before.
- [ ] 5.3 Run the full suite ten times over and verify it is green every time.
