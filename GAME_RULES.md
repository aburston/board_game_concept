# The Rules of the Game

Every rule the game actually plays by, stated in one place, in the order you
meet them. Then the questions that are still open — the ones that are design
choices rather than defects.

Sources: `openspec/specs/` is the stated intent and `src/board_game_concept/` is
what runs; the two agree. `SPEC_COVERAGE.md` records where they did not, and
what was done about each.

Rules are numbered `R1.1`, open questions `Q1`, so you can point at one.

---

# Part 1 — The rules

## R1. What the game is

**R1.1** Two or more players design their own unit types, deploy units of those
types onto a shared grid, and then each turn order each unit to step one square
in one of four directions. Units that end up on the same square fight.

**R1.2 The invariant: no randomness in the resolution of the rules.** A turn is
a pure function of the board and the orders given — the same orders on the same
board always resolve the same way. There is no dice, no hidden roll, and no
random number anywhere in the game. Nor is there any rule decided by the order a
list happens to hold its members in: that is unpredictable to a player in
exactly the way a die roll would be, and harder to see. Where two things could
happen, the rules decide which.

This constrains every rule in this document and every rule added to it. It is
enforced, not remembered: `tests/test_determinism.py` resolves hundreds of
random boards against every ordering of their units and requires one answer
each.

**R1.3** There are three kinds of session against one game: the **server**
(player 0, the administrator, and the commit authority), one **client** per
player, and any number of read-only **observers**.

**R1.4** The game ends when one player is the last with a unit left standing,
or in a draw when the last players are wiped out together. See **R7**.

---

## R2. Setting up

**R2.1 The board.** A game is created with a board of **8 x 8** already on it,
so a game that nobody sets up further is still a game that can be played. The
administrator may resize it with `set board <size_x> <size_y>` or
`load board <file>`, and may resize it again, until the setup is committed.
Each dimension must be an **integer from 2 to 10** inclusive.

**R2.2 Coordinates.** A square is `(x, y)`. `x` runs left to right, `y` runs
**top to bottom**, both from 0. `(0, 0)` is the top-left square. `show board`
draws row `y=0` first, so north is up the screen.

**R2.3 Players.** The administrator registers each player before play starts,
with `add player <number> [budget]` or `load player <file>`. Player numbers are
integers. Player 0 is the administrator and holds no units. No player can be
added once the game has started.

**R2.3.1 The point budget.** Each player is registered with a **point budget**,
which is what bounds the army they may deploy (**R2.9**). It is an integer from
**1 to 1000**, and is **250** where the administrator does not name one - what
the default army (**R2.13**) costs, and 18 points over, so that a player can
change what they were given without first taking something back. Two
players of the same game may be given different budgets. A budget is fixed at
registration: nothing in play raises or lowers it. A player file may carry a
`budget:` key; one that does not gets the default.

**R2.4 Unit types.** Each player defines their own unit types with
`add type <name> <symbol> <attack> <health> <energy>`:

| Field | Rule |
|---|---|
| `name` | one or more characters |
| `symbol` | **exactly one** character — this is how the unit is drawn |
| `attack` | integer, **0 to 10** |
| `health` | integer, **1 to 10** |
| `energy` | integer, **0 to 100** |

**Attack 0 is allowed, with or without energy.** With no energy it is a wall
(**R2.10**): health standing on a square. With energy it is a **scout** — it
goes where it likes and strikes nothing, and it is priced accordingly, since
what it costs is `attack + health + energy` (**R2.9**) and its attack is
nothing. What is refused is **energy 0 with an attack above it**: an attack
the type could never pay for is a wall that was charged for a weapon.

**A type with any energy must hold at least its movement cost in it.** A
move costs a unit a quarter of its health, rounded up (**R4.3**), and rest gives
back 1 a turn (**R3.9**), so a type with less energy than that could never
afford a single move at any point in its life. `add type Heavy H 3 6 1` is
refused, because health 6 costs 2 to move; `add type Heavy H 3 6 2` is a unit
that can cross one square and must then stand still for two turns. A scout is
held to this like anything else that means to move. Only a type with **no
energy at all** is exempt: 0 energy against a fare it can never pay is the
whole point of a wall (**R2.10**).

A type is rejected at the moment it is defined, not later during play. Types are
private to the player who defined them: an opponent learns of one only by
fighting a unit of it (**R6.2**).

**R2.5 What the three statistics mean.**
- **attack** — damage dealt per attack, *and* the energy that attack costs.
- **health** — total damage the unit absorbs before it is destroyed, *and* the
  energy each of its moves costs (**R4.3**). Health is paid for twice over:
  once at the till, and again every square the unit walks.
- **energy** — the single resource spent by both moving and attacking. A unit
  that takes no action during a turn gets **1** of it back (**R3.9**).

