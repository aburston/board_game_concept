## MODIFIED Requirements

### Requirement: A Player Is Registered With A Point Budget

The system SHALL give every player a point budget when they are registered,
and SHALL fix it for the life of the game. The budget SHALL be an integer from
1 to 1000. Where the administrator does not name one, the budget SHALL be 250.

The default is 250 because a player is given a default army that costs 232,
and a budget that only just covers it would leave nothing to edit with: every
change would have to begin by taking something back.

The budget SHALL be a property of the player rather than of the game, so two
players of one game may be registered with different budgets. Nothing in play
SHALL change a budget once it is set: there is no command that raises or
lowers it, and resolving a turn does not.

#### Scenario: Registering with the default budget

- **WHEN** a player is registered without a budget being named
- **THEN** that player's budget is 250

#### Scenario: Registering with a budget

- **WHEN** a player is registered with a budget of 150
- **THEN** that player's budget is 150

#### Scenario: Two players with different budgets

- **WHEN** one player is registered with a budget of 60 and another with 200
- **THEN** each holds the budget they were registered with
- **AND** neither budget is affected by the other

#### Scenario: A budget outside the permitted range

- **WHEN** a player is registered with a budget below 1 or above 1000, or with
  a budget that is not an integer
- **THEN** registration fails, naming the permitted range
- **AND** no player is registered

#### Scenario: A budget does not change

- **WHEN** a player's units are deployed, destroyed, or a turn is resolved
- **THEN** that player's budget is the same number it was registered with
