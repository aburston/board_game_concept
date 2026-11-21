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

### Requirement: The Rewritten Default Programs Play As Before

Each rewritten default program SHALL behave exactly as the program it
replaces: on every board, memory and inbox it SHALL give the same order,
sleep, memory and messages and spend the same ticks, so that a game played
with the stock army resolves as it did before the rewrite.

#### Scenario: Old and new on the same board

- **WHEN** a rewritten default program and the program it replaced are run against the same board, memory and inbox
- **THEN** they give the same order, sleep, memory and messages and spend the same ticks

#### Scenario: A stock game is unchanged

- **WHEN** two players commit the stock army unchanged
- **THEN** every turn resolves as it did with the programs the rewrite replaced
