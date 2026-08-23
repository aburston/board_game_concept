## MODIFIED Requirements

### Requirement: Pending Order Detection

The system SHALL detect that a player's own committed orders are still pending
and report that the turn is incomplete. A player's orders SHALL be treated as
pending until the turn that consumes them has been published in full, so that a
session loading a game while a turn is being resolved is told the turn is
incomplete rather than being given a partly published one.

A draft SHALL NOT be treated as a pending commit: a player who has drafted work
and not committed it has an open turn, not an unresolved one.

#### Scenario: Detecting an unresolved commit

- **WHEN** a player loads a game and their own pending order file still exists
- **THEN** the game data reports unprocessed moves

#### Scenario: Loading while a turn is being resolved

- **WHEN** a player loads a game after the server has begun resolving the turn they committed to and before it has published everything that turn produced
- **THEN** the game data reports unprocessed moves
- **AND** the player is not shown a partly published turn

#### Scenario: A draft is not an unresolved commit

- **WHEN** a player loads a game holding a draft and no published orders
- **THEN** the game data reports no unprocessed moves
- **AND** the player may continue to give orders

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

A player's pending orders SHALL NOT be removed until everything the turn
produced has been published, because their removal is what releases a player
waiting on that turn. Orders published on a player's behalf for the turn *about
to be* resolved SHALL be written after that removal, so that seeding the next
turn cannot erase them.

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

#### Scenario: Orders are removed only once the turn is published

- **WHEN** the server resolves a turn
- **THEN** it writes the turn number, each player's file and refusals, the record of every unit, and every player's view
- **AND** only then removes the pending order files

#### Scenario: Seeding the next turn does not erase it

- **WHEN** the server resolves a turn for a game whose player was loaded from a file holding units
- **THEN** that player's units are published as their orders for the turn about to be resolved
- **AND** those orders survive the removal of the turn's consumed orders
- **AND** the units reach the board when that turn is resolved

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
