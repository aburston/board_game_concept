## 1. The rule, at the service tier

- [ ] 1.1 Add a case to `tests/test_account_service.py` proving the
      administrator may claim a seat: an administrator with its password
      changed, a game registering players 1 and 2, and
      `accounts.claim_seat(store, repository, administrator, gameno, 1)`
      accepted. Verify: `store.holds_seat(gameno, 1, administrator.account_id)`
      is true afterwards, and `store.read_membership(gameno, 1)` names the
      administrator's account.
- [ ] 1.2 Prove `may_act_as` grants the administrator its held seat and still
      refuses the seats it does not hold. Verify: it answers true for 1, false
      for 2, and still true for 0 and 1000 of the same game.
- [ ] 1.3 Prove the claiming rules are not relaxed for the administrator: a seat
      another account holds is refused, a number the game did not register is
      refused, and a claim after a turn has resolved is refused. Verify: each
      raises `AccountError` with the same message a player's claim raises, and
      the membership is unchanged after each.
- [ ] 1.4 Prove `release_seat` treats the administrator as any holder: it may
      give up a seat it holds before the game starts, is refused after, and is
      refused a seat it does not hold. Verify: the refusal after the game starts
      is the same one a player is given.

## 2. The equivalence, at the served contract

- [ ] 2.1 Add `tests/test_admin_plays.py` with a fixture that builds two games
      in one store, set up identically - same board size, same registered seats
      and budgets - with seat 1 of the first held by a registered player and
      seat 1 of the second held by the administrator, and seat 2 of each held by
      a registered player. Verify: both claims are accepted, and both games
      report the same state and the same open seat count.
- [ ] 2.2 Drive both games through the same calls in the same order: design a
      type, deploy a unit, designate the flag, commit setup for both seats, then
      order a move and commit a turn. Verify: every call returns the same status
      code in both games.
- [ ] 2.3 Compare every view of seat 1 between the two games as whole values -
      `board`, `types`, `units`, `players`, `pending`, `events`, `designs`,
      `flags` - and the seat's state. Verify: each pair is equal, and the
      comparison names which subject differed when one does. Normalise only the
      game number, and do so by naming it rather than by scrubbing the values.
- [ ] 2.4 Prove the seat is blinkered: read the administrator's seat 1 units and
      board, and check that seat 2's undiscovered unit is in neither. Verify:
      the same read as player 0 of that same game does hold it, so the test
      distinguishes "the seat cannot see it" from "nothing can".
- [ ] 2.5 Prove the barrier waits for an administrator-held seat: commit seat 1
      alone. Verify: the response is `202`, `resolved` is false, the turn number
      has not advanced, and `waiting_on` names seat 2.
- [ ] 2.6 Prove a refusal is the ordinary refusal: give the administrator's seat
      a command that seat may not give - a unit over its budget, and an order
      for a unit belonging to seat 2. Verify: the status and the message are
      those the player-held seat gets for the same command, compared against the
      first game rather than hard-coded.
- [ ] 2.7 Prove the administrator may administer a game it plays in: act as
      player 0 of the second game while holding seat 1 of it. Verify: the read
      as 0 succeeds, and seat 1's views are unchanged by it - compared against
      the same views read before.

## 3. One account playing a whole game

- [ ] 3.1 Add a case to `tests/test_admin_plays.py` where the administrator sets
      a game up, claims every seat, and plays it from setup to a resolved turn
      unaided. Verify: `whoami` lists every seat, and each seat's setup commit
      is accepted.
- [ ] 3.2 Prove the barrier holds within one account: for each turn, commit the
      seats one at a time. Verify: every commit but the last answers `202` with
      the remaining seats in `waiting_on`, and the last answers `200` with
      `resolved` true and the turn number advanced.
- [ ] 3.3 Play the game to an outcome, one account at every seat - drive units
      together until a flag carrier falls. Verify: the outcome is reported and
      names the winner, as it would with a person at each seat.
- [ ] 3.4 Prove the two seats stay two identities under one account: order a
      unit as seat 1 and read seat 2's pending orders. Verify: seat 2's pending
      is empty and its draft is untouched.

## 4. The command line

- [ ] 4.1 Widen `tests/conftest.py:authorise` with an optional argument naming
      which account should hold the seat, defaulting to the registered player it
      makes today. Verify: every existing suite passes unchanged, and the new
      argument arranges a seat held by the administrator.
- [ ] 4.2 Add a case to `tests/test_cli_client_surface.py` running `bgcclient`
      against a served game for a seat the administrator holds, with the
      administrator's token in `BOARD_GAME_TOKEN`. Verify: the session opens,
      `show board` and `show players` print what the client role prints, and the
      process exits zero.
- [ ] 4.3 Prove the role is not widened by the account behind the token: ask the
      administrator's `bgcclient` session for a command only `bgcserver` offers
      - `add player`. Verify: it is refused as an invalid command, exactly as it
      is for a player's token, and `help` lists the client's commands and not
      the server's.
- [ ] 4.4 Prove the administrator's token is still refused a seat it does not
      hold: run `bgcclient` for a seat held by another account. Verify: the
      refusal is reported and no session is opened, as
      `A Command-Line Role Proves Itself With A Token` requires.

## 5. The lobby

- [ ] 5.1 Add a case to `tests/test_web_flow.py` taking a seat as the
      administrator through exactly the calls `lobby.js` makes - list games,
      claim the seat, re-read the account. Verify: the seat is claimed, the
      listing shows the administrator as its holder, and `whoami` carries it.
- [ ] 5.2 Prove the observer is offered none: claim a seat as the observer over
      the same calls. Verify: it is refused, and the seat is still open
      afterwards.
- [ ] 5.3 Hold `lobby.js` to deciding by entitlement rather than by kind: the
      seat action is offered when the account may hold the seat and withheld
      when it may not. Verify: the refusal path a browser would meet is the same
      one the contract gives, so the button is never drawn for a claim the
      server would refuse.
- [ ] 5.4 Prove the administrator's own screens are offered beside its seat
      rather than instead of it: with a seat held in a listed game, both the
      seat's way in and the administrator's way in are present. Verify: the
      game is marked as theirs, and the watch route is offered as well.

## 6. Writing it down

- [ ] 6.1 Update `SPEC_COVERAGE.md`: name the new requirements under
      `identity-and-accounts` and `web-interface`, and say which suite covers
      each. Verify: every scenario added by this change is named by a test that
      exists.
- [ ] 6.2 Add a paragraph to `README.md` saying how to play a game single-handed
      to test a change: register the administrator's password change, create and
      set up a game, claim every seat, and drive them. Verify: the steps as
      written work against a fresh store, run through once.
- [ ] 6.3 Record any task above that failed as a divergence in
      `SPEC_COVERAGE.md`, in the form the existing entries use - what was
      expected, what happened, and what fixed it. Verify: if none failed, say so
      rather than leaving the section silent about a change that touched it.
- [ ] 6.4 Run the whole suite on both backends - `pytest` and
      `BOARD_GAME_BACKEND=sqlite pytest`. Verify: both pass, and the new suites
      are not pinned to a backend, since nothing in them knows how a game is
      stored.
