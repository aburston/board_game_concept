## ADDED Requirements

### Requirement: The Armoury Lists What Is Deployed And Offers To Take It Back

The system SHALL list, in the armoury, the units this seat has deployed and
not committed, each with the square it stands on, and SHALL offer to take any
of them back. Taking one back SHALL free its square and its points, and the
board SHALL be redrawn without it.

The list SHALL NOT be offered once the seat's setup is committed, where taking
a unit back is refused.

#### Scenario: The deployed units are listed

- **WHEN** a seat has deployed units and not committed them
- **THEN** each is listed with its name, its type and its square

#### Scenario: Taking one back from the armoury

- **WHEN** the player takes a listed unit back
- **THEN** it is gone from the list and from the board
- **AND** the other units are untouched

#### Scenario: A commit refused for a clash can be fixed

- **WHEN** a commit is refused because a unit clashes with a square another player has committed to
- **THEN** the seat stays in the armoury with its units listed
- **AND** taking the clashing unit back and committing again is accepted

### Requirement: An Order Can Be Taken Back From The Board

The system SHALL offer, for a unit under orders whose turn is not committed, a
way to take that order back — both from the keyboard, beside the arrow keys
that give one, and as a control for a hand on a mouse. It SHALL offer it only
for a unit that has an order to take back, and SHALL say so in the keyboard
help.

#### Scenario: Taking an order back with the keyboard

- **WHEN** a unit is selected and has been ordered to move, and the take-back key is pressed
- **THEN** the unit holds no order
- **AND** the arrow drawn for it is gone

#### Scenario: A unit with no order

- **WHEN** a unit with no order is selected
- **THEN** no take-back control is offered for it

### Requirement: A Statistic Cannot Be Typed Outside Its Range

The system SHALL bound the number fields it offers to the ranges the rules
enforce — a unit type's attack, health and energy, the board's size, and a
seat's number and budget — so that a value the server would refuse cannot be
submitted from the interface. A negative attack was accepted by the field,
sent, and refused only by the server.

#### Scenario: A negative statistic

- **WHEN** a negative value is entered for a unit type's attack, health or energy
- **THEN** the form does not submit it

#### Scenario: The bounds are the rules'

- **WHEN** the design fields are shown
- **THEN** attack accepts 0 to 10, health 1 to 10, and energy 0 to 100