**R2.6 Deploying units.** `add unit <type> <name> <x> <y>` creates one unit as a
copy of one of your own types, at those coordinates. It is refused if:
- there is no board yet, or
- the coordinates are off the board, or
- you already have a unit of that name (**R2.7**), or
- the square is already held, or already claimed by another unit waiting to be
  deployed this turn, or
- your point budget will not pay for it (**R2.9**).

**R2.6a Where you may deploy.** In a game of **exactly two players** the board
is halved by rows during setup: the **lower-numbered** player deploys in the
rows nearer row 0 and the other in the rows nearer the last. Columns are never
restricted, so a half is the full width of the board. Where the number of rows
is **odd**, the single middle row is **neutral** and belongs to neither player.

Every other number of players - one, three, more - may deploy anywhere on the
board. The same rule is applied; it just does not divide anything.

The area you may deploy in is published, so a client can show it to you.

**R2.7 Unit names.** A name must be unique **within one player's** units. Two
different players may both have a unit called `scout`; an order is always
resolved against the units the ordering player owns, and so is what each
player is told a turn did (**R6.8**). The default army (**R2.13**) hands both
players the same fifteen names, so this is the ordinary case rather than an
awkward one.

**R2.8 Setup ends at your first commit.** Before your first `commit` you may
define types and deploy units but may not order movement. After it you may order
movement but may no longer define types or deploy units. There is no way to
reinforce later.

**R2.9 What a unit costs.** A type costs `attack + health + energy` points, so
`add type Cross X 1 10 10` costs **21**. The cheapest type a player can define
costs 3 and the dearest costs 120. Defining a type is free; **deploying** is
what spends. Each unit deployed costs its type's price again, so four Crosses
cost 84 of a 100-point budget and a fifth is refused.

What you have spent is the total price of every unit you have deployed,
including the ones that have since been destroyed. **There are no refunds**:
points buy a unit, not the time it survives for. A deployment that would take
you past your budget is refused, naming the cost and what you have left; one
that spends exactly what is left is allowed. `show types` prints each type's
`COST`, and `show players` prints your `BUDGET`, `SPENT` and `LEFT`.

The rule is applied again when the turn resolves, so a deployment that reaches
the server without passing through a client — a loaded player file, most
likely — is refused there instead, and reported as a rejected order. Where more
deployments arrive in one turn than the budget can pay for, they are charged in
order of unit name, so which ones survive is decided by the rules and not by the
order they were written in.

**R2.10 Walls and scouts.** A type with **attack 0 and energy 0** is a wall:
health standing on a square. A type with **attack 0 and energy above it** is a
**scout**: it moves like anything else and lands nothing when it arrives,
taking whatever is dealt to it. A scout is a unit like any other for every
other rule - it blocks a square, it can carry the flag (**R2.11**), and its
energy means it can act, so it **does** keep its owner in the game where a
wall does not (**R7.1**). It can never be ordered to move, because a move costs it
a quarter of its health in energy (**R4.3**) and it holds none, and never will
(**R3.9**
gives nothing back to a type designed with none). It never attacks and never defends itself, so an exchange in
which only walls stand lands no attacks and nobody is destroyed (**R5.6**). It
can be destroyed like anything else, it blocks a square like anything else, and
it costs its health and nothing else — a wall of 10 health costs 10 points.

Because a wall can never recover and never act, **it does not keep its owner in
the game** (**R7.1**). An army of nothing but walls has already lost; walls are
ground you deny an opponent, not an army.

**R2.11 One of your units carries your flag.** You designate it during setup
with `set flag <unit>`, naming one of your own units, and you may change your
mind until you commit; after that it is fixed for the game and cannot be moved
to another unit. Carrying costs nothing and changes nothing about the unit: a
carrier fights, moves and costs exactly what its type says. A setup is
**refused** unless exactly one of your units carries your flag — a player who
cannot lose a flag would be playing a different game from everybody else at
the table — and a player who deployed nothing therefore cannot commit at all.

This rule is a **break**: a game set up before flags existed cannot be played
on, because its units carry none and nothing will read a flag that is not
there. Finish such a game by starting a new one.

**R2.13 A game comes with an army.** Nothing below is a rule you have to obey.
It is what a game hands you so that you can play one without inventing one
first, and every piece of it is an ordinary setup decision you may change.

*The catalogue.* Every player is registered holding these eight types. They
cost nothing until you deploy one (**R2.9**), you may redefine any of them
under its own name, add your own alongside, and never deploy the ones you do
not want.

