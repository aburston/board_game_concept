## MODIFIED Requirements

### Requirement: A Game Can Be Created Over The Served Interface

The system SHALL let the administrator create a game over the served
interface, and SHALL refuse to create one to any other identity. A created
game SHALL be new: a board of the default size, no registered players, and
nothing played.

Creating a game SHALL be refused where a game of that number already exists,
and SHALL leave the existing game untouched.

#### Scenario: The administrator creates a game

- **WHEN** the administrator asks for a new game
- **THEN** the game exists and is listed
- **AND** it has a board of the default size and no registered players

#### Scenario: A player tries to create a game

- **WHEN** an identity that is not the administrator asks for a new game
- **THEN** it is refused
- **AND** no game is created

#### Scenario: A game number already in use

- **WHEN** a game is created with the number of a game that exists
- **THEN** it is refused
- **AND** the existing game is unchanged

#### Scenario: A created game is set up as any other

- **WHEN** a game created this way is set up
- **THEN** its board is resized and its players registered by the same
  commands as a game created any other way
