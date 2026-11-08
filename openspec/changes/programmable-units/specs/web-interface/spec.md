# Spec Delta

## ADDED Requirements

### Requirement: A Program Is Written In The Armoury

The system SHALL let a player write or paste the program of one of their
types in the armoury during setup, SHALL list it back with each line's tick
cost beside it and the total of a straight run, and SHALL show, from the
type's compute, how many ticks one energy buys it and the cap on ticks in a
turn. A line the instruction set refuses SHALL be marked where it stands,
naming what is wrong, and the program SHALL NOT be sent until every line is
accepted. The compute statistic SHALL be chosen beside the other three, and
the armoury SHALL refuse a program on a type whose compute is 0, saying it
has no controller.

#### Scenario: Writing a program

- **WHEN** a player types a program for one of their types
- **THEN** each line shows its tick cost as it is typed
- **AND** the total ticks of a straight run, the ticks an energy buys and the per-turn cap are shown

#### Scenario: A bad line

- **WHEN** a line is not an instruction the set accepts
- **THEN** that line is marked with what is wrong
- **AND** the program is not sent until it is fixed

#### Scenario: A type with no controller

- **WHEN** a type's compute is 0
- **THEN** the armoury offers no program for it, saying it has no controller

### Requirement: The Game Is Watched As A Replay

The system SHALL show a resolved game as a replay: a scrubber over every turn
of the record, controls to play, pause, step forward and step back, and a
speed the viewer chooses. The board at each turn SHALL be drawn from the
record, with every unit of every player on it, and movement between turns
SHALL be shown as movement from the old square to the new. The replay SHALL
open at the final turn, showing the result. While any player's setup is
uncommitted the interface SHALL say the game is waiting for setups, naming
whose, and SHALL move to the replay of its own accord when the game resolves.

#### Scenario: Scrubbing

- **WHEN** the viewer drags the scrubber to turn 12
- **THEN** the board after turn 12 is drawn, with every unit on it

#### Scenario: Playing at a speed

- **WHEN** the viewer presses play at a chosen speed
- **THEN** turns are shown one after another at that speed, each unit moving from its old square to its new
- **AND** pause stops on the turn being shown

#### Scenario: Stepping

- **WHEN** the viewer steps forward and then back
- **THEN** the next turn is shown, then the one before

#### Scenario: Waiting for setups

- **WHEN** a player has committed and another has not
- **THEN** the interface says it is waiting and whose setups are to come
- **AND** when the last is committed it shows the replay without being reloaded

#### Scenario: Opening a resolved game

- **WHEN** a seat opens a game that has been resolved
- **THEN** the replay opens at its final turn and shows the result

### Requirement: What A Seat's Army Knew Is Shown On Request

The system SHALL let a seat switch the replay's board, at any turn, between
the whole board and the board as that seat's army knew it after that turn:
known-empty squares, friends, remembered enemies with the turn they were met,
flags, and unknown squares drawn as unknown. The observer and the
administrator SHALL be able to choose any seat's knowledge.

#### Scenario: What my army knew

- **WHEN** a seat switches turn 12 to what its army knew
- **THEN** only squares its army had stood on or fought on are drawn as known
- **AND** a remembered enemy is drawn with the turn it was met

#### Scenario: Back to the whole board

- **WHEN** the seat switches back
- **THEN** every unit on the board after turn 12 is drawn

### Requirement: A Seat Reads Its Controllers' Traces

The system SHALL show a seat, for the turn being replayed, what each of its
own units' controllers did: ticks spent, energy charged, the order given,
what was said and to whom, any message dropped, whether it slept or was
woken, and whether it halted and at which instruction. It SHALL show no other
seat's traces, programs or compute. The observer and the administrator SHALL
see every seat's.

#### Scenario: Reading a trace

- **WHEN** a seat replays a turn
- **THEN** each of its units lists its ticks, energy charged, order, words and any halt for that turn

#### Scenario: A halt is shown where it happened

- **WHEN** a unit's controller halted at the cap on that turn
- **THEN** its trace says so and names the instruction
- **AND** the unit is shown holding

