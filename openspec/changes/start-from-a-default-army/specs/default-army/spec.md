## Purpose

What a new game and a newly registered player start with, so that a game can be
played without first being invented: the default board size, the default
catalogue of unit types, the default deployment built from that catalogue, and
the rules for when each is given and when it is not.

Everything given here is a starting point rather than a fixture. It is made of
ordinary setup decisions - a type defined, a unit deployed, a flag carried - so
a player edits it with the commands they already have, and nothing in it is
something they could not have typed themselves.

## ADDED Requirements

### Requirement: A New Game Has A Default Board

The system SHALL give a created game a board of the default size, which SHALL
be 8 squares by 8 squares, rather than leaving it unsized.

The board SHALL be an ordinary board in every other respect: the administrator
can resize it, and resize it again, until setup is committed.

#### Scenario: A game is created

- **WHEN** a game is created
- **THEN** its board is 8 by 8
- **AND** it is reported with that size wherever games are listed

#### Scenario: The administrator resizes the default board

- **WHEN** the administrator sizes the board of a created game to 12 by 6
- **THEN** the board is 12 by 6
- **AND** the default size is not restored

### Requirement: Every Registered Player Is Given The Default Catalogue

The system SHALL give every player registered in a game a catalogue of eight
unit types. Each SHALL be a type as any other, and SHALL cost the sum of its
statistics like any other.

The catalogue SHALL be:

| Name   | Symbol | Attack | Health | Energy | Cost | Move fare |
|--------|--------|--------|--------|--------|------|-----------|
| Wall   | `#`    | 0      | 10     | 0      | 10   | 3         |
| Scout  | `o`    | 0      | 2      | 12     | 14   | 1         |
| Pawn   | `p`    | 1      | 4      | 2      | 7    | 1         |
| Runner | `r`    | 2      | 4      | 10     | 16   | 1         |
| Line   | `L`    | 3      | 6      | 12     | 21   | 2         |
| Lance  | `!`    | 8      | 2      | 10     | 20   | 1         |
| Keep   | `K`    | 1      | 10     | 5      | 16   | 3         |
| Heavy  | `H`    | 5      | 10     | 15     | 30   | 3         |

Defining a type spends nothing, so the catalogue SHALL cost a player nothing
until they deploy a unit of one of its types.

The catalogue SHALL be the player's own. A player SHALL be able to redefine
any of its types under the same name, define types of their own alongside it,
and never deploy the ones they do not want.

#### Scenario: A player is registered

- **WHEN** a player is registered in a game
- **THEN** they hold the eight catalogue types
- **AND** each has the statistics named above

#### Scenario: The catalogue is free until it is used

- **WHEN** a player has been given the catalogue and has deployed nothing
- **THEN** they have spent none of their budget

#### Scenario: A player redefines a catalogue type

- **WHEN** a player defines a type named `Heavy` with statistics of their own
- **THEN** the type named `Heavy` holds the statistics they gave it
- **AND** the rest of the catalogue is unchanged

#### Scenario: A player adds to the catalogue

- **WHEN** a player defines a type under a name the catalogue does not use
- **THEN** they hold that type as well as the eight

### Requirement: A Two-Player Game Is Given A Default Deployment

The system SHALL deploy a default array of fifteen units for each player of a
two-player game, and SHALL set that player's flag on the Keep.

The array SHALL be described by depth from the player's own edge of the board,
and SHALL be laid out the same way for both players, so that each faces a
mirror of the other. Depth 0 is the row at the player's own edge; depth 1 is
the row in front of it. Columns SHALL be the same for both players.

| Depth | c0     | c1   | c2    | c3    | c4    | c5   | c6     | c7   |
|-------|--------|------|-------|-------|-------|------|--------|------|
| 1     | Pawn   | Pawn | Wall  | Heavy | Heavy | Wall | Pawn   | Pawn |
| 0     | Runner | Line | Scout | Keep  | Lance | Line | Runner | -    |

