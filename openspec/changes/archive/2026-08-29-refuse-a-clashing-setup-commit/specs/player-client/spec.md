## ADDED Requirements

### Requirement: A Unit Deployed And Not Committed Can Be Taken Back

The system SHALL let a player take back one of their own units while their
setup has not been committed, naming the unit. Taking one back SHALL free the
square it stood on, return the points it cost, and release its name for reuse:
it is the same as never having deployed it. Where the unit carried the
player's flag, the flag SHALL be left carried by nobody, and the setup SHALL
be refused until another unit carries it.

The system SHALL refuse to take back a unit once the player's setup has been
committed: from that point the units are published and playing, and what
happens to them is the game's business rather than the player's. It SHALL
refuse a unit that belongs to another player, and one that does not exist,
saying which.

This is what makes a refused commit something a player can act on: a setup
turned back for clashing with another player's square is fixed by taking the
offending unit back and deploying it elsewhere.

#### Scenario: Taking a unit back

- **WHEN** a player takes back a unit they deployed and have not committed
- **THEN** the unit is gone from their army
- **AND** the square it stood on is free
- **AND** the points it cost are theirs to spend again
- **AND** its name can be used for another unit

#### Scenario: Taking back the flag carrier

- **WHEN** a player takes back the unit carrying their flag
- **THEN** no unit carries their flag
- **AND** their setup cannot be committed until one does

#### Scenario: After the setup is committed

- **WHEN** a player whose setup is committed tries to take a unit back
- **THEN** it is refused, saying the setup is committed

#### Scenario: A unit that is not theirs

- **WHEN** a player tries to take back a unit belonging to another player, or one that does not exist
- **THEN** it is refused, saying no unit of theirs is called that

#### Scenario: It survives the session being reopened

- **WHEN** a player takes a unit back and opens their session again
- **THEN** the unit is still gone

### Requirement: An Order Given And Not Committed Can Be Taken Back

The system SHALL let a player take back the order one of their own units was
given this turn, naming the unit, for as long as the turn has not been
committed. The unit SHALL be left with no order at all rather than an order to
hold: a unit that was never ordered and one whose order was taken back are the
same unit, so it pays no fare, moves nowhere, and rests like any other unit
that was given nothing to do.

The system SHALL refuse this before the first turn is complete, where there
are no orders to take back, and SHALL refuse it for a unit that is not the
player's or does not exist.

#### Scenario: Taking back an order

- **WHEN** a player takes back the order they gave one of their units this turn
- **THEN** that unit holds no direction and is not moving

#### Scenario: The unit does not move

- **WHEN** the turn resolves after an order was taken back
- **THEN** the unit is where it was, and paid no fare

#### Scenario: The unit rests

- **WHEN** the turn resolves after an order was taken back, and the unit is below the energy its type was designed with
- **THEN** it recovers a point, as a unit given no order does

#### Scenario: Before the first turn

- **WHEN** a player tries to take back an order during setup
- **THEN** it is refused, saying there are no orders until the first turn is complete
