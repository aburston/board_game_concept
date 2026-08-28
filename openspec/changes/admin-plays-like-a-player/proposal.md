## Why

Testing a game needs two seats and, until now, two people: the administrator
sets a game up, and somebody else has to register an account and take a seat
before anything can be played through. That is a poor way to check a change to
the rules, and it is why so little of the played game is covered by a test that
drives it the way a person drives it.

The administrator can already play. `service/accounts.py` refuses it nothing:
`claim_seat` never asks what kind the claiming account is, and `may_act_as`
grants a seat on the membership rather than on the kind. Driven end to end, an
administrator holding seat 1 is given the same board, the same budget and the
same refusals a registered player holding seat 1 is given, and the turn waits
for it the same way.

None of which is written down, and none of which is tested. One scenario in
`identity-and-accounts` says the administrator "may hold a seat"; nothing says
what holding one entitles it to, and no test in the suite claims a seat as the
administrator at all. A capability the project wants to lean on for testing is
resting on a property nobody stated and nothing checks - so the next change to
touch `may_act_as`, the visibility filter or the commit barrier can take it
away, and every test would still pass.

Write the property down, and cover it.

## What Changes

- **A seat the administrator holds is an ordinary seat.** State the equivalence
  as a requirement: for a seat number an account holds, the kind of the holding
  account SHALL NOT be consulted when deciding what the seat sees, what it may
  spend, what it may command, what it is refused, or whether the turn waits for
  it.

- **The administrator's privileges do not reach into its seat.** Being player 0
  of every game and being entitled to the observer's view are things the
  administrator has *as those numbers*. A seat it holds is played blind, like
  everybody else's. This is the half of the rule that makes the account useful
  for testing rather than useless: a test that drives the administrator through
  a seat is testing what a player would meet.

- **One account may play a whole game.** `identity-and-accounts` already lets an
  account hold several seats in one game; say plainly that the administrator may
  do so too, and that a single account holding every seat plays a complete game
  - which is what a test harness wants and what nothing currently states.

- **The lobby offers the administrator a seat.** The browser already does this;
  the spec does not say so. Make it explicit that a seat is offered to any
  account that may hold one, and withheld only from the observer.

- No behaviour changes. Every scenario below is written against what the code
  does today, verified by driving it. This is a change that makes an existing
  property load-bearing, not one that adds a property.

## Capabilities

### Modified Capabilities

- `identity-and-accounts`: what a seat held by the administrator entitles it to,
  that its administrative privileges do not reach into that seat, and that one
  account may hold every seat of a game and play it through.
- `web-interface`: the lobby offers a seat to any account that may hold one, and
  withholds it only from the observer.

## Impact

- **specs**: two delta specs. No requirement is weakened; the equivalence is
  added beside the permission that already exists.
- **service**: no change expected. `claim_seat` and `may_act_as` already answer
  as the new requirement demands, and the tasks below verify that rather than
  assuming it. Anything found to disagree is a defect to fix and to record in
  `SPEC_COVERAGE.md`.
- **http**, **cli**, **web**: no change expected, on the same terms.
- **tests**: the bulk of the work. A new `tests/test_admin_plays.py` holding the
  equivalence at the served contract - every view of an administrator-held seat
  compared against the same view of a player-held seat, and a whole game played
  by one account holding every seat. Cases added to the service suite, the CLI
  client surface suite and the web flow suite so each tier proves its own share.
- **docs**: `SPEC_COVERAGE.md` gains the new capability coverage, and `README.md`
  gains the one paragraph that tells somebody how to play a game single-handed
  to test it.
