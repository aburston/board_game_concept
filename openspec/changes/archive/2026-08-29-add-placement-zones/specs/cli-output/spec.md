## ADDED Requirements

### Requirement: A Placement Area Can Be Shown From The Command Line

The system SHALL let a role show the placement area the browser reads, so that
the area published through the contract is readable from a command line too and
the browser stays one client of the contract among the roles rather than the
only way to see the limit.

The `show placement` subject SHALL answer with the area this session may deploy
in, as a table and, on request, as JSON, the way every other `show` subject
does.

#### Scenario: A player shows its placement area

- **WHEN** a player asks to show its placement area during setup
- **THEN** the area it may deploy in is shown

#### Scenario: The area is available as JSON

- **WHEN** a role asks to show the placement area as JSON
- **THEN** the same area is given as a JSON document