| Name | Symbol | Attack | Health | Energy | Cost | Move fare |
|---|---|---|---|---|---|---|
| Wall | `W` | 0 | 10 | 0 | 10 | 3 |
| Scout | `o` | 0 | 2 | 12 | 14 | 1 |
| Pawn | `p` | 1 | 4 | 2 | 7 | 1 |
| Runner | `r` | 2 | 4 | 10 | 16 | 1 |
| Line | `L` | 3 | 6 | 12 | 21 | 2 |
| Lance | `!` | 8 | 2 | 10 | 20 | 1 |
| Keep | `K` | 1 | 10 | 5 | 16 | 3 |
| Heavy | `H` | 5 | 10 | 15 | 30 | 3 |

*The array.* In a **two-player** game each player also opens their seat with
sixteen of those units already deployed in their own half (**R2.6a**), and
their flag (**R2.11**) already on the left-hand Keep. It costs **242** of the
250-point budget. Both players get the same layout, mirrored, reading from
each player's own edge inwards:

```
    depth 1   p  p  W  H  H  W  p  p      the slow rank, nearest the enemy
    depth 0   r  o  L  K  K  L  o  r      the fast rank, and the flag
```

Both rows are **symmetric about the middle of the board**: what stands in one
column stands in its mirror. There is no reason for one flank to be stronger
than the other before anybody has moved. It is why there are two Keeps —
eight columns leave no middle square for one — and why the Lance is in the
catalogue but not in the opening array: four pairs a row is eight pairs, and
eight pairs of eight different types come to 268 points.

The slow units stand in **front**, which is the opposite of chess, because a
unit's reach is its energy divided by its move fare (**R4.3**). A Heavy has
five moves in it and a strike costs five more, so one deployed at the back of
your half arrives at the fighting line with nothing left to fight with. A
Runner has ten moves. The units that can afford to travel are the ones that
can start further back.

*When you get no army.* The array is deployed only where it can stand as it
is: a game of exactly two players, on a board with room for it inside your own
half, and a budget that covers it. Otherwise you are given the catalogue and
you deploy by hand, as you always could.

*Changing it.* Take a unit back with `remove unit <name>` (**R2.12**) and its
points come back with it. In a browser, clicking a unit you have placed takes
it back; clicking an empty square in your own half deploys there. Take the whole array back and it stays gone - it is
not deployed again when you next open your seat.

*A note on the administrator.* The board and the number of players can still
be changed after you have been given an army. If the board is resized under
you, or a third player registered, your array may no longer be somewhere you
are allowed to stand - your commit is refused, saying so, and you take the
units back and place them again (**R3.5a**).

**R2.12 You can take back a unit you have not committed.** `remove unit
<name>` puts it back in your hand: the square falls free, the points are
unspent, and the name can be used again. It is the same as never having
deployed it. Once your setup is committed the units are published and playing,
and what happens to them is the game's business rather than yours — so this is
refused after the commit, as everything else in setup is.

---

## R3. The turn

**R3.1 Simultaneous commit.** Every player issues all their orders, then
`commit`. The server holds the turn open until **every player still in the
game** has committed, then applies all orders together. A player who has been
eliminated (**R7.1**) is not waited for. Nobody gains from committing early or
late, and nobody gains from the order the server happens to read the orders
in.

**R3.2 Commits are final, and nothing before one is.** Once you commit you
cannot withdraw or amend. Your client blocks and waits for the server rather
than accepting further orders. Until then every order is still yours to
change: `hold <unit>` takes back the order a unit was given this turn, leaving
it with none at all — which is holding, so it rests (**R3.9**) like any unit
that was told to do nothing.

**R3.3 Orders are used once.** After a turn resolves, every unit's direction is
cleared and its state returns to `NOP`. An order never carries over to the next
turn. A unit given no order stays where it is.

**R3.4 A turn resolves in four phases, in this order:**
1. **Deployment** — units waiting to be placed are put on the board.
2. **Movement** — every unit's destination is worked out against the board *as
   the turn began*, and then every move is applied at once. Squares that end up
   holding more than one unit are collected.
3. **Combat** — every one of those squares is fought out to a conclusion.
4. **Rest** — every unit that did none of the above gets a point of energy
   back (**R3.9**).

Because destinations are decided before any move is applied, the outcome of a
turn never depends on the order the units happen to be held in. Both later
phases complete inside the same turn: a fight never carries over.

**R3.5 Deployment happens on the turn you commit it.** A newly created unit is
placed on the board when the turn resolves. If its square is taken by then, the
deployment is refused, no unit is created, and the turn resolves without it —
the turn is not failed.

**R3.5a A setup commit that clashes with a committed square is refused.** You
cannot see anybody else's units while you are setting up, so two of you can
choose one square without knowing it. Committing a setup that deploys onto a
square another player has already committed a unit to is **refused**, naming
the square: nothing of yours is published, nothing is marked committed, and
your setup is still yours to change. Take the unit back (**R2.12**), put it
somewhere else, and commit again.