#### Scenario: The other seat's thinking is withheld

- **WHEN** a seat replays a turn
- **THEN** nothing of any other seat's controllers is shown

## MODIFIED Requirements

### Requirement: The Armoury Shows What A Design Costs As It Is Designed

The system SHALL let a player design unit types and deploy units from them
during setup, and SHALL show the cost of a design as it is being chosen rather
than only when it is refused.

It SHALL show the player's budget, what they have spent and what is left, and
SHALL show which of their types they can still afford to deploy.

#### Scenario: The cost moves with the design

- **WHEN** a type's attack, health, energy or compute is being chosen
- **THEN** the cost shown is the sum of the four as currently chosen

#### Scenario: The budget is shown before it is spent

- **WHEN** the armoury is shown
- **THEN** the player's budget, spend and remainder are shown
- **AND** each type says whether another unit of it is affordable

#### Scenario: A deployment that cannot be afforded

- **WHEN** a unit is deployed that the remaining budget cannot pay for
- **THEN** the refusal is shown against the deployment
- **AND** the budget and the board are unchanged

#### Scenario: A type that can never be deployed

- **WHEN** a type is defined that costs more than the player's whole budget
- **THEN** it is defined, since defining is free
- **AND** it is shown as unaffordable rather than as deployable

### Requirement: A Board Shows Only What The Seat May See

The system SHALL draw the board during setup from the view published for the
seat being played, and SHALL NOT draw anything that view does not hold. Once
the game is resolved the board SHALL be drawn from the record, which shows
every seat the whole board, as `visibility` grants once a game is finished.

The interface SHALL NOT decide what to conceal. What a seat may see is decided
where `visibility` decides it, and everything the interface is given is
therefore already fit to be shown.

#### Scenario: Drawing the board

- **WHEN** the board is drawn for a seat whose game is not yet resolved
- **THEN** it shows the units that seat's published view holds
- **AND** nothing else stands on any square

#### Scenario: An enemy not in contact

- **WHEN** an enemy unit has not been in contact with this seat's units and the game is not yet resolved
- **THEN** it is not drawn
- **AND** its square is drawn as empty

#### Scenario: Drawing the replay

- **WHEN** the board is drawn for a seat from a resolved game's record
- **THEN** it shows every unit of every player as the record holds them

#### Scenario: The observer's board

- **WHEN** the board is drawn for the observer
- **THEN** it shows every unit of every player, as `visibility` grants it

### Requirement: A Unit Is Moved By Dragging It

The system SHALL let a unit be moved by dragging it and dropping it on a
square, with a mouse and with a finger, on the board a seat deploys on.

Picking a piece up and putting it down is what a person does to a board, and
the interface offered nothing of the kind: a unit could be placed only by
choosing a square.

- While setting up, dropping a deployed unit on a square that seat may deploy
  in SHALL move it there, and the unit SHALL keep its name, its type and its
  designation as the flag carrier.
- A drop the rules do not allow - a square outside the seat's placement area,
  a square already occupied, or anywhere off the board - SHALL change
  nothing, and SHALL say why, leaving the unit where it was.
- Dragging SHALL NOT be the only way to deploy: choosing a square SHALL keep
  working.
- Dragging SHALL be offered only where deploying is offered: not to a
  watching session, not once the seat has committed, and not in the replay.
- A drag SHALL move a unit only where it began on a square one of the seat's
  own units stands on.

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

- **WHEN** a unit is dragged on the replay board
- **THEN** no order is given: orders are the controllers' alone
- **AND** the board is unchanged

#### Scenario: Dropping a unit somewhere it cannot reach

- **WHEN** a deployed unit is dropped off the board during setup
- **THEN** it is still on the square it was on

#### Scenario: Dragging with a finger

- **WHEN** the interface is used on a touchscreen
- **THEN** a unit can be dragged and dropped with a finger
- **AND** the board does not scroll or select text while a unit is being
  dragged

#### Scenario: The keyboard is still there

