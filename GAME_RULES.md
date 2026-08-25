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

**R2.1 The board.** The administrator sizes the board once, with
`set board <size_x> <size_y>` or `load board <file>`. Each dimension must be an
**integer from 2 to 10** inclusive. A board that already exists cannot be
resized.

**R2.2 Coordinates.** A square is `(x, y)`. `x` runs left to right, `y` runs
**top to bottom**, both from 0. `(0, 0)` is the top-left square. `show board`
draws row `y=0` first, so north is up the screen.

**R2.3 Players.** The administrator registers each player before play starts,
with `add player <number> [budget]` or `load player <file>`. Player numbers are
integers. Player 0 is the administrator and holds no units. No player can be
added once the game has started.

**R2.3.1 The point budget.** Each player is registered with a **point budget**,
which is what bounds the army they may deploy (**R2.9**). It is an integer from
**1 to 1000**, and is **100** where the administrator does not name one. Two
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

**Attack 0 and energy 0 go together, and make a wall (R2.10).** A type with one
of them at zero and the other above it is refused.

**A type that is not a wall must hold at least its health in energy.** A move
costs a unit its health (**R4.3**) and rest gives back 1 a turn (**R3.9**), so a
type with less energy than health could never afford a single move at any point
in its life. `add type Heavy H 3 6 5` is refused; `add type Heavy H 3 6 6` is a
unit that can cross one square and must then stand still for six turns. A wall
is exempt: its 0 energy against a fare it can never pay is the whole point of
it (**R2.10**).

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

**R2.7 Unit names.** A name must be unique **within one player's** units. Two
different players may both have a unit called `scout`; an order is always
resolved against the units the ordering player owns.

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

**R2.10 Walls.** A type with **attack 0 and energy 0** is a wall: health
standing on a square. It can never be ordered to move, because a move costs it
its health in energy (**R4.3**) and it holds none, and never will (**R3.9**
gives nothing back to a type designed with none). It never attacks and never defends itself, so a round in
which only walls could act lands no attacks and the fight ends (**R5.6**). It
can be destroyed like anything else, it blocks a square like anything else, and
it costs its health and nothing else — a wall of 10 health costs 10 points.

Because a wall can never recover and never act, **it does not keep its owner in
the game** (**R7.1**). An army of nothing but walls has already lost; walls are
ground you deny an opponent, not an army.

---

## R3. The turn

**R3.1 Simultaneous commit.** Every player issues all their orders, then
`commit`. The server holds the turn open until **every player still in the
game** has committed, then applies all orders together. A player who has been
eliminated (**R7.1**) is not waited for. Nobody gains from committing early or
late, and nobody gains from the order the server happens to read the orders
in.

**R3.2 Commits are final.** Once you commit you cannot withdraw or amend. Your
client blocks and waits for the server rather than accepting further orders.

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
the turn is not failed. When **two** deployments contend for one square in the
same turn, **both** are refused, so neither player gains from being read
first.

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

**R4.3 Moving costs energy.** A move costs a unit **its maximum health** in
energy — the health its type was designed with — whatever the unit finds at its
destination. A 1-health scout crosses a square for 1; a 10-health brute pays 10
for the same square. The fare is read from the design and never from the health
play has worn down, so a unit that has been hurt pays exactly what it paid while
whole: damage is not weight shed.

Weight therefore costs mobility. A unit's energy divided by its health is the
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

A unit needs only the fare — its health in energy — to arrive. A unit that
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

**R5.2 Combat runs in rounds, and it is simultaneous.** In each round, the units
undestroyed **at the start of the round** each attack **every other** unit
undestroyed at the start of the round. A unit destroyed part-way through a round
still lands its own attack for that round. It takes no part in later rounds.

**R5.3 A round of fighting costs the attacker its attack value in energy —
once**, however many opponents it strikes in that round, and deals that same
value in damage to each of them. A round is all or nothing: a unit that cannot
pay strikes nobody, so no opponent is favoured by where it stands in the square.
Facing three opponents therefore costs no more energy than facing one, though
you take three attacks in return.

**R5.4 A unit that cannot pay for an attack simply does not make it.** It deals
no damage and spends nothing. It is not destroyed for it.

**R5.5 Damage comes off health. Health at zero or below destroys the unit.**
Health is the only thing that destroys a unit — running out of energy never
does.