The setup committed **first** keeps the square. That is a change from refusing
both, which was there so that neither player gained from the order they were
read in; the price of being able to do something about a clash is that
committing early decides it. It also tells you that the square is taken,
which you would not otherwise know until you met what is standing there — the
least that lets you deploy somewhere else. Both are accepted **for setup**,
and this rule reaches nothing else: deployments happen only during setup.

Where deployments reach the server without a commit — a loaded player file, or
orders written by hand — **both** are still refused when the turn resolves, so
nothing that goes round the commit gains by it.

**R3.6 A refused order does not stop the turn.** The server refuses the single
order, records it against that player, and carries on. Each player is written a
list of what was refused; the client prints it before taking the next command.
The list describes only the turn just resolved — it does not accumulate.

**R3.7 Every order that does nothing says so.** Anything of yours the turn
would not carry out is reported back to you: an order refused while it was
being applied, a move nobody could pay for, a move off the board, and a contest
of yours that ended undecided. Each names the unit, its square, and the reason.

**R3.9 A unit that does nothing recovers 1 energy.** At the end of every turn,
each unit standing on the board that **was given no order** and **paid for
nothing** while the turn resolved gets 1 energy back. It never recovers past
the energy its type was designed with, and a destroyed unit recovers nothing.

Both halves matter. A unit ordered to move has acted whether or not the move
happened — one ordered off the board pays nothing (**R4.6**) and still does not
rest, so walking into the edge is not a way to refuel. A unit that was attacked
and could not afford to strike back has done nothing at all, and does rest:
being hit is not an action.

Rest happens after combat and before the game is judged (**R7**), so a unit
that spends its last energy acting is out before it can recover it, while one
that merely stood still is not.

**R3.8 Turns are numbered.** Resolved turns count from 1, and the number is
recorded with the board, with each player's view, and with each player's list of
refused orders, so every record says which turn it describes. The
administrator's commit that ends setup is not a turn and is not numbered.

---

## R4. Movement

**R4.1 One square, four directions.** `move <unit> <north|south|east|west>`.
No diagonals, no multi-square moves, no standing order.

| Direction | Effect |
|---|---|
| `north` | y − 1 |
| `south` | y + 1 |
| `east`  | x + 1 |
| `west`  | x − 1 |

**R4.2 You may only order your own units, and only units on the board.**

**R4.3 Moving costs energy.** A move costs a unit **a quarter of its maximum
health, rounded up** — a quarter of the health its type was designed with —
whatever the unit finds at its destination. The fare is read from the design and
never from the health play has worn down, so a unit that has been hurt pays
exactly what it paid while whole: damage is not weight shed.

Health is 1 to 10, so the fare is one of three numbers:

| maximum health | fare per square |
|---|---|
| 1, 2, 3, 4 | **1** |
| 5, 6, 7, 8 | **2** |
| 9, 10 | **3** |

Two things follow from that table, and both are worth knowing before you buy.
**The fare is a step, not a slope**: health 4 is four times the durability of
health 1 for the same fare, and is the best value on the board. **Health 5 is
the worst**: one more point of health than health 4, for double the running
cost, for ever.

Rounding is upward, so **no unit ever moves for nothing**. A fare of zero would
put a unit outside the energy economy entirely — it could cross the board for
ever and never need to rest — and it is the cheapest units that would escape.

Weight therefore costs mobility. A unit's energy divided by its fare is the
number of squares it has left in it, and armour is paid for twice — once at the
till (**R2.9**), and again every square it walks.

**R4.4 You pay for every move that happens, including starting a fight.**
Stepping onto an occupied square is charged exactly like stepping onto an empty
one.

**R4.5 If you cannot pay, you do not move.** The unit stays put and its energy
is unchanged. The order is still consumed and is not retried next turn, and the
refusal is reported to you.

**R4.6 The board edge stops you.** A unit ordered off the board stays at the
edge square, pays nothing, and its order is consumed. The refusal is reported to
you, and the turn continues normally for everyone else.

**R4.7 What a unit finds where it lands decides what happens.** Because every
destination is worked out before any move is applied, this is judged on where
units *finish* the turn, not on where they started it:

| The destination, once every move has been applied | Result |
|---|---|
| Held by nobody else | The unit moves in alone and its old square becomes empty. |
| Held by other units that also moved in | They contest the square. |
| Held by a unit that did not move | They contest the square. |

A unit needs only the fare — a quarter of its health in energy — to arrive. A
unit that
cannot then afford to attack still arrives, and is inert in the fight it has
walked into.

**R4.8 A unit that follows another out of its square arrives cleanly.** If the
unit standing in your destination is itself moving away this turn, you simply
take the square: nothing is contested.

**R4.9 Two units ordered into each other's squares collide.** They do not pass
through one another. Neither completes its move, each pays its own fare — which
is its own health, and need not match the other's — and they
fight where they stand:
- one survivor → it completes its move into the square the loser held;
- no survivor → both squares are left empty;
- both survive → each stays in the square it started the turn in.

