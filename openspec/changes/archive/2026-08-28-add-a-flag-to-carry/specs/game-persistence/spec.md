## ADDED Requirements

### Requirement: Flag Publication

The system SHALL publish, on every resolution, the square each player's flag
is on and whether it is still standing, as a record every player may read
whatever their visibility. It SHALL NOT publish the name, type or statistics
of the unit carrying it: those reach a player only through their own view, as
contact allows.

#### Scenario: Publishing the flags

- **WHEN** a turn is resolved
- **THEN** each player's flag is published with its owner and its square

#### Scenario: A flag that has fallen

- **WHEN** a resolution destroys a flag carrier
- **THEN** that flag is published as fallen, with no square

#### Scenario: What is not published with it

- **WHEN** the published flags are read
- **THEN** no carrier's name, type, symbol or statistics are in them

## MODIFIED Requirements

### Requirement: Unit State Persistence

The system SHALL persist the full state of every unit on the board and restore
it on load, including units already destroyed and units sharing a square. A unit
SHALL be restored in a state that takes no action of its own: restoring is not
an order, and a restored unit SHALL NOT be treated as waiting to be deployed.

#### Scenario: Saving units

- **WHEN** the server saves a game
- **THEN** every unit's player, type, name, symbol, attack, health, energy, coordinates, state, direction, destroyed flag, on-board flag, and whether it carries its player's flag are written to `data/units.yaml`

#### Scenario: Restoring the carrier

- **WHEN** a game holding a flag carrier is loaded
- **THEN** the same unit carries that player's flag

#### Scenario: A game stored before flags existed

- **WHEN** a game whose stored units carry no such field is loaded
- **THEN** it loads
- **AND** no unit carries a flag

#### Scenario: Restoring units

- **WHEN** a game is loaded and `data/units.yaml` exists
- **THEN** each unit is recreated on the board with its stored health, energy, destroyed flag, and on-board flag

#### Scenario: A restored unit is not waiting to deploy

- **WHEN** a unit is restored
- **THEN** it is not in the state that means a unit is waiting to be placed
- **AND** resolving the next turn does not deploy it again

#### Scenario: Restoring a destroyed unit

- **WHEN** a destroyed unit is restored
- **THEN** it is restored destroyed and off the board
- **AND** it occupies no square
- **AND** resolving the next turn does not place it on one

#### Scenario: Restoring a shared square

- **WHEN** a saved game holds several units on one square
- **THEN** loading it restores every one of those units to that square
- **AND** loading does not fail
- **AND** the rule refusing deployment onto an occupied square does not apply
