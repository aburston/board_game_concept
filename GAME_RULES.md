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
in one of four directions. Units that end up on the same square fight. There is
no dice, no randomness, and no hidden roll: given the same orders the same turn
always resolves the same way.

**R1.2** There are three kinds of session against one game: the **server**
(player 0, the administrator, and the commit authority), one **client** per
player, and any number of read-only **observers**.

**R1.3** The game ends when one player is the last with a unit left standing,
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
with `add player <number>` or `load player <file>`. Player numbers are integers.
Player 0 is the administrator and holds no units. No player can be added once
the game has started.

**R2.4 Unit types.** Each player defines their own unit types with
`add type <name> <symbol> <attack> <health> <energy>`:

| Field | Rule |
|---|---|
| `name` | one or more characters |
| `symbol` | **exactly one** character — this is how the unit is drawn |
| `attack` | integer, **1 to 10** |
| `health` | integer, **1 to 10** |
| `energy` | integer, **1 to 100** |

A type is rejected at the moment it is defined, not later during play. Types are
private to the player who defined them: an opponent learns of one only by
fighting a unit of it (**R6.2**).

**R2.5 What the three statistics mean.**
- **attack** — damage dealt per attack, *and* the energy that attack costs.
- **health** — total damage the unit absorbs before it is destroyed.
- **energy** — the single resource spent by both moving and attacking. It is
  never replenished (**Q1**).

**R2.6 Deploying units.** `add unit <type> <name> <x> <y>` creates one unit as a
copy of one of your own types, at those coordinates. It is refused if:
- there is no board yet, or
- the coordinates are off the board, or
- you already have a unit of that name (**R2.7**), or
- the square is already held, or already claimed by another unit waiting to be
  deployed this turn.

**R2.7 Unit names.** A name must be unique **within one player's** units. Two
different players may both have a unit called `scout`; an order is always
resolved against the units the ordering player owns.

**R2.8 Setup ends at your first commit.** Before your first `commit` you may
define types and deploy units but may not order movement. After it you may order
movement but may no longer define types or deploy units. There is no way to
reinforce later.

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

**R3.4 A turn resolves in three phases, in this order:**
1. **Deployment** — units waiting to be placed are put on the board.
2. **Movement** — every unit's destination is worked out against the board *as
   the turn began*, and then every move is applied at once. Squares that end up
   holding more than one unit are collected.
3. **Combat** — every one of those squares is fought out to a conclusion.

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

**R4.3 Moving costs energy.** A move costs **1 energy**, always, whatever the
unit finds at its destination. A unit's energy is therefore the number of
actions it has left in it.

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

A unit needs only the fare — 1 energy — to arrive. A unit that cannot then
afford to attack still arrives, and is inert in the fight it has walked into.

**R4.8 A unit that follows another out of its square arrives cleanly.** If the
unit standing in your destination is itself moving away this turn, you simply
take the square: nothing is contested.

**R4.9 Two units ordered into each other's squares collide.** They do not pass
through one another. Neither completes its move, both pay the fare, and they
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

**R5.3 Every attack costs the attacker its attack value in energy** and deals
that same value in damage. In an *N*-way fight a unit pays `attack × (N − 1)`
per round.

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
still keeps its owner in the game (**R7.1**). Energy is never replenished, so
this is permanent — see **Q1**.

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

**R7.1 You are eliminated when you have nothing left standing.** A player is out
once every unit they own has been destroyed. A unit that is on the board and not
destroyed keeps you in, whatever its energy: an inert unit is spent, not lost. A
player who deployed nothing is out on the first turn with units on the board.

