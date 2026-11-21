## ADDED Requirements

### Requirement: The Default Programs Read As Words

The catalogue's default programs SHALL be written with the preprocessor that
`program-preprocessor` defines, so as to read as plainly as the language
allows: each SHALL include `<unit.h>`, name the registers it keeps values in,
use the header's names for directions and map answers rather than bare
numbers, and carry no templating a player could not type themselves.

#### Scenario: A default program reads as words

- **WHEN** a player reads back the program of any catalogue type
- **THEN** it includes `<unit.h>` and names its registers and constants
- **AND** no instruction in its own text names a direction or map answer by number

#### Scenario: A player copies a default program

- **WHEN** a player sets the text a catalogue type's program reads back as on a type of their own
- **THEN** it is accepted, and their type thinks as the catalogue's does

### Requirement: The Rewritten Default Programs Keep Their Doctrine

Each rewritten default program SHALL be written for readability first and MAY
differ in its instructions, register use and exact choices from the program it
replaces, but SHALL keep the doctrine the catalogue states for it, SHALL be
deterministic, SHALL fit its type's tick cap on every turn, and SHALL still
satisfy every scenario this specification sets for the stock army.

#### Scenario: The hunter keeps its doctrine

- **WHEN** a rewritten hunter stands with an enemy flag in reach and one of its own units on the direct way
- **THEN** it steps round its own unit towards the flag, and sleeps a turn when it cannot afford a step and a strike or when both ways round are its own units

#### Scenario: The explorer keeps its doctrine

- **WHEN** a rewritten explorer has an unknown square to reach
- **THEN** it steps towards it onto a square its map calls unknown or empty, never onto one of its own, a known enemy or off the board, and sleeps when nothing is left to find or twenty turns have not brought it nearer

#### Scenario: The vanguard keeps its doctrine

- **WHEN** a rewritten vanguard can afford a step and a strike and the square in front of it is not one of its own
- **THEN** it steps towards the enemy's edge, and sleeps a turn otherwise

#### Scenario: The stock army still plays

- **WHEN** two players commit the stock army unchanged under the rewritten programs
- **THEN** every scenario of "Every Registered Player Is Given The Default Catalogue" and the two-player array holds: at least one unit moves on turn one, every unit with a controller but the Keeps leaves its square within twenty turns, a blocked hunter sleeps, and the two seats mirror each other
