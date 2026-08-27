# web-interface Specification

## Purpose

Playing the game in a browser.

One page, and a client of the same contract every other client uses. It is
described here as behaviour rather than as appearance: what a person must be
able to find out and do, and which of the game's rules the interface is
responsible for making visible rather than leaving to be discovered.

Three of those rules are invisible at a command line until they have already
cost somebody a turn - what a move costs, that a unit given no order recovers
a point, and that an enemy dropping off the board is `visibility` working
rather than a defect. Showing them is the interface's job, and stating that
here is what keeps it from being dropped as decoration.

Nothing here relaxes what a session may see. The interface draws the view it
is given, and that view is already limited to what `visibility` allows.

## Requirements

### Requirement: The Interface Is A Client Of The Served Contract

The system SHALL serve a web interface that reaches the game only through the
same contract any other client uses, and SHALL NOT give it a route, a
response or a piece of state that is not equally available to another client.

Nothing the interface does SHALL be carried out by anything but the commands
and the views the contract already defines. Where the interface cannot express
something, that is a gap in the contract rather than a reason for a private
route.

#### Scenario: Every action is a contract action

- **WHEN** the interface deploys a unit, orders a move or commits a turn
- **THEN** it does so through the same command and the same endpoint a
  command-line role uses

#### Scenario: No private state

- **WHEN** the interface draws a board, a list of units or a set of orders
- **THEN** everything it draws came from a view the contract offers
- **AND** no part of it came from a route serving the interface alone

#### Scenario: The same game from two clients

- **WHEN** a game is played partly through the interface and partly through a
  command-line role
- **THEN** each sees what the other did
- **AND** neither is in a state the other cannot read

### Requirement: A Person Finds And Joins A Game From A Lobby

The system SHALL present a lobby listing the games that exist, and for each
the seats it holds, which are taken and by whom, and which are open. A person
SHALL be able to take an open seat from the lobby, and to return to a game
they already hold a seat in.

The lobby SHALL show how many seats are still open in a game that is being set
up, so that a person can see whether it is waiting for them.

#### Scenario: Seeing the games

- **WHEN** the lobby is shown
- **THEN** every game is listed with its state and its seats
- **AND** each seat says whether it is taken and by whom

#### Scenario: Taking a seat

- **WHEN** an open seat is taken from the lobby
- **THEN** the person holds that seat
- **AND** they are brought to that game

#### Scenario: Returning to a game

- **WHEN** a person holding a seat opens the lobby
- **THEN** the games they hold a seat in are shown as theirs
- **AND** they may return to any of them

#### Scenario: A seat taken while it was being looked at

- **WHEN** a seat is taken by somebody else and then taken from the lobby
- **THEN** the refusal is reported
- **AND** the lobby shows the seat as taken

### Requirement: A Seat Is Carried In The Address

The system SHALL identify which seat the interface is playing by the address
being viewed, and SHALL NOT hold it as a state that the whole interface
shares.

Two views of the interface open at once SHALL be able to play two different
seats without either disturbing the other. An address naming a seat SHALL
bring a person back to that seat of that game.

#### Scenario: Two seats at once

- **WHEN** one person holding two seats in a game opens each seat's address
- **THEN** each shows that seat's own board, orders and uncommitted work
- **AND** acting in one does not change what the other shows

#### Scenario: Returning by address

- **WHEN** an address naming a game and a seat is opened again
- **THEN** the interface shows that seat of that game

#### Scenario: A seat that is not held

- **WHEN** an address names a seat the person does not hold
- **THEN** the refusal is reported
- **AND** no board of that seat is shown

### Requirement: The Armoury Shows What A Design Costs As It Is Designed

The system SHALL let a player design unit types and deploy units from them
during setup, and SHALL show the cost of a design as it is being chosen rather
than only when it is refused.

It SHALL show the player's budget, what they have spent and what is left, and
SHALL show which of their types they can still afford to deploy.

#### Scenario: The cost moves with the design

- **WHEN** a type's attack, health or energy is being chosen
- **THEN** the cost shown is the sum of the three as currently chosen

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

The system SHALL draw the board from the view published for the seat being
played, and SHALL NOT draw anything that view does not hold.

The interface SHALL NOT decide what to conceal. What a seat may see is decided
where `visibility` decides it, and everything the interface is given is
therefore already fit to be shown.

#### Scenario: Drawing the board

- **WHEN** the board is drawn for a seat
- **THEN** it shows the units that seat's published view holds
- **AND** nothing else stands on any square

#### Scenario: An enemy not in contact

- **WHEN** an enemy unit has not been in contact with this seat's units
- **THEN** it is not drawn
- **AND** its square is drawn as empty

#### Scenario: The observer's board

- **WHEN** the board is drawn for the observer
- **THEN** it shows every unit of every player, as `visibility` grants it