- **WHEN** a player chooses a square from the keyboard instead
- **THEN** they deploy and take back units exactly as before

#### Scenario: Nothing to drag

- **WHEN** the session is watching, or the seat has committed, or the game is
  resolved
- **THEN** dragging a unit does nothing

#### Scenario: A drag from an empty square is a box, not a move

- **WHEN** a drag begins on a square none of the player's units stands on
- **THEN** no unit is moved
- **AND** no selection box is drawn, there being nothing to select a group for

### Requirement: Committing Is Final And Is Shown To Be

The system SHALL make a player confirm a commit before it is sent, saying that
it cannot be withdrawn or amended and that the game will be played out from
it. After committing, it SHALL NOT offer to change the setup.

#### Scenario: Confirming a commit

- **WHEN** a commit is asked for
- **THEN** the player is told it cannot be withdrawn or amended, and that the game plays out from it
- **AND** it is sent only once they confirm

#### Scenario: After committing

- **WHEN** a setup has been committed
- **THEN** no type, program, unit or flag can be changed
- **AND** the board can still be seen

#### Scenario: The commit that has just landed

- **WHEN** a commit has been accepted
- **THEN** the interface says so without being reloaded
- **AND** it stops offering to commit

### Requirement: What The Last Turn Did Is Shown

The system SHALL show, for the turn being replayed, how the board changed
and every order of the seat's units that the turn did not carry out, each
naming the unit, its square and the reason.

The board's change SHALL be shown as movement from where the units were to
where they are, so that what happened is visible rather than only its result.

#### Scenario: Units that moved

- **WHEN** a replayed turn moved units
- **THEN** each is shown moving from its old square to its new one

#### Scenario: Orders that were refused

- **WHEN** a replayed turn refused an order of one of the seat's units
- **THEN** it is shown, naming the unit, its square and the reason

#### Scenario: Nothing refused

- **WHEN** a replayed turn refused nothing of the seat's
- **THEN** nothing is shown as refused

#### Scenario: The report describes one turn

- **WHEN** the replay moves to another turn
- **THEN** what is shown describes that turn
- **AND** the previous turn's refusals are not shown with it

### Requirement: What The Turn Did Is Told As A Feed

The system SHALL show, for the turn being replayed, an account of what the
turn did in the order it happened - units placed and moved, engagements,
every attack with the damage it dealt, and every unit destroyed - and SHALL
let the turns before it be read, so a player can read back how the position
was arrived at.

The account SHALL be the one the server wrote for that seat. The interface
SHALL NOT decide for itself what may be told.

#### Scenario: A fight the seat was in

- **WHEN** a replayed turn is one in which one of the seat's units fought
- **THEN** the account names who struck whom, for how much, and where
- **AND** says which units were destroyed

#### Scenario: A turn that is over

- **WHEN** the replay is at a later turn
- **THEN** the earlier turns' accounts can still be read

#### Scenario: Nothing the seat could see

- **WHEN** a replayed turn is one in which nothing the seat could see happened
- **THEN** the account says so rather than showing another seat's turn

### Requirement: A Decided Game Is Shown As Decided

The system SHALL show the outcome of a resolved game, saying who won, that it
was a draw, or that it stopped undecided and why, and SHALL show it at the
replay's final turn.

#### Scenario: A game that is won

- **WHEN** a game is decided with a winner
- **THEN** the outcome names the winner in words a player reads
- **AND** it says whether that winner is this seat

#### Scenario: A draw

- **WHEN** the last players lose their last playable unit together
- **THEN** the outcome is shown as a draw

#### Scenario: An undecided stop

- **WHEN** a game stopped because its state repeated or the cap was reached
- **THEN** the outcome says so, and on which turn

#### Scenario: The final board stays visible

- **WHEN** a game has been resolved
- **THEN** the board as it finished can still be seen

#### Scenario: An eliminated player

- **WHEN** a player was eliminated before the game was decided
- **THEN** the replay tells them they are out when it reaches that turn
- **AND** they may still watch the rest of the record

### Requirement: The Game Can Be Played From The Keyboard

