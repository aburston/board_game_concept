# Spec Delta

## Purpose

The macro language a unit program is written in: a deterministic subset of
the C preprocessor that lets a player give registers, numbers and recurring
idioms readable names, expanded into the instruction set before the program
is checked, priced and run.

## ADDED Requirements

### Requirement: A Program Is Expanded Before It Is Checked

The system SHALL expand a program's text with the preprocessor before checking
it, and SHALL check, price and run only the expansion. A line whose first
non-blank character is `#` SHALL be a directive. Expansion SHALL be a pure
function of the program's text: it SHALL read no file, clock or environment.

#### Scenario: A program with a macro

- **WHEN** a player sets a program containing `#define GO_HOME JMP home` and a line `GO_HOME`
- **THEN** the program is accepted, and that line runs as `JMP home`

#### Scenario: A program with no directive

- **WHEN** a program contains no directive and none of its words is a defined macro
- **THEN** it is checked, priced and run exactly as it would be without the preprocessor

#### Scenario: Expansion is the same every time

- **WHEN** the same program text is expanded twice
- **THEN** both expansions are identical, instruction for instruction

### Requirement: Object-Like Macros Name Registers And Numbers

`#define NAME body` SHALL make every later occurrence of `NAME` as a whole
word stand for `body`, until `#undef NAME`. Names SHALL be case-sensitive and
SHALL be words of letters, digits and underscores not starting with a digit.
A name SHALL NOT be expanded inside a `;` comment. Defining a name twice with
different bodies, without an `#undef` between, SHALL be refused.

#### Scenario: Naming a register

- **WHEN** a program defines `#define here_x r6` and later runs `MOV here_x, r0`
- **THEN** that line runs as `MOV r6, r0`

#### Scenario: Naming a number

- **WHEN** a program defines `#define FRIEND 2` and runs `SUB r0, FRIEND`
- **THEN** that line runs as `SUB r0, 2`

#### Scenario: Part of a word is not a macro

- **WHEN** `x` is defined and a program contains the label `next`
- **THEN** `next` is unchanged

#### Scenario: Comments are left alone

- **WHEN** a defined name appears after `;` on a line
- **THEN** the comment is not expanded and costs nothing

#### Scenario: A conflicting redefinition

- **WHEN** a program defines `SPEED` as `1` and later as `2` with no `#undef` between
- **THEN** it is refused, naming the second definition's line

### Requirement: Function-Like Macros Act As Inline Functions

`#define NAME(p1, p2, ...) body`, with no space before `(`, SHALL make
`NAME(a1, a2, ...)` stand for `body` with each parameter replaced by its
argument, arguments themselves expanded first. A use with the wrong number of
arguments SHALL be refused naming the line. `##` SHALL paste the tokens either
side of it into one word.

#### Scenario: An inline function

- **WHEN** a program defines `#define IF_BELOW(a, b, where) JIF lt a, b, where` and runs `IF_BELOW(r0, r3, gocol)`
- **THEN** that line runs as `JIF lt r0, r3, gocol`

#### Scenario: Arguments are expanded

- **WHEN** `here_x` is defined as `r6` and a line reads `IF_BELOW(here_x, r3, gocol)`
- **THEN** that line runs as `JIF lt r6, r3, gocol`

#### Scenario: Too few arguments

- **WHEN** a two-parameter macro is used with one argument
- **THEN** the program is refused, naming the line and the macro

#### Scenario: Pasting a label

- **WHEN** a macro body holds `JMP go_ ## dir` and is used with argument `east`
- **THEN** it expands to `JMP go_east`

### Requirement: A Macro May Stand For Several Instructions

A macro body continued onto following lines by a `\` at the end of a line
SHALL expand to one line per physical line of the body, so that a macro can
stand for several instructions. Each SHALL be checked and run as an
instruction of its own.

#### Scenario: A multi-instruction macro

- **WHEN** a program defines `STEP_EAST` as the two lines `MOVE east` and `HALT`, joined by `\`, and uses `STEP_EAST`
- **THEN** that use runs as `MOVE east` then `HALT`, costing 1 tick

### Requirement: Labels In A Macro Are Private To Each Use

A label written `@name` in a macro body, where it is defined and wherever it
is jumped or called to, SHALL be private to each expansion of that macro, so
that a macro using one can be used more than once in a program. An `@name`
outside a macro body SHALL be refused.

#### Scenario: A branching macro used twice

- **WHEN** a macro whose body defines and jumps to `@skip` is used twice in one program
- **THEN** the program is accepted and each use jumps within itself

#### Scenario: A private label outside a macro

- **WHEN** a program's own line, not a macro body, contains `@skip`
- **THEN** it is refused, naming the line

### Requirement: Conditional Lines

`#ifdef NAME` and `#ifndef NAME`, closed by `#endif` with an optional
`#else`, SHALL keep or drop the lines between by whether `NAME` is defined,
and SHALL nest. An unclosed or unmatched conditional SHALL be refused.
`#error text` on a kept line SHALL refuse the program with that text.