**R7.2 The last player standing wins.** The game is decided at the end of the
turn in which every other player becomes eliminated. If the last players are
wiped out together, it is a **draw**.

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
| `add player <number>` | ✔ | | |
| `load board <file>` | ✔ | | |
| `load player <file>` | ✔ | | |
| `add type <name> <symbol> <attack> <health> <energy>` | | ✔ | |
| `add unit <type> <name> <x> <y>` | | ✔ | |
| `move <unit> <north\|south\|east\|west>` | | ✔ | |
| `commit` | ✔ | ✔ | |
| `reload` | | | ✔ |
| `show board` / `types` / `units` / `players` | ✔ | ✔ | ✔ |
| `show pending` | ✔ | | ✔ |

The observer is read-only because it is never given the commands that write.
A blank line does nothing; an unrecognised command is reported and the session
continues.

---
---

# Part 2 — What is still open

The seventeen questions this file first raised were answered by the
`fix-rules-defects` change, which is archived under `openspec/changes/`. Fourteen
of them were defects and are fixed; their reproductions and what was done about
each are in `SPEC_COVERAGE.md`. Three were never defects. They are design
choices, and they are still yours to make.

---

## Q1. Energy never comes back, so an exhausted unit is a permanent obstacle

**What happens.** Energy is spent by moving and by attacking and is never
replenished. A unit that spends down below its attack value can still shuffle
around at 1 energy a move but can never fight again; at 0 energy it can do
nothing at all — while still holding its square, still blocking, and still
killable (**R5.10**). Two inert units can hold a square against each other for
the rest of the game.

**Why it is still here.** Attrition to exhaustion is a coherent design, and it
now has somewhere to end: the win condition (**R7**) decides a game whose units
have run down, rather than leaving it running forever. Changing it changes how
every game plays.

**To decide.** Energy regeneration — for every unit each turn, or only for one
that took no action? A way to withdraw or scuttle a spent unit? Or leave it, and
let the win condition carry the endgame.

---

## Q2. Identical units always destroy each other

**What happens.** Every attack in a round lands regardless of the damage its
attacker takes in that same round (**R5.2**), so two identical units always
destroy each other, and in a three-way fight between identical units all three
die. With attack and health both capped at 1–10, a fight is decided purely by
`ceil(health ÷ attack)` and a tie kills everyone.

**Why it is still here.** It is deliberate, and it is what makes a contest's
outcome independent of which unit is listed first — the same property the
movement phase was rewritten to get (**R3.4**). Giving one side priority within
a round would put an ordering rule back into the one place that no longer has
one.

**To decide.** Keep simultaneous resolution, or add an initiative statistic and
accept that a fight then depends on it rather than on the two units alone.

---

## Q3. The specs say "cell" and the source says "square"

Both mean the same thing. The specs under `openspec/specs/` say **cell**; the
source, the events a player reads, and this file say **square**. Aligning them
is a mechanical rename across every capability with no behavioural content, and
carrying it alongside a change that rewrote half those requirements would have
made both harder to review. It is still its own job.

---

# Where each rule comes from

| Rules | Specified in | Verified against |
|---|---|---|
| R2.1–R2.2 | `board-model` | `domain/board.py` |
| R2.3 | `game-server` | `service/games.py` |
| R2.4–R2.5 | `unit-types` | `domain/unit.py` |
| R2.6–R2.8 | `board-model`, `turn-commit`, `player-client` | `service/games.py`, `domain/board.py` |
| R3.1–R3.8 | `turn-commit`, `game-persistence`, `game-outcome` | `service/turn.py`, `domain/board.py` (`commit`) |
| R4.1–R4.10 | `unit-movement` | `domain/unit.py` (`planMove`), `domain/board.py` (`_move`) |
| R5.1–R5.11 | `combat-resolution` | `domain/unit.py` (`exchangeAttacks`, `resolveContest`, `resolveCollision`) |
| R6.1–R6.6 | `visibility` | `storage/serialise.py`, `service/game.py` |
| R7.1–R7.4 | `game-outcome` | `service/turn.py`, `cli/*.py` |
| R8 | `game-server`, `player-client`, `game-observer` | `cli/roles.py`, `cli/grammar.py` |
