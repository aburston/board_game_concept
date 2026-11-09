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

**R1.1** Two or more players design their own unit types, write the program
each type's controller runs, deploy units of those types onto a shared grid,
and commit. Nobody orders anything after that: the game is played to its end
the moment the last setup is committed, every turn resolved one after another
by the controllers alone, and watched afterwards as a replay. Each turn every
unit's controller reads what its army knows and gives its order - a step one
square in one of four directions, or nothing. Units that end up on the same
square fight.

**R1.2 The invariant: no randomness in the resolution of the rules.** A turn is
a pure function of the board and the programs on it — the same programs on the
same board always resolve the same way, and so does the whole game. There is no dice, no hidden roll, and no
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
or in a draw when the last players are wiped out together - or stops
**undecided**, when its whole state repeats or the turn cap is reached. See
**R7**.

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
**1 to 1000**, and is **320** where the administrator does not name one - what
the default army (**R2.13**) costs, and 12 points over, so that a player can
change what they were given without first taking something back. Two
players of the same game may be given different budgets. A budget is fixed at
registration: nothing in play raises or lowers it. A player file may carry a
`budget:` key; one that does not gets the default.

**R2.4 Unit types.** Each player defines their own unit types with
`add type <name> <symbol> <attack> <health> <energy> [<compute>]`:

| Field | Rule |
|---|---|
| `name` | one or more characters |
| `symbol` | **exactly one** character — this is how the unit is drawn |
| `attack` | integer, **0 to 10** |
| `health` | integer, **1 to 10** |
| `energy` | integer, **0 to 100** |
| `compute` | integer, **0 to 10**; 0 when left out |

**Attack 0 is allowed, with or without energy.** With no energy it is a wall
(**R2.10**): health standing on a square. With energy and compute it is a
**scout** — it goes where it likes and strikes nothing, and it is priced
accordingly, since what it costs is `attack + health + energy + compute`
(**R2.9**) and its attack is nothing.

**Compute 0 is a type with no controller.** It runs no program, gives no
order and never moves of its own accord: it holds its square, and with an
attack and energy it strikes back at what walks into it - a **turret**
(**R2.10**). A type with compute above 0 has a controller and carries a
program (**R10**); setting a program on a type with compute 0 is refused,
saying it has no controller. **Energy 0 is refused with compute above it**:
a controller that could never pay for a tick of thinking.

**A type that thinks must hold at least its movement cost in energy.** A
move costs a unit a quarter of its health, rounded up (**R4.3**), and rest
gives back 1 a turn (**R3.9**), so a type with less energy than that could
never afford a single move at any point in its life. `add type Heavy H 3 6 1
1` is refused, because health 6 costs 2 to move; `add type Heavy H 3 6 2 1`
is a unit that can cross one square and must then stand still for two turns.
A scout is held to this like anything else that means to move. A type with
**no compute** is exempt: it will never be told to move, so what it holds is
what it strikes with, and a turret with one energy and a strike it can pay
for once is a design and not a mistake.

A type is rejected at the moment it is defined, not later during play. Types are
private to the player who defined them: an opponent learns of one only by
fighting a unit of it (**R6.2**).

**R2.5 What the four statistics mean.**
- **attack** — damage dealt per attack, *and* the energy that attack costs.
- **health** — total damage the unit absorbs before it is destroyed, *and* the
  energy each of its moves costs (**R4.3**). Health is paid for twice over:
  once at the till, and again every square the unit walks.
- **energy** — the single resource spent by moving, by attacking and by
  thinking. A unit that takes no action during a turn gets **1** of it back
  (**R3.9**).
- **compute** — how much the unit's controller may think in a turn, and how
  cheaply: a hundred ticks a turn per point, and a hundred ticks of thinking
  per point for one energy (**R10.3**). 0 is no controller at all.

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
different players may both have a unit called `scout`; a controller's order is
always its own unit's, a message is addressed among one army's units, and
what each player is told a turn did is decided by whose units it was about
(**R6.8**). The default army (**R2.13**) hands both players the same sixteen
names, so this is the ordinary case rather than an awkward one.

**R2.8 Setup ends at your commit, and so does everything you do.** Before
your `commit` you may define types, write their programs (**R10.1**), deploy
units and designate the flag. After it nothing of yours can be changed, and
nothing is asked of you again: there are no orders to give, because every
order from here on is a controller's. There is no way to reinforce later.