#### Scenario: A default a program may override

- **WHEN** a program reads `#ifndef TARGET` / `#define TARGET FLAG enemy` / `#endif` and defines no `TARGET` before it
- **THEN** `TARGET` expands to `FLAG enemy`

#### Scenario: A missing endif

- **WHEN** an `#ifdef` is never closed
- **THEN** the program is refused, naming the `#ifdef` line

#### Scenario: A deliberate error

- **WHEN** a kept line reads `#error set NEED first`
- **THEN** the program is refused with `set NEED first`, naming the line

### Requirement: Only Built-In Headers Can Be Included

`#include <name>` SHALL insert a header the game itself holds, and SHALL
refuse any name it does not hold. No form of `#include` SHALL read a file.
A header included twice SHALL be inserted once. The game SHALL hold the
header `unit.h` and SHALL publish the text of every header it holds.

#### Scenario: Including the unit header

- **WHEN** a program begins `#include <unit.h>`
- **THEN** every name the header defines is available to the rest of it

#### Scenario: Including a file

- **WHEN** a program reads `#include "orders.asm"` or `#include </etc/passwd>`
- **THEN** it is refused, naming the line, and nothing is read

#### Scenario: Reading a header

- **WHEN** a player asks the server for the program tariff
- **THEN** the text of `unit.h` is part of what it answers

### Requirement: The Unit Header Names The Machine

`unit.h` SHALL define the four directions as the numbers `MOVE` takes, the
five answers of `MAP` and the registers each sensor writes, and SHALL provide
inline helpers for the conditions `JIF` tests and for common steps. Every
helper SHALL expand to exactly the instructions it is written for, so that a
program using one costs what the same program written out costs.

#### Scenario: Directions and map answers

- **WHEN** a program includes `unit.h`
- **THEN** `NORTH`, `EAST`, `SOUTH`, `WEST` are 1 to 4, and `UNKNOWN`, `EMPTY`, `FRIEND`, `ENEMY`, `OFF_BOARD` are 0 to 4

#### Scenario: A helper costs what it replaces

- **WHEN** a program written with `unit.h` helpers and the same program written in raw instructions are run against the same board
- **THEN** they give the same order and spend the same ticks

### Requirement: Macros Cost Nothing

A directive, a macro definition and a header SHALL cost no ticks. A line that
uses a macro SHALL cost the ticks of the instructions it expands to, by the
published tariff.

#### Scenario: Pricing a macro line

- **WHEN** a line expands to `SELF`, `SUB r3, 2` and `JIF neg r3, rest`
- **THEN** its listed cost is 3 ticks
- **AND** the `#define` that made it is listed with no cost

### Requirement: Expansion Is Bounded

The system SHALL refuse a program whose expansion holds more than 4096
instructions, or which nests macro expansion deeper than 64, naming the
source line where the bound was passed. A macro SHALL NOT be expanded within
its own expansion.

#### Scenario: A macro that names itself

- **WHEN** a program defines `#define LOOP LOOP` and uses `LOOP`
- **THEN** the use expands to `LOOP` once and is refused as not an instruction, naming the line

#### Scenario: An expansion that explodes

- **WHEN** a program's macros double at each of twenty levels
- **THEN** it is refused, naming the line, rather than expanded

### Requirement: Everything Speaks Of The Source Line

Every refusal, listing and trace SHALL name the line of the text the player
wrote. A refusal of an expanded instruction SHALL also name the macro it came
from. A listing SHALL give each source line the ticks of its expansion and
SHALL show what a macro line expands to. A halt SHALL be traced at the source
line whose expansion it stopped in.

#### Scenario: An error inside a macro

- **WHEN** a macro body holds `MOVE up` and is used on line 12
- **THEN** the refusal names line 12 and the macro

#### Scenario: Listing a macro line

- **WHEN** a player lists a program with a line that uses a three-instruction macro
- **THEN** that line is listed once with the three instructions' ticks, and the three instructions are shown with it

#### Scenario: A halt inside a macro

- **WHEN** a controller halts at the cap in an instruction that came from a macro used on line 20
- **THEN** its owner reads that it halted at line 20

### Requirement: The Source Is What A Type Carries

A type SHALL carry its program's source text, directives and macro uses
included. The source SHALL be what its owner reads back and what is fixed at
commit, and SHALL be withheld from other seats as any program is.

#### Scenario: Reading back a program

- **WHEN** a player sets a program written with macros and reads it back
- **THEN** they read the text as they wrote it, with each line's ticks

#### Scenario: Another seat's macros

- **WHEN** another seat reads the record of a turn
- **THEN** nothing of the program's source or its expansion is in it
