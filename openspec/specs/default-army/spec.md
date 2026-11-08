# default-army Specification

## Purpose

What a new game and a newly registered player start with, so that a game can be
played without first being invented: the default board size, the default
catalogue of unit types, the default deployment built from that catalogue, and
the rules for when each is given and when it is not.

Everything given here is a starting point rather than a fixture. It is made of
ordinary setup decisions - a type defined, a unit deployed, a flag carried - so
a player edits it with the commands they already have, and nothing in it is
something they could not have typed themselves.

## Requirements

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
four statistics like any other. Each type with compute SHALL carry a default
program, so that a player who changes nothing fields an army that plays.

No type in the catalogue SHALL be drawn with the glyph an empty square is
drawn with, because a unit a player cannot tell from a bare square is a unit
they cannot see on their own board.

The catalogue SHALL be:

| Name   | Symbol | Attack | Health | Energy | Compute | Cost | Move fare | Default program |
|--------|--------|--------|--------|--------|---------|------|-----------|-----------------|
| Wall   | `W`    | 0      | 10     | 0      | 0       | 10   | 3         | none: no controller |
| Scout  | `o`    | 0      | 2      | 12     | 6       | 20   | 1         | explorer: walks to the nearest unknown square, stepping round its own units, the enemies its army knows of and the board's edge, a step aside when the way is blocked; sleeps when there is nothing left to find, or when twenty turns have not brought it nearer to what it is looking for |
| Pawn   | `p`    | 1      | 4      | 2      | 3       | 10   | 1         | vanguard: steps towards the enemy's edge when it can afford a step and a strike, never onto one of its own, and fights what it walks into; sleeps a turn otherwise |
| Runner | `r`    | 2      | 4      | 10     | 5       | 21   | 1         | hunter: walks to the nearest enemy flag, round its own units, fighting what it meets |
| Line   | `L`    | 3      | 6      | 12     | 4       | 25   | 2         | hunter |
| Lance  | `!`    | 8      | 2      | 10     | 4       | 24   | 1         | hunter |
| Keep   | `K`    | 1      | 10     | 5      | 8       | 24   | 3         | warden: holds its square, sleeping a hundred turns at a time, and strikes back when woken |
| Heavy  | `H`    | 5      | 10     | 15     | 4       | 34   | 3         | hunter |

The default programs SHALL be written in the instruction set `unit-program`
defines, SHALL be deterministic, and SHALL each fit the tick cap of the type
that carries them on every turn. The hunter SHALL sleep when it cannot afford
both a step and a strike, so that it arrives able to fight, and SHALL sleep a
turn rather than hold when both ways round stand its own units, so that
waiting for the way to clear costs nothing. The vanguard SHALL never step
onto a square one of its own stands on.

Defining a type spends nothing, so the catalogue SHALL cost a player nothing
until they deploy a unit of one of its types.

The catalogue SHALL be the player's own. A player SHALL be able to redefine
any of its types under the same name, with a program of their own or none,
define types of their own alongside it, and never deploy the ones they do not
want.

#### Scenario: A player is registered

- **WHEN** a player is registered in a game
- **THEN** they hold the eight catalogue types
- **AND** each has the statistics and the default program named above

#### Scenario: The catalogue is free until it is used

- **WHEN** a player has been given the catalogue and has deployed nothing
- **THEN** they have spent none of their budget

#### Scenario: A player redefines a catalogue type

- **WHEN** a player defines a type named `Heavy` with statistics and a program of their own
- **THEN** the type named `Heavy` holds the statistics and program they gave it
- **AND** the rest of the catalogue is unchanged

#### Scenario: A player adds to the catalogue

- **WHEN** a player defines a type under a name the catalogue does not use
- **THEN** they hold that type as well as the eight

#### Scenario: A seat that changes nothing plays

- **WHEN** two players commit the stock army unchanged
- **THEN** the game is resolved with every unit running its type's default program
- **AND** at least one unit of each army moves on the first turn of play