**R4.10 There is no way to stack with your own units.** Two of your own units on
one square fight each other (**R5.7**).

---

## R5. Combat

**R5.1 A fight is any square holding more than one unit** once every move has
been applied, however they got there — one unit stepping onto another, or
several stepping into the same empty square at once. A head-on collision
(**R4.9**) is fought on the same terms.

**R5.2 A fight is one exchange a turn, and it is simultaneous.** The units
standing in the square each attack **every other** unit standing there, once,
all at the same instant. A unit destroyed by the exchange still lands its own
attack in it. Then the exchange is over: nobody strikes twice in a turn. To
press a fight you order the unit back into the square next turn, and the turn
after — a defended square is taken over several turns, not ground out in one.

**R5.3 The exchange costs the attacker its attack value in energy — once**,
however many opponents it strikes, and deals that same value in damage to each
of them. It is all or nothing: a unit that cannot pay strikes nobody, so no
opponent is favoured by where it stands in the square. Facing three opponents
costs no more energy than facing one, though you take three attacks in return.
Because there is one exchange a turn, a fight never costs a unit more than its
attack value in a single turn, whatever it walks into.

**R5.4 A unit that cannot pay for an attack simply does not make it.** It deals
no damage and spends nothing. It is not destroyed for it.

**R5.5 Damage comes off health. Health at zero or below destroys the unit.**
Health is the only thing that destroys a unit — running out of energy never
does.

**R5.6 The exchange happens once, and that is the fight for the turn.** There
is no repeat: whoever is left standing after the one exchange is left standing.
If that is more than one unit the square is undecided (**R5.8**) and the units
that moved in fall back — a fight that destroys nothing settles nothing, and is
paid for again only if you order the unit back in.

**R5.7 Friendly fire is total.** Every unit in the square attacks every other
unit in it, regardless of who owns it. Two of your own units meeting on a square
will kill each other on exactly the same terms as enemies.

**R5.8 How the square is left:**

| Outcome | Result |
|---|---|
| Exactly one survivor | It alone holds the square. |
| No survivors | The square is empty. |
| More than one survivor (**undecided**) | Every survivor that *moved in* this turn goes back to the square it came from. A survivor that was already standing there keeps the square. |
| A survivor whose old square was taken during the turn | It stays on the contested square, on the board, and that square counts as occupied to anyone entering it. |

**R5.9 Destruction is final.** A destroyed unit is marked off-board and taken
out of its square without disturbing anyone still standing in it. It takes no
part in any later turn, it can never be deployed or restored to the board, its
name cannot be reused, and no square falling empty brings it back. It stays in
the record as a casualty (**R6.6**).

**R5.10 Inert units.** A unit whose energy has fallen below its attack value can
no longer attack or defend itself, but is *not* removed. It stays on the board,
holds its square, blocks movement, and can only be cleared by being killed. It
keeps its owner in the game whatever it holds, because a unit that stands still
recovers 1 energy a turn (**R3.9**): an inert unit is one that needs to rest,
not one that is finished. A **wall** (**R2.10**) is the exception — its type was
designed with no energy, so it has nothing to recover to, and it is the one
kind of unit that does not keep its owner in the game (**R7.1**).

**R5.11 Two consequences worth spelling out, because they decide how the game
plays:**
- **A strike kills only if it is lethal on its own.** One exchange deals the
  attack value once, so a unit is destroyed this turn only if that single
  strike takes it to zero health. Anything it does not kill survives, and the
  contest is undecided — the movers fall back and you pay again next turn to
  press it. Wearing a unit down takes as many turns as `ceil(health ÷ attack)`
  strikes, one strike a turn.
