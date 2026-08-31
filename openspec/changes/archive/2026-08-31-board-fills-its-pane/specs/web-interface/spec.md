## ADDED Requirements

### Requirement: The Board Is Drawn At The Size Of Its Pane

The system SHALL draw the board at the width of the pane it is in, keeping its
proportions, rather than at a fixed size decided by the number of squares.

The board is what a player reads the game from, and it was the smallest thing
on the screen: a small board in a wide pane left most of that pane empty and
every unit the size of a full stop.

The board SHALL NOT be drawn taller than the window it is in, so that a board
with more rows than columns can still be seen at once, and SHALL NOT be
stretched: a square stays square at every size.

#### Scenario: A board in a wide pane

- **WHEN** the board is drawn in a pane wider than its natural size
- **THEN** it is drawn at the width of that pane
- **AND** each square is still square

#### Scenario: A board taller than the window

- **WHEN** the width of the pane would make the board taller than the window
- **THEN** it is drawn no taller than the window, keeping its proportions

#### Scenario: A narrow screen

- **WHEN** the board is drawn on a screen narrower than its natural size
- **THEN** it is drawn to fit that screen rather than pushing the page sideways

### Requirement: What A Glyph Means Belongs To The Glyph

The system SHALL explain what it has drawn on the board through the thing it
has drawn — what is said of a unit, a flag, a square or a mark when it is
pointed at or read out — and SHALL NOT explain it in prose beneath the board.

A key under a board is read once and read past for the rest of the game, while
taking the room the board itself should have. What a unit is, that a flag is a
flag, that a square was fought over: each of these was written out below a
board that was already drawing them.

A unit's description SHALL say what it is and whose it is, what it was built
with and what it has left, and SHALL say the two things about it that a player
could not otherwise see: that it is deployed and not yet on the field, and
that the order it is under has been committed.

This SHALL apply to explanation only. Nothing a player compares or acts on
SHALL be moved into a pointer: the statistics stay in the tables that list
them, the flag its carrier holds stays in the roster, what the turn did stays
in the account of the turn, and that a committed setup takes the field with
the first turn is still said in words that need no pointer.

#### Scenario: The board's pane

- **WHEN** the board is drawn
- **THEN** no key, legend or note explaining its glyphs is drawn beneath it

#### Scenario: A unit not yet on the field

- **WHEN** a unit was deployed in a committed setup the first turn has not
  resolved
- **THEN** its description says it is not on the field yet
- **AND** the screen still says in words that the first turn is what puts it
  there

#### Scenario: A committed order

- **WHEN** a unit is under an order that has been committed
- **THEN** its description says the order cannot be changed until the turn
  resolves

#### Scenario: What is still said in words

- **WHEN** a player reads the screen without pointing at anything
- **THEN** the statistics, who carries the flag and what the last turn did are
  all still there to read

## MODIFIED Requirements

### Requirement: The Controls For Ordering Are In The Board's Pane

The system SHALL put the controls that order the selected unit in the same
pane as the board, beneath it, so that choosing a unit, ordering it and seeing
the order drawn all happen in one place. They SHALL NOT be in a separate card
across the screen from the board they act on.

The controls SHALL be laid out as a **compass**: the four headings placed
where the squares they point at are, around a fifth in the centre that means
"stay where you are". Each SHALL be drawn as the arrow for its heading rather
than as its name, and the centre as a mark of its own; each SHALL carry the
words for a reader that cannot see the arrow.

The centre SHALL be offered whether or not the unit is under orders. Holding
is a choice a player makes — a unit given no order recovers a point — and it
is the same control whether it is choosing to stay or taking back an order
given a moment ago. Where there is an order to take back, the centre SHALL say
so and be drawn as the thing that undoes it.

Where no unit is selected the pane SHALL show no ordering controls at all,
and SHALL NOT fill their place with an instruction: how a unit is chosen and
ordered is said by the units themselves, which is where a hand and a reader
both already are.

The board's pane SHALL also offer committing the turn, so that the last order
and the commit that publishes it are given in the same place. It SHALL be the
same commit as the one the orders tray offers — confirmed before it is sent,
and refused nowhere the other is accepted — and where the turn is already
committed both SHALL say so instead of offering to commit again.

#### Scenario: Ordering a unit

- **WHEN** a unit is selected
- **THEN** the controls for it are shown under the board
- **AND** pressing one draws the order on the board above them

#### Scenario: Laid out as a compass

- **WHEN** the controls are shown
- **THEN** north is above the centre and south below it
- **AND** west is left of the centre and east right of it

#### Scenario: The centre with no order to take back

- **WHEN** the selected unit has no order
- **THEN** the centre is still offered, as holding

#### Scenario: The centre with an order to take back

- **WHEN** the selected unit is under orders
- **THEN** the centre says it takes the order back
- **AND** pressing it leaves the unit with no order

#### Scenario: Read without seeing the arrows

- **WHEN** the controls are read by something that cannot see a glyph
- **THEN** each is named by what it does

#### Scenario: Nothing selected

- **WHEN** no unit is selected
- **THEN** no ordering controls are shown, and nothing is written in their
  place
- **AND** each of the player's units still says how it is chosen and ordered

#### Scenario: Committing from the board

- **WHEN** a player commits from the control in the board's pane and confirms
  it
- **THEN** the turn is committed, exactly as committing from the orders tray
  commits it

#### Scenario: A turn already committed

- **WHEN** the turn has been committed and has not resolved
- **THEN** the board's pane says so rather than offering to commit again
