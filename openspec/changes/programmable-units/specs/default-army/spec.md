# Spec Delta

## MODIFIED Requirements

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
| Scout  | `o`    | 0      | 2      | 12     | 6       | 20   | 1         | explorer: walks to the nearest unknown square, sleeps when there is none |
| Pawn   | `p`    | 1      | 4      | 2      | 2       | 9    | 1         | sentry: steps onto an enemy it fought last turn if it can afford to, else sleeps two turns |
| Runner | `r`    | 2      | 4      | 10     | 5       | 21   | 1         | hunter: walks to the nearest enemy flag, round its own units, fighting what it meets |
| Line   | `L`    | 3      | 6      | 12     | 4       | 25   | 2         | hunter |
| Lance  | `!`    | 8      | 2      | 10     | 3       | 23   | 1         | hunter |
| Keep   | `K`    | 1      | 10     | 5      | 8       | 24   | 3         | warden: holds its square, sleeping a hundred turns at a time, and strikes back when woken |
| Heavy  | `H`    | 5      | 10     | 15     | 4       | 34   | 3         | hunter |

The default programs SHALL be written in the instruction set `unit-program`
defines, SHALL be deterministic, and SHALL each fit the tick cap of the type
that carries them on every turn. The hunter SHALL sleep when it cannot afford
both a step and a strike, so that it arrives able to fight.

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

### Requirement: The Default Deployment Is Paid For Like Any Other

The system SHALL charge the default array against the player's budget by the
rules that charge any deployment. What the player has spent SHALL be derived
from the board, so a default unit taken back SHALL return its points.

A player given the default budget and the default array SHALL hold 16 points
they have not spent.

#### Scenario: What the array costs

- **WHEN** a player is given the default array on the default budget
- **THEN** they have spent 304 points
- **AND** 16 points remain

#### Scenario: Taking a default unit back returns its points

- **WHEN** a player takes back a Heavy from the default array
- **THEN** 34 points are returned to them

#### Scenario: A budget too small for the array

- **WHEN** a player is registered with a budget smaller than the array costs
- **THEN** they are given no default array
- **AND** they hold the catalogue
