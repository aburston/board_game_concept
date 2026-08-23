# The Rules of the Game

Every rule the game actually plays by, stated in one place, in the order you
meet them. Then a list of the places where the rules are unclear, weak, or
where two documents say different things.

Sources: `openspec/specs/` is the stated intent, `src/board_game_concept/` is
what runs. Where they disagree, this file says so and says which is which.
Every claim in Part 2 was reproduced against the code, not inferred from
reading it; the reproduction is given with each one.

Rules are numbered `R1.1`, questions `Q1`, so you can point at one.

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

**R1.3** The game does not end. See **Q7**.

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
private to the player who defined them — in intent; see **Q5**.

**R2.5 What the three statistics mean.**
- **attack** — damage dealt per attack, *and* the energy that attack costs.
- **health** — total damage the unit absorbs before it is destroyed.
- **energy** — the single resource spent by both moving and attacking. It is
  never replenished (**Q8**).

**R2.6 Deploying units.** `add unit <type> <name> <x> <y>` creates one unit as a
copy of one of your own types, at those coordinates. It is refused if:
- there is no board yet, or
- the coordinates are off the board, or
- you already have a unit of that name (**R2.7**), or
- the square is already held, or already claimed by another unit waiting to be
  deployed this turn.

**R2.7 Unit names.** A name must be unique **within one player's** units. Two
different players may both have a unit called `scout` — but see **Q6**, which is
a live defect in exactly that case.

**R2.8 Setup ends at your first commit.** Before your first `commit` you may
define types and deploy units but may not order movement. After it you may order
movement but may no longer define types or deploy units. There is no way to
reinforce later.

---

## R3. The turn

**R3.1 Simultaneous commit.** Every player issues all their orders, then
`commit`. The server holds the turn open until **every** registered player has
committed, then applies all orders together. Nobody gains from committing early
or late — in intent; see **Q3**.

**R3.2 Commits are final.** Once you commit you cannot withdraw or amend. Your
client blocks and waits for the server rather than accepting further orders.

**R3.3 Orders are used once.** After a turn resolves, every unit's direction is
cleared and its state returns to `NOP`. An order never carries over to the next
turn. A unit given no order stays where it is.

**R3.4 A turn resolves in two phases, in this order:**
1. **Movement** — every unit on the board resolves its order, and squares that
   end up holding more than one unit are collected.
2. **Combat** — every one of those squares is fought out to a conclusion.

Both phases complete inside the same turn. A fight never carries over.

**R3.5 Deployment happens on the turn you commit it.** A newly created unit is
placed on the board when the turn resolves. If its square is taken by then, the
deployment is refused, no unit is created, and the turn resolves without it —
the turn is not failed.

**R3.6 A refused order does not stop the turn.** The server refuses the single
order, records it against that player, and carries on. Each player is written a
list of what was refused; the client prints it before taking the next command.
The list describes only the turn just resolved — it does not accumulate.

**R3.7 Not every failure is reported.** Only orders the server refuses while
*applying* them produce a rejection. Orders that fail during the *movement
phase* — a move nobody can pay for, a move off the board, an engagement refused
for lack of energy — are dropped in silence. See **Q11**.

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

**R4.3 Moving costs energy.** The cost is `energy // 100 + 1`. Since energy is
capped at 100, that is **1 for any unit with 0–99 energy, and 2 for a unit
sitting at exactly 100**. In practice every move costs 1, except the very first
move of a unit built with full 100 energy. See **Q4** — this formula almost
certainly does not do what it looks like it does.

**R4.4 You pay for every move that happens, including starting a fight.**
Stepping onto an occupied square is charged exactly like stepping onto an empty
one.

**R4.5 If you cannot pay, you do not move.** The unit stays put and its energy
is unchanged. The order is still consumed and is not retried next turn.

**R4.6 The board edge stops you.** A unit ordered off the board stays at the
edge square, pays nothing, and its order is consumed. The turn continues
normally for everyone else.

**R4.7 What is on the destination square decides what happens:**