**R2.9 What a unit costs.** A type costs `attack + health + energy + compute`
points, so `add type Cross X 1 10 10` costs **21** and `add type Runner r 2 4
10 5` costs **21** too. The cheapest type a player can define costs 3 and the
dearest costs 130. Defining a type is free, and so is writing its program;
**deploying** is what spends. Each unit deployed costs its type's price again,
so four Crosses cost 84 of a 100-point budget and a fifth is refused.

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

**R2.10 Walls, turrets and scouts.** A type with **attack 0, energy 0 and
compute 0** is a wall: health standing on a square. It can never move, because
a move costs it a quarter of its health in energy (**R4.3**) and it holds
none, and never will (**R3.9** gives nothing back to a type designed with
none). It never attacks and never defends itself, so an exchange in which only
walls stand lands no attacks and nobody is destroyed (**R5.6**). It can be
destroyed like anything else, it blocks a square like anything else, and it
costs its health and nothing else — a wall of 10 health costs 10 points.

A type with **attack and energy above 0 and compute 0** is a **turret**: it
has no controller, so it never moves of its own accord, but it strikes back
at whatever walks into it, pays for the strike as any unit does, and rests
when it did nothing. A type with **attack 0, energy above it and compute
above 0** is a **scout**: it goes where its program sends it and lands
nothing when it arrives, taking whatever is dealt to it. A scout is a unit
like any other for every other rule - it blocks a square, it can carry the
flag (**R2.11**), and its energy means it can act.

Because a wall can never recover and never act, **it does not keep its owner in
the game** (**R7.1**). A turret and a scout do: each can act. An army of
nothing but walls has already lost; walls are ground you deny an opponent,
not an army.

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

| Name | Symbol | Attack | Health | Energy | Compute | Cost | Move fare | Program |
|---|---|---|---|---|---|---|---|---|
| Wall | `W` | 0 | 10 | 0 | 0 | 10 | 3 | none: no controller |
| Scout | `o` | 0 | 2 | 12 | 6 | 20 | 1 | explorer: walks at the nearest unknown square, round whatever is in the way, and gives up on one it cannot get nearer to |
| Pawn | `p` | 1 | 4 | 2 | 3 | 10 | 1 | vanguard: steps at the enemy's edge when it can afford to, never onto its own |
| Runner | `r` | 2 | 4 | 10 | 5 | 21 | 1 | hunter: walks at the enemy flag |
| Line | `L` | 3 | 6 | 12 | 4 | 25 | 2 | hunter |
| Lance | `!` | 8 | 2 | 10 | 4 | 24 | 1 | hunter |
| Keep | `K` | 1 | 10 | 5 | 8 | 24 | 3 | warden: sleeps, and strikes back when woken |
| Heavy | `H` | 5 | 10 | 15 | 4 | 34 | 3 | hunter |

Every type with compute carries a default program (**R10**), written to fit
its cap on every turn, so that a player who changes nothing fields an army
that plays. `show program <type>` lists any of them; `set program <type>
<file>` replaces one.

*The array.* In a **two-player** game each player also opens their seat with
sixteen of those units already deployed in their own half (**R2.6a**), and
their flag (**R2.11**) already on the left-hand Keep. It costs **308** of the
320-point budget. Both players get the same layout, mirrored, reading from
each player's own edge inwards:

```
    depth 1   p  p  L  H  H  L  p  p      the rank that goes, nearest the enemy
    depth 0   r  o  W  K  K  W  o  r      the rank that follows, the flag, and its walls
```

Both rows are **symmetric about the middle of the board**: what stands in one
column stands in its mirror. There is no reason for one flank to be stronger
than the other before anybody has moved. It is why there are two Keeps —
eight columns leave no middle square for one — and why the Lance is in the
catalogue but not in the opening array: four pairs a row is eight pairs, and
eight pairs of eight different types come to more than the budget.

The slow units stand in **front**, which is the opposite of chess, because a
unit's reach is its energy divided by its move fare (**R4.3**). A Heavy has
five moves in it and a strike costs five more, so one deployed at the back of
your half arrives at the fighting line with nothing left to fight with. A
Runner has ten moves. The units that can afford to travel are the ones that
can start further back.

Everything in the front rank has a program that leaves it - the Pawns
advance, the Lines and Heavies hunt - so nothing behind it is boxed in: the
Runners and Scouts follow the front rank out as the squares in front of
them clear. The Walls stand in the back rank beside the Keeps, where what a
wall cannot do, move, is what a flag's flanks want. The first array had the
Walls in front and the Lines behind, and the first programmed series showed
what that fielded: two Heavies walked out alone and twelve units stood
boxed in for the rest of the game.

