## MODIFIED Requirements

### Requirement: Empty Square Representation

The system SHALL represent an unoccupied square with a distinct empty marker
that renders as a single space (` `). The marker SHALL be one character wide,
so a drawn board's columns line up whether a square is held or not, and the
grid's own rules SHALL remain what says where the squares are.

No printable character SHALL be reserved by the empty marker: a unit type may
be given any single non-whitespace symbol, `#` included, and a symbol drawn on
the board can never be mistaken for an empty square.

#### Scenario: Rendering an empty square

- **WHEN** an empty square is rendered
- **THEN** it displays as a single space

#### Scenario: An empty square keeps its column

- **WHEN** a board holding one unit is drawn as a grid
- **THEN** every row is the same width, with one character between each pair of
  rules, and only the unit's square reads as anything other than a space

#### Scenario: A unit whose symbol is a hash

- **WHEN** a unit whose type's symbol is `#` stands on a square
- **THEN** that square is drawn as `#` and the squares around it are drawn as
  spaces, so the unit is visible as a unit