| Destination | Result |
|---|---|
| Empty | The unit moves in and its old square becomes empty. |
| Already claimed by other units moving in this turn | The unit joins them; the square will be contested. |
| Held by a standing unit | **Engagement.** The unit moves in and both are put in contention — but only if it has energy **≥ its attack value** *and* can pay the move cost. If either is short, nothing happens at all: no move, no fight, no message. |

**R4.8 There is no way to stack with your own units.** Two of your own units on
one square fight each other (**R5.7**).

---

## R5. Combat

**R5.1 A fight is any square holding more than one unit** at the end of the
movement phase, however they got there — one attacking a standing unit, or
several stepping into the same empty square at once.

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

**R5.9 Destroyed units leave the board.** They are marked off-board, taken out
of their square without disturbing anyone still standing in it, and take no part
in later movement or combat. They remain in the saved game and are still listed
by `show units` with `destroyed: True`. See **Q1** — in practice they come back.

**R5.10 Inert units.** A unit whose energy has fallen below its attack value can
no longer attack or defend itself, but is *not* removed. It stays on the board,
holds its square, blocks movement, forces anyone entering to attack, and can
only be cleared by being killed. See **Q8**.

**R5.11 Two consequences worth spelling out, because they decide how the game
plays:**
- **Identical units always destroy each other.** All attacks in a round land
  regardless of damage taken in that round, so a mirror match is mutual
  annihilation, never a win.
- **A fight is decided entirely by `ceil(health ÷ attack)`** — how many rounds
  each side needs to kill the other. Equal counts kill both. Energy only decides
  whether a unit can fight at all.

---

## R6. What a player can see

**R6.1 You always see your own units,** wherever they are.

**R6.2 You see an enemy unit only by fighting it.** Visibility is recorded when
two units actually *exchange attacks* in a contested square. Merely being next
to an enemy, or passing through it (**Q3**), reveals nothing.

**R6.3 Visibility is not cumulative.** Every unit's record of what it has seen is
wiped at the start of each turn's resolution. An enemy you fought last turn and
did not touch this turn drops off your board and out of `show units`.

**R6.4 The server publishes each player a view** of what they may see, and the
client draws that in preference to the full board. A unit fought by several of
your units is still named once.

**R6.5 The observer sees everything** — all units, all squares, all types,
regardless of ownership or contact.

**R6.6 Hidden information is presentation, not enforcement.** The client process
loads the whole board, and `show types` lists every player's types. See **Q5**.

---

## R7. Ending the game

**R7.1 There is no end.** No win, no loss, no draw, no turn limit, no
game-over. The server's turn cycle runs until somebody stops it. `README.md`,
`design.md` and `MODULE_DESCRIPTION.md` all describe a win condition; no
capability specifies one and no code implements one. See **Q7**.

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

# Part 2 — What is not clear, and what is wrong

Ordered roughly by how much it matters. Each item says what happens today, how
to see it, why it matters, and what you might decide instead.

---

## Q1. Destroyed units come back to life

**What happens.** Every turn, a client republishes *all* of its units as its
order file — including its dead ones. A dead unit is republished in the `INITIAL`
state, which the server reads as *deploy this unit*. While the square it died on
is still occupied, the server refuses the order. The first turn that square is
empty when orders are applied, the server **creates the unit again, at full
health and full energy**, standing where it died.

Worse, `Board.add` appends the unit to the board's unit list *before* it checks
for a duplicate name, so even the "refused" case can leave a live unit behind.

**Reproduction.** Two units of equal stats destroy each other on a square. Play
one more turn in which nothing moves onto that square. The dead unit is on the
board again, at full strength. Confirmed both ways: via mutual destruction (the
duplicate-name path) and via a killer that walks away and leaves the square
empty (the free-square path).

**Why it matters.** It contradicts `combat-resolution` — *Destroyed Units Leave
The Board*: "it is not considered for movement or combat in later turns" — and
`game-persistence` — *A refused order leaves no unit behind*. It makes the game
unplayable past the first casualty. All 227 tests pass, because nothing plays a
game on past a unit's death.

**To decide.** Presumably "dead is permanently dead". If so the fix has three
parts: a client should not republish destroyed units as orders; a destroyed unit
should never be restored in the `INITIAL` state; and `Board.add` should validate
completely before it registers anything.

