## ADDED Requirements

### Requirement: A Group Of Units Is Selected By Drawing A Box

The system SHALL let a player select several of their own units at once on
the ordering board by pressing on a square none of their units stands on,
dragging, and releasing: every one of that seat's standing units whose square
lies inside the rectangle between where the press began and where it was
released SHALL be selected, and nothing else SHALL be.

While the pointer is down the rectangle SHALL be drawn on the board, so a
player can see what they are about to take.

- The box SHALL replace whatever was selected before it, not add to it.
- A box that catches none of the seat's units SHALL leave nothing selected.
- Enemy units, flags and empty squares inside the box SHALL be ignored: a
  selection is a set of units this seat may order.
- A box SHALL be able to begin **outside the grid**, in a margin around it.
  A box has to begin somewhere no unit stands, and a group in a corner has no
  such square beside it — every one is either a unit or off the board, so
  without a margin to start in that group cannot be boxed at all. A corner
  begun outside the grid SHALL count as the edge square nearest it.
- A press and release on the same square, with no drag, is not a box: it is a
  click, and is dealt with as a click. What counts as a drag here SHALL be a
  deliberate movement — far enough that the small travel of a hand giving a
  double-click never draws a box, because a box that caught nothing would
  take away the selection that double-click was about to order.
- The box SHALL be offered only where ordering is offered: not to a watching
  session, not once the seat has committed the turn, and not once the game is
  decided.
- On a touchscreen the box SHALL be drawn with **two fingers**: the rectangle
  runs between them and is taken when either is lifted. One finger SHALL go on
  scrolling the page as it does today — a board can fill a phone's screen, and
  a player who could not scroll past it would be stranded.

#### Scenario: Boxing several units

- **WHEN** a player presses on an empty square, drags across three of their
  own units and releases
- **THEN** those three units are selected
- **AND** nothing that was selected before still is

#### Scenario: The box is drawn while it is dragged

- **WHEN** the pointer is dragged with the button down from an empty square
- **THEN** a rectangle between the press and the pointer is drawn on the board

#### Scenario: Boxing a group standing in a corner

- **WHEN** a player presses in the margin outside the corner of the board and
  drags across the units standing in that corner
- **THEN** those units are selected

#### Scenario: A double-click is not a box

- **WHEN** a player double-clicks a square, moving the pointer slightly
  between the two clicks as a hand does
- **THEN** no box is drawn and the selection is unchanged
- **AND** the double-click orders the selection as it would have done

#### Scenario: A box that catches nothing

- **WHEN** a box is drawn across squares holding none of the player's units
- **THEN** no unit is selected

#### Scenario: Enemy units are not caught

- **WHEN** a box is drawn across a square holding an enemy unit the player
  can see
- **THEN** that unit is not selected

#### Scenario: Boxing with two fingers

- **WHEN** a player puts two fingers on the board at opposite corners of a
  group of their units and lifts one
- **THEN** the units between them are selected

#### Scenario: One finger still scrolls

- **WHEN** a player drags one finger across the board
- **THEN** the page scrolls and no box is drawn

#### Scenario: Nothing to box

- **WHEN** the session is watching, or the seat has committed, or the game is
  decided
- **THEN** dragging across the board selects nothing

### Requirement: Shift And Click Builds And Trims A Selection

The system SHALL let a player hold shift and click one of their own units to
add it to the current selection, and hold shift and click a unit already in
the selection to take it out again. A shift-click SHALL NOT clear the rest of
the selection, and a shift-click on anything that is not one of the seat's own
standing units SHALL NOT change the selection at all.

A plain click on one of the seat's own units SHALL select that unit alone,
clearing any group.

Shift SHALL be the only modifier that changes what a click does; no other
modifier SHALL select differently. Editing a selection unit by unit is the
whole of what a modifier is for here — there is no second gesture that
extends a range or selects everything between two squares.

#### Scenario: Adding a unit to a group

- **WHEN** two units are selected and the player shift-clicks a third of
  their own
- **THEN** all three are selected

#### Scenario: Taking a unit back out

