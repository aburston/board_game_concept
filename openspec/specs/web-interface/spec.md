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

An open seat SHALL be offered to every account that may hold one - a registered
player and the administrator alike - and SHALL be withheld only from the
observer, which holds no seat in any game. The lobby SHALL decide what to offer
by whether the account may take the seat, and not by the kind of account it is
looking at.

A seat the administrator holds SHALL be shown, entered and played through the
same screens as any other seat, and the administrator's own screens - creating
a game, setting one up, watching one - SHALL be offered beside them rather than
in place of them.

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

#### Scenario: The administrator is offered an open seat

- **WHEN** the administrator opens the lobby on a game being set up with an open
  seat
- **THEN** that seat is offered to be taken
- **AND** taking it brings them to that seat as it would anybody

#### Scenario: The observer is offered none

- **WHEN** the observer opens the lobby on a game with an open seat
- **THEN** no seat is offered to be taken
- **AND** the game may still be watched

#### Scenario: Playing and administering from one lobby

- **WHEN** the administrator holds a seat in a game the lobby lists
- **THEN** the game is shown as theirs and the seat may be played
- **AND** the administrator's own way into that game is offered as well

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

### Requirement: A Half-Made Choice Survives A Redraw

The interface draws every screen again from one state object whenever anything
changes, so a choice held only in the page is thrown away by work done beside
it. The system SHALL keep a choice that is still being used where a redraw
cannot lose it, so that using one form does not empty another.

The type a unit is being deployed from SHALL be kept as it was left, so that
several units of one type can be placed without choosing it again for each.

A board size that has been typed and not yet sent SHALL be kept while seats are
registered and removed, and SHALL go back to reading the board once a size has
been accepted.

#### Scenario: Deploying several units of one type

- **WHEN** a unit is deployed and the screen is drawn again
- **THEN** the chooser still names the type that was deployed
- **AND** the next square deploys another unit of it

#### Scenario: A type that is no longer offered

- **WHEN** the chooser was left on a type the seat no longer has
- **THEN** it falls back to the first type offered

#### Scenario: Registering a seat with a size half-typed

- **WHEN** a width and height are typed and a seat is registered or removed before they are sent
- **THEN** the width and height are still as they were typed

#### Scenario: A size that has been accepted

- **WHEN** a board size is sent and accepted
- **THEN** the fields show the size the board now is

### Requirement: The Deploy Board Greys Out Where A Seat May Not Place

While a seat is deploying units, the system SHALL draw the squares that seat
may not place in as greyed out, reading the allowed area from the contract
rather than working the rule out itself, and SHALL NOT let a unit be placed on
a greyed square. It SHALL say, near the board, why part of it is greyed — that
in a two-player game each player deploys on their own half and the middle row,
where there is one, is neutral.

The greying SHALL apply only while placing units during setup. Once setup is
committed, or on the play board of a resolved game, the board SHALL be drawn
without it.

#### Scenario: A restricted seat sees the other half greyed

- **WHEN** a seat in a two-player game is deploying units
- **THEN** the squares of the other half, and any neutral row, are drawn greyed out
- **AND** the seat's own half is drawn normally

#### Scenario: Nothing can be deployed on a greyed square

- **WHEN** a seat chooses a greyed square while deploying
- **THEN** no unit is deployed there

#### Scenario: An unrestricted seat sees no greying

- **WHEN** a seat in a game that is not two-player is deploying units
- **THEN** the whole board is drawn without greying

#### Scenario: The greying is only for placing

- **WHEN** the seat has committed its setup, or is looking at the play board
- **THEN** the board is drawn without any placement greying

### Requirement: The Armoury Lists What Is Deployed And Offers To Take It Back

The system SHALL list, in the armoury, the units this seat has deployed and
not committed, each with the square it stands on, and SHALL offer to take any
of them back. Taking one back SHALL free its square and its points, and the
board SHALL be redrawn without it.

The list SHALL NOT be offered once the seat's setup is committed, where taking
a unit back is refused.

#### Scenario: The deployed units are listed

- **WHEN** a seat has deployed units and not committed them
- **THEN** each is listed with its name, its type and its square

#### Scenario: Taking one back from the armoury

- **WHEN** the player takes a listed unit back
- **THEN** it is gone from the list and from the board
- **AND** the other units are untouched

#### Scenario: A commit refused for a clash can be fixed

- **WHEN** a commit is refused because a unit clashes with a square another player has committed to
- **THEN** the seat stays in the armoury with its units listed
- **AND** taking the clashing unit back and committing again is accepted

### Requirement: An Order Can Be Taken Back From The Board