*When you get no army.* The array is deployed only where it can stand as it
is: a game of exactly two players, on a board with room for it inside your own
half, and a budget that covers it. Otherwise you are given the catalogue and
you deploy by hand, as you always could.

*Changing it.* Take a unit back with `remove unit <name>` (**R2.12**) and its
points come back with it. In a browser, clicking a unit you have placed takes
it back; clicking an empty square in your own half deploys there. Give a type
a program of your own with `set program`. Take the whole array back and it
stays gone - it is not deployed again when you next open your seat.

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

**R3.1 One commit each, and the game plays itself.** Every player sets up and
then `commit`s once. The server holds the game open until **every registered
player** has committed a setup, and then resolves the whole game in one held
act: turn after turn, one straight after another, until it is decided
(**R7.2**), its whole state repeats (**R7.5**), nothing has happened for
fifty turns (**R7.7**) or the turn cap is reached (**R7.6**). Nobody is waited for after the last setup commit, nobody gains
from committing early or late, and nobody gains from the order the server
happens to read the setups in. A player whose setup is committed waits for
the others' and is then shown the result; a player who opens a resolved game
is shown the result and the record (**R3.10**).

**R3.2 Commits are final, and nothing before one is.** Once you commit you
cannot withdraw or amend anything: not a type, not a program, not a unit, not
the flag. Until then every setup decision is still yours to change (**R2.12**).

**R3.3 Orders are the controllers', and are used once.** Every order in the
game is given by a unit's controller during the think phase (**R10**). After a
turn resolves, every unit's direction is cleared and its state returns to
`NOP`. An order never carries over to the next turn. A unit given no order -
by a controller that chose not to, that halted, that is asleep, or that has
none - stays where it is.

**R3.4 A turn resolves in six phases, in this order:**
1. **Thinking** — every awake controller runs its type's program against the
   board *as the turn began*, as its army knew it (**R6.9**), and gives its
   unit's order, says what it says and sleeps if it chooses to. One snapshot
   per army, taken before any controller runs, so no controller sees
   another's order, message or move from the same turn.
2. **Deployment** — units waiting to be placed are put on the board (the
   setup turn only).
3. **Movement** — every unit's destination is worked out against the board *as
   the turn began*, and then every move is applied at once. Squares that end up
   holding more than one unit are collected.
4. **Combat** — every one of those squares is fought out to a conclusion.
5. **The map** — every army's map is updated from where its units stand and
   what they fought (**R6.9**), and every unit struck is woken (**R10.6**).
6. **Rest** — every unit that did none of the above gets a point of energy
   back (**R3.9**).

Because destinations are decided before any move is applied, the outcome of a
turn never depends on the order the units happen to be held in. Every phase
completes inside the same turn: a fight never carries over, and a message
said this turn is read next turn (**R10.7**).

**R3.5 Deployment happens on the setup turn.** A unit is placed on the board
when the setups are resolved, which is the first turn of the record. If its
square is taken by then, the deployment is refused, no unit is created, and
the turn resolves without it — the turn is not failed.

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
least that lets you deploy somewhere else.

Where deployments reach the server without a commit — a loaded player file, or
orders written by hand — **both** are still refused when the turn resolves, so
nothing that goes round the commit gains by it.

**R3.6 A refused order does not stop the turn.** The server refuses the single
order, records it against the owner of the unit it refused, and carries on.
Each player is written a list of what was refused, with the turn; the record
holds it turn by turn (**R3.10**). The list describes only the turn it belongs
to — it does not accumulate.

**R3.7 Every order that does nothing says so.** Anything of yours a turn would
not carry out is in the record for you: an order refused while it was being
applied, a move nobody could pay for, a move off the board, and a contest of
yours that ended undecided. Each names the unit, its square, and the reason -
and it is your own unit, never another player's of the same name (**R6.8**).

**R3.9 A unit that does nothing recovers 1 energy.** At the end of every turn,
each unit standing on the board that **was given no order**, **paid for
nothing** while the turn resolved and **whose meter did not charge it**
(**R10.3**) gets 1 energy back. It never recovers past the energy its type was
designed with, and a destroyed unit recovers nothing. A sleeping unit rests
every turn it sleeps: sleeping is doing nothing at all.

Both halves matter. A unit ordered to move has acted whether or not the move
happened — one ordered off the board pays nothing (**R4.6**) and still does not
rest, so walking into the edge is not a way to refuel. A unit that was attacked
and could not afford to strike back has done nothing at all, and does rest:
being hit is not an action. A unit whose controller thought and gave no order
rests unless the thinking itself cost it an energy that turn.