- **WHEN** three units are selected and the player shift-clicks one of them
- **THEN** the other two are selected and that one is not

#### Scenario: Shift-clicking an enemy or an empty square

- **WHEN** the player shift-clicks a square holding no unit of theirs
- **THEN** the selection is unchanged

#### Scenario: A plain click narrows to one

- **WHEN** three units are selected and the player clicks one of their units
  without shift
- **THEN** only that unit is selected

### Requirement: A Selected Group Is Ordered In One Gesture

The system SHALL let every selected unit be ordered to move the same way in
one action, from the mouse and from the keyboard.

From the mouse, a **double-click on any square** SHALL order the whole
selection. It says a **direction, not a destination**: a unit moves one square
a turn, so a square further off is not a longer move but the same move,
pointed at. This SHALL hold for a selection of one unit exactly as it holds
for a group — one unit is the case where the group has one member, and
nothing about the gesture changes with the size of what is selected.

The square double-clicked SHALL be an ordinary target whatever stands on it —
empty, an enemy, or one of the seat's own units. Moving onto another unit is
how a player attacks, and the squares next to a unit are exactly the ones most
likely to be occupied, so a gesture that could not name an occupied square
could not give the most ordinary order on the board.

The direction SHALL be read from where the double-clicked square lies relative
to the **centre of the selection** — the mean of the selected units' squares:

- whichever of the horizontal and vertical distances from that centre is the
  greater decides the axis, and its sign decides the heading;
- where the two distances are equal, the horizontal axis SHALL decide, so
  that the same double-click always gives the same order;
- a double-click on the selection's own centre square gives no direction, and
  SHALL order nothing and say so.

A double-click on one of the seat's **own** units names a direction in exactly
the same way. It acts on the selection, not on the unit under the pointer —
see the requirement on what a double-click acts on.

From the keyboard, an arrow key SHALL order every selected unit that way,
exactly as it orders a single selected unit today.

Each selected unit SHALL be ordered on its own account, as though it had been
ordered by itself: a group order is a move for each unit, one square, at that
unit's own cost, and the group is not carried to the double-clicked square.
Where the rules refuse the move for some of the units — no energy left, off
the board, or otherwise — those units SHALL be left exactly as they were, the
rest SHALL still be ordered, and the player SHALL be told by name which were
refused and why.

A unit that is no longer on the board — destroyed, or no longer this seat's —
SHALL fall out of the selection rather than be ordered.

#### Scenario: Ordering a group with a double-click

- **WHEN** four units are selected and the player double-clicks a square well
  to the east of the middle of them
- **THEN** all four are ordered to move east
- **AND** an arrow east is drawn on each of them

#### Scenario: Ordering one unit by pointing rather than by naming a square

- **WHEN** one unit is selected and the player double-clicks a square several
  squares to the east of it
- **THEN** that unit is ordered to move east, one square

#### Scenario: Ordering onto a square an enemy stands on

- **WHEN** a unit is selected and the player double-clicks a square an enemy
  unit stands on
- **THEN** the selected unit is ordered towards it

#### Scenario: The direction comes from the centre, not the unit

- **WHEN** a group is selected and a square north of the group's centre is
  double-clicked
- **THEN** every selected unit is ordered north, including those that stand
  north of the square that was clicked

#### Scenario: A double-click on the diagonal

- **WHEN** the double-clicked square is as far across as it is up from the
  selection's centre
- **THEN** the order given is east or west, and the same one every time

#### Scenario: A double-click on the centre itself

- **WHEN** the double-clicked square is the selection's own centre
- **THEN** no order is given
- **AND** the player is told the direction could not be read

#### Scenario: Ordering a group from the keyboard

- **WHEN** several units are selected and an arrow key is pressed
- **THEN** every selected unit is ordered that way

#### Scenario: Part of a group cannot move

- **WHEN** a group is ordered and one of its units has not the energy to move
- **THEN** the rest of the group is ordered
- **AND** the player is told which unit was refused and why
- **AND** that unit is left as it was

#### Scenario: A destroyed unit is not ordered