### Requirement: Contact Lost Is Shown As Contact Lost

The system SHALL tell a player when an enemy unit they could see has dropped
out of their view because contact was not repeated, rather than letting it
disappear without explanation.

The interface SHALL NOT draw a unit on a square its view no longer places it
on. A player is not entitled to remember where an enemy was, and an interface
that showed it would give them what the rules withhold.

#### Scenario: An enemy fought last turn and not this one

- **WHEN** an enemy unit that was visible is no longer in this seat's view
- **THEN** the player is told contact with it was lost
- **AND** no unit is drawn where it stood

#### Scenario: Contact kept

- **WHEN** an enemy unit is in this seat's view again this turn
- **THEN** it is drawn where the view places it
- **AND** nothing says contact was lost

#### Scenario: No remembered position

- **WHEN** contact with an enemy unit has been lost
- **THEN** the board shows nothing on the square it was last seen on

### Requirement: An Order Shows What It Costs Before It Is Committed

The system SHALL show, for every order a player has given but not committed,
which unit it is for, what it asks, and what carrying it out will cost that
unit. It SHALL show what each unit has to spend beside what its order will
spend.

A unit under no order SHALL be shown as recovering the point that
`turn-commit` gives a unit that does nothing, rather than being shown as
having nothing to say.

#### Scenario: The fare is shown with the order

- **WHEN** a unit is ordered to move
- **THEN** the order shows the energy that move will cost
- **AND** the unit's energy is shown beside it

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

### Requirement: Uncommitted Orders Survive The Interface Being Closed

The system SHALL keep a player's uncommitted orders where the contract keeps
them, so that closing and reopening the interface returns the orders as they
were.

Orders SHALL belong to the turn they were given for, and SHALL NOT be restored
into a later turn.

#### Scenario: Closing and reopening

- **WHEN** orders are given and the interface is closed and opened again at
  the same seat
- **THEN** the same orders are shown, uncommitted

#### Scenario: Orders do not outlive their turn

- **WHEN** the turn orders were given for has resolved
- **THEN** those orders are not shown against the new turn

### Requirement: Committing Is Final And Is Shown To Be

The system SHALL make a player confirm a commit before it is sent, saying that
it cannot be withdrawn or amended. After committing, it SHALL NOT offer to
give, change or withdraw an order for that turn.

#### Scenario: Confirming a commit

- **WHEN** a commit is asked for
- **THEN** the player is told it cannot be withdrawn or amended
- **AND** it is sent only once they confirm

#### Scenario: After committing

- **WHEN** a turn has been committed
- **THEN** no order can be given, changed or withdrawn for that turn
- **AND** the board can still be seen

#### Scenario: The commit that has just landed

- **WHEN** a commit has been accepted
- **THEN** the interface says so without being reloaded
- **AND** it stops offering to commit that turn again

### Requirement: Waiting Says Who Is Being Waited For

The system SHALL show, while a turn is held open, that it is waiting and which
players have not committed, and SHALL move on of its own accord when the turn
resolves.

A player SHALL NOT have to reload the interface to learn that a turn resolved.

#### Scenario: Waiting for others

- **WHEN** a player has committed and others have not
- **THEN** the interface says it is waiting
- **AND** names the players it is waiting for

#### Scenario: The turn resolves

- **WHEN** every player still in the game has committed and the turn resolves
- **THEN** the interface shows the resolved turn without being reloaded

#### Scenario: An eliminated player is not waited for

- **WHEN** a player has been eliminated
- **THEN** they are not named among those being waited for

### Requirement: What The Last Turn Did Is Shown

The system SHALL show, when a turn has resolved, how the board changed and
every order of the player's that the turn did not carry out, each naming the
unit, its square and the reason.

The board's change SHALL be shown as movement from where the units were to
where they are, so that what happened is visible rather than only its result.

#### Scenario: Units that moved

- **WHEN** a turn resolves and the player's units have moved
- **THEN** each is shown moving from its old square to its new one

#### Scenario: Orders that were refused

- **WHEN** a turn resolves having refused an order of the player's
- **THEN** it is shown, naming the unit, its square and the reason

#### Scenario: Nothing refused

- **WHEN** a turn resolves and nothing of the player's was refused
- **THEN** nothing is shown as refused

#### Scenario: The report describes one turn

- **WHEN** a second turn resolves
- **THEN** what is shown describes that turn
- **AND** the previous turn's refusals are not shown again

### Requirement: Every Unit's Health Is Shown Against What It Was Built With

The system SHALL show, for every unit it draws, the health that unit has left
and the health its type was designed with, and SHALL do so on the board and in
the orders tray rather than only where a pointer is held still.

A unit a blow from destruction and a unit nobody has touched SHALL NOT be
drawn alike.