The array SHALL cost 232 points, and SHALL use only types the catalogue holds.

Every unit in the array SHALL fall inside the placement area the player is
allowed to deploy in, so that the array can be committed as it stands.

#### Scenario: Both players are given the array

- **WHEN** a two-player game has been created and both players registered
- **THEN** each player holds fifteen units laid out as above
- **AND** the lower-numbered player's depth 0 is the board's first row
- **AND** the other player's depth 0 is the board's last row

#### Scenario: The array is placed where the player may place

- **WHEN** a player is given the default array
- **THEN** every unit of it stands inside that player's placement area

#### Scenario: A player is told only about their own army

- **WHEN** a turn is resolved and each player reads what it did
- **THEN** neither is told where the other's units were placed

#### Scenario: The Keep carries the flag

- **WHEN** a player is given the default array
- **THEN** their flag stands on the Keep
- **AND** the setup can be committed without any further decision

#### Scenario: The array is committed as it stands

- **WHEN** both players commit the setup they were given, unedited
- **THEN** both setups are accepted
- **AND** the game reaches its first turn

### Requirement: The Default Deployment Is Given Once And Then Left Alone

The system SHALL give a player the default deployment only where that player
has made no setup decision of their own. Once they have, the deployment they
hold SHALL be theirs, and the system SHALL NOT add to it, restore it, or
replace it.

A player SHALL be able to take the default units back and deploy others in
their place, by the commands that take back any deployment.

#### Scenario: A player edits the array and opens their seat again

- **WHEN** a player takes back a Heavy, deploys a Line in its place, and opens
  their seat again
- **THEN** they hold the Line and not the Heavy
- **AND** no default unit is restored

#### Scenario: A player takes the whole array back

- **WHEN** a player takes back every unit of the default array
- **THEN** they hold no units
- **AND** opening their seat again does not deploy the array a second time

#### Scenario: The array is not deployed twice

- **WHEN** a player who was given the array opens their seat repeatedly before
  committing
- **THEN** they hold fifteen units, not thirty

### Requirement: The Default Deployment Is Given Only Where It Fits

The system SHALL deploy the default array only in a game of exactly two
players whose board has room for it inside each player's placement area.
Where it does not fit, no unit SHALL be deployed and no flag SHALL be set, and
the player SHALL still be given the catalogue.

A player who was given no deployment SHALL set up as they always did: design,
deploy and carry the flag by hand.

#### Scenario: A game of three players

- **WHEN** three players are registered in a game
- **THEN** none of them is given the default array
- **AND** each of them holds the catalogue

#### Scenario: A game of one player

- **WHEN** one player is registered in a game
- **THEN** they are given no default array
- **AND** they hold the catalogue

#### Scenario: A board too small for the array

- **WHEN** a two-player game's board is too small to hold the array inside a
  player's placement area
- **THEN** that player is given no default array
- **AND** they hold the catalogue
- **AND** they can deploy by hand as they always could

#### Scenario: Setting up by hand after no deployment

- **WHEN** a player who was given no array designs a type, deploys a unit and
  carries the flag
- **THEN** the setup is committed as any hand-made setup is

### Requirement: The Default Deployment Is Paid For Like Any Other

The system SHALL charge the default array against the player's budget by the
rules that charge any deployment. What the player has spent SHALL be derived
from the board, so a default unit taken back SHALL return its points.

A player given the default budget and the default array SHALL hold 18 points
they have not spent.

#### Scenario: What the array costs

- **WHEN** a player is given the default array on the default budget
- **THEN** they have spent 232 points
- **AND** 18 points remain

#### Scenario: Taking a default unit back returns its points

- **WHEN** a player takes back a Heavy from the default array
- **THEN** 30 points are returned to them

#### Scenario: A budget too small for the array

- **WHEN** a player is registered with a budget smaller than the array costs
- **THEN** they are given no default array
- **AND** they hold the catalogue