- **WHEN** a selected unit is destroyed by a turn resolving
- **THEN** it is no longer part of the selection

### Requirement: Ordering With The Mouse Takes A Deliberate Double-Click

The system SHALL require a double-click to give an order with the mouse, so
that a single click can be what a click should be — looking and choosing —
and never an order given by accident.

- A **single click on a square** SHALL move the keyboard cursor there, SHALL
  clear the selection, and SHALL NOT give any order. Clicking away from your
  own units is how a selection is put down: it SHALL clear whether the square
  is empty or an enemy stands on it, which is one rule rather than two.
- Clearing this way SHALL NOT cost a player the order they were about to give:
  because the single click is held to see whether a second is coming, the
  first click of a double-click never runs, and a double-click SHALL order the
  selection it was given rather than a selection its own first click had
  emptied.
- A **double-click on a square** SHALL order the selection, as the group
  requirement describes: it names a direction rather than a destination, and
  the square need not be one of the four beside the unit. A double-click on
  the square a lone selected unit already stands on names no direction, and
  SHALL order nothing and say why.
- A click that turns out to be the first half of a double-click SHALL NOT
  also do what a single click does: one gesture gives one outcome.

#### Scenario: A single click no longer orders

- **WHEN** a unit is selected and the player single-clicks the square beside it
- **THEN** no order is given
- **AND** the unit is still selected

#### Scenario: A double-click orders the selected unit

- **WHEN** one unit is selected and the player double-clicks the square beside
  it
- **THEN** that unit is ordered to move that way

#### Scenario: A double-click well away from the unit

- **WHEN** one unit is selected and a square several squares off is
  double-clicked
- **THEN** the unit is ordered one square in that direction

#### Scenario: Clicking away puts the selection down

- **WHEN** a group is selected and the player clicks a square none of their
  units stands on
- **THEN** nothing is selected

#### Scenario: A double-click still orders the group it was given

- **WHEN** a group is selected and the player double-clicks a square to one
  side of it
- **THEN** every selected unit is ordered that way
- **AND** the clearing a single click would have done does not happen first

#### Scenario: One gesture, one outcome

- **WHEN** a square is double-clicked
- **THEN** the cursor move a single click would have made does not also happen

### Requirement: A Double-Click Acts On What Is Selected

The system SHALL make a double-click act on the **current selection**, never
on whatever happens to lie under the pointer. What is double-clicked says
which way the selection goes; it is not itself the thing being ordered.

This SHALL hold wherever the double-click lands — an empty square, a square an
enemy stands on, or one of the seat's own units. A player ordering a move onto
another unit is pointing at that unit, and a gesture that acted on the unit
under the pointer instead could not express the most ordinary order on the
board.

Where something is selected:

- a double-click that names a direction SHALL order the whole selection that
  way;
- a double-click that names **no** direction — the centre of the selection,
  which for a single selected unit is that unit's own square — SHALL take back
  every selected unit's order, so the thing double-clicked twice is the thing
  undone.

Where **nothing** is selected, a double-click on one of the seat's own units
SHALL take that unit's order back. With no selection to serve there is no
direction to name, and taking an order back is the only thing the gesture can
still mean.

A unit with no order to take back SHALL be left as it is, and the gesture
SHALL change nothing else. Taking an order back leaves the unit holding, which
is what it has always meant: a unit under no order rests.

#### Scenario: Ordering a group onto another unit

- **WHEN** several units are selected and the player double-clicks one of
  their own units standing to the east of them
- **THEN** every selected unit is ordered east
- **AND** the double-clicked unit's own orders are unchanged

#### Scenario: Taking a group's orders back

- **WHEN** several units are selected and ordered, and the player
  double-clicks the middle of the group
- **THEN** none of them is under orders
- **AND** the arrows drawn for them are gone

#### Scenario: Taking one unit's order back

- **WHEN** one unit is selected and ordered, and it is double-clicked
- **THEN** it holds no order

#### Scenario: Taking an order back with nothing selected

- **WHEN** nothing is selected and a unit under orders is double-clicked
- **THEN** that unit holds no order

#### Scenario: Nothing to take back