---

## Q2. A player is told about a rejected order every turn, forever

**What happens.** The same root cause as **Q1**. From the turn a unit dies
onward, its owner sees, at every single prompt:

```
1 order(s) rejected last turn:
  - x1 at (1,0): unit x1 already exists for player 1
```

**Why it matters.** The rejection channel is the only way the server can tell a
player anything. Filling it with a message about a unit that died ten turns ago
makes it useless for the messages that matter.

---

## Q3. Turn resolution is not actually simultaneous

**What happens.** `Board.commit` resolves each unit's move in the order the
units were **registered**, not all at once. What a unit finds on its destination
square depends on whether the unit standing there has already had its own move
resolved. Two things follow:

- **Order decides whether a fight happens at all.** Two friendly units in a row,
  both ordered east: if the rear one was registered first, it "engages" the
  front one, and then the front one's own order resolves and it walks out of the
  engagement. If the front one was registered first, both simply move and
  nothing is contested. Same orders, same board, different events.

- **Units pass straight through each other.** Two enemies one square apart,
  ordered toward each other, swap squares. An `engaged` event is logged, no
  damage is dealt, and — because no attack was exchanged — **neither player
  learns the other unit exists** (**R6.2**). Two armies can walk through each
  other and end up behind each other's lines having seen nothing.

**Reproduction.** Place two units adjacent, order them into each other, and read
the events. Then rebuild the same board registering them in the other order.

**Why it matters.** `turn-commit` opens with "No player's orders are applied
before another's, so no player gains an advantage from committing early or
late." That is the one property the whole commit barrier exists to guarantee,
and registration order quietly breaks it. `SPEC_COVERAGE.md` notes the
pass-through under "Unspecified, and worth deciding" but not the more general
ordering dependence.

**To decide.** Three rules are missing and each needs writing down:
1. May a unit leave a contest it is already in, during the same turn?
2. May two units trade squares?
3. What does a unit find on a square another unit is simultaneously leaving?

The usual fix is to make the movement phase two passes: compute every
destination first against the *starting* board, then apply them all, so nothing
depends on registration order. A swap then becomes a head-on collision rather
than a free pass.

---

## Q4. The movement cost formula never varies

**What happens.** Movement costs `energy // 100 + 1`. Energy is capped at 100
(**R2.4**), so the first term is 0 for every unit that has spent anything at
all. The cost is **always 1**, except for a unit sitting on exactly 100 energy,
whose first move costs 2.

**Why it matters.** Energy is therefore just a count of actions, and the formula
implies a design — cost scaling with something — that never happens. It is easy
to read the spec scenario ("the cost charged is `E // 100 + 1`") and believe
movement gets cheaper or dearer as a unit tires. It does not.

