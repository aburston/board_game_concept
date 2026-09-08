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

### Requirement: A New Game Is Offered The Next Free Number

The system SHALL offer, when a game is made, the lowest number no game in the
lobby has, counting from 1, and SHALL offer it again as soon as a game has
been made.

It is the offer the setup screen makes for a seat, for the same reason: the
number of the next game is one the lobby already knows, and typing it was a
chance to collide with a game that exists — which is refused, after the form
has been sent. The lowest free rather than one past the highest, so a number
no game has any longer is offered again rather than left as a gap.

What is offered SHALL be a suggestion and not a limit: a number typed over it
SHALL be the number the game is made with, and SHALL be kept while the lobby
is drawn again.

#### Scenario: The first game

- **WHEN** the lobby lists no games
- **THEN** the number offered is 1

#### Scenario: One game after another

- **WHEN** a game is made
- **THEN** the number offered is the next one free

#### Scenario: A number the administrator chose instead

- **WHEN** a number is typed over the one offered and the game is made
- **THEN** the game has the number that was typed
- **AND** the number offered next is again the lowest that is free

#### Scenario: A number half-typed when the lobby is drawn again

- **WHEN** a number is typed and the lobby is drawn again before it is sent
- **THEN** the number is still as it was typed

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

A seat number typed over the one the interface offers SHALL be kept the same
way, and SHALL go back to being offered once a seat has been registered.

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

#### Scenario: A seat number typed over the one offered

- **WHEN** a seat number is typed and the board is sized before it is sent
- **THEN** the number is still as it was typed

### Requirement: A New Seat Is Offered The Next Free Number

The system SHALL offer, when a seat is registered, the lowest player number
that no seat in the game holds, counting from 1, and SHALL offer it again as
soon as a seat has been registered.

Registering four seats meant typing 1, 2, 3 and 4 — four numbers the screen
already knew, and four chances to type a number nobody meant to register.

The lowest free number rather than one past the highest: a game a seat has
been removed from has a gap, and the next seat registered fills it rather than
leaving the numbering with a hole in it for the rest of the game. The number
offered SHALL be one a seat may have, so the administrator's own number and
the observer's are never offered.

#### Scenario: The first seat of a new game

- **WHEN** a game has no seats registered
- **THEN** the number offered is 1

#### Scenario: One seat after another

- **WHEN** a seat is registered
- **THEN** the number offered is the next one free

#### Scenario: A gap left by a seat that was removed

- **WHEN** a seat is removed from the middle of the numbering
- **THEN** the number offered is that seat's, rather than one past the highest

#### Scenario: A number the administrator chose instead

- **WHEN** a number is typed over the one offered and registered
- **THEN** the seat has the number that was typed
- **AND** the number offered next is again the lowest that is free

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

The health drawn on the board SHALL be coloured by **how much is left, not by
whose the unit is**, in the same three bands and at the same boundaries as a
unit's energy — green above two thirds, amber from a third to two thirds, red
at a third or below — so that the two things drawn round a unit are read the
same way and a player learns one scale rather than two.

This SHALL hold for every unit drawn, an enemy's as well as the seat's own,
so that a player can see which enemy is nearly finished. Whose a unit is SHALL
still be said, by its ring and its glyph.

Level SHALL NOT be told by colour alone: the length of the bar says it too,
and the figures are given in the unit's description and in the tray.

#### Scenario: A unit that has been fought

- **WHEN** a unit has lost health
- **THEN** what it has left and what it was built with are both shown
- **AND** it is drawn differently from a unit at full health

#### Scenario: On a device with no pointer

- **WHEN** the interface is used on a touchscreen
- **THEN** health is readable without hovering anything

#### Scenario: Health read by colour

- **WHEN** a unit has most of its health
- **THEN** its health is drawn green
- **AND** amber where a third to two thirds is left, and red at a third or
  below

#### Scenario: The same scale for health and energy

- **WHEN** a unit's health and its energy are at the same share of what they
  were built with
- **THEN** both are drawn in the same colour

#### Scenario: An enemy nearly finished

- **WHEN** an enemy unit this seat can see is down to a third of its health
- **THEN** its health is drawn red
- **AND** the unit is still shown to be an enemy

#### Scenario: A watched board

- **WHEN** a watching session is drawing units coloured by player number
- **THEN** health and energy are still drawn by how much is left
- **AND** which player a unit belongs to is still said by its ring and its
  glyph

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

### Requirement: A Unit's Ring Shows The Energy It Has Left

The system SHALL draw each unit's outer ring in proportion to the energy it
has left against the energy its type was designed with, so that a spent unit
can be told from a fresh one on the board itself rather than only in a table.

A unit that cannot pay for what it wants to do is the thing a player most
needs to see before ordering it, and the board is what they are looking at.

The proportion SHALL be drawn **outside** the ring rather than over it. The
ring is what says whose a unit is — its colour, and the dashed outline an
enemy is given — and an arc painted along the same line hid that, worst on a
unit with most of its energy left, which covers most of its own ring. The
ring SHALL be drawn whole and uncovered whatever the proportion, and the arc
SHALL stay within the unit's square.

The arc SHALL be coloured by **how much is left, not by whose the unit is**:

- above two thirds, green;
- from a third to two thirds, amber;
- at a third or below, red.

The colours SHALL be distinguishable in both the light and the dark scheme,
and level SHALL NOT be told by colour alone — the length of the arc says it
too, and the exact figures are given in the unit's own description and in the
orders tray.

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

#### Scenario: The ring is not covered by the arc

- **WHEN** a unit has most of its energy left
- **THEN** its ring is drawn whole, in the colour that says whose it is
- **AND** the arc is drawn outside the ring, covering none of it

#### Scenario: Energy read by colour

- **WHEN** a unit has most of its energy
- **THEN** the arc is green
- **AND** it is amber where a third to two thirds is left, and red at a third
  or below

#### Scenario: An enemy's energy is read the same way

- **WHEN** an enemy unit this seat can see is low on energy
- **THEN** its arc is red, as one of the seat's own would be
- **AND** the unit is still shown to be an enemy by its ring and its glyph

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
