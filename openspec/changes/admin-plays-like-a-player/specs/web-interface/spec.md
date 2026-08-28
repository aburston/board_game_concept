## MODIFIED Requirements

### Requirement: A Person Finds And Joins A Game From A Lobby

The system SHALL present a lobby listing the games that exist, and for each
the seats it holds, which are taken and by whom, and which are open. A person
SHALL be able to take an open seat from the lobby, and to return to a game
they already hold a seat in.

The lobby SHALL show how many seats are still open in a game that is being set
up, so that a person can see whether it is waiting for them.

An open seat SHALL be offered to every account that may hold one - a registered
player and the administrator alike - and SHALL be withheld only from the
observer, which holds no seat in any game. The lobby SHALL decide what to offer
by whether the account may take the seat, and not by the kind of account it is
looking at.

A seat the administrator holds SHALL be shown, entered and played through the
same screens as any other seat, and the administrator's own screens - creating
a game, setting one up, watching one - SHALL be offered beside them rather than
in place of them.

#### Scenario: Seeing the games

- **WHEN** the lobby is shown
- **THEN** every game is listed with its state and its seats
- **AND** each seat says whether it is taken and by whom

#### Scenario: Taking a seat

- **WHEN** an open seat is taken from the lobby
- **THEN** the person holds that seat
- **AND** they are brought to that game

#### Scenario: Returning to a game

- **WHEN** a person holding a seat opens the lobby
- **THEN** the games they hold a seat in are shown as theirs
- **AND** they may return to any of them

#### Scenario: A seat taken while it was being looked at

- **WHEN** a seat is taken by somebody else and then taken from the lobby
- **THEN** the refusal is reported
- **AND** the lobby shows the seat as taken

#### Scenario: The administrator is offered an open seat

- **WHEN** the administrator opens the lobby on a game being set up with an open
  seat
- **THEN** that seat is offered to be taken
- **AND** taking it brings them to that seat as it would anybody

#### Scenario: The observer is offered none

- **WHEN** the observer opens the lobby on a game with an open seat
- **THEN** no seat is offered to be taken
- **AND** the game may still be watched

#### Scenario: Playing and administering from one lobby

- **WHEN** the administrator holds a seat in a game the lobby lists
- **THEN** the game is shown as theirs and the seat may be played
- **AND** the administrator's own way into that game is offered as well
