## MODIFIED Requirements

### Requirement: A Program Is Checked When It Is Set

A program SHALL be checked when it is set, after it is expanded: an
instruction that is not in the set, a malformed operand, a jump or call to a
label that does not exist, or a directive the preprocessor refuses SHALL be
refused, naming the source line, and the type's program SHALL be unchanged.
A program SHALL NOT be refused for what it would do.

#### Scenario: A program with an unknown instruction

- **WHEN** a player sets a program containing a line that is not an instruction
- **THEN** it is refused, naming the line
- **AND** the type's program is as it was

#### Scenario: An unknown instruction from a macro

- **WHEN** a macro expands to a line that is not an instruction
- **THEN** it is refused, naming the source line that used the macro and the macro's name

#### Scenario: A bad directive

- **WHEN** a program contains a directive the preprocessor does not accept
- **THEN** it is refused, naming the line
- **AND** the type's program is as it was

#### Scenario: A jump to nowhere

- **WHEN** a program jumps to a label it does not define
- **THEN** it is refused, naming the line

#### Scenario: A call to nowhere

- **WHEN** a program calls a label it does not define
- **THEN** it is refused, naming the line

#### Scenario: A sleep longer than the longest

- **WHEN** a program runs `SLEEP` with a number above 100, or below 1
- **THEN** it is refused when it is set, naming the line

#### Scenario: A program that would loop

- **WHEN** a program's only path is a loop with no exit
- **THEN** it is accepted; the cap stops it when it runs

## ADDED Requirements

### Requirement: A Program's Text May Use Macros

A program's text MAY hold preprocessor directives and macro uses, as
`program-preprocessor` defines, alongside instructions, labels and comments.
The instructions every unit of the type runs SHALL be those of the program's
expansion.

#### Scenario: Setting a program written with macros

- **WHEN** a player sets a program that includes `<unit.h>` and uses its names
- **THEN** every unit of that type runs the program's expansion from the first turn of play