The system SHALL offer, for a unit under orders whose turn is not committed, a
way to take that order back — both from the keyboard, beside the arrow keys
that give one, and as a control for a hand on a mouse. It SHALL offer it only
for a unit that has an order to take back, and SHALL say so in the keyboard
help.

#### Scenario: Taking an order back with the keyboard

- **WHEN** a unit is selected and has been ordered to move, and the take-back key is pressed
- **THEN** the unit holds no order
- **AND** the arrow drawn for it is gone

#### Scenario: A unit with no order

- **WHEN** a unit with no order is selected
- **THEN** no take-back control is offered for it

### Requirement: A Statistic Cannot Be Typed Outside Its Range

The system SHALL bound the number fields it offers to the ranges the rules
enforce — a unit type's attack, health and energy, the board's size, and a
seat's number and budget — so that a value the server would refuse cannot be
submitted from the interface. A negative attack was accepted by the field,
sent, and refused only by the server.

#### Scenario: A negative statistic

- **WHEN** a negative value is entered for a unit type's attack, health or energy
- **THEN** the form does not submit it

#### Scenario: The bounds are the rules'

- **WHEN** the design fields are shown
- **THEN** attack accepts 0 to 10, health 1 to 10, and energy 0 to 100

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

### Requirement: A Setup Can Be Changed Until It Is Committed

The system SHALL let the administrator size the board again, and add and
remove seats, for as long as the setup holding them has not been committed,
and SHALL say that this is what it is offering.

#### Scenario: Sizing the board again

- **WHEN** the administrator sizes a board that already has a size, before
  committing
- **THEN** the board becomes that size

#### Scenario: Removing a seat

- **WHEN** the administrator removes a registered seat before committing
- **THEN** it is no longer registered and no longer offered in the lobby

#### Scenario: After committing

- **WHEN** the setup has been committed
- **THEN** neither the size nor the seats are offered for changing
- **AND** the lobby stops offering to set that game up
- **AND** the administrator's setup screen says the setup is committed rather
  than showing forms whose every answer would be refused

#### Scenario: A setup that cannot be committed

- **WHEN** the administrator commits a setup that has no board
- **THEN** the commit is refused, saying the board must be set first
- **AND** the game is left exactly as it was, with its setup still to do

#### Scenario: Several games at once

- **WHEN** one game's setup is committed and another's is not
- **THEN** each says which of the two it is
- **AND** only the one still to be set up is offered a setup screen

### Requirement: Losing The Server Is Said And Recovered From

The system SHALL say, when the server stops answering, that it is not
reaching it and is still trying, and SHALL keep trying rather than stopping
at the first failure.

A screen that has quietly stopped asking looks exactly like a game in which
nothing is happening, so a player waiting for a turn cannot tell the
difference between the others thinking and their own tab having given up.

#### Scenario: The server goes away under an open screen

- **WHEN** a request fails because the server did not answer
- **THEN** the screen says it is not reaching the server and is still trying

#### Scenario: The server comes back

- **WHEN** the server answers again
- **THEN** the screen carries on from where it was, without being reloaded
- **AND** stops saying it is not reaching the server

#### Scenario: A refusal is not a lost connection

- **WHEN** a request is refused because the session is not signed in
- **THEN** the screen asks for a sign-in rather than retrying for ever

### Requirement: A Committed Setup Is Shown As Committed

The system SHALL show a player who has committed a setup what they committed,
where they committed it, and that it takes the field when the first turn
resolves.

Until that turn resolves the army is published orders and stands on no board,
so a screen drawn from the board alone shows a player nothing of theirs and
reads as work lost.

A seat that has committed SHALL be taken to the board rather than to the
armoury, and the armoury SHALL NOT offer to design or deploy for a seat whose
setup is committed. This SHALL hold once the turn has resolved as well as
before it: a seat whose army was published and then destroyed has no setup
left to do, and offering it the forms invites commands that are all refused.

#### Scenario: The board before the first turn

- **WHEN** a player has committed a setup and the first turn has not resolved
- **THEN** the units they committed are shown where they deployed them
- **AND** they are shown as not yet on the board
- **AND** the screen says the first turn is what puts them there

#### Scenario: Coming back from the lobby

- **WHEN** a player who has committed a setup opens their seat from the lobby
- **THEN** they are taken to the board

#### Scenario: The armoury after committing

- **WHEN** a player who has committed a setup reaches the armoury
- **THEN** it says the setup is committed and offers no design or deployment

#### Scenario: The armoury after the setup turn has resolved