#### Scenario: A unit that has been fought

- **WHEN** a unit has lost health
- **THEN** what it has left and what it was built with are both shown
- **AND** it is drawn differently from a unit at full health

#### Scenario: On a device with no pointer

- **WHEN** the interface is used on a touchscreen
- **THEN** health is readable without hovering anything

### Requirement: The Forces Are Listed Where They Can Be Compared

The system SHALL list, beside the board, the player's own units with what each
has left and what it was built with, and every enemy type that player has met
with the statistics it was designed with.

A player deciding whether to attack is comparing two designs. Statistics kept
only in a tooltip cannot be compared, and cannot be read at all on a
touchscreen.

The list SHALL be shown to a watching session as well, which has no orders
tray to read statistics from.

#### Scenario: Weighing an attack

- **WHEN** a player has met an enemy type
- **THEN** its attack, health and energy are listed beside their own units'

#### Scenario: A unit that has been lost

- **WHEN** one of the player's units has been destroyed
- **THEN** it is listed and marked as destroyed rather than dropped

#### Scenario: Watching

- **WHEN** a session is watching rather than holding a seat
- **THEN** it can read the statistics of every unit it can see

### Requirement: An Order In Flight Is Drawn On The Board

The system SHALL draw, for each of the player's units under orders, the
direction it has been ordered in, out of the unit and towards the square it
would move to, and SHALL draw it distinctly enough to be read at a glance.

#### Scenario: A unit under orders

- **WHEN** a unit has been ordered to move
- **THEN** an arrow from that unit towards the square it is headed for is
  drawn on the board

#### Scenario: A unit holding

- **WHEN** a unit has no order
- **THEN** no arrow is drawn for it

### Requirement: The Board Says How To Order From The Keyboard

The system SHALL say, where a person's pointer already is, that a unit is
ordered by choosing it and pressing an arrow key.

#### Scenario: Hovering a unit

- **WHEN** the pointer rests on one of the player's units
- **THEN** the unit's statistics are given
- **AND** so is how to order it from the keyboard

#### Scenario: Hovering an enemy unit

- **WHEN** the pointer rests on an enemy unit the player can see
- **THEN** that unit's statistics are given

### Requirement: What The Turn Did Is Told As A Feed

The system SHALL show, when a turn has resolved, an account of what the turn
did in the order it happened - units placed and moved, engagements, every
attack with the damage it dealt, and every unit destroyed - and SHALL keep the
turns before it, so a player can read back how the position was arrived at.

The account SHALL be the one the server wrote for that seat. The interface
SHALL NOT decide for itself what may be told.

#### Scenario: A fight the seat was in

- **WHEN** a turn resolves in which one of the player's units fought
- **THEN** the account names who struck whom, for how much, and where
- **AND** says which units were destroyed

#### Scenario: A turn that is over

- **WHEN** later turns have resolved
- **THEN** the earlier turns can still be read

#### Scenario: Nothing the seat could see

- **WHEN** a turn resolves in which nothing the seat could see happened
- **THEN** the account says so rather than showing another seat's turn

### Requirement: Where The Fighting Was Is Marked On The Board

The system SHALL mark, on the squares themselves, where the last turn was
fought, what it cost this seat there, and where a unit fell.

A coordinate in a list is not a picture of a battle, and the board is what a
player is looking at.

#### Scenario: A square that was fought over

- **WHEN** a turn resolves having fought over a square the seat can see
- **THEN** that square is marked as fought over
- **AND** the damage the seat's own units took there is shown on it

#### Scenario: A unit destroyed

- **WHEN** a unit is destroyed on a square
- **THEN** the square is marked as one where a unit fell

#### Scenario: A quiet turn

- **WHEN** a turn resolves with no fighting the seat can see
- **THEN** no square is marked

### Requirement: A Decided Game Is Shown As Decided

The system SHALL show the outcome when a game has been decided, saying who won
or that it was a draw, and SHALL stop offering orders and commits while still
showing the final board.

#### Scenario: A game that is won

- **WHEN** a game is decided with a winner
- **THEN** the outcome names the winner in words a player reads
- **AND** it says whether that winner is this seat
- **AND** no order or commit is offered

#### Scenario: A draw

- **WHEN** the last players lose their last playable unit together
- **THEN** the outcome is shown as a draw

#### Scenario: The final board stays visible

- **WHEN** a game has been decided
- **THEN** the board as it finished can still be seen

#### Scenario: An eliminated player

- **WHEN** a player is eliminated before the game is decided
- **THEN** they are told they are out
- **AND** they may still watch the game they are in

### Requirement: The Game Can Be Played From The Keyboard

The system SHALL let a player select a unit, give it an order, and commit,
using the keyboard alone. Every action the interface offers by pointing SHALL
be reachable without pointing.

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