**R5.6 Rounds repeat until either at most one unit is left undestroyed, or a
round lands no attacks at all** (because nobody left can pay). Combat always
terminates inside the turn.

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
- **Identical units always destroy each other.** All attacks in a round land
  regardless of damage taken in that round, so a mirror match is mutual
  annihilation, never a win.
  See **Q2** — this is a design choice, not an accident.
- **A fight is decided entirely by `ceil(health ÷ attack)`** — how many rounds
  each side needs to kill the other. Equal counts kill both. Energy only decides
  whether a unit can fight at all.

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

**R6.5 The observer sees everything** — all units, all squares, all types,
regardless of ownership or contact.

**R6.6 Your casualties stay on your list.** Your own destroyed units keep being
listed for you, marked destroyed and off the board, so you can see what you have
lost. They are never drawn on a square. An enemy unit you destroyed appears in
your view for that turn only, and drops out like any other contact (**R6.3**).

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

**R7.2 The last player standing wins.** The game is decided at the end of the
turn in which every other player becomes eliminated. If the last players lose
their last playable unit together, it is a **draw**.

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
| `load board <file>` | ✔ | | |
| `load player <file>` | ✔ | | |
| `add type <name> <symbol> <attack> <health> <energy>` | | ✔ | |
| `add unit <type> <name> <x> <y>` | | ✔ | |
| `move <unit> <north\|south\|east\|west>` | | ✔ | |
| `commit` | ✔ | ✔ | |
| `reload` | | | ✔ |
| `show board` / `types` / `units` / `players` | ✔ | ✔ | ✔ |
| `show pending` | ✔ | | ✔ |

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

| What | What it costs | Rule |
|---|---|---|
| Defining a type | nothing | **R2.4** |
| Deploying a unit | **points**: `attack + health + energy`, its type's price | **R2.9** |
| — a unit that is destroyed | nothing back; there are no refunds | **R2.9** |
| A move onto an empty square | **1 energy** | **R4.3** |
| A move onto an occupied square | **1 energy** — the same fare, whatever it walks into | **R4.4** |
| A head-on collision | **1 energy each**, though neither unit moves | **R4.9** |
| A move nobody can pay for | **nothing** — the unit stays put, and the order is consumed | **R4.5** |
| A move off the board | **nothing** — the unit stays at the edge, and the order is consumed | **R4.6** |
| A round of combat | **the attacker's `attack` value**, charged once for the round however many opponents it strikes in it | **R5.3** |
| — a round it cannot afford in full | **nothing** — it strikes nobody rather than striking some | **R5.4** |
| — a round fought by a wall | **nothing** — a wall never attacks | **R2.10** |
| Being attacked | **nothing in energy**; damage comes off health | **R5.5** |
| A turn in which a unit did nothing | **gains 1 energy**, never above the energy its type was designed with | **R3.9** |
| — a turn in which it was given any order | **gains nothing**, even if the order cost it nothing | **R3.9** |

Three things follow from the table that are worth stating out loud, because
they decide how the game is played and none of them is obvious from any single
row:

**A kill costs about the victim's health, whatever your attack is.** Killing a
unit of health `h` takes `ceil(h ÷ a)` rounds at `a` energy each, so the bill
is `a × ceil(h ÷ a)` — always at least `h`, and exactly `h` when `a` divides
it. Attack 10 and attack 1 pay the same 10 energy to kill a ten-health unit;
attack 10 pays ten times over for a one-health one. What a high attack buys is
not efficiency, it is **speed**: the same energy spent in one round rather than
ten, which is what decides a duel (**R5.11**).

**Energy is paid for twice.** Once in points when the unit is bought, and then
again a point at a time as it walks and fights. A unit's energy is both a line
in its price and the number of actions left in it.

**Standing still is a move you can make.** It is the only way to get energy
back, it costs a turn, and it is refused to anything you gave an order to —
so a unit ordered into the board's edge, which pays nothing, still learns
nothing and gains nothing from the turn.

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

**What happens.** Every attack in a round lands regardless of the damage its
attacker takes in that same round (**R5.2**), so two identical units always
destroy each other, and in a three-way fight between identical units all three
die. With attack and health both capped at 1–10, a fight is decided purely by
`ceil(health ÷ attack)` and a tie kills everyone.

**Why it is still here.** It is deliberate, and it is what makes a contest's
outcome independent of which unit is listed first — the same property the
movement phase was rewritten to get (**R3.4**), and now an invariant of the game
(**R1.2**). Giving one side priority within a round would put an ordering rule
back into a place that no longer has one, so any initiative rule has to decide
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
