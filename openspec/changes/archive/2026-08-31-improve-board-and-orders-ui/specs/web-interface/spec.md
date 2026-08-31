## ADDED Requirements

### Requirement: A Setup Can Be Cleared In One Action

The system SHALL offer, while a seat's setup is not committed and it has
deployed at least one unit, a single control that takes back every unit that
seat has deployed, freeing all of their squares and all of their points.

Taking an army back one unit at a time is the only way to start again, and a
player who has laid out a dozen units and changed their mind is asked for a
dozen decisions to unmake one. Because it undoes more than a click usually
does, it SHALL be confirmed before anything is taken back, and refusing the
confirmation SHALL leave the setup untouched.

The control SHALL NOT be offered where there is nothing to take back, nor
once the seat's setup is committed, where taking a unit back is refused.

#### Scenario: Clearing a deployed army

- **WHEN** a seat with deployed, uncommitted units uses the control and
  confirms it
- **THEN** none of that seat's units are deployed
- **AND** the board and the deployed list are drawn without them
- **AND** the whole of the seat's budget is available again

#### Scenario: Thinking better of it

- **WHEN** the control is used and the confirmation is refused
- **THEN** every unit is still deployed where it was

#### Scenario: Nothing to clear

- **WHEN** a seat has deployed nothing
- **THEN** no control to clear is offered

#### Scenario: A setup that is already committed

- **WHEN** a seat's setup is committed
- **THEN** no control to clear is offered

#### Scenario: Only this seat's units

- **WHEN** a seat clears its board in a game where other seats have deployed
- **THEN** only that seat's units are taken back

### Requirement: A Unit Is Moved By Dragging It

The system SHALL let a unit be moved by dragging it and dropping it on a
square, with a mouse and with a finger, on both the board a seat deploys on
and the board it gives orders on.

Picking a piece up and putting it down is what a person does to a board, and
the interface offered nothing of the kind: a unit could be placed only by
choosing a square, and ordered only through a compass or the arrow keys.

- While setting up, dropping a deployed unit on a square that seat may deploy
  in SHALL move it there, and the unit SHALL keep its name, its type and its
  designation as the flag carrier.
- While ordering, dropping a unit on one of the four squares next to the one
  it stands on SHALL order it to move that way, exactly as the compass does.
- A drop the rules do not allow — a square outside the seat's placement area,
  a square already occupied, a square that is not next to the unit, or
  anywhere off the board — SHALL change nothing, and SHALL say why, leaving
  the unit where it was and any order it already had as it was.
- Dragging SHALL NOT be the only way to do either thing: choosing a square to
  deploy on, the compass, the orders rows and the arrow keys SHALL all keep
  working.
- Dragging SHALL be offered only where the thing it would do is offered:
  not to a watching session, not once the seat has committed, and not once
  the game is decided.

#### Scenario: Dragging a deployed unit to another square

- **WHEN** a player drags one of their deployed units onto an empty square
  they may deploy in, while their setup is not committed
- **THEN** the unit stands on that square
- **AND** it is the same unit, with its name, its type and its flag if it
  carried one

#### Scenario: Dragging a unit somewhere it may not be deployed

- **WHEN** a deployed unit is dropped on a square the seat may not deploy in
  or that something already stands on
- **THEN** the unit is still on the square it was on
- **AND** the player is told why the drop was refused

#### Scenario: Dragging a unit to order it

- **WHEN** a player drags one of their units onto a square next to it during
  a turn that is not committed
- **THEN** that unit is ordered to move that way
- **AND** the arrow for the order is drawn on the board

#### Scenario: Dropping a unit somewhere it cannot reach

- **WHEN** a unit is dropped on a square that is not next to the one it
  stands on
- **THEN** no order is given
- **AND** any order the unit already had is unchanged

#### Scenario: Dragging with a finger

- **WHEN** the interface is used on a touchscreen
- **THEN** a unit can be dragged and dropped with a finger
- **AND** the board does not scroll or select text while a unit is being
  dragged

