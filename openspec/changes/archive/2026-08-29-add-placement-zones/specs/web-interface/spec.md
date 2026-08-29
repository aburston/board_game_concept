## ADDED Requirements

### Requirement: The Deploy Board Greys Out Where A Seat May Not Place

While a seat is deploying units, the system SHALL draw the squares that seat
may not place in as greyed out, reading the allowed area from the contract
rather than working the rule out itself, and SHALL NOT let a unit be placed on
a greyed square. It SHALL say, near the board, why part of it is greyed — that
in a two-player game each player deploys on their own half and the middle row,
where there is one, is neutral.

The greying SHALL apply only while placing units during setup. Once setup is
committed, or on the play board of a resolved game, the board SHALL be drawn
without it.

#### Scenario: A restricted seat sees the other half greyed

- **WHEN** a seat in a two-player game is deploying units
- **THEN** the squares of the other half, and any neutral row, are drawn greyed out
- **AND** the seat's own half is drawn normally

#### Scenario: Nothing can be deployed on a greyed square

- **WHEN** a seat chooses a greyed square while deploying
- **THEN** no unit is deployed there

#### Scenario: An unrestricted seat sees no greying

- **WHEN** a seat in a game that is not two-player is deploying units
- **THEN** the whole board is drawn without greying

#### Scenario: The greying is only for placing

- **WHEN** the seat has committed its setup, or is looking at the play board
- **THEN** the board is drawn without any placement greying
