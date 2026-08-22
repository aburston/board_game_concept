## MODIFIED Requirements

### Requirement: Unit State Persistence

The system SHALL persist the full state of every unit on the board and restore
it on load, including units already destroyed and units sharing a square.

#### Scenario: Saving units

- **WHEN** the server saves a game
- **THEN** every unit's player, type, name, symbol, attack, health, energy, coordinates, state, direction, destroyed flag, and on-board flag are written to `data/units.yaml`

#### Scenario: Restoring units

- **WHEN** a game is loaded and `data/units.yaml` exists
- **THEN** each unit is recreated on the board with its stored health, energy, destroyed flag, and on-board flag

#### Scenario: Restoring a shared square

- **WHEN** a saved game holds several units on one square
- **THEN** loading it restores every one of those units to that square
- **AND** loading does not fail
- **AND** the rule refusing deployment onto an occupied square does not apply

### Requirement: Order Publication

The system SHALL have players publish pending orders as a per-player file that
the server consumes when resolving a turn, and SHALL apply each order to the
unit it names rather than to whatever occupies the square.

#### Scenario: Player publishes orders

- **WHEN** a player commits
- **THEN** their pending orders are written to `players/<number>_units.yaml`
- **AND** a marker file `players/commit_<number>` records that they have committed

#### Scenario: Server consumes orders

- **WHEN** the server resolves a turn
- **THEN** it applies each player's pending orders according to unit state: deploying units in `INITIAL`, moving units in `MOVING`, and leaving units in `NOP` in place
- **AND** it removes the pending order files afterwards

#### Scenario: Invalid order state

- **WHEN** a player publishes an order with a state that is not `INITIAL`, `MOVING`, or `NOP`
- **THEN** the server rejects it as invalid

#### Scenario: Applying an order to a unit on a shared square

- **WHEN** the server applies a move order for a unit whose square holds several units
- **THEN** the order is applied to the named unit belonging to the ordering player
- **AND** the other units in that square are unaffected
