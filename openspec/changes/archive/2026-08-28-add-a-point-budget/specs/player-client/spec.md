## MODIFIED Requirements

### Requirement: Deploying Units

The system SHALL let a player deploy units during setup via
`add unit <type> <name> <x> <y>`, and SHALL refuse a deployment onto a square
the client already knows is taken, without ending the session.

A deployment SHALL also be refused when the named type costs more than the
player has left of their point budget, as `point-budget` describes. The
refusal SHALL name the cost, what the player has left, and their budget, and
SHALL leave the session running and the game unchanged.

#### Scenario: Deploying a unit

- **WHEN** the player runs `add unit` with a known type, a name, and coordinates
- **THEN** a unit of that type is placed at those coordinates for that player
- **AND** the type's cost is spent from the player's budget

#### Scenario: Wrong argument count

- **WHEN** `add unit` is given other than four arguments
- **THEN** the client reports that four arguments are required and takes no action

#### Scenario: No board loaded

- **WHEN** `add unit` is run before a board exists
- **THEN** the client reports that the board must be loaded first

#### Scenario: Deploying after setup

- **WHEN** `add unit` is run after the first turn has been resolved
- **THEN** the client refuses, reporting that units cannot be added after the first turn

#### Scenario: Invalid deployment

- **WHEN** `add unit` names an unknown type, or gives coordinates outside the board, or reuses one of the player's unit names
- **THEN** the client reports the error and takes no action

#### Scenario: Deploying onto a square the player already holds

- **WHEN** `add unit` names coordinates the player has already placed a unit on
- **THEN** the client reports that the square is occupied and takes no action
- **AND** the session continues and accepts further commands

#### Scenario: Deploying more than the budget can pay for

- **WHEN** `add unit` names a type costing more than the player has left
- **THEN** the client reports the cost, what is left, and the budget
- **AND** no unit is placed and nothing is spent
- **AND** the session continues and accepts further commands
