## Why

Two players cannot see each other's units while they are setting up, so two of
them can deploy onto the same square without knowing it. Today that is only
discovered when the turn resolves, and both deployments are refused: each
player loses the unit, is told after the fact, and can do nothing about it —
their setup is committed and closed. In the worst case every deployment
clashes and the game is decided before it began.

Refusing the commit instead leaves the setup open. The player is told which
square is taken, deploys somewhere else, and commits again — which is what a
player would do if they could see the board.

Since `placement-zones` gives each of exactly two players their own half, this
only arises with three players or more, but the rule is general and is applied
to any setup commit.

## What Changes

- A setup commit SHALL be refused when one of its deployments lands on a
  square another player has already committed a unit to. The refusal names the
  square.
- The refused player's setup is **not** committed: their units and types stand
  as they were, so they can move the unit and commit again.
- The first setup to be committed keeps the square. **BREAKING**: this
  replaces "when two deployments contend for one square, both are refused",
  which existed so that no player gained from the order their orders were read
  in. Commit order now decides who keeps a contested square.
- Deployments that reach the server without a commit — a loaded player file,
  or orders written by hand — are still refused at resolution as they are
  today, because nothing checked them on the way in.
- **An order given and not committed can be taken back** too — `hold <unit>`
  at a prompt, Delete or a control on the board — leaving the unit with no
  order rather than an order to hold, so it rests like any quiet unit. Nothing
  is final until the turn is committed, and an order was.
- **The interface stops offering values the rules refuse.** Its number fields
  are bounded to the ranges the domain enforces, so a negative attack cannot
  be typed and sent to be refused by the server.
- **A unit deployed and not committed can be taken back**, freeing its square,
  its points and its name. Without it a refused commit is not something a
  player can act on: the offending unit could not be moved and could not be
  got rid of, so the refusal would leave them as stuck as the old behaviour
  did. `remove unit <name>` at a prompt, and a take-back button beside each
  deployed unit in the armoury.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `turn-commit`: a setup commit is refused when it clashes with a square
  another player has already committed to, leaving that player's setup open;
  and the first commit keeps the square rather than both being refused.
- `player-client`: a unit deployed and not committed can be taken back, and so
  can an order given and not committed.
- `web-interface`: the armoury lists what is deployed and offers to take any
  of it back; an order can be taken back from the board; and a number field
  cannot be given a value the rules would refuse.

## Impact

- `service/turn.py`: `publish` checks a setup commit against the deployments
  already published by other players, before it writes anything, so a refused
  commit leaves the game exactly as it was.
- The resolution-time contention refusal stays as the backstop for orders that
  never went through a commit.
- No storage or contract change: the squares already committed are read from
  the orders the repository already holds.

## Consequences worth stating

- **Commit order now matters.** The player who commits first keeps a contested
  square. This is a deliberate reversal of a rule written to prevent exactly
  that, and it is the price of being able to do something about a clash.
- **A refusal discloses a square.** Telling a player that a square is taken
  tells them an opponent has a unit there, which contact-based visibility
  otherwise withholds during setup. It is the minimum that lets them deploy
  elsewhere, and it names the square rather than the unit or its owner.
