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

The system SHALL tell a player whose flag has fallen, when the replay reaches
that turn, that they are out of the game and why, and SHALL keep showing them
the board and what the turns do to the end of the record.

#### Scenario: Losing the flag

- **WHEN** the replay reaches the turn that destroys a player's flag carrier
- **THEN** that player is told they are out, and why

#### Scenario: Watching afterwards

- **WHEN** the replay moves past that turn
- **THEN** the board and the account of each turn keep arriving

### Requirement: A Program Is Written In The Armoury

The system SHALL let a player write or paste the program of one of their
types in the armoury during setup, listing each line's tick cost beside it
and what the type's compute buys. A line the instruction set refuses SHALL
be marked where it stands, and the program SHALL NOT be sent until every
line is accepted. Compute SHALL be chosen beside the other three statistics,
and a type whose compute is 0 SHALL be offered no program.

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
of the record, controls to play, pause, step forward and back, and a speed
the viewer chooses, the board at each turn drawn from the record with every
unit on it. While any player's setup is uncommitted the interface SHALL say
it is waiting for setups, naming whose, and SHALL move to the replay of its
own accord when the game resolves.

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