- **Identical units no longer destroy each other in a turn.** Two matched units
  each take one strike and both live, unless that one strike is lethal (attack
  at least the other's health). A mirror match is a stand-off that has to be
  fought out over turns, not a mutual annihilation in one. See **Q2**.

---

## R6. What a player can see

**R6.1 You always see your own units,** wherever they are.

**R6.2 You see an enemy unit only by fighting it.** Visibility is recorded when
two units actually *exchange attacks*, whether in a contested square or in a
head-on collision (**R4.9**). Merely being next to an enemy reveals nothing.
Contact also reveals that unit's **type**, with the statistics its owner
designed it with.

**R6.3 Visibility is not cumulative.** Every unit's record of what it has seen is
wiped at the start of each turn's resolution. An enemy you fought last turn and
did not touch this turn drops off your board and out of `show units`.

**R6.4 The server publishes each player a view** of what they may see, and that
view is the *only* board the client is given — it never reads the record of
every unit. A unit fought by several of your units is still named once.

**R6.5 A flag is the one thing shown without contact.** Every player is shown
which square each flag stands on and which player it belongs to, whoever they
have met (**R2.11**). Nothing else about the unit carrying it is shown — not
its name, its type, its symbol or its statistics — until contact discloses
them the way contact discloses any unit's (**R6.2**). You know where to go,
not what you will meet. A flag whose carrier has been destroyed is reported as
fallen and stands on no square.

**R6.6 The observer sees everything** — all units, all squares, all types,
regardless of ownership or contact.

**R6.7 Your casualties stay on your list.** Your own destroyed units keep being
listed for you, marked destroyed and off the board, so you can see what you have
lost. They are never drawn on a square. An enemy unit you destroyed appears in
your view for that turn only, and drops out like any other contact (**R6.3**).

**R6.8 You are told what a turn did to your own units, and nothing of what
other players did to each other.** A fight is told to the people in it: if one
of your units struck, was struck, moved or fell, you are told, by name and
square. If two other players fight, you are told nothing of it — not the
blows, not the square, not that it happened — even where you could see both of
them. Being able to see two units is not being in their fight, and an account
of a turn is a way of learning where somebody is.

What a square **came to** is told to everyone who was in it: a unit falling in
front of you is not something that can be kept from you, and being told you
killed something is the point of having struck it. The observer reads the
whole log (**R6.6**).

Whose units an entry is about is what decides this, not the names in it. Two
players may hold a unit of one name (**R2.7**) - the default army gives them
fifteen - and each is told only about their own.

---

## R7. Ending the game

**R7.1 You are eliminated when you have nothing left that could ever act
again.** A player is out once every unit they own is either destroyed or is a
**wall** (**R2.10**). What matters is whether a unit has a future, not what it
holds this turn: a unit at zero energy recovers a point for every turn it does
nothing (**R3.9**), so it is spent for the moment rather than finished, and it
keeps you in. A wall is the one unit that never recovers, because its type was
designed with no energy at all — it can never move and never strike, so it holds
a square for you and nothing else. It is the *only* such unit, and that is what
the energy-at-least-health rule of **R2.4** is for: without it a type could be
designed that rests for ever and never affords a square, which would be a wall
in everything but name while still keeping its owner in the game. A player who deployed nothing is out on the
first turn with units on the board.

**R7.1a You are also eliminated when your flag falls.** A player whose flag
carrier is destroyed is out at that resolution, whatever else they still hold
(**R2.11**). What keeps you in is something that can act *and* a flag still
standing — so a carrier that never reached the board puts you out the same
way. Your setup cannot be committed without one, but a deployment can still be
refused as the turn resolves (**R3.5**), and a player holding an army with no
flag would be the one player the flag could never be taken from.

**R7.1b An eliminated player's units are left standing and go inert.** They
hold the squares they are on, take no orders and land no attack, and they are
still attacked and destroyed like any other unit — clearing them is how the
square is taken. An army without its flag is terrain: it blocks a square until
somebody clears it, and it decides nobody's game.

**R7.2 The last player standing wins.** The game is decided at the end of the
turn in which every other player becomes eliminated. If the last players lose
their last playable unit together, it is a **draw**.

**R7.2a The game begins when the players' setups are resolved**, not when the
first unit lands. The administrator's commit that ends setup is resolved like
a turn before anybody has committed one of their own, and eliminates nobody.
Everything after it is the game — including a first turn that refuses every
deployment, which leaves both players with nothing standing and is a draw.
Judging that turn on what survived it left a game that could be neither played
on nor finished.

**R7.3 A game with fewer than two registered players is never decided.** There
is nobody to be the last player standing against; a solo game is a sandbox.

**R7.4 A decided game stops.** No further turn is resolved and no further order
is accepted. The server reports the result and exits; a client reports it and
refuses orders and commits, though it will still show you the final board; the
observer reports it too. An eliminated player is told they are out and stops
being waited for at the commit barrier.

---

## R8. What each role may type

Every role: `help`, `exit`, `show ...`.

| Command | Server | Client | Observer |
|---|:--:|:--:|:--:|
| `set board <x> <y>` | ✔ | | |
| `add player <number> [budget]` | ✔ | | |
| `remove player <number>` | ✔ | | |
| `load board <file>` | ✔ | | |
| `load player <file>` | ✔ | | |
| `add type <name> <symbol> <attack> <health> <energy>` | | ✔ | |
| `add unit <type> <name> <x> <y>` | | ✔ | |
| `remove unit <name>` | | ✔ | |
| `set flag <unit>` | | ✔ | |
| `move <unit> <north\|south\|east\|west>` | | ✔ | |
| `hold <unit>` | | ✔ | |
| `commit` | ✔ | ✔ | |
| `reload` | | | ✔ |
| `show board` / `types` / `units` / `players` | ✔ | ✔ | ✔ |
| `show pending` / `events` / `designs` / `flags` | ✔ | ✔ | ✔ |
| `show placement` | ✔ | ✔ | ✔ |

Every `show` answers with a table: a header naming its columns, then one row per
thing, lined up so a row can be read across and a column compared down.
`show board` draws the grid and, below it, a legend of what the symbols on it
stand for. A subject with nothing in it yet says so in a line rather than
printing an empty table.

Ending a `show` in `json` — `show units json` — writes the same content as a
single JSON document instead, for a caller that is not a person. It holds one
key, named for the subject, and the fields a player acts on; it is not the
storage format, and nothing else is printed with it. `json` is the only word a
subject may be followed by: anything else is reported as an invalid show
command.

The observer is read-only because it is never given the commands that write.
A blank line does nothing; an unrecognised command is reported and the session
continues. A session ends on `exit`, and also when its input runs out — so a
role can be driven from a script or a pipe as well as from a keyboard.

---

## R9. Every cost in one place

Nothing new is stated here. This is the rules above, gathered into one table,
because what a thing costs is the question most often asked of them and the
answer is currently spread across four sections. **Where this table and a rule
disagree, the rule is right** — and `tests/test_cost_table.py` holds the
numbers in it to the ones the game actually charges.

There are two currencies. **Points** are spent once, at deployment, out of a
budget fixed for the game (**R2.3.1**). **Energy** belongs to the unit and is
spent a little at a time, by moving and by attacking, and by nothing else.

The fare for a move is not a constant: it is **a quarter of the health the
unit's type was designed with, rounded up** (**R4.3**), read from the design and
never from the health play has worn down. Health is 1 to 10, so the fare is 1
for health 1 to 4, 2 for health 5 to 8, and 3 for health 9 or 10 — and never 0,
because it rounds up.

| What | What it costs | Rule |
|---|---|---|
| Defining a type | nothing — but a type with any energy must be designed holding at least its movement cost in it, or it could never afford one move | **R2.4** |
| Deploying a unit | **points**: `attack + health + energy`, its type's price | **R2.9** |
| — a unit that is destroyed | nothing back; there are no refunds | **R2.9** |
| A move onto an empty square | **a quarter of the unit's maximum health, rounded up**, in energy | **R4.3** |
| A move onto an occupied square | **the same fare**, whatever it walks into | **R4.4** |
| A head-on collision | **the fare, from both units**, though neither moves | **R4.9** |
| A move nobody can pay for | **nothing** — the unit stays put, and the order is consumed | **R4.5** |
| A move off the board | **nothing** — the unit stays at the edge, and the order is consumed | **R4.6** |
| A turn's fight in a square | **the attacker's `attack` value**, charged once for the one exchange however many opponents it strikes | **R5.3** |
| — an exchange it cannot afford in full | **nothing** — it strikes nobody rather than striking some | **R5.4** |
| — an exchange fought by a wall | **nothing** — a wall never attacks | **R2.10** |
| Being attacked | **nothing in energy**; damage comes off health | **R5.5** |
| A turn in which a unit did nothing | **gains 1 energy**, never above the energy its type was designed with | **R3.9** |
| — a turn in which it was given any order | **gains nothing**, even if the order cost it nothing | **R3.9** |

Three things follow from the table that are worth stating out loud, because
they decide how the game is played and none of them is obvious from any single
row:

**A kill costs about the victim's health, whatever your attack is, but it
costs it over turns.** Killing a unit of health `h` takes `ceil(h ÷ a)` strikes
at `a` energy each — one strike a turn — so the bill is `a × ceil(h ÷ a)`
energy, always at least `h` and exactly `h` when `a` divides it, spread across
`ceil(h ÷ a)` turns. Attack 10 and attack 1 pay the same 10 energy to kill a
ten-health unit; attack 10 pays ten times over for a one-health one. What a
high attack buys is not efficiency, it is **speed**: attack `h` or more kills
in a single turn, where a low attack has to hold the square and strike again
turn after turn (**R5.11**), giving the enemy every turn between to reinforce
or retreat.

**Health is paid for three times.** Once at the till, in points. Again every
square the unit walks, because the fare is a quarter of its health. And a third
time by the enemy, who must spend about the whole of it in energy to kill it,
over as many turns as it takes to land `ceil(health ÷ attack)` strikes.
A unit's `energy ÷ fare` is simply the number of squares it has left in it, so
armour and mobility are the same dial turned in opposite directions.

Because the fare rounds up in steps of four, that dial has **notches rather
than a slope**. Health 1, 2, 3 and 4 all cost 1 a square, so health 4 is four
times the durability of health 1 for exactly the same mobility — the best value
in the game. Health 5 buys one more point of durability and doubles the running
cost for the rest of the game — the worst. The same edge sits between 8 and 9.

**Energy is paid for twice.** Once in points when the unit is bought, and then
again a point at a time as it walks and fights. A unit's energy is both a line
in its price and the number of actions left in it.

**Standing still is a move you can make.** It is the only way to get energy
back, it costs a turn, and it is refused to anything you gave an order to —
so a unit ordered into the board's edge, which pays nothing, still learns
nothing and gains nothing from the turn. Rest returns 1 whatever the unit is,
so a heavy unit takes a quarter of its health in quiet turns to buy back one
square — three, at health 9 or 10.

---
---

# Part 2 — What is still open

The seventeen questions this file first raised have all been answered. Fifteen
were defects and are fixed; their reproductions and what was done about each are
in `SPEC_COVERAGE.md`, along with two more found afterwards. The board position
the specs called a *cell* and the source called a *square* is a **square**
everywhere now.

Two questions were never defects. They are design choices. **Q1 has since been
decided** — energy regenerates for a unit that took no action, and a unit at
zero no longer keeps its owner in the game — and is kept here with what was
decided and why. **Q2 is still yours to make.**

---

## Q1. Energy never came back — answered

**What it was.** Energy was spent by moving and by attacking and never
replenished, so a unit that spent down below its attack value could never fight
again and one at 0 energy could do nothing at all, while still holding its
square. Two inert units could hold a square against each other for the rest of
the game, and every match was a race to the bottom of two pockets.

**What was decided.** Both halves of it, in the end:

- A unit that **takes no action** in a turn recovers **1 energy**, never past
  the energy its type was designed with (**R3.9**). Standing still is now a
  move you can make, resting is a decision with a cost — a turn — and an
  exhausted unit is a unit that needs to withdraw rather than one that is
  finished.
- Elimination is judged on whether a unit **could ever act again** (**R7.1**)
  rather than on what it holds this turn. Zero energy was a death sentence
  while energy never came back, and counting a unit out for it was right then;
  with rest it is a bad afternoon, and only a **wall** — designed with no
  energy — can never come back from it.

**What it opened.** Two things worth watching, now that a spent unit is not
finished: a defender that is never reached recovers for free, which makes a
holding position stronger than it was; and a **wall** (**R2.10**) is the one
kind of unit rest can never help, because its type was designed with no energy
at all.

---

## Q2. Identical units always destroy each other

**What happens.** A fight is one exchange a turn (**R5.2**), so two identical
units each take one strike and both survive — unless that single strike is
lethal, meaning attack is at least health. Below that they stand off, undecided,
and have to be ordered back into the square turn after turn; a kill takes
`ceil(health ÷ attack)` strikes, one a turn. Only when a single strike already
finishes the other do identical units annihilate together, and a three-way of
those dies to the last unit at once.

**Why it is still here.** It is deliberate, and it is what makes a contest's
outcome independent of which unit is listed first — the same property the
movement phase was rewritten to get (**R3.4**), and now an invariant of the game
(**R1.2**). Giving one side priority within the exchange would put an ordering
rule back into a place that no longer has one, so any initiative rule has to decide
the order from the units themselves rather than from where they stand in a
list.

**To decide.** Keep simultaneous resolution, or add an initiative statistic and
accept that a fight then depends on it rather than on the two units alone.

---

# Where each rule comes from

| Rules | Specified in | Verified against |
|---|---|---|
| R2.1–R2.2 | `board-model` | `domain/board.py` |
| R2.3, R2.3.1 | `game-server`, `point-budget` | `service/games.py`, `domain/player.py` |
| R2.4–R2.5 | `unit-types` | `domain/unit.py` |
| R2.6–R2.8 | `board-model`, `turn-commit`, `player-client` | `service/games.py`, `domain/board.py` |
| R2.9 | `point-budget` | `domain/budget.py`, `service/games.py`, `service/turn.py` |
| R2.10 | `unit-types` | `domain/unit.py` (`UnitType.__init__`, `exchangeAttacks`) |
| R3.1–R3.9 | `turn-commit`, `game-persistence`, `game-outcome` | `service/turn.py`, `domain/board.py` (`commit`, `_rest`) |
| R4.1–R4.10 | `unit-movement` | `domain/unit.py` (`planMove`), `domain/board.py` (`_move`) |
| R5.1–R5.11 | `combat-resolution` | `domain/unit.py` (`exchangeAttacks`, `resolveContest`, `resolveCollision`) |
| R6.1–R6.6 | `visibility` | `storage/serialise.py`, `service/game.py` |
| R7.1–R7.4 | `game-outcome` | `service/turn.py`, `cli/*.py` |
| R8 | `game-server`, `player-client`, `game-observer` | `cli/roles.py`, `cli/grammar.py` |
| R9 | nothing of its own — it restates the rules above | `tests/test_cost_table.py` |
