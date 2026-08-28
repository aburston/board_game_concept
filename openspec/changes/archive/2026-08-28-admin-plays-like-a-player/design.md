## Context

See `proposal.md` — Why, and `specs/identity-and-accounts/spec.md` for what is
being stated. This change is unusual in that the behaviour already exists; what
shapes the approach is where it comes from, and how easily it could be lost.

- **Entitlement is asked in one place.** `service/accounts.may_act_as` is the
  single rule: 0 is the administrator, 1000 is the observer or the
  administrator, and 1 to 999 is `store.holds_seat(gameno, number, account_id)`.
  A seat is granted on a membership row, and the row does not record what kind
  of account holds it. That is the whole reason the administrator can play.
- **Entitlement and visibility are different questions, asked by different
  code.** `service/identity.py` answers what a *number* may see -
  `sees_everything(0)` and `sees_everything(1000)` - and has never heard of an
  account. `service/accounts.py` answers which numbers an *account* may be. The
  administrator's privilege lives entirely in the second, and the view a session
  is given is computed from the first. Nothing joins them, which is why holding
  a seat gives an administrator that seat's blinkered view and not the whole
  board.
- **Kind is consulted in four places, and none of them is gameplay.** A sweep of
  `src/` for `is_administrator()`, `is_observer()` and `kind === 'admin'` finds
  creating a game, resetting another account's password, `may_act_as` itself,
  and which affordances the lobby draws. No view, no command, no barrier, no
  budget.
- **Nothing tests it.** No test in the suite claims a seat as the administrator.
  `tests/conftest.py:authorise` reaches for `make_admin` when the number is 0
  and for a registered player otherwise, so even the suites that drive whole
  games never exercise the case.

The property is real, it is a consequence of the layering, and it is
undefended.

## Goals / Non-Goals

**Goals:**

- State the equivalence as a requirement, in the capability that owns
  entitlement.
- Cover it at every tier that could break it: the service rule, the served
  contract, the command line, and the browser.
- Make the equivalence test a *comparison* rather than a list of assertions, so
  it keeps holding as views gain fields.
- Leave a way for one person to play a game through, written down where somebody
  looking to test a rule change will find it.

**Non-Goals:**

- Changing what the administrator may do. No privilege is added or removed.
- Easing the password-change gate on `admin`, or seeding accounts for tests. Real
  friction, but a separate change - `require_usable` is a rule about an account,
  and loosening it for convenience is exactly the kind of thing this change
  exists to stop happening by accident.
- A test-only route, fixture or flag that a person could not use. The point is
  that the administrator plays through the contract everybody else plays
  through; a shortcut around it would test the shortcut.
- Letting the administrator claim a seat in a game that has started, or hold a
  seat without a membership. Both would be new privileges, and both would make
  the account a worse test subject rather than a better one.

## Decisions

### The equivalence is tested by comparison, not by assertion

Two games are set up identically in the same store. Seat 1 of one is held by a
registered player; seat 1 of the other is held by the administrator. Both are
driven through the same calls, and then every view of each is read and the two
compared as whole values.

The alternative - asserting the administrator's board has the right squares in
it - tests what the assertions happen to mention. The comparison tests
everything the view holds, including fields added later, and fails the day a
field starts carrying the holder's kind into a seat's answer. It is also the
only form of the test that states the requirement rather than an instance of it:
the requirement is that the two are the same, so the test should be that the two
are the same.

The games must be set up identically for the comparison to mean anything, which
constrains how the fixture is written: same board size, same registered seats
and budgets, same types, same squares, same order of commands. Anything that
varies between the two - a game number appearing in a view, a timestamp - has to
be either excluded from both games' setup or normalised before comparing, and
normalising has to be explicit rather than a blanket scrub, or the test quietly
stops covering the field it normalised.

### The service tier is tested on the rule, not through a game

`may_act_as` and `claim_seat` are asked directly, with an administrator account
and a store, as `tests/test_account_service.py` already asks them for players.
That suite is where the rule is stated in code, and a change to the rule should
fail there first and fastest - before the HTTP suite, which would fail too but
would take a game's worth of setup to say so.

### One account holding every seat is tested as a whole game, not as two claims

The interesting part is not that the claims are accepted; it is that the commit
barrier does not collapse when one account commits both sides. So the case plays
a real game: set up, both seats deployed, both committed, a turn ordered and
resolved, and the outcome read. It asserts the barrier held after the first
commit of each turn, which is the thing that would break if a barrier were ever
keyed on the account rather than the seat.

### The CLI case reuses the existing subprocess harness

`tests/cli_harness.py` already starts a role as a subprocess against a served
game with `BOARD_GAME_TOKEN` in its environment, and `tests/conftest.py` already
mints tokens. The administrator case is the existing client-surface pattern with
a different account behind the token, so it belongs in
`tests/test_cli_client_surface.py` rather than in a suite of its own.

What it proves that the HTTP suite does not: that nothing between the prompt and
the request narrows a role by the account behind its token. The role a command
line takes is fixed by which executable was run, and the server decides the rest
- so `bgcclient` with the administrator's token is a client, not a server.

### `conftest.authorise` gains a way to name the administrator as a seat holder

Today it decides by number: 0 is the administrator, anything else is a
registered player whose seat it claims through the store. The new suites need
the administrator to hold seat 1, which that cannot express.

The smallest change is an optional argument saying which account should hold the
seat, defaulting to the registered player it makes today, so every existing
caller is unaffected. Widening the helper rather than writing a second one keeps
one place that knows how a seat is arranged for a test.

Claiming through the store directly, as it does now, stays right for the helper:
it lets a suite arrange a game that has already started. The suites that are
*about* claiming go through `service.accounts.claim_seat` instead, because for
them the refusals are the point.

### Nothing is fixed speculatively

Every scenario is written against behaviour that was driven and observed before
this change was proposed. The tasks below are worded as verification, and a task
that fails is a defect to be recorded in `SPEC_COVERAGE.md` and fixed on its own
terms - not a sign the requirement is wrong. The requirement is what the project
wants; the code agreeing with it today is what makes this change cheap.

## Risks / Trade-offs

- **The comparison test could pass for the wrong reason** - both games broken
  the same way. Mitigated by keeping the existing per-tier assertions beside it:
  the web flow suite already checks that a player's board hides what it should,
  so the comparison is anchored to a view known to be right rather than only to
  itself.

- **Two games in one store, in one test, is more setup than the suites usually
  carry**, and a failure in it will be slower to read than a single-game
  failure. Accepted: the requirement is a statement about two games, and a test
  that only ever set up one could not make it. The fixture is worth writing
  carefully and commenting.

- **Writing the equivalence down makes it a constraint on later changes.** Some
  future feature may want the administrator's seat to differ - a debugging view,
  say. That is the intended effect: it should have to argue with a requirement
  rather than quietly land. The requirement names what may not be consulted, not
  how anything is implemented, so a feature that genuinely needs it can modify
  the requirement and say why.

- **Documenting solo play invites it as a way to play rather than to test.** A
  person holding every seat sees every side's blind view in turn, which is not
  the game the rules describe. The `README.md` paragraph says what it is for.
