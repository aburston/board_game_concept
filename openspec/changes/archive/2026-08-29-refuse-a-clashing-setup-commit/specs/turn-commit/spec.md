## ADDED Requirements

### Requirement: A Setup Commit Clashing With A Committed Square Is Refused

The system SHALL refuse a player's **setup** commit when one of the units it
deploys stands on a square another player has already committed a unit to, and
SHALL name that square in the refusal so the player can deploy elsewhere.

The refused commit SHALL leave that player's setup exactly as it was — nothing
committed, nothing published, every unit and type still theirs to change — so
that they may move the unit and commit again. Setup stays open for them, and
the turn is not held to have begun.

The square SHALL be kept by the setup that was committed first. Where a
deployment reaches the server without having been through a commit — a loaded
player file, or orders written by hand — it SHALL still be refused when the
turn resolves, because nothing checked it on the way in.

This rule SHALL apply to the **setup commit only**. Two things follow from it
that are accepted for setup and would not be for a turn of play: the order in
which players commit decides who keeps a contested square, and the refusal
tells the refused player that the square is occupied, which contact-based
visibility otherwise withholds. Deployments happen only during setup, so
there is nothing for this to reach on any later turn.

#### Scenario: A setup commit that lands on a committed square

- **WHEN** a player commits a setup deploying a unit onto a square another player has already committed a unit to
- **THEN** the commit is refused, naming the square
- **AND** that player's setup is still uncommitted, with its units and types unchanged

#### Scenario: The refused player deploys elsewhere and commits

- **WHEN** a player whose setup commit was refused for a clash moves the unit to a free square and commits again
- **THEN** the commit is accepted

#### Scenario: The first setup committed keeps the square

- **WHEN** two players commit setups deploying onto the same square, one after the other
- **THEN** the first keeps the square and stays committed
- **AND** only the second is refused

#### Scenario: A setup that clashes with nothing

- **WHEN** a player commits a setup whose deployments are all on squares nobody has committed to
- **THEN** the commit is accepted

#### Scenario: A clash reaching the server without a commit

- **WHEN** deployments onto one square reach the server without having been through a commit
- **THEN** they are refused when the turn resolves, as they are today

## REMOVED Requirements

### Requirement: Deployment On First Resolution

**Reason**: The clause "when two deployments contend for one square in the same
turn, the system SHALL refuse both, so that no player gains from the order
their orders happen to be read in" no longer holds for a setup commit: the
commit is refused instead, and the setup that was committed first keeps the
square. Replaced by "Deployment On First Resolution, After A Commit That Was
Accepted", which keeps every other part of the rule unchanged.

**Migration**: A clash between two setup commits is now refused at the second
commit rather than destroying both deployments at resolution. A clash that
reaches the server without a commit is still refused at resolution and still
refuses every claimant, so nothing that bypasses a commit gains an advantage.

## ADDED Requirements

### Requirement: Deployment On First Resolution, After A Commit That Was Accepted

The system SHALL place newly created units onto the board when the turn is
resolved. Deploying a brand new unit onto a square that is already taken is
illegal: the system SHALL refuse the deployment and SHALL resolve the turn
without it, rather than failing the turn.

Where two deployments that never passed through an accepted commit contend for
one square in the same turn, the system SHALL refuse both, so that nothing
which bypasses a commit is favoured by the order it happens to be read in.

#### Scenario: Deploying a new unit

- **WHEN** a turn is resolved and a unit is in the `INITIAL` state
- **THEN** the unit is placed at its assigned coordinates
- **AND** the unit moves to the `NOP` state

#### Scenario: Deploying onto an occupied square

- **WHEN** a unit is deployed at coordinates that already hold a unit
- **THEN** the deployment is refused with an error naming the unit and the square
- **AND** no unit is created
- **AND** the unit already holding the square is unaffected

#### Scenario: Two unchecked deployments onto one square in the same turn

- **WHEN** two units that never passed through an accepted commit are deployed at the same coordinates before the turn is resolved
- **THEN** both are refused
- **AND** the turn resolves with neither on that square
- **AND** the square is left empty

#### Scenario: Deployment is not movement

- **WHEN** a unit already on the board is ordered to move into a square another unit holds
- **THEN** the order is allowed
- **AND** the two units contest the square
