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

#### Scenario: A player with no units commits

- **WHEN** a player who holds no units commits, publishing an order file that lists none
- **THEN** the server resolves the turn with no orders from that player
- **AND** the turn completes for every other player

#### Scenario: Invalid order state

- **WHEN** a player publishes an order with a state that is not `INITIAL`, `MOVING`, or `NOP`
- **THEN** the server rejects it as invalid
- **AND** records the rejection for that player
- **AND** resolves the turn without it, rather than failing

#### Scenario: A move order naming a unit the player does not own

- **WHEN** a player publishes a move order for a unit that is not theirs or does not exist
- **THEN** the server rejects the order
- **AND** resolves the turn without it

#### Scenario: Applying an order to a unit on a shared square

- **WHEN** the server applies a move order for a unit whose square holds several units
- **THEN** the order is applied to the named unit belonging to the ordering player
- **AND** the other units in that square are unaffected

## ADDED Requirements

### Requirement: Rejected Order Publication

The system SHALL publish the orders it refused while resolving a turn as a
per-player file the client reads, so that a player learns why an order of theirs
had no effect. The file SHALL be written for every player on every resolved
turn, so it always describes the turn just resolved.

#### Scenario: An order is refused

- **WHEN** the server refuses one of a player's orders while resolving a turn
- **THEN** it writes that order to `players/<number>_rejected.yaml`
- **AND** records the unit's name, type, coordinates, and the reason it was refused

#### Scenario: No orders were refused

- **WHEN** the server resolves a turn without refusing any of a player's orders
- **THEN** `players/<number>_rejected.yaml` is written with no entries

#### Scenario: Rejections do not accumulate

- **WHEN** the server resolves a turn
- **THEN** the file it writes replaces the previous turn's rejections rather than adding to them

#### Scenario: Rejected orders are not player files

- **WHEN** the client scans the players directory to load player data
- **THEN** it skips the rejection files
- **AND** reads them separately

#### Scenario: A refused order leaves no unit behind

- **WHEN** the server refuses a deployment
- **THEN** no unit of that name exists on the board for that player
- **AND** the player is free to deploy it elsewhere on a later turn
