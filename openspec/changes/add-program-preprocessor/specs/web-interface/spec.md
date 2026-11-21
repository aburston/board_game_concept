## ADDED Requirements

### Requirement: The Armoury Prices Macro Lines By Their Expansion

In the armoury's program listing, a line that uses a macro SHALL be priced by
the ticks of its expansion and SHALL show what it expands to, a directive SHALL
cost nothing, and a line the preprocessor refuses SHALL be marked with what is
wrong, so that the program is not sent until it is fixed. The text of the
built-in headers SHALL be readable from the armoury.

#### Scenario: Writing a program with macros

- **WHEN** a player types `#include <unit.h>` and a line using one of its helpers
- **THEN** the include line shows no cost and the helper line shows the ticks of what it expands to
- **AND** the player can see what that line expands to

#### Scenario: A bad macro use

- **WHEN** a line uses a macro with the wrong number of arguments
- **THEN** that line is marked with what is wrong
- **AND** the program is not sent until it is fixed

#### Scenario: Reading the unit header

- **WHEN** a player asks to see `unit.h` from the program editor
- **THEN** its full text is shown