There is a related loose end: `unit.py` still carries a header comment
describing a `speed` statistic ("speed 10 is to move once per clock tick and 1
is to move once every 10th tick") that no longer exists anywhere in the code.

**To decide.** Either say plainly that a move costs 1 and drop the formula, or
decide what it was meant to scale with — distance travelled, a per-type speed
stat, or a cost that rises as a unit runs down — and give it a range that
actually bites.

---

## Q5. Hidden information is not hidden

**What happens.** Two leaks, both easy to see:

- **`show types` lists every player's types, before any contact.** Player 1,
  having met nobody, runs `show types` and gets back the name, symbol, attack,
  health and energy of every type player 2 has defined. `player-client` says
  "the player's own types are listed, together with any enemy types they have
  seen".

- **The client process holds the whole board.** It loads `data/units.yaml`,
  which is the authoritative record of every unit and its position, and *then*
  filters it for display. The unfiltered board is in memory, and the file is
  readable on disk by anyone running the client.

**Reproduction.** Set up a two-player game, resolve one turn, run `show types`
as player 1.

**Why it matters.** It decides what kind of game this is. `visibility` is
written as a real rule — enemies hidden until contact, and forgotten again when
you disengage. If a player can read the enemy's whole army design and every
position at any time, that rule is decoration.

**To decide.** Either visibility is enforced — the client is never sent data it
may not see, it loads only its own view, and enemy types arrive only through
contact — or it is an honour-system convenience and should be described as one.
Note that fixing this properly means the client can no longer hold a full
`Board`, which is also what makes **Q6** possible.

---

## Q6. You cannot move your own unit if an opponent used the name first

**What happens.** `order_move` looks a unit up by name across *all* players,
takes the first match, and only then checks ownership — so if the opponent's
unit of that name was registered first, your own order is refused with "can't
move units belonging to other players". Your unit becomes permanently
unorderable.

**Reproduction.** Player 2 deploys `scout`, then player 1 deploys `scout`.
Player 1 orders `move scout east`. Refused.

**Why it matters.** `board-model` explicitly guarantees that two players may
reuse the same unit name, and it is the natural thing for two players to do. The
lookup should be scoped to the ordering player — `getUnitByName` already takes a
player argument; this one call site does not pass it.

---

## Q7. There is no win condition, and the documents disagree about what it would be

**What happens.** Nothing ends the game. The server loops forever. Three
documents describe an ending and no two agree:

- `README.md`: "last player with a functional unit"
- `MODULE_DESCRIPTION.md`: the same
- `design.md`: "Win if other players pieces all run out of energy or has no more
  pieces left"

`design.md` treats a unit out of energy as finished. `combat-resolution` says
the opposite in as many words: running out of energy does not destroy a unit, it
makes it **inert**, and it keeps holding its square (**R5.10**).

**A second problem.** A player with no units left must still `commit` every
turn, or the barrier blocks everyone. A player who quits, or is wiped out,
freezes the game.

**To decide.**
1. What is a "functional" unit? Undestroyed? Or undestroyed *and* able to act —
   which is to say, is an inert unit alive?
2. What if the last two units destroy each other — draw, or does the game go on
   with nobody able to win?
3. Does a player drop out of the commit barrier when they have nothing left, or
   does the game end at that moment?
4. Is there a turn limit or a stalemate rule? Nothing anywhere counts turns
   (**Q16**), so today you could not write one.

---

## Q8. Inert is a trap with no way out

**What happens.** Energy is never replenished. A unit that spends down below its
attack value can still shuffle around at 1 energy a move, but can never attack
or defend again. At 0 energy it can do nothing at all — while still occupying a
square, still blocking, and still killable. Two inert units can hold a square
against each other indefinitely.

**Why it matters.** Late in a game, most units are inert obstacles and nothing
can resolve. Combined with **Q7**, the game reaches a state where nothing can
happen and it cannot end.

**To decide.** Energy regeneration (per turn, or for units that did not act)? A
way to remove or recover an exhausted unit? Or accept attrition to stalemate as
the design, and let the win condition handle it.

---

## Q9. An undecided fight costs both sides energy and changes nothing

**What happens.** Two units step onto the same square, neither can pay to
attack, both are pushed back to where they came from (**R5.8**) — each having
paid the move cost. Repeat the same order next turn and the same thing happens
again, until both are at zero.

**Why it matters.** It is a legitimate way to bleed an opponent dry, or an
accidental treadmill neither player can see they are on — the movement events
say a unit moved and fell back, but nothing says *why* the fight was undecided.

**To decide.** Is this a tactic or a bug? If a tactic, the players need to be
able to see it happening.

---

## Q10. Mirror matches are always mutual annihilation

**What happens.** Every attack in a round lands regardless of damage taken in
that round (**R5.2**), so two identical units always destroy each other. In a
three-way fight between identical units, all three die. With attack and health
both capped at 1–10, a fight is decided purely by `ceil(health ÷ attack)`, and a
tie kills everyone.

**Reproduction.** Three units of attack 2, health 10 stepping onto one square:
all three destroyed, each at −2 health.

**Why it matters.** It is a real design choice, and it is specified deliberately
— but it means there is no such thing as winning a fight against a copy of your
own design, and it makes contested squares mutually suicidal. Worth confirming
you want it before anything is built on top of it.

**To decide.** Keep simultaneous resolution, or give the defender or the
attacker priority within a round, or add an initiative statistic.

---

## Q11. Failed moves are silent

**What happens.** These all leave a unit exactly where it was, with no message
to anyone:
- A move the unit cannot pay for (**R4.5**).
- A move off the board edge (**R4.6**).
- An engagement refused because the mover has too little energy to attack, or
  too little to pay the move (**R4.7**).
- A deployment order in the `NOP` state whose square is occupied — this path
  does not even record a rejection.

**Why it matters.** `game-persistence` builds a whole rejection channel so a
player "learns why an order of theirs had no effect", and then the most common
reasons for an order having no effect never reach it. From the player's side,
"my unit didn't move" is indistinguishable from "the server never got my order".

**To decide.** Every order that does not do what it said should produce a
rejection entry. That means the movement phase needs to be able to record one,
which today it cannot — `Board.commit` returns events, and `turn.resolve`
collects rejections, and the two are not connected.

---

## Q12. Who wins a deployment collision is decided by player number

**What happens.** When two players deploy onto the same square on the same turn,
`turn-commit` says the server refuses one of them. Which one is decided by the
order the server iterates players — which is player number, ascending. Player 1
beats player 2, every time, forever.

**Why it matters.** Neither player can see the other's units during setup, so
the collision is genuinely blind — and the tiebreak is a fixed advantage to the
lowest-numbered player. `turn-commit`'s own scenario says only "the server
refuses one of the two", which reads as if it does not matter.

**To decide.** Say the rule out loud (lowest player number wins), or make it
alternate by turn, or refuse *both* deployments so neither player gains.

---

## Q13. Orientation and coordinates are never written down

**What happens.** North decreases `y`, the board is drawn with `y=0` on the top
row, so north is up the screen and `(0, 0)` is the top-left. This is true of the
code and nothing states it.

**Why it matters.** It is the first thing a player needs and the first thing an
API or web front-end will get wrong. Stated here as **R2.2**; it should be in
`board-model`.

---

## Q14. Destroyed units are still listed

**What happens.** `show units` lists destroyed units, with `destroyed: True` and
`on_board: False`. A player's view still names an enemy they destroyed this
turn. Neither is specified either way.

**To decide.** Are dead units part of what a player sees — a casualty list — or
should they drop out of `show units`? If they are a casualty list, it should say
so rather than reading as though the unit is still on the board.

---

## Q15. "cell" and "square" are the same thing

The specs say **cell**, the source says **square** (`Board.squareIsFree`, and
most comments). Already noted under Housekeeping in `SPEC_COVERAGE.md`. This
file uses "square", because that is what the events a player reads say.

---

## Q16. Nothing counts turns

There is no turn number anywhere — not in the saved game, not in a view, not in
a rejection. A rejection file says what was refused but not when. You cannot
write a turn limit, a draw-by-repetition rule, or a replay without one, and
"rejections describe only the last resolved turn" is enforced by overwriting the
file rather than by anything a reader can check.

---

## Q17. The README describes a game that is not this one

`README.md` leads with "Program each unit to play the game" and "Run the game
automatically resolving the winner". Neither exists: units are ordered by hand,
one command at a time, every turn, and nothing resolves a winner. The web
service, the REST API and the SQLite backend are also aspirational.

`MODULE_DESCRIPTION.md` is accurate about this and says so under "Not built
yet". `README.md` should not read as though the feature is there.

---

# Where each rule comes from

| Rules | Specified in | Verified against |
|---|---|---|
| R2.1–R2.2 | `board-model` | `domain/board.py` |
| R2.3 | `game-server` | `service/games.py` |
| R2.4–R2.5 | `unit-types` | `domain/unit.py` |
| R2.6–R2.8 | `board-model`, `turn-commit`, `player-client` | `service/games.py`, `domain/board.py` |
| R3.1–R3.7 | `turn-commit`, `game-persistence` | `service/turn.py`, `domain/board.py` |
| R4.1–R4.8 | `unit-movement` | `domain/unit.py` (`preCommit`) |
| R5.1–R5.11 | `combat-resolution` | `domain/unit.py` (`resolveContest`) |
| R6.1–R6.6 | `visibility` | `storage/serialise.py`, `service/game.py` |
| R7.1 | nothing | — |
| R8 | `game-server`, `player-client`, `game-observer` | `cli/roles.py`, `cli/grammar.py` |