- **WHEN** a player whose setup has been resolved reaches the armoury
- **THEN** it says the setup is over and offers no design or deployment
- **AND** it sends them to the board

#### Scenario: Who is being waited for

- **WHEN** a player has committed a setup and another seat has not
- **THEN** the seats still to commit a setup are named

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

An order SHALL stay drawn once the turn is committed, until the turn resolves.
Committing publishes the orders and locks them, but does not carry them out, so
the units still stand where they did; a board that stopped drawing them on
commit showed the player who had just committed a whole plan a board that
looked as though they had done nothing.

#### Scenario: A unit under orders

- **WHEN** a unit has been ordered to move
- **THEN** an arrow from that unit towards the square it is headed for is
  drawn on the board

#### Scenario: A unit holding

- **WHEN** a unit has no order
- **THEN** no arrow is drawn for it

#### Scenario: Orders stay drawn after the turn is committed

- **WHEN** the player commits a turn in which units were ordered to move, and the turn has not yet resolved
- **THEN** the arrows for those committed moves are still drawn on the board
- **AND** the screen still says the turn is committed and cannot be changed until it resolves

#### Scenario: The board is cleared of orders once the turn resolves

- **WHEN** the committed turn resolves
- **THEN** the board is drawn from the resolved positions, with no arrow left from the turn that resolved

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

### Requirement: A Unit's Ring Shows The Energy It Has Left

The system SHALL draw each unit's outer ring in proportion to the energy it
has left against the energy its type was designed with, so that a spent unit
can be told from a fresh one on the board itself rather than only in a table.

A unit that cannot pay for what it wants to do is the thing a player most
needs to see before ordering it, and the board is what they are looking at.

#### Scenario: A unit with all its energy

- **WHEN** a unit has the energy its type was designed with
- **THEN** its ring is drawn complete

#### Scenario: A unit part spent

- **WHEN** a unit has some of its energy left
- **THEN** that share of its ring is drawn, and the rest is not

#### Scenario: A spent unit

- **WHEN** a unit has no energy left
- **THEN** none of the proportion is drawn, and the unit is still drawn on its
  square

#### Scenario: A unit whose energy is not known

- **WHEN** a unit's type is not known to this seat, so what it was designed
  with cannot be said
- **THEN** the ring is drawn plainly rather than as a proportion of nothing

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

### Requirement: The Flag Is Designated In The Armoury

The system SHALL let a player choose which of their deployed units carries
their flag while they are setting up, SHALL show which one currently does, and
SHALL NOT offer the choice once the setup is committed.

Where a player has deployed units and designated none, the interface SHALL say
that a carrier is needed before the setup can be committed, before the commit
is attempted rather than after.

#### Scenario: Choosing a carrier

- **WHEN** a player chooses one of their deployed units during setup
- **THEN** that unit is shown as carrying the flag

#### Scenario: Changing the choice

- **WHEN** a player chooses a different unit before committing
- **THEN** only the second is shown as carrying it

#### Scenario: Committing without one

- **WHEN** a player has deployed units and designated no carrier
- **THEN** the interface says a carrier is needed
- **AND** does not offer to commit the setup

#### Scenario: After committing

- **WHEN** the setup is committed
- **THEN** the carrier is shown and cannot be changed

### Requirement: Every Flag Is Drawn On The Board

The system SHALL draw every flag in the game on the square it stands on,
whoever it belongs to and whether or not its carrier has been met, and SHALL
say in the roster which unit carries the player's own flag.

A flag drawn for a carrier the seat has not met SHALL show the square and the
owner and nothing else: no symbol, no type and no statistics.

#### Scenario: An enemy flag out of contact

- **WHEN** an enemy flag stands on a square the seat cannot otherwise see
- **THEN** the square is drawn with a flag mark naming the player it belongs to
- **AND** no unit, type or statistics are drawn for it

#### Scenario: The seat's own flag

- **WHEN** the seat's own units are listed
- **THEN** the one carrying the flag is marked as the carrier

#### Scenario: A flag that has fallen

- **WHEN** a flag carrier has been destroyed
- **THEN** no flag is drawn on any square for that player

### Requirement: An Eliminated Player Is Told They Are Out

The system SHALL tell a player whose flag has fallen that they are out of the
game, SHALL stop offering orders and commits, and SHALL keep showing them the
board and what the turns do.

#### Scenario: Losing the flag

- **WHEN** the turn that destroys a player's flag carrier resolves
- **THEN** that player is told they are out, and why
- **AND** no order or commit is offered

#### Scenario: Watching afterwards

- **WHEN** an eliminated player stays on the screen
- **THEN** the board and the account of each turn keep arriving