#### Scenario: The keyboard is still there

- **WHEN** a player uses the arrow keys instead
- **THEN** they select and order units exactly as before

#### Scenario: Nothing to drag

- **WHEN** the session is watching, or the seat has committed, or the game is
  decided
- **THEN** dragging a unit does nothing

### Requirement: The Board And The Trays Take Turns Where They Do Not Fit

The system SHALL, where the board and the tabs beside it cannot be shown side
by side, show one of them at a time and offer one control that switches
between them, saying which is being shown.

On a phone the board and the trays are one column, so reading the orders means
scrolling the board away and ordering means scrolling back — with the arrow
that was just drawn off the top of the screen. Where both fit, both are shown:
the control SHALL NOT be offered at a width that has room for the pair, and
SHALL NOT hide anything there.

The choice SHALL survive the screen being redrawn, so that giving an order
does not throw the player back to the other view.

#### Scenario: Two panes that do not fit

- **WHEN** the play screen is used at a width too narrow for the board and
  the trays side by side
- **THEN** one of them is shown, with a control that switches to the other
- **AND** the control says which is being shown

#### Scenario: Switching to the trays and back

- **WHEN** the control is used
- **THEN** the other pane is shown in place of the one that was

#### Scenario: Ordering does not switch the view back

- **WHEN** a unit is ordered while the trays are being shown
- **THEN** the trays are still what is shown

#### Scenario: A screen with room for both

- **WHEN** the play screen is used at a width that fits the board and the
  trays side by side
- **THEN** both are shown, and no switch is offered

#### Scenario: Reached without a pointer

- **WHEN** the switch is used from the keyboard
- **THEN** it switches the view, and says which view it has switched to

## MODIFIED Requirements

### Requirement: An Order Shows What It Costs Before It Is Committed

The system SHALL show, for every order a player has given but not committed,
which unit it is for, what it asks, and what carrying it out will cost that
unit. It SHALL show what each unit has to spend beside what its order will
spend.

What a unit has to spend SHALL be shown against the energy its type was
designed with — `3/5` rather than `3` — the way its health is shown, so that a
unit that has been spending and one that has not can be told apart where the
order is given. Each unit's attack SHALL be shown there too: what a unit hits
for is half of every decision to order it towards an enemy, and it was
readable only in another card.

A unit under no order SHALL be shown as recovering the point that
`turn-commit` gives a unit that does nothing, rather than being shown as
having nothing to say.

#### Scenario: The fare is shown with the order

- **WHEN** a unit is ordered to move
- **THEN** the order shows the energy that move will cost
- **AND** the unit's energy is shown beside it

#### Scenario: Energy against what the type was built with

- **WHEN** a unit has spent some of its energy
- **THEN** what it has left and what its type was designed with are both
  shown against its order

#### Scenario: What the unit hits for

- **WHEN** a unit is listed for ordering
- **THEN** its attack is shown in the same row

#### Scenario: An order the unit cannot pay for

- **WHEN** a unit is ordered to move and has less energy than the move costs
- **THEN** the order is shown as one the unit cannot pay for
- **AND** the player may still commit it, since the turn decides what happens

#### Scenario: A unit given no order

- **WHEN** a unit has been given no order
- **THEN** it is shown as resting and recovering a point

#### Scenario: Changing an order before committing

- **WHEN** a unit already under an order is ordered a different way
- **THEN** the order shown for it is the later one
- **AND** only one order is shown for that unit

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
- **THEN** the board pane says to choose one rather than showing controls
  that would do nothing

#### Scenario: Committing from the board

- **WHEN** a player commits from the control in the board's pane and confirms
  it
- **THEN** the turn is committed, exactly as committing from the orders tray
  commits it

#### Scenario: A turn already committed

- **WHEN** the turn has been committed and has not resolved
- **THEN** the board's pane says so rather than offering to commit again
