## MODIFIED Requirements

### Requirement: Only The Roles Are Installed

The system SHALL install a command for each interactive role and for nothing
else. Developer tooling, including the standalone test harness, SHALL NOT be
installed as a command; it remains runnable as a module by anyone working on the
package.

Support files that are not programs — the shell completion scripts among them —
SHALL be shipped as files to source or copy, named and documented where the
commands are documented. They SHALL NOT add a name to the path, and the set of
commands installing the package puts on the path SHALL remain exactly the three
roles.

#### Scenario: No command for the test harness

- **WHEN** the package is installed
- **THEN** the standalone test harness has no command of its own on the path

#### Scenario: The harness is still runnable

- **WHEN** someone working on the package runs the harness as a module
- **THEN** it runs and reports its results

#### Scenario: Shell completion adds no command

- **WHEN** the package is installed and its shell completion is sourced
- **THEN** the commands on the path are the three roles and nothing else
- **AND** the completion is a file the shell reads, not a program that is run