Rest happens after combat and before the game is judged (**R7**), so a unit
that spends its last energy acting is out before it can recover it, while one
that merely stood still is not.

**R3.10 Every turn is recorded.** Each resolved turn is written to the record
as it happens: the board, every unit, every flag, what the turn did, each
army's map and every controller's trace (**R10.8**), and whether it ended the
game. The record is what the replay reads (**R8**): any turn, forwards and
back, with the board drawn whole for everybody once the game is over, each
player's own traces and refusals, and the board as their own army knew it on
request.

**R3.8 Turns are numbered.** Resolved turns count from 1, and the number is
recorded with the board, with each player's view, with each turn of the
record and with each player's list of refused orders, so every record says
which turn it describes. The administrator's commit that ends setup is turn 0
of the record: the board as it was before anybody's army reached it.

---

## R4. Movement

**R4.1 One square, four directions.** A controller's `MOVE north|east|south|
west` (**R10.2**), or a register holding one of those four. No diagonals, no
multi-square moves, no standing order - a controller that wants to keep
walking says so again every turn.

| Direction | Effect |
|---|---|
| `north` | y − 1 |
| `south` | y + 1 |
| `east`  | x + 1 |
| `west`  | x − 1 |

**R4.2 A controller orders its own unit and nothing else, and only while it
stands on the board.** No program reaches another unit: it can tell one what
it saw (**R10.7**), and the other decides for itself.

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

**R4.5 If it cannot pay, it does not move.** The unit stays put and its energy
is unchanged. The order is still consumed and is not retried next turn, and the
refusal is in the record for you (**R3.7**).

**R4.6 The board edge stops it.** A unit ordered off the board stays at the
edge square, pays nothing, and its order is consumed. The refusal is in the
record for you, and the turn continues normally for everyone else.

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
one square fight each other (**R5.7**), and a square never ends a turn holding
two units (**R5.8a**).

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
| A survivor whose old square was taken during the turn | It **crashes into** whoever took it (**R5.8a**). |

**R5.8a A unit forced back crashes into whoever is behind it.** A unit that
falls back from an undecided contest often finds the square it came from
taken — the unit behind it stepped into it as it advanced. It does not stop
and it does not pass through: the two **crash**, and that is a fight on the
ordinary terms (**R5.2**) — one exchange, simultaneous, so a unit that is hit
hits back even when the blow that lands on it destroys it.

**Being forced back is free.** You pay for the move you ordered, and that one
payment covers being shoved out of it again: no fare to go back, and no
energy for the blow you land on your way. A unit still has to be able to
fight to land one — energy says whether a unit can strike at all (**R5.10**),
paid for or not — but being shoved does not drain it. This is only about the
turn you were pushed in: next turn everything resets, and walking back into
that square is an ordinary move at the ordinary fare (**R4.4**). Friendly fire is
total (**R5.7**), so a column walking into something it cannot shift piles
into itself and every unit in it pays for the pile-up.

Then:
- the unit falling back died → it holds nothing;
- the unit in the way died → the square is free and the one falling back
  takes it;
- both stood → the one in the way gives ground and falls back in its own
  turn, crashing into whoever is behind *it*, down the column.

So a unit can be damaged **twice in one turn**: once by what it moved into,
and again by being forced back into its own. What it cannot do is strike the
same unit twice — see **R5.2a**.

**R5.2a One strike per pair per turn.** A unit strikes each *other* unit at
most once a turn, however many exchanges the turn holds. Meeting the same
opponent in a contest and again in the pile-up behind it lands one blow, not
two, and a unit with nothing new to strike pays nothing.

**No square ever holds two units at the end of a turn.** That is what all of
this is for. Two units sharing a square could not fight their way apart and
could not step apart, and two of your own could end up stacked, which
**R4.10** says cannot happen.

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
  contest is undecided — the movers fall back and the unit pays again next turn
  if its controller presses it. Wearing a unit down takes as many turns as `ceil(health ÷ attack)`
  strikes, one strike a turn.
- **Identical units no longer destroy each other in a turn.** Two matched units
  each take one strike and both live, unless that one strike is lethal (attack
  at least the other's health). A mirror match is a stand-off that has to be
  fought out over turns, not a mutual annihilation in one. See **Q2**. Two
  controllers that press the same stand-off every turn with nothing changing
  between them is a state that repeats, and the game stops on it (**R7.5**).

---

## R6. What a player can see

**R6.1 You always see your own units,** wherever they are.

**R6.2 You see an enemy unit only by fighting it.** Visibility is recorded when
two units *contest a square*, whether by one walking into the other or in a
head-on collision (**R4.9**) - and whether or not either can land a blow: two
Scouts that collide have met, though neither strikes. Merely being next to an
enemy reveals nothing.
Contact also reveals that unit's **type**, with the attack, health and energy
its owner designed it with - and **nothing of how it thinks**: not its
compute, not its program, not what its controller did. A type's controller
is its owner's to read and the observer's, and nobody else's, in the record
as everywhere.

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

**R6.9 Your army shares one map, and fills it only by standing and
fighting.** Every army keeps a map of the board, one per player, read by every
controller of that army (**R10.4**) and written by nobody's program: a square
one of your units stands on at the end of a turn is known empty from then on,
stamped with the turn it was last stood on; an enemy one of your units fought
this turn is known where it stands at the end of the turn, with its type's
attack and health and the turn it was met; every other square is unknown.
Nothing reveals a square you have not walked or fought on - there is no free
detection, and a controller that wants to know what is there has to go and
find out. The map is updated once a turn, after combat (**R3.4**), so a
controller reads what its army knew at the end of the previous turn. Your
own units are always on it, and every flag (**R6.5**). A compute-0 unit's
fight feeds the map like any other's: it has no controller, but it is still
one of your units.

A remembered enemy stays where it was met until one of your units stands on
that square and finds it empty, or meets it again somewhere else: the map
does not forget, and it is not told when an enemy walks away. A unit that has
been destroyed reports nothing more.

**R6.10 The replay shows everyone the whole board.** Once a game is resolved,
every turn of its record is drawn for every seat with every unit on it, as the
observer has always been shown it: a game that is over has nothing left to
hide. What stays private in the record is what was private in play - each
seat's traces and programs are its own (**R6.2**) - and the board as *your
army knew it* is yours to switch to at any turn, which is what your
controllers were reading.

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
sixteen - and each is told only about their own, in the account of a turn and
in the list of what it refused alike.

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

**R7.5 A game whose state repeats stops, undecided.** After every turn the
whole state of the game is hashed: every unit's square, health, energy,
memory, meter, sleep and inbox, and every army's map. The controllers are
deterministic (**R1.2**), so a game whose whole state has been seen before
can never change again: it is stopped there and recorded as **undecided**,
saying so and naming the turn it first stood like this. Two armies that never
move, two stand-offs pressed turn after turn, a hunter patrolling a loop -
each ends this way rather than running for ever. The stamp a standing unit
puts on its own square every turn (**R6.9**) is left out of the hash, since
it would otherwise make a game that never changes look as though it did. A
program that reads the turn number and acts on a particular one can still
make a repeated state play on differently; the cap (**R7.6**) is the backstop
for that.

**R7.6 A game stops at the turn cap.** A game that is neither decided nor
repeating by turn **500** is stopped there and recorded as undecided, saying
the cap was reached. The cap exists so that a game always ends; it is not a
rule anybody plays to.

**R7.7 A game in which nothing happens stops, undecided.** When **fifty**
turns pass in which no unit changes square, no blow is landed, nothing is
destroyed and no flag falls, the game is stopped and recorded as undecided,
saying so and naming the last turn on which anything happened. Thinking,
sleeping and resting are not things happening. A sleeping unit's countdown
and a controller's meter keep a static board from ever repeating its whole
state (**R7.5**), and a board nobody has moved or struck on for fifty turns
is one nobody is watching. Whichever of the three stops - the repeat, the
quiet, the cap - comes first ends the game.

**R7.3 A game with fewer than two registered players is never decided.** There
is nobody to be the last player standing against; a solo game is a sandbox.

**R7.4 A decided game stops, and so does an undecided one.** No further turn
is resolved and nothing is accepted. The server reports the result - the
winner, the draw, or the undecided stop and why, with the turn - and exits;
a client opening the game reports it and shows the final turn of the record,
refusing every setup command; the observer reports it too. An eliminated
player is told they are out when the replay reaches the turn their flag fell.

---

## R8. What each role may type

Every role: `help`, `exit`, `show ...`, and the account commands.

| Command | Server | Client | Observer |
|---|:--:|:--:|:--:|
| `set board <x> <y>` | ✔ | | |
| `add player <number> [budget]` | ✔ | | |
| `remove player <number>` | ✔ | | |
| `load board <file>` | ✔ | | |
| `load player <file>` | ✔ | | |
| `add type <name> <symbol> <attack> <health> <energy> [<compute>]` | | ✔ | |
| `set program <type> <file>` | | ✔ | |
| `add unit <type> <name> <x> <y>` | | ✔ | |
| `remove unit <name>` | | ✔ | |
| `set flag <unit>` | | ✔ | |
| `commit` | ✔ | ✔ | |
| `reload` | | | ✔ |
| `show board` / `types` / `units` / `players` | ✔ | ✔ | ✔ |
| `show pending` / `events` / `designs` / `flags` | ✔ | ✔ | ✔ |
| `show placement` | ✔ | ✔ | ✔ |
| `show program <type>` | ✔ | ✔ | ✔ |
| `show turn <n> [known]` / `next` / `prev` | ✔ | ✔ | ✔ |

There is no `move` and no `hold`: a player gives no orders. `set program`
reads the file where the client runs and lists the program back with the tick
cost of each line; `show program` lists any type the session may read - a
player's own, or anybody's for the server and the observer.

`show turn <n>` reads one turn of the record of a resolved game: the board
after it with every unit on it, what the turn did, what it would not do for
your units, and your controllers' traces - every seat's, for the server and
the observer. `next` and `prev` step from the turn last shown. `known` draws
the board as your own army knew it after that turn (**R6.9**). While any
player's setup is uncommitted these are refused, saying the game has not been
resolved and whose setups are to come. A client or observer opening a
resolved game shows the result and the final turn without being asked;
`bgcserver --replay` opens a resolved game at the prompt for the
administrator, where without the flag it reports the outcome and exits.

Every `show` answers with a table: a header naming its columns, then one row per
thing, lined up so a row can be read across and a column compared down.
`show board` draws the grid and, below it, a legend of what the symbols on it
stand for. A subject with nothing in it yet says so in a line rather than
printing an empty table.

Ending a `show` in `json` — `show units json`, `show turn 3 known json` —
writes the same content as a single JSON document instead, for a caller that
is not a person. It holds one key, named for the subject, and the fields a
player acts on; it is not the storage format, and nothing else is printed with
it. `json` is the only word a subject may be followed by: anything else is
reported as an invalid show command.

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

There are three currencies. **Points** are spent once, at deployment, out of
a budget fixed for the game (**R2.3.1**). **Energy** belongs to the unit and
is spent a little at a time, by moving, by attacking and by thinking, and by
nothing else. **Ticks** are what thinking is measured in: every instruction
costs a stated number, a turn's thinking is capped, and the meter turns ticks
into energy (**R10.3**).

The fare for a move is not a constant: it is **a quarter of the health the
unit's type was designed with, rounded up** (**R4.3**), read from the design and
never from the health play has worn down. Health is 1 to 10, so the fare is 1
for health 1 to 4, 2 for health 5 to 8, and 3 for health 9 or 10 — and never 0,
because it rounds up.

| What | What it costs | Rule |
|---|---|---|
| Defining a type | nothing — but a type that thinks must be designed holding at least its movement cost in energy, or it could never afford one move | **R2.4** |
| Writing a program | nothing; the program is paid for as it runs | **R10.1** |
| Deploying a unit | **points**: `attack + health + energy + compute`, its type's price | **R2.9** |
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
| A turn's thinking | **ticks**, one instruction at a time as the tariff in **R10.2** says; at most `100 × compute` in one turn, and a controller that reaches the cap gives no order | **R10.3** |
| — the meter | **1 energy for every `100 × compute` ticks** thought, carried across turns, charged the moment the meter fills; a unit with no energy to pay halts at the instruction that would fill it | **R10.3** |
| — a turn asleep | **nothing**: a sleeping controller does not run, and the unit rests | **R10.6** |
| A turn in which a unit did nothing | **gains 1 energy**, never above the energy its type was designed with | **R3.9** |
| — a turn in which it was given any order, or its meter charged it | **gains nothing**, even if the order cost it nothing | **R3.9** |

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

**Standing still is a move a controller can make.** It is the only way to
get energy back, it costs a turn, and it is refused to anything that was given
an order — so a unit its controller sent into the board's edge, which pays
nothing, still learns nothing and gains nothing from the turn. Rest returns 1
whatever the unit is, so a heavy unit takes a quarter of its health in quiet
turns to buy back one square — three, at health 9 or 10.

**Thinking is paid for in energy, slowly.** A controller that thinks `t`
ticks a turn on compute `c` pays one energy every `10c ÷ t` turns, and that
energy comes out of the same pocket as the moves and the strikes. The
cheapest thought is no thought: `SLEEP` for as long as you dare (**R10.6**),
and let the blow that wakes you be the signal. The dearest is a program that
reaches its cap every turn, which costs exactly one energy a turn and gives no
order for it.

---

## R10. The controller

**R10.1 A type carries a program, and every unit of it runs the program.**
A program is text in a small assembly language, set during setup with
`set program <type> <file>` (or written in a browser's armoury), fixed by the
commit, and refused at the moment it is set if any line is not an instruction
the set accepts - naming the line. A type with compute 0 has no controller
and carries no program (**R2.4**). The program is private to the player who
wrote it (**R6.2**).

**R10.2 The machine and its tariff.** Eight registers `r0` to `r7`, a memory
of words addressed by number and unbounded, and an inbox of messages. Every
instruction costs a fixed number of ticks whatever it returns, so a program's
bill is the same on every board:

| Instruction | Ticks | What it does |
|---|---|---|
| `SELF` | 1 | my square into `r0`, `r1`; my health, energy into `r2`, `r3`; my player into `r4` |
| `TURN` | 1 | the turn number into `r0` |
| `EXTENT` | 1 | the board's width and height into `r0`, `r1` |
| `FLAG mine\|enemy` | 2 | where that flag stands into `r0`, `r1`, or -1 if fallen or unknown |
| `CONTACT` | 2 | the enemy I fought last turn: its square into `r0`, `r1`, its attack and health into `r2`, `r3`; -1 if none |
| `MAP rX, rY` | 3 | what my army knows of that square into `r0`: 0 unknown, 1 empty, 2 friend, 3 enemy, 4 off the board; with the turn it was learned in `r1` and, for an enemy, its attack and health in `r2`, `r3` |
| `NEAREST friend\|enemy\|unknown` | 4 | the nearest such square into `r0`, `r1`, or -1 if none; ties by distance, then the row nearer your own edge of the board, then the lower `x` |
| `RECV` | 2 | the oldest message in my inbox into `r0`, `r1`, `r2`, or -1 if none |
| `FLUSH` | 1 | empty my inbox |
| `SET rX, n` | 1 | a constant into a register |
| `MOV rX, rY` | 1 | copy a register |
| `ADD`, `SUB rX, rY\|n` | 1 | arithmetic into `rX` |
| `ABS rX`, `SIGN rX` | 1 | magnitude, or -1, 0, 1 |
| `DIST rX, rY` | 1 | the distance from my square to `(rX, rY)` into `r0` |
| `LOAD rX, rY\|n`, `STORE rX, rY\|n` | 1 | my memory, by address |
| `JMP label` | 1 | go to a label |
| `JIF cond r..., label` | 1 | go if `zero`, `notzero`, `neg`, `pos` of one register, or `eq`, `lt` of two |
| `CALL label` | 1 | run the code at a label as a subroutine, and come back to the next line at its `RET`; calls nest sixteen deep |
| `RET` | 1 | back to the line after the last `CALL`; with no call to return to, stop thinking as `HALT` does |
| `HALT` | 0 | stop thinking; the order so far stands |
| `MOVE north\|east\|south\|west\|rX` | 1 | my order for the turn; a later `MOVE` replaces an earlier |
| `HOLD` | 1 | no order, said on purpose |
| `SAY to\|all, w, w, w` | 5 | three words to a friendly unit by name, or to every friend |
| `SLEEP n` | 1 | sleep for `n` turns, 1 to 100, and stop thinking |

Labels are a word and a colon at the start of a line; `;` begins a comment.
A jump or a call to a label that is not there is refused with the program.

A **subroutine** is code at a label that ends in `RET`: `CALL` it from
anywhere and the program carries on at the line after the call. It shares
the eight registers and the memory with whatever called it - there are no
arguments but the registers you leave for it - and the return stack it
uses lasts one run of the program: a `SLEEP` or a `HALT` inside a
subroutine ends the run, and the next begins at the top with nothing to
return to. A seventeenth nested `CALL` halts the controller where it
stands, as the cap does, so a program that recurses without end is stopped
where it recursed.

**R10.3 The meter: how thinking is paid for.** A controller may think at most
**`100 × compute` ticks in one turn**; one that reaches the cap halts where it
stands and gives **no order** that turn - whatever it had decided before the
cap was a thought it did not finish. Every tick thought goes onto the unit's
**meter**, which holds `100 × compute` ticks and charges the unit **one energy
each time it fills**, carrying the remainder into the next turn: a program of
60 ticks a turn on compute 2 pays its first energy on the fourth turn with 40
ticks carried. The first tariff gave ten ticks a point; two series showed no
controller ever stopped at its cap while every default program was written
to the last tick of it, so a point buys ten times the thinking now at the
same price and the same worst case of one energy a turn. A unit whose energy is 0 cannot pay, and its controller halts
at the instruction that would fill the meter, giving no order. The meter is
charged before the turn's moves and strikes, so a unit can think itself out
of the energy for the move it was about to order; the move is then refused
(**R4.5**) and reported.

**R10.4 What a controller sees.** Its own unit, the turn, the board's extent,
where the flags stand, the enemy it fought last turn, and its army's shared
map (**R6.9**) as it stood at the end of the previous turn. Nothing else: no
other unit's order, nothing of any square its army has not stood on or fought
on. Every controller of an army reads the same snapshot, taken before any of
them runs.

**R10.5 Memory and the inbox persist.** A unit's memory and inbox survive from
turn to turn for as long as the unit stands; nothing else of the machine
does - the registers start empty every turn. Memory is practically unbounded,
and nothing is charged for holding it. A destroyed unit's memory dies with
it.

**R10.6 Sleep.** `SLEEP n` puts the unit to sleep for `n` turns, 1 to 100:
its controller does not run and pays nothing, and the unit rests (**R3.9**)
every turn it sleeps. **A blow wakes it**: a unit struck in a contest fights
back in that same exchange as any unit does (**R5.2**), its sleep is cancelled
at the end of that turn, and its controller runs again next turn. Nothing
else wakes it - not a message, not an enemy walking past. There is no sleep
for ever: 100 is the most, and a unit that would rather not think pays a tick
every hundred turns to say so again.

**R10.7 The radio.** `SAY` sends three words to one friendly unit by name, or
to every friend with `all`, anywhere on the board; a message to a unit that is
not a friend is dropped and noted in the sender's trace. Messages said this
turn are delivered after every controller has run, in a settled order - the
turn, then the sender's name, then the order said - and are read next turn
with `RECV`, oldest first. A message does not wake a sleeper; it waits in the
inbox. The map (**R6.9**) is shared without any of this: the radio carries
what a program chooses to say, and the map carries what the army saw.

**R10.8 The trace.** Every turn, every controller that ran leaves a trace in
the record (**R3.10**): the ticks it thought, the energy the meter charged,
the order it gave, what it said and to whom, any message dropped, whether it
slept or was woken, and whether it halted and at which instruction. A trace
is its owner's to read and the observer's; nothing of it reaches another
player (**R6.2**).

**R10.9 Every default program fits its cap.** The programs the catalogue
ships with (**R2.13**) are written to run within their type's cap on every
turn of a stock-army game, and `tests/test_default_army.py` plays one to hold
them to it.

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
and their controllers have to send them back into the square turn after turn;
a kill takes `ceil(health ÷ attack)` strikes, one a turn. Only when a single strike already
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
| R2.13 | `default-army` | `domain/army.py`, `tests/test_default_army.py` |
| R3.1–R3.10 | `turn-commit`, `game-persistence`, `game-outcome` | `service/turn.py` (`resolve_game`, `turn_record`), `domain/board.py` (`commit`, `_think`, `_rest`) |
| R4.1–R4.10 | `unit-movement` | `domain/unit.py` (`planMove`), `domain/board.py` (`_move`) |
| R5.1–R5.11 | `combat-resolution` | `domain/unit.py` (`exchangeAttacks`, `resolveContest`, `resolveCollision`) |
| R6.1–R6.10 | `visibility`, `unit-program` | `storage/serialise.py`, `service/game.py`, `domain/army_map.py`, `service/replay.py` |
| R7.1–R7.6 | `game-outcome` | `service/turn.py`, `cli/*.py` |
| R8 | `game-server`, `player-client`, `game-observer` | `cli/roles.py`, `cli/grammar.py`, `cli/show.py` |
| R9 | nothing of its own — it restates the rules above | `tests/test_cost_table.py` |
| R10 | `unit-program` | `domain/program.py`, `domain/unit.py` (`think`), `domain/board.py` (`_think`), `tests/test_program_*.py`, `tests/test_meter.py`, `tests/test_sleep.py`, `tests/test_think_phase.py` |
