# cli-output Specification

## Purpose

How a command-line role writes what it was asked for. One view of the game per
subject, built once, is then either drawn as a table for a person or written as
JSON for a caller that is not one - so the two can never describe different
games. This is display only: it is not the format a game is stored or published
in, and it carries nothing that only means something to storage.

## Requirements

### Requirement: One View Behind Both Formats

Every `show` subject SHALL be rendered from a single view of the game — one
structure per subject, built once — which is then either drawn as a table or
written as JSON. A role SHALL NOT build its own view of a subject, and the two
formats SHALL NOT be produced from separate reads of the game, so the table and
the JSON can never disagree about what is on the board.

The view SHALL be built under the same visibility limit that applies to the
role asking for it: what a player may not see is absent from the view, and so
is absent from both formats.

#### Scenario: Same content in both formats

- **WHEN** a subject is shown as a table and then as JSON without the game
  changing in between
- **THEN** the rows of the table and the entries of the JSON document describe
  the same things, with the same values

#### Scenario: Visibility applies to both formats

- **WHEN** a player shows a subject as JSON
- **THEN** the JSON holds nothing the table form would have withheld from that
  player

#### Scenario: A listing a role prints without being asked

- **WHEN** a role lists units for a reason other than a `show` command, such as
  reading an order back to the player who gave it
- **THEN** it prints the same table `show units` would have printed, from the
  same view

### Requirement: Table Layout

Tabular `show` output SHALL be plain ASCII text with no colour, no cursor
control and no box-drawing characters, so it reads the same in a terminal, in a
pipe and in a test transcript.

A table SHALL consist of a header line naming each column, followed by one line
per row. Every column SHALL be padded to the width of the widest value in it,
including its header, so values line up down the page. Columns SHALL be
separated by at least two spaces. Numeric columns SHALL be right-aligned and
all other columns left-aligned. No line SHALL carry trailing whitespace.

A value the game does not have SHALL be written as `-` rather than as an empty
column or the word `None`.

#### Scenario: Columns line up

- **WHEN** a table with more than one row is printed
- **THEN** each column starts at the same character position on every line,
  header included

#### Scenario: Header names the columns

- **WHEN** a table is printed
- **THEN** its first line names every column in the order the rows present them

#### Scenario: Numbers are right-aligned

- **WHEN** a numeric column holds values of different widths
- **THEN** their last digits line up

#### Scenario: Missing value

- **WHEN** a row has no value for a column
- **THEN** that column reads `-`

#### Scenario: Nothing to show

- **WHEN** a subject has no rows at all
- **THEN** one line is printed saying there is nothing of that kind yet
- **AND** no header and no empty table are printed

### Requirement: Table Columns Per Subject

Each `show` subject SHALL present the columns named here, in this order, and
SHALL name them with these headers.

`types`: `PLAYER`, `NAME`, `SYMBOL`, `ATTACK`, `HEALTH`, `ENERGY`.

`units`: `PLAYER`, `NAME`, `TYPE`, `SYMBOL`, `ATTACK`, `HEALTH`, `ENERGY`,
`X`, `Y`, `STATE`, `DIRECTION`. `ATTACK`, `HEALTH` and `ENERGY` SHALL be the
unit's current values, which play wears down, not its type's. A unit that is
not on the board SHALL read `-` for `X` and `Y`. `DIRECTION` SHALL be the
direction of the order the unit is holding, and SHALL NOT be presented as a
heading the unit keeps: a unit does not face anywhere, and an order is used
once, so a unit holding no order SHALL read `-`.

`players`: `PLAYER`, `STATUS`.

`pending`: `PLAYER`, `UNIT`, `ORDER`, `X`, `Y`. A player asking holds their
own published orders and no other player's, which is what makes this theirs
to read: it is how an army that has been committed and not yet deployed is
read back.

`events`: `TURN`, `WHAT`, `WHERE`. One row per thing the turn did, oldest
first, in the words the domain gives it - the same sentence any other client
draws for the same event. `WHERE` SHALL be the square it happened on, filled
in for the events that are reported from inside a contest and do not repeat
the square in their own words.

`designs`: `PLAYER`, `NAME`, `SYMBOL`, `ATTACK`, `HEALTH`, `ENERGY`, `COST`,
`MET`. The statistics SHALL be the design as its owner built it rather than
the state a unit of it happened to be in when it was met, and `MET` the turn
it was first met on.

`board`: the existing ASCII grid, followed by a blank line and a legend table
with the columns `SYMBOL`, `PLAYER`, `TYPE`, holding one row per distinct
symbol drawn on the grid.

#### Scenario: Unit statistics are the unit's own