The system SHALL let a player design a type, write its program, deploy units,
designate the flag, commit, and drive the replay - scrub, play, pause, step
and change speed - using the keyboard alone. Every action the interface offers
by pointing SHALL be reachable without pointing.

What has been selected SHALL be visible, and by more than colour alone.

#### Scenario: Playing a turn without a pointer

- **WHEN** a player uses only the keyboard
- **THEN** they can design types, write programs, deploy and take back units, designate the flag and commit
- **AND** they can step through the replay's turns, play and pause, and change the speed

#### Scenario: A group built with a pointer is ordered from the keyboard

- **WHEN** a player presses an arrow key on the replay board
- **THEN** the keyboard cursor moves; no unit is ordered, there being no groups and no orders

#### Scenario: The selection is visible

- **WHEN** a unit or a control is selected
- **THEN** which it is is shown by something other than colour alone

#### Scenario: Moving about the board

- **WHEN** the keyboard is used to move about the board
- **THEN** the square or unit reached is announced by what is shown

### Requirement: An Eliminated Player Is Told They Are Out

The system SHALL tell a player whose flag has fallen, when the replay reaches
that turn, that they are out of the game and why, and SHALL keep showing them
the board and what the turns do to the end of the record.

#### Scenario: Losing the flag

- **WHEN** the replay reaches the turn that destroys a player's flag carrier
- **THEN** that player is told they are out, and why

#### Scenario: Watching afterwards

- **WHEN** the replay moves past that turn
- **THEN** the board and the account of each turn keep arriving

## REMOVED Requirements

### Requirement: An Order Can Be Taken Back From The Board

**Reason**: A player gives no orders; their units' controllers do.

**Migration**: Remove the take-back control and key with the ordering board.

### Requirement: An Order Shows What It Costs Before It Is Committed

**Reason**: There are no orders of the player's to cost. What a program will
cost is shown in the armoury's listing, per line and per energy.

**Migration**: Remove the orders rows; the listing replaces them.

### Requirement: Uncommitted Orders Survive The Interface Being Closed

**Reason**: There are no uncommitted orders. A drafted setup, programs
included, survives as `turn-commit`'s drafting states.

**Migration**: Remove the per-turn order draft from the interface.

### Requirement: Waiting Says Who Is Being Waited For

**Reason**: Turns are not held open. The one wait left - for the other
players' setups - is stated by `The Game Is Watched As A Replay`.

**Migration**: Replace the turn wait with the setup wait.

### Requirement: An Order In Flight Is Drawn On The Board

**Reason**: No order is in flight: the replay shows the move itself.

**Migration**: Remove the order arrows; movement between replayed turns is
drawn as movement.

### Requirement: The Controls For Ordering Are In The Board's Pane

**Reason**: There are no ordering controls.

**Migration**: The pane beneath the board holds the replay controls.

### Requirement: A Group Of Units Is Selected By Drawing A Box

**Reason**: Selection existed to order several units at once; nothing is
ordered.

**Migration**: Remove box selection and the shared drag guard's box branch.

### Requirement: Shift And Click Builds And Trims A Selection

**Reason**: As above.

**Migration**: Remove.

### Requirement: A Selected Group Is Ordered In One Gesture

**Reason**: As above.

**Migration**: Remove the compass and `directionForGroup`.

### Requirement: Ordering With The Mouse Takes A Deliberate Double-Click

**Reason**: Nothing is ordered with the mouse.

**Migration**: A single click on a unit in the replay shows its trace; there
is no double-click action.

### Requirement: A Double-Click Acts On What Is Selected

**Reason**: As above.

**Migration**: Remove.

### Requirement: Every Selected Unit Is Shown As Selected

**Reason**: There is no multi-unit selection. A single selected unit's
visibility is kept by `The Game Can Be Played From The Keyboard`.

**Migration**: Remove the count and the group marks.

### Requirement: The Board Says How To Order From The Keyboard

**Reason**: Nothing is ordered from the keyboard.

**Migration**: The hint over a unit in the replay says how to read its trace.
