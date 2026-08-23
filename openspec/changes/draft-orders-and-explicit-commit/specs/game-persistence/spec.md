## ADDED Requirements

### Requirement: Draft Persistence

The system SHALL store each session's uncommitted work in a per-session file
under the game's players directory, separate from the orders that session has
published. The file SHALL record the turn the work was drafted for.

A draft file SHALL be read only for the session that owns it. Loading a game
SHALL NOT read another session's draft, in the same way that a client reads its
own view rather than the shared record of all units.

A draft SHALL be removed when its owner commits, the work having become their
published orders.

#### Scenario: Writing a draft

- **WHEN** a session carries out an action without committing
- **THEN** the action is written to that session's draft file under `games/_<gameno>/players`
- **AND** the file records the turn it was drafted for

#### Scenario: Reading a draft back

- **WHEN** a game is loaded and the loading session's draft file exists and names the current turn
- **THEN** the actions it holds are applied to the game the session sees

#### Scenario: A session does not read another's draft

- **WHEN** a game is loaded
- **THEN** no draft file belonging to another player is read
- **AND** the administrator's session reads no player's draft

#### Scenario: Committing removes the draft

- **WHEN** a player commits
- **THEN** their draft file is removed
- **AND** their published orders hold the work it held

#### Scenario: A game with no draft

- **WHEN** a game is loaded and the loading session has no draft file
- **THEN** the game loads as though the draft were empty
- **AND** nothing is reported as missing

## MODIFIED Requirements

### Requirement: Order Publication

The system SHALL have players publish pending orders as a per-player file that
the server consumes when resolving a turn, and SHALL apply each order to the
unit it names rather than to whatever occupies the square. A player SHALL publish
orders only for units in play: a destroyed unit SHALL NOT be published as an
order of any kind.

Committing SHALL be recorded as a fact about a player and a turn, rather than
inferred from the presence of a file, so that the system can answer whether a
given player has committed for the turn now open. Which players the commit
barrier is waiting for SHALL be determined from that record.

#### Scenario: Player publishes orders

- **WHEN** a player commits
- **THEN** their pending orders are written to `players/<number>_units.yaml`
- **AND** a marker file `players/commit_<number>` records that they have committed
- **AND** the marker records the turn they committed for

#### Scenario: Determining who has committed

- **WHEN** the system is asked which players have committed for the turn now open
- **THEN** the answer comes from the commit records
- **AND** a player whose most recent commit was for an earlier turn is not counted

#### Scenario: A player who has drafted but not committed

- **WHEN** a player has drafted orders and has not committed
- **THEN** they are not counted as having committed
- **AND** the turn is still held open for them

#### Scenario: Destroyed units are not published as orders

- **WHEN** a player commits while holding destroyed units
- **THEN** no order is published for any destroyed unit
- **AND** the server has nothing to refuse on their account

#### Scenario: Server consumes orders

- **WHEN** the server resolves a turn
- **THEN** it applies each player's pending orders according to unit state: deploying units in `INITIAL`, moving units in `MOVING`, and leaving units in `NOP` in place
- **AND** it removes the pending order files afterwards

#### Scenario: An order naming a destroyed unit

- **WHEN** a player publishes an order for a unit the server holds as destroyed
- **THEN** the server refuses the order
- **AND** creates no unit
- **AND** resolves the turn without it

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

### Requirement: Pending Order Detection

The system SHALL detect that a player's own committed orders are still pending
and report that the turn is incomplete. A draft SHALL NOT be treated as a
pending commit: a player who has drafted work and not committed it has an open
turn, not an unresolved one.

#### Scenario: Detecting an unresolved commit

- **WHEN** a player loads a game and their own pending order file still exists
- **THEN** the game data reports unprocessed moves

#### Scenario: A draft is not an unresolved commit

- **WHEN** a player loads a game holding a draft and no published orders
- **THEN** the game data reports no unprocessed moves
- **AND** the player may continue to give orders