- **WHEN** a unit with no order is double-clicked and nothing is selected
- **THEN** nothing changes for it

### Requirement: Every Selected Unit Is Shown As Selected

The system SHALL show every unit in the current selection on the board, by
something other than colour alone, and SHALL say in words how many are
selected so that a reader who cannot see the board knows what an arrow key
would order.

#### Scenario: A group is visibly selected

- **WHEN** several units are selected
- **THEN** each of them is marked on the board
- **AND** the mark is not colour alone

#### Scenario: The size of the selection is said

- **WHEN** more than one unit is selected
- **THEN** the interface says how many units are selected

## MODIFIED Requirements

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
- A drag SHALL move a unit only where it began on a square one of the seat's
  own units stands on. On the ordering board a drag that begins anywhere else
  draws a selection box instead, and moves nothing.

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

#### Scenario: A drag from an empty square is a box, not a move

- **WHEN** a drag on the ordering board begins on a square none of the
  player's units stands on
- **THEN** a selection box is drawn and no unit is moved

### Requirement: An Order Can Be Taken Back From The Board

The system SHALL offer, for a unit under orders whose turn is not committed, a
way to take that order back — both from the keyboard, beside the arrow keys
that give one, and as a control for a hand on a mouse. It SHALL offer it only
for a unit that has an order to take back, and SHALL say so in the keyboard
help.

Where more than one unit is selected, the take-back SHALL act on the whole
selection: the keyboard's take-back key and the compass's centre SHALL take
back the order of every selected unit that has one, and SHALL be offered while
any of them has one.

#### Scenario: Taking an order back with the keyboard

- **WHEN** a unit is selected and has been ordered to move, and the take-back key is pressed
- **THEN** the unit holds no order
- **AND** the arrow drawn for it is gone

#### Scenario: A unit with no order

- **WHEN** a unit with no order is selected
- **THEN** no take-back control is offered for it

#### Scenario: Taking a group's orders back from the keyboard

- **WHEN** several units are selected and some of them are under orders, and
  the take-back key is pressed
- **THEN** none of the selected units is under orders

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

The compass SHALL act on the whole selection. Where more than one unit is
selected it SHALL be shown for the group, SHALL name how many units it will
order, and pressing a heading SHALL order every selected unit that way, on the
same terms as any other group order.

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

#### Scenario: The compass with a group selected

- **WHEN** several units are selected
- **THEN** the compass says how many units it will order
- **AND** pressing a heading orders every one of them that way

#### Scenario: Committing from the board

- **WHEN** a player commits from the control in the board's pane and confirms
  it
- **THEN** the turn is committed, exactly as committing from the orders tray
  commits it

#### Scenario: A turn already committed

- **WHEN** the turn has been committed and has not resolved
- **THEN** the board's pane says so rather than offering to commit again

### Requirement: The Game Can Be Played From The Keyboard

The system SHALL let a player select a unit, give it an order, and commit,
using the keyboard alone. Every action the interface offers by pointing SHALL
be reachable without pointing.

Building a selection of several units is a convenience of the pointer, and
SHALL NOT be required from the keyboard. Everything a group makes quicker
SHALL remain reachable from the keyboard one unit at a time: a keyboard
player selects a unit, orders it, takes the order back and commits, exactly
as they do today. Where a selection of several units has been built with a
pointer, the arrow keys and the take-back key SHALL act on all of it.

What has been selected SHALL be visible, and by more than colour alone.

#### Scenario: Playing a turn without a pointer

- **WHEN** a player uses only the keyboard
- **THEN** they can select each of their units, order it in any of the four
  directions, and commit the turn

#### Scenario: The selection is visible

- **WHEN** a unit is selected
- **THEN** which unit it is is shown by something other than colour alone

#### Scenario: Moving about the board

- **WHEN** the keyboard is used to move about the board
- **THEN** the square or unit reached is announced by what is shown

#### Scenario: A group built with a pointer is ordered from the keyboard

- **WHEN** several units have been selected with a box or with shift-click,
  and an arrow key is pressed
- **THEN** every one of those units is ordered that way