#### Scenario: The whole army gets out

- **WHEN** two players commit the stock army unchanged
- **THEN** every unit of each array with a controller, the Keeps excepted, stands on a square other than the one it was seeded on at some turn within the first twenty turns of play

#### Scenario: A blocked hunter costs nothing

- **WHEN** a unit running the hunter finds one of its own both ways round on a turn
- **THEN** it sleeps that turn and pays no energy for the thinking beyond the ticks it took to find out

### Requirement: A Two-Player Game Is Given A Default Deployment

The system SHALL deploy a default array of sixteen units for each player of a
two-player game, and SHALL set that player's flag on one of its Keeps.

The array SHALL be symmetric about the middle of the board: whatever stands in
a column SHALL stand in that column's mirror. An army that is stronger on one
flank than the other before anybody has moved is an accident rather than a
design, and it is what forces a pair of Keeps - an eight-column row has no
middle square to stand a single one on. Which of the pair carries the flag
SHALL be fixed by the rules rather than left to the order a list is held in.

The array SHALL be described by depth from the player's own edge of the board,
and SHALL be laid out the same way for both players, so that each faces a
mirror of the other. Depth 0 is the row at the player's own edge; depth 1 is
the row in front of it. Columns SHALL be the same for both players.

| Depth | c0     | c1    | c2   | c3   | c4   | c5   | c6    | c7     |
|-------|--------|-------|------|------|------|------|-------|--------|
| 1     | Pawn   | Pawn  | Line | Heavy| Heavy| Line | Pawn  | Pawn   |
| 0     | Runner | Scout | Wall | Keep | Keep | Wall | Scout | Runner |

The front rank SHALL be made of units whose default programs leave it, so
that the rank behind is not boxed in by it: nothing in the array's back rank
SHALL stand behind a unit that never moves. The Walls SHALL stand beside the
Keeps, where what they cannot do - move - is what a flag's flanks want.

The array SHALL cost 308 points, and SHALL use only types the catalogue holds.
It SHALL NOT be required to use every one of them: eight pairs of eight
different types cost more than the default budget covers.

#### Scenario: Both players are given the array

- **WHEN** a two-player game is created and both players are registered
- **THEN** each player's seat opens holding the sixteen units of the array, deployed

#### Scenario: The array is placed where the player may place

- **WHEN** the array is deployed for a player
- **THEN** every unit of it stands inside the rows that player may deploy in

#### Scenario: A player is told only about their own army

- **WHEN** a player opens their seat holding the array
- **THEN** they see their own sixteen units and none of the other player's

#### Scenario: The array is a mirror of itself

- **WHEN** the array is deployed
- **THEN** the unit in each column of each row is of the same type as the unit in that column's mirror

#### Scenario: A Keep carries the flag

- **WHEN** the array is deployed for a player
- **THEN** that player's flag is on the Keep in the lower-numbered of the two middle columns

#### Scenario: The array is committed as it stands

- **WHEN** a player commits without changing the array
- **THEN** the commit is accepted and every unit of the array is published

#### Scenario: Nothing stands behind a unit that never moves

- **WHEN** the array is deployed
- **THEN** every unit in the back rank with a controller stands behind a unit whose default program moves it

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
- **THEN** they hold sixteen units, not thirty-two

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

A player given the default budget and the default array SHALL hold 12 points
they have not spent.

#### Scenario: What the array costs

- **WHEN** a player is given the default array on the default budget
- **THEN** they have spent 308 points
- **AND** 12 points remain

#### Scenario: Taking a default unit back returns its points

- **WHEN** a player takes back a Heavy from the default array
- **THEN** 34 points are returned to them

#### Scenario: A budget too small for the array

- **WHEN** a player is registered with a budget smaller than the array costs
- **THEN** they are given no default array
- **AND** they hold the catalogue
