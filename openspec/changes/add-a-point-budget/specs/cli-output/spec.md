## MODIFIED Requirements

### Requirement: Table Columns Per Subject

Each `show` subject SHALL present the columns named here, in this order, and
SHALL name them with these headers.

`types`: `PLAYER`, `NAME`, `SYMBOL`, `ATTACK`, `HEALTH`, `ENERGY`, `COST`.
`COST` SHALL be the type's point cost as `point-budget` prices it, so a player
can read what deploying one unit of the type will spend.

`units`: `PLAYER`, `NAME`, `TYPE`, `SYMBOL`, `ATTACK`, `HEALTH`, `ENERGY`,
`X`, `Y`, `STATE`, `DIRECTION`. `ATTACK`, `HEALTH` and `ENERGY` SHALL be the
unit's current values, which play wears down, not its type's. A unit that is
not on the board SHALL read `-` for `X` and `Y`. `DIRECTION` SHALL be the
direction of the order the unit is holding, and SHALL NOT be presented as a
heading the unit keeps: a unit does not face anywhere, and an order is used
once, so a unit holding no order SHALL read `-`.

`players`: `PLAYER`, `STATUS`, `BUDGET`, `SPENT`, `LEFT`. The three point
columns SHALL be that player's point budget, what they have spent of it, and
what is left. Where the session is not entitled to know them — another
player's, seen from a player's own session — all three SHALL read `-`.

`pending`: `PLAYER`, `UNIT`, `ORDER`, `X`, `Y`.

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

#### Scenario: A type's cost

- **WHEN** a type with attack 1, health 10 and energy 10 is listed
- **THEN** its `COST` column reads 21

#### Scenario: A player's own points

- **WHEN** a player lists the registered players and has spent 63 of a
  100-point budget
- **THEN** their own row reads 100, 63 and 37 under `BUDGET`, `SPENT` and `LEFT`

#### Scenario: Another player's points are not shown

- **WHEN** a player lists the registered players
- **THEN** another player's `BUDGET`, `SPENT` and `LEFT` columns all read `-`

#### Scenario: The administrator sees every player's points

- **WHEN** the administrator or the observer lists the registered players
- **THEN** every row carries that player's `BUDGET`, `SPENT` and `LEFT`

#### Scenario: Board legend

- **WHEN** `show board` is entered and the board holds units
- **THEN** the grid is printed as it always was
- **AND** a legend below it names the player and unit type each symbol on the
  grid stands for

#### Scenario: Board legend with an empty board

- **WHEN** `show board` is entered and no unit is visible on the board
- **THEN** the grid is printed and no legend is printed

### Requirement: JSON Output

Every `show` subject SHALL accept the word `json` after its subject, and SHALL
then write its content as a single JSON document to standard output instead of
a table.

The document SHALL be a JSON object with one key naming the subject — `types`,
`units`, `players`, `pending` or `board` — whose value holds the same content
the table would have shown. List subjects SHALL hold an array, empty when there
is nothing to show, rather than a message. Field names SHALL be lower case and
stable, and numbers SHALL be written as JSON numbers, not as strings. A number
the session is not entitled to know SHALL be written as JSON `null` rather than
as the `-` the table draws for it or as a guessed value. Nothing but the JSON
document SHALL be written for the command, so a caller can read the whole of
standard output between prompts as JSON.

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

#### Scenario: A point column that is not known

- **WHEN** `show players json` is entered by a player and another player's
  points are not theirs to know
- **THEN** that entry's budget, spent and left fields are `null`

#### Scenario: The board as JSON

- **WHEN** `show board json` is entered
- **THEN** the document holds the board's dimensions and its rows of squares as
  the role may see them