- **WHEN** a unit has lost health in combat
- **THEN** its `HEALTH` column shows what it has left, not what its type was
  built with

#### Scenario: A unit that is not on the board

- **WHEN** a unit is destroyed or has not been deployed
- **THEN** its `X` and `Y` columns read `-`

#### Scenario: Board legend

- **WHEN** `show board` is entered and the board holds units
- **THEN** the grid is printed as it always was
- **AND** a legend below it names the player and unit type each symbol on the
  grid stands for

#### Scenario: Board legend with an empty board

- **WHEN** `show board` is entered and no unit is visible on the board
- **THEN** the grid is printed and no legend is printed

### Requirement: Readable Values

Tabular output SHALL name things the way a player speaks of them, never with
the numbers used to store them.

A unit's state SHALL be written as `waiting` before it is deployed, `moving`
when it holds a movement order, `holding` when it holds no order, and
`destroyed` when it has been destroyed. The direction of an order SHALL be
written as `north`, `east`, `south` or `west`, or `-` where there is no order
to point anywhere. A player's status SHALL be written as `active` or
`eliminated`. A pending order SHALL be written as `move <direction>`, `deploy`
or `hold`.

#### Scenario: State is a word

- **WHEN** a unit holding a movement order is listed
- **THEN** its `STATE` column reads `moving` and not a number

#### Scenario: A direction is a word

- **WHEN** a unit ordered north is listed
- **THEN** its `DIRECTION` column reads `north` and not a number

#### Scenario: A unit under no orders has no direction

- **WHEN** a unit that is not holding an order is listed
- **THEN** its `DIRECTION` column reads `-`

#### Scenario: Eliminated player

- **WHEN** a player known to be eliminated is listed
- **THEN** their `STATUS` column reads `eliminated`

#### Scenario: Pending order

- **WHEN** a player has ordered a unit north for the coming turn
- **THEN** the `ORDER` column of that row reads `move north`

### Requirement: JSON Output

Every `show` subject SHALL accept the word `json` after its subject, and SHALL
then write its content as a single JSON document to standard output instead of
a table.

The document SHALL be a JSON object with one key naming the subject — `types`,
`units`, `players`, `pending` or `board` — whose value holds the same content
the table would have shown. List subjects SHALL hold an array, empty when there
is nothing to show, rather than a message. Field names SHALL be lower case and
stable, and numbers SHALL be written as JSON numbers, not as strings. Nothing
but the JSON document SHALL be written for the command, so a caller can read
the whole of standard output between prompts as JSON.

The JSON form SHALL NOT be the storage format: it names what a caller acts on
and SHALL NOT carry storage-internal fields.

#### Scenario: JSON is valid and complete

- **WHEN** `show units json` is entered
- **THEN** exactly one JSON document is printed
- **AND** it parses, and holds one entry per unit the table form would list

#### Scenario: Empty JSON result

- **WHEN** a list subject is shown as JSON and there is nothing to show
- **THEN** the document holds an empty array under that subject's key
- **AND** no "nothing to show" message is printed

#### Scenario: Numbers are numbers

- **WHEN** a subject holding statistics is shown as JSON
- **THEN** its numeric fields parse as JSON numbers

#### Scenario: The board as JSON

- **WHEN** `show board json` is entered
- **THEN** the document holds the board's dimensions and its rows of squares as
  the role may see them

### Requirement: A Command Line Can Read Everything A Browser Can

Every view the served contract offers SHALL be readable from a command-line
role, so that what a person can find out does not depend on which client they
are holding.

The interface is a client of the contract and so are the roles. A view the
browser draws and no role can ask for makes the browser the product rather
than a client of one.

#### Scenario: A view the interface reads

- **WHEN** the interface reads a view of a seat
- **THEN** some role's `show` offers that subject

#### Scenario: A command the interface sends

- **WHEN** the interface sends a command that changes a game
- **THEN** the grammar has a line that builds the same command

### Requirement: Show Grammar

The grammar SHALL read `show <subject> [json]`, where the only word accepted
after a subject is `json`. Any other trailing word SHALL be reported as an
invalid show command rather than ignored. The generated help SHALL show the
`json` form alongside each subject a role may use.

#### Scenario: Table by default

- **WHEN** `show units` is entered
- **THEN** the table form is printed

#### Scenario: JSON on request

- **WHEN** `show units json` is entered
- **THEN** the JSON form is printed

#### Scenario: Unrecognised trailing word

- **WHEN** `show units wibble` is entered
- **THEN** the command is reported as an invalid show command
- **AND** nothing is printed for it

#### Scenario: Help lists the JSON form

- **WHEN** `help` is entered
- **THEN** the `json` form is listed for the show subjects that role accepts
