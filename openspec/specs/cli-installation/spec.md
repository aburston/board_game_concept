# cli-installation Specification

## Purpose

What the command-line roles are called, how installing the package puts them
on the path, and where they look for a game. A role has one name: the command
it is installed as, the file that implements it, and the name it gives itself
in its prompt and its usage are all the same word.

## Requirements

### Requirement: Unique Command Names

The system SHALL expose each command-line role under a name unique to this
project: `bgcserver` for the administrator, `bgcclient` for a player, and
`bgcobserver` for the read-only view. No two roles SHALL share a name, and no
role SHALL be named after the file it happens to live in.

#### Scenario: Every role has its own command

- **WHEN** the package is installed
- **THEN** `bgcserver`, `bgcclient` and `bgcobserver` are each available as a
  command
- **AND** each one starts the role it names

#### Scenario: A role names itself by its command

- **WHEN** a role prints its prompt, its usage or an argument error
- **THEN** it names itself by its installed command name
- **AND** the name does not depend on the path the command was invoked by

### Requirement: One Name Per Role

The system SHALL give a role the same name in the repository as on the path: the
file implementing a role SHALL be named for the command it is installed as. A
command name SHALL NOT be a name that appears nowhere in the source it is built
from.

#### Scenario: Finding the code behind a command

- **WHEN** someone looks for the source of an installed command
- **THEN** a file of that name implements it
- **AND** searching the repository for the command's name reaches that file

#### Scenario: The packaging introduces no new name

- **WHEN** a role's command is declared
- **THEN** it names the module of the same name
- **AND** installing it invents no name that the source does not already use

### Requirement: Installation Onto The Path

The system SHALL install the three role commands as executables on the path as
part of installing the package, so that each can be run by name without naming a
Python interpreter, a script file or a directory.

#### Scenario: Installing the package installs the commands

- **WHEN** the package is installed into an environment
- **THEN** the three commands are on that environment's path
- **AND** running one by name alone starts its role

#### Scenario: No interpreter or file path needed

- **WHEN** a role is started by its command name
- **THEN** it runs without the caller naming `python`, a `.py` file or the
  directory the package was installed from

### Requirement: Only The Roles Are Installed

The system SHALL install a command for each interactive role and for nothing
else. Developer tooling, including the standalone test harness, SHALL NOT be
installed as a command; it remains runnable as a module by anyone working on the
package.

#### Scenario: No command for the test harness

- **WHEN** the package is installed
- **THEN** the standalone test harness has no command of its own on the path

#### Scenario: The harness is still runnable

- **WHEN** someone working on the package runs the harness as a module
- **THEN** it runs and reports its results

### Requirement: Games Are Found Relative To The Working Directory

The system SHALL resolve a game against the working directory the command was
run in, not against wherever the command itself was installed. A game number
therefore names `games/_<gameno>` beneath the current directory.

#### Scenario: Opening a game from the directory it lives in

- **WHEN** a role is started by command name in a directory holding `games/`
- **THEN** it reads and writes that game under that directory

#### Scenario: The install location does not hold games

- **WHEN** a role is started from a different working directory
- **THEN** it resolves the game against that directory
- **AND** it does not read or write games beneath wherever it was installed
