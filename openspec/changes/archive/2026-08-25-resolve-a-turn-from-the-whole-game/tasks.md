## 1. Reproduce it before touching anything

- [x] 1.1 Play the scenario over the endpoint — two players, a unit each,
      commit one after the other — and verify the second player is declared the
      winner on turn 1, with only their own unit left in `units`.
- [x] 1.2 Play the same game against the service layer and verify it is
      undecided, so that what is broken is the transport and not the rules.

## 2. Resolve from the whole game

- [x] 2.1 Have the player branch of `POST /commit` resolve as
      `identity.ADMINISTRATOR` (design.md — Decision 1), and build its payload
      from the committing player's own reloaded session (Decision 2).
- [x] 2.2 Refuse a resolution from a session that is not entitled to the whole
      game and allowed to change it, in `turn.resolve` itself and before
      anything is written (Decisions 3 and 4). Verify the refusal leaves the
      turn there to be resolved by the administrator.

## 3. Cover the scenario

- [x] 3.1 `tests/test_two_player_commit.py`: play the game over the endpoint —
      the first commit waits, the second resolves, both players' units are on
      the board, neither player is eliminated, the game is undecided, and it
      goes on to a second turn. Unpinned, so it runs on whichever backend the
      run is for (design.md — Decision 5).
- [x] 3.2 The same game against the service layer in the same file, as the
      control that passed before the fix and after it.
- [x] 3.3 `tests/test_client_over_http.py`: the same game end to end through
      two `bgcclient` subprocesses, beside the one-player test that missed it.
- [x] 3.4 `tests/test_turn_publication.py`: a player's session and the
      observer's are each refused a resolution.
- [x] 3.5 Verify the coverage fails without the fix: with the resolver opened
      as the committing player again, five of the seven scenario tests and the
      end-to-end test fail.

## 4. Make CI run what it collects

- [x] 4.1 Turn the build job into a matrix over `yaml` and `sqlite`, passing
      the backend to pytest through `BOARD_GAME_BACKEND` (design.md —
      Decision 6). `fail-fast: false`.
- [x] 4.2 Verify both jobs pass locally with the package installed as CI
      installs it, so the console scripts are on the path and the subprocess
      tests really run.

## 5. Finish

- [x] 5.1 State the rule in `openspec/specs/turn-commit/spec.md`.
- [x] 5.2 Record it in `SPEC_COVERAGE.md` as divergence 30, naming the tests
      and what let it through CI.
- [x] 5.3 Run the full suite on both backends and
      `flake8 . --select=E9,F63,F7,F82` as CI does. Verify green.
