# Spec Coverage

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for
spec-driven development. The specifications under `openspec/specs/` are the
source of truth for intended behaviour.

## Capabilities

| Capability | Covers |
|---|---|
| `unit-types` | Unit type definition, statistic ranges, state and direction constants |
| `board-model` | Board creation, unit placement, name uniqueness, lookup, rendering |
| `unit-movement` | Movement orders, simultaneous resolution, head-on collisions, edge handling, energy cost |
| `combat-resolution` | Contested squares, simultaneous attack rounds, damage, destruction is final |
| `turn-commit` | Turn resolution, determinism, the commit barrier, setup vs play |
| `visibility` | Own units always visible, enemies revealed by contact, per-player views as the only board a client is given |
| `game-persistence` | On-disk game layout, YAML formats, orders as transport |
| `player-client` | The `bgcclient` command surface |
| `game-server` | The `bgcserver` command surface and unattended turn cycle |
| `game-observer` | The `bgcobserver` read-only command surface |
| `game-outcome` | Player elimination, victory, draw, how a decided game stops, turn numbering |
| `cli-completion` | What completes at each point in a session, where the candidates come from, and the shell completion for launching a role |

Validate them with:

```
openspec validate --specs --strict
```

The invariant every capability is written under is stated in `turn-commit` —
**no randomness in the resolution of the rules**. `tests/test_determinism.py`
holds the game to it: hundreds of random boards resolved against every ordering
of their units, requiring one answer each, plus a check that nothing under
`domain/` reaches for a random number generator, a clock, or an identity that
varies between runs. Any proposed rule must be decidable from the board and the
orders alone.

The scenarios in `player-client`, `game-server` and `game-observer` are covered
one for one by `tests/test_cli_client_surface.py`,
`tests/test_cli_server_surface.py` and `tests/test_cli_observer_surface.py`,
which drive each role as a subprocess and assert what it prints. Run them with:

```
pytest tests/test_cli_client_surface.py tests/test_cli_server_surface.py tests/test_cli_observer_surface.py
```

They are what any change to the command surface is checked against.

## Known divergences

The specs describe intended behaviour. The following are places where the
implementation diverged from them. Each was reproduced against
`src/board_game_concept/` rather than inferred from reading, and all have since
been fixed, so the specs under `openspec/specs/` describe the behaviour the code
now has.

The first three were reported as issues. Numbers 4 to 10 were found by writing
the scenarios in `player-client`, `game-server` and `game-observer` out as tests
— one per scenario, driving each role as a subprocess — before the
`split-into-layers` change began moving anything; each names the scenario that
found it, and each has a test in `tests/test_cli_*_surface.py`. Number 11 was
found by playing a game.

Numbers 12 to 21 were found by reading the specs and the source back as one set
of rules, which is `GAME_RULES.md`, and reproducing each candidate against the
code rather than inferring it. All were fixed by the `fix-rules-defects` change.
Numbers 22 and 23 were found afterwards, one by playing a game through the
console scripts and one by questioning a rule.
The gap that let the worst of them survive 227 passing tests is that nothing
played a game on past a unit's death; `tests/test_full_game.py` does.

Every change named below is archived under `openspec/changes/archive/`.

### 1. Deploying onto an occupied square crashes (issue #1) — fixed

`UnitType.preCommit` and `UnitType.commit` raised an uncaught `AssertionError`
(`can't add <name> to board at (x,y)`) when a unit was deployed onto a square
that already held one, which propagated out of turn resolution and terminated
the session rather than being reported.

Addressed by the `fix-combat-stalemate-hang` change. Deploying a brand new unit
onto a square that is already taken — or already claimed by a unit waiting to be
placed, which is the case the issue reports — is illegal, and `Board.add` now
refuses it before any state is mutated. The client reports the refusal and stays
usable; the server logs it and resolves the turn without that order. Moving onto
an occupied square is unaffected: that is combat, and stays legal.

The refusal is reported back to the player who gave the order. The server
publishes what it refused as `players/<number>_rejected.yaml` and the client
prints it before taking the next command, naming the unit, its square and the
reason. The refused unit is dropped rather than held, so the player is free to
place it somewhere else on a later turn.

### 2. A contest neither unit can win hangs the server (issue #2) — fixed

`UnitType.commit` looped `while unit_count > 1`, and `unit_count` only decreased
when a unit was destroyed. Two units that contested a square but could not damage
each other — for example, both with energy below their attack value — never
reduced the count, and the loop never terminated. This was an unbounded spin,
not a slow turn: the server stopped making progress.

Reproduction: two units with energy below their attack value moved into the same
square.

Addressed by the `fix-combat-stalemate-hang` change: combat ends when a round
lands no attacks, and an undecided contest returns every unit that moved in to
the square it came from, so nobody wins the square. The same change fixes a
survivor-count bug that emptied a contested square out from under a unit that
was still standing, and stops units destroyed in an earlier round from attacking in
later ones.

### 3. A unit seen more than once crashed the client (issue #3) — fixed

`visibility` requires contact to reveal an enemy unit to the player who made it.
Contact was recorded once per attack rather than once per unit, so two units
that fought over several rounds recorded each other many times; the per-player
view then named the enemy once per contact, and the client died restoring a unit
it had already restored. The report the player saw was misleading twice over:
`Board.add`'s duplicate-name assertion interpolated `player.name` while `Player`
defines only `number`, so evaluating the message raised
`AttributeError: 'Player' object has no attribute 'name'` over the top of it.

Reproduction: two units with more health than one round of attacks can spend
moved into the same square, and a client for either player was then started.

Addressed by the `fix-duplicate-seen-units` change: contact is recorded once per
unit, a view names each unit it reveals once, restoring a unit the board already
holds puts the saved state back into it rather than failing, and the
duplicate-name error names the player by number.

### 4. A bare `add` or `load` kills the server — fixed

`game-server` requires the server to report that one argument is required when
`add player`, `load board` or `load player` is given the wrong number of them.
The arity guard on both verbs tested `len(tokens) == 2`, which is true of
`add player` but not of a bare `add`, so the shorter form fell past the guard to
`tokens[1]` and raised an uncaught `IndexError` that ended the session. The same
guard meant `add player` and `load player` — the case it was presumably written
for — reported a generic "invalid add command" instead of the arity message the
scenario asks for.

Reproduction: `add` or `load` alone at the server prompt.

Addressed by the `split-into-layers` change: the guard tests `len(tokens) < 2`,
so a bare verb is reported and each subcommand reaches its own arity check.

Found by: `game-server` — Registering Players / Wrong argument count, and
Loading Configuration From Files / Wrong argument count.

### 5. `show players` dies on a field nothing sets — fixed

`game-server` requires `show players` to list the registered players. It printed
an `email` field instead, which nothing anywhere sets: not `add player`, not
`load player`, not `GameData.load`. The only other trace of the idea was an empty
`add_player(name, email)` stub. With no players registered the loop body never
ran and the command appeared to work, so the `KeyError` surfaced only once the
game had a player in it — which is to say, always in a real game and never in a
smoke test.

Reproduction: `add player 1`, then `show players`.

Addressed by the `split-into-layers` change: the command prints the player
number, as the client and observer already did, and the stub is removed.

### 6. A board dimension below the minimum is reported as non-numeric — fixed

`game-server` requires a dimension below 2 to be reported as needing to be
greater than 1. `Board` asserts its own limits, and the constructor call sat
inside a `try` whose `except BaseException` reported "x and y must be a
numbers", so an out-of-range dimension was reported as though it were not a
number at all. The two checks written for the case, below that block, were
unreachable.

Reproduction: `set board 1 1`.

Addressed by the `split-into-layers` change: the dimensions are parsed, then
range checked, then used to construct the board, and the board is left to report
its own upper limit.

### 7. A unit a player has just deployed is invisible to them — fixed

`player-client` requires `show units` to list the player's own units and
`add unit` to place one. The client draws the view the server last published in
preference to its own board, so a unit deployed during setup appeared in neither
`show board` nor `show units` until a turn containing it had been resolved. Its
owner had no way to see what they had placed.

That precedence is deliberate and could not simply be reversed: the published
view is what limits a player's visibility, while the client holds the whole board
in memory, so drawing the local board instead would have shown every player every
enemy position.

Reproduction: deploy a unit in a game the server has already committed, then
`show board`.

Addressed by the `split-into-layers` change: a unit the player deploys is added
to the published view as well as to the local board. Only the player's own unit
is mirrored, so nothing the server has not already revealed becomes visible.

### 8. A game set up with `load player` cannot be reopened — fixed

`game-observer` requires the observer to open a game and display it. A player
file records its number as an integer, while `UnitType.dump` writes that number
back into `data/units.yaml` as a quoted string. A game set up through
`load player` was therefore keyed by integers but described by unit records
naming strings, and rebuilding the board looked each unit's player up under a key
that was not there, raising `KeyError`.

The observer died on startup. The server would have died the same way on its next
load, one commit barrier past the point any test had reached, so the crash lived
behind a passing suite.

Reproduction: `load player player_1.yaml`, `commit`, then start the observer
against that game.

Addressed by the `split-into-layers` change: player numbers are converted to
integers at every point they are read — the server prompt, a loaded player file,
a unit dump and the client's argument — and `Player` asserts that it holds one,
so the two ways of creating a game can no longer disagree about what a player is
called.

### 9. The packaged console scripts cannot start anything — fixed

`player-client`, `game-server` and `game-observer` each require their role to
start when invoked with its arguments. `pyproject.toml` declares
`bgcserver`, `bgcclient` and `bgcobserver` as the way to
invoke them, and every one of those raised
`TypeError: main() missing 1 required positional argument: 'argv'` and stopped.
Each role's `main` took `argv`, while the console script setuptools generates
calls it with nothing. Only launching the module files directly, as the tests
did, ever worked.

Reproduction: `pip install -e .`, then run `bgcserver`.

Addressed by the `split-into-layers` change: `main` defaults its argument to
`sys.argv`. Each role now has a test that calls `main()` with no arguments the
way the generated wrapper does.

### 10. Loading a game races the server deleting orders — fixed

`game-persistence` requires the server to remove each player's pending order
file once it has resolved a turn, and requires a client loading a game to
notice its own orders are still pending. Loading opened every file in the
players directory and then decided what it was by searching the repr of the
open file object for a substring of its name — so it opened files it only
meant to skip, including the order files the server deletes as it resolves.
A file listed a moment earlier could be gone by the time it was opened, and
the load died of `FileNotFoundError`.

The window is small, which is why this never showed while both sides waited
whole seconds for each other. Signalling closed those gaps and the race began
to fire.

Reproduction: run a client through a commit while the server resolves the turn,
repeatedly.

Addressed by the `split-into-layers` change: a file is classified by its name,
so the files that are only skipped are never opened, and the two that are read
tolerate having been removed since the directory was listed. Matching on the
name also made the match exact, where searching for a substring meant
`commit_1` matched `commit_11` and one player could be mistaken for another.

### 11. Starting a fight was the one move nobody paid for — fixed

`unit-movement` requires every resolved move to be charged `E // 100 + 1` and
refused when the unit cannot pay. `UnitType.preCommit` resolves a move down one
of three branches, chosen by what stands on the destination square. Two of them
charged for the move. The third — moving onto a square a unit is standing on,
which is how a fight starts — tested that the mover had the energy to attack
and then moved it for nothing.

A unit crossing open ground paid for every step; one that kept meeting
opponents advanced for free. Two units walking toward each other along a row
finished having paid different amounts for the same journey, decided by which
of them the turn resolved first.

Reproduction: put two units a few squares apart on one row, order them toward
each other for three turns, and compare their energy.

Addressed by the `charge-for-engaging` change: engaging is charged like any
other move, and is refused when the mover cannot pay, as well as when it has
too little energy to attack. `unit-movement` gains a scenario saying so, since
the requirement covering it was general enough to be read as not applying.

### 12. Destroyed units came back to life (`Q1`) — fixed

A unit is a shallow copy of its type, and a type's state is `INITIAL`, which
means *waiting to be deployed*. Restoring a saved game never set the state, so
every restored unit — destroyed ones included — came back in it. A client
republished all of its units as its orders each turn, so a destroyed unit went
out as a deployment order; the server refused it while the square it died on was
occupied, and the first turn that square was empty when orders were applied, it
created the unit again at full health and full energy.

`Board.add` made it worse: it appended the unit to `board.units` *before*
checking for a duplicate name, so even the refused case left a live unit behind
that the next turn deployed.

Reproduction: two units of equal statistics destroy each other; play one more
turn in which nothing moves onto that square. Both paths were confirmed — the
duplicate-name path via mutual destruction, and the free-square path via a
killer that walks away.

Addressed in three places, so no single path can resurrect a unit: restoring
sets the state explicitly and never to `INITIAL`; a player publishes orders only
for units in play; and the server refuses any order naming a unit it holds as
destroyed. `Board.add` now validates everything before it registers anything.

### 13. A player was told about a dead unit every turn, forever (`Q2`) — fixed

The same root cause. From the turn a unit died, its owner saw
`1 order(s) rejected last turn: x1 at (1,0): unit x1 already exists` at every
prompt, filling the only channel the server has for telling a player anything.

### 14. Turn resolution followed registration order (`Q3`) — fixed

`Board.commit` resolved each unit's move against a live board, so what a unit
found at its destination depended on whether the unit standing there had already
moved. `turn-commit` opens by promising that no player's orders are applied
before another's; registration order quietly broke it.

Reproduction: a brute-force search over 4000 random two- and three-unit
scenarios, comparing the final state across every permutation of registration
order, found 93 that diverged. The clearest: a unit follows another into the
square it is leaving, and whether it gets there depends on which was resolved
first.

Addressed by the `fix-rules-defects` change: movement is planned against the
board as the turn began and then applied all at once, in the board rather than
in each unit. `tests/test_rules_defects.py` asserts that the same orders on the
same board give the same result whatever order the units were registered in.

### 15. Two units ordered at each other passed straight through (`Q3`) — fixed

A consequence of the same design. The first unit "engaged" the second, and then
the second's own order was resolved and it walked out of the engagement into the
square the first had just left. They swapped squares, no damage was dealt, and —
because no attack was exchanged — neither player learned the other unit existed.

Addressed by the `fix-rules-defects` change: two units ordered into each other's
squares collide. Neither completes its move, both pay, and they fight where they
stand; the survivor completes the move.

`SPEC_COVERAGE.md` previously listed this under "Unspecified, and worth
deciding". It is specified now, in `unit-movement`.

### 16. The movement cost formula never varied (`Q4`) — fixed

`unit-movement` charged `energy // 100 + 1`. Energy is capped at 100, so the
first term is zero for every unit that has spent anything: the cost was always
1, except 2 from exactly 100. The formula read as though it scaled with
something and never did.

Addressed by the `fix-rules-defects` change: a move costs 1. The vestigial
`speed` statistic still described in a comment in `unit.py`, from a design that
no longer exists anywhere in the code, went with it.

### 17. Hidden information was hidden only when drawn (`Q5`) — fixed

The client loaded `data/units.yaml` — the record of every unit and its position
— and filtered it at the point of display. The unfiltered board was in memory
and the file was readable on disk. `show types` did not filter at all: it listed
every registered player's types, so a player who had met nobody could read the
enemy's whole army design.

Reproduction: set up a two-player game, resolve one turn, run `show types` as
player 1.

Addressed by the `fix-rules-defects` change: a player's session reads only its
own published view and its own player file, and holds one board rather than two.
An enemy type arrives with the unit that carried it into contact, so a type is
disclosed on the same terms as the unit. `visibility` gains a requirement saying
that hiding a unit when it is drawn is not sufficient.

### 18. A shared unit name made your own order unanswerable (`Q6`) — fixed

`board-model` guarantees that two players may reuse a unit name. `order_move`
looked a unit up by name across all players, took the first match, and only then
checked ownership, so the player whose unit was registered second was refused
with "can't move units belonging to other players". The server registers players
in ascending order, so it was always the higher-numbered player.

Reproduction: two players each deploy a unit called `scout`; player 2 orders
`move scout east`.

Addressed by the `fix-rules-defects` change: the lookup is scoped to the
ordering player, which `getUnitByName` already supported.

### 19. Failed moves were dropped in silence (`Q9`, `Q11`) — fixed

`game-persistence` builds a rejection channel so that a player "learns why an
order of theirs had no effect", and then the most common reasons never reached
it: a move nobody could pay for, a move off the board edge, and a contest that
ended undecided all left the unit where it was with no word to anyone. From the
player's side, "my unit didn't move" was indistinguishable from "the server
never got my order".

Addressed by the `fix-rules-defects` change: the movement phase emits an event
for each of them, and `turn.resolve` turns the ones that name a unit into
rejection entries. The engine still knows nothing about players' files.

### 20. A deployment tie was won by the lower player number (`Q12`) — fixed

`turn-commit` said only that the server "refuses one of the two". Which one was
decided by the order the server iterated players, which is player number
ascending: a fixed advantage to player 1, in a race neither player could see
they were in, since neither can see the other's units during setup.

Addressed by the `fix-rules-defects` change: both deployments are refused and
both players are told. It is the only rule that does not depend on reading
order.

### 21. Nothing counted turns, and no game could end (`Q7`, `Q16`) — fixed

`README.md`, `design.md` and `MODULE_DESCRIPTION.md` all described a win
condition. None existed: the server's turn cycle ran forever, and a player who
had been wiped out still held the commit barrier open for everyone else. The
three documents also disagreed about what a "functional" unit was —
`design.md` treated a unit out of energy as finished, which is the opposite of
what `combat-resolution` says.

Addressed by the `fix-rules-defects` change: a new `game-outcome` capability. A
player is eliminated when every unit they own is destroyed; an inert unit still
counts as alive, which settles the disagreement in `combat-resolution`'s favour.
The last player standing wins, simultaneous elimination is a draw, eliminated
players stop being waited for, and a decided game stops. Turns are numbered, and
the number is written with every record published for a turn.

### 22. A role read from a pipe spun forever at end of input — fixed

`read_command` read a line with `sys.stdin.readline()`, which returns the empty
string at end of input and a newline for a blank line. After stripping, the two
were the same string, so a role whose input had run dry was told there was
nothing to do, prompted again, and was told the same thing — forever, at
whatever speed the terminal could print.

It never showed to a person, who types `exit`. It made the roles unusable from a
script: piping a set of commands into a client ran them and then filled the pipe
with prompts.

Reproduction: `printf 'help\n' | bgcclient <game> 1`.

Addressed by the `end-session-on-eof` change: end of input comes back as the
`exit` command, which every role already ends on, so the fix reaches all three
without touching one of them. No capability had said what should happen at end
of input, so the loop was free to do the wrong thing; all three now have a
scenario saying it ends the session.

### 23. A crowd drained a unit at a rate decided by who was standing in it — fixed

`combat-resolution` charged a unit its attack value in energy "for each attack
it makes", and a unit in a contested square attacks every other unit in it. A
three-way fight therefore cost twice the energy per round, a four-way three
times, at a rate the unit did not choose and could not see coming.

The same per-opponent charge left a rule decided by list position: a unit that
could afford some but not all of its attacks struck whichever opponents came
first in the square. Three units with attack 2 and energy 2 — one strike each —
produced six different damage distributions across the six orderings of the
square. That is the same order-dependence number 14 removed from movement, one
layer down.

Reproduction: three units of attack 2, health 10 and energy 2 contesting one
square, resolved against every ordering of the square.

Addressed by the `charge-attack-once-per-round` change: a unit pays its attack
value once per round of a contest, however many it strikes, and a round is all
or nothing — so there is no half-paid round left to hand out and no tiebreak to
arbitrate. The same change writes the no-randomness invariant into `turn-commit`
and enforces it with `tests/test_determinism.py`, which found two narration
defects on its way past: whether a move read as "moves" or "engages" was decided
by which mover was placed first, and a head-on collision named its two units in
board order. Both are now decided from the plan rather than from loop order.

### 24. A session that ended before it committed lost everything it had done — fixed

Nothing a session did reached disk until it committed. `define_type` and
`deploy_unit` mutated the loaded game and wrote nothing; `order_move` set the
order on a unit held in memory. Only `commit` wrote, publishing the board as
orders and the player's types as their file. A client that died during setup —
or was closed, or lost its terminal — cost its owner every type they had
designed and every unit they had placed, with nothing on disk to show any of it
had happened. The same was true of the administrator's board and player list.

No requirement said the work had to survive, because no requirement had been
written about work that was not yet committed: `turn-commit` described
committing and `game-persistence` described what a commit publishes, and
between the two there was nothing.

Reproduction: define a type, deploy a unit, kill the client, and start it again
for the same game.

Addressed by the `draft-orders-and-explicit-commit` change: what a session has
done since it last committed is written down as it does it, as the commands
that did it, and put back when its owner reopens the game. A draft is private
to the session that made it, so making the work durable did not make an
opponent's deliberation visible; it belongs to one turn, so work left behind by
a session that ended mid-resolution is discarded rather than replayed into a
turn it was never meant for; and a command that can no longer be carried out is
dropped and reported rather than refusing to open the game.

The same change stopped inferring a commit from `players/<n>_units.yaml`
existing. That file meant "committed for this turn" only because the server
deletes it when it resolves one, so the fact lived in the absence of a
deletion. It is now recorded against a player and a turn, and spent when that
turn is resolved. Two things the inference had been doing unnoticed came out
with it: a turn that resolves without advancing the turn number — every turn in
which no unit reaches the board — would otherwise find the barrier still
satisfied by the commits that opened it and resolve for ever; and `load player`
relied on the server writing a loaded player's units as orders being what
committed them, since nobody types `commit` for a player who arrived in a file.

Held by `tests/test_server_client_integration.py::TestWorkSurvivesASession`,
`tests/test_draft_replay.py`, `tests/test_draft_recording.py`,
`tests/test_draft_serialisation.py`, `tests/test_draft_cli.py` and
`tests/test_commit_record.py`.

### 25. The observer was the administrator, and read its uncommitted setup — fixed

`bgcobserver.py` opened its session as player 0, and so did `bgcserver.py`.
`Game` decided what a session may see with `sees_everything = player_number ==
0`, so the two roles that differ in the most important way — one may change the
game and one may not — were the same identity to everything below the CLI. The
command line got away with it because they are different binaries with
different grammars: `cli/roles.py` simply did not give the observer the commands
that write, and nothing else enforced it.

Drafting made it visible. An observer opening a game read the administrator's
draft and held it as its own:

```
    administrator sets board 6 7, adds player 1, does NOT commit
    observer opens the same game
      → observer board size: (6, 7)
      → observer holds a draft of: ['set_board', 'add_player']
```

So the observer saw setup nobody had published, and a session meant to write
nothing was one recorded command away from writing into somebody else's draft.

Reproduction: size a board and register a player at the server prompt without
committing, then start an observer on the same game.

Addressed by the `give-the-observer-its-own-number` change: the observer is
1000, the administrator stays 0, and `service/identity.py` answers what each is
entitled to. The `== 0` tests turned out to be three different questions wearing
one test — may this session see everything, does it own units, must its number
be a registered player — which is why they became questions rather than a wider
comparison. `games.perform` now refuses a command from an identity that may not
change a game, so the refusal no longer depends on a role table the caller may
not go through.

Held by `tests/test_player_numbering.py` and `tests/test_identity_cli.py`.

### 26. Any number at all could be registered as a player — fixed

`add player` had no range check. `add player 0` registered the administrator as
a player of the game they were running, and `add player 1000` was accepted too,
which became a direct collision once 1000 meant the observer. `Player` asserted
only that a number was a non-negative integer, so `add player -1` raised an
`AssertionError` — and the roles catch `GameError`, so it escaped and **killed
the server**. That is the same class as number 4 above, which was fixed for a
bare `add` and left live for a negative number.

Reproduction: `add player -1` at the server prompt.

Addressed by the same change: `Player` states the range 1 to 999, as `Board`
already states its own limits, and the service turns the refusal into one a
caller can act on exactly as `set_board_size` does. The range is the domain's
because a player number arrives by three doors — the prompt, a loaded player
file, and a game read off disk — and a check at any one of them is a check the
others do not get. A game on disk holding a number that cannot be a player's is
reported as a game that cannot be read rather than opening into an unclear
state.

Held by `tests/test_player_numbering.py` and `tests/test_identity_cli.py`.

### 27. A player could stop waiting before the turn was published — fixed

A client waits for its turn by testing whether its own order file is still
there: `turn.wait_for_turn` blocks while `has_orders` is true, and
`Game.load` reads `unprocessed_moves` from the same file. Resolution deleted
that file near the start and published each player's view near the end, so a
client arriving inside the window never waited at all — it found no orders,
concluded the turn was over, and read a view belonging to the previous turn.

The wake at the end was always correct. What was wrong is that a client which
was not asleep for it had already been let go.

Caught in the act: a client that had just committed its only unit redrew an
empty board and then timed out waiting for that unit's symbol.

```
    bgcclient> commit complete
    waiting for turn to complete...
    bgcclient> +-+-+-+-+
               |#|#|#|#|          <- no units
               +-+-+-+-+
```

It showed twice in twenty-six runs of the suite. The ordering was unchanged
since the `split-into-layers` change, so neither drafting nor the observer's
numbering caused it; both only made it easier to see. This is the same file
being deleted while the turn is still being written that produced number 10
above.

Reproduction: commit a turn and read the committing player's view at the moment
their orders are removed.

Addressed by the `wake-a-player-when-the-turn-is-published` change: resolution
publishes everything the turn produced — the turn number, each player's file and
refusals, the record of every unit, and every player's view — and only then
removes the consumed orders. Nothing in that span reads an order file, because
orders are applied from what `load` put in memory, which is what makes the
deletion free to be last. The orders a `load player` file seeds for the *next*
turn are written after the removal rather than before it; a removal placed after
them erases them, and a game set up that way never gets its units onto the
board.

Held by `tests/test_turn_publication.py`, which asserts the order of the
operations one resolution performs rather than racing it, and fails in
milliseconds if the order is changed back.

**Not addressed**: a reader that holds no orders is gated by nothing, so the
administrator and the observer can still load while a file is midway through
being written. That is a different defect — the atomicity of one write rather
than the order of several — and its fix is writing to a temporary name and
renaming, not reordering.

## Unspecified, and worth deciding

Nothing, at present. The two entries that stood here — units passing through
each other, and the missing win condition — were both settled by the
`fix-rules-defects` change and are recorded above as numbers 15 and 21.

Two questions are still open and are design choices rather than defects: energy
never regenerating, and identical units always destroying each other. They are
set out in Part 2 of `GAME_RULES.md`.

## Left to a follow-up

The `format-show-command-output` change gave every `show` subject a table and a
`json` form, rendered from one view per subject in `cli/views.py`, and put the
client's read-back after `move` through the same renderer. Two pieces of
printing were deliberately left outside it, and are worth the same pass:

- **The server's turn log.** The unattended cycle prints the grid and the
  published YAML for each resolved turn. That is a log of what was published
  rather than an answer to a command, and it is what `game-persistence`
  describes, so it was left as it is.
- **Prompts, refusals and status lines.** `commit complete`, `waiting for turn
  to complete...`, the rejected-order list and the outcome line are unchanged.

The `add-cli-autocomplete` change left two things outside completion, both
deliberately:

- **Numbers and names being invented.** A coordinate, a statistic and the name
  of a type being defined complete to nothing, because only the person typing
  knows what they are. Completion offers what fits the grammar, not a guess.
- **A history file.** History lasts as long as the session. Keeping it between
  sessions would mean deciding where to write it and what one game may learn
  about another, which is a separate question from completing a line.

Completion also offers a name the game may still refuse: a unit with no energy
left completes, and moving it may then be rejected. Completion answers what
words fit where, and the service layer keeps deciding what may be done.

One word in `cli-output` is not reachable through the roles today: a unit's
state reads `waiting` only while it is on a board and not yet deployed, and
`deploy unit` resolves that at once for the session that gave it. The view
still says `waiting` for such a unit, which is what the server's board holds
mid-resolution and what a caller reading a board directly would see.

## Documented but not implemented

- **Web service.** The Flask/REST API and SQLite backend in `README.md` are
  aspirational; no such code exists. The prerequisite an API needs — somewhere
  to put an order that has not been committed yet — was built by the
  `draft-orders-and-explicit-commit` change, so a request handler no longer
  has to hold a session's state in memory to accept one.
- **Unit programming.** The concept the project is named for — programming a
  unit to play itself — does not exist. Units are ordered by hand each turn.

## Housekeeping

**A board position is a square.** The specs used to call it a *cell* and the
source a *square*, which meant the two documents describing one game did not
share a word for its most basic thing. The specs, the source, the tests and the
prose now all say **square**, `domain/cell.py` is `domain/square.py`, and the
grid inside `Board` holds `_squares`.

It was done as one scripted sweep rather than through a change. A delta would
have had to restate 42 of the 100 requirements verbatim but for one word, which
is more error-prone than the rename and worse to review. What makes it safe is
the check, not the ceremony: every spec file was diffed against its previous
version with `cell` and `square` both normalised away, and the two were
identical — 100 requirements and 318 scenarios, unchanged. The suite passes and
`openspec validate --specs --strict` is clean.

Two places deliberately still say *cell*, because renaming inside them would
falsify a record: `openspec/changes/archive/`, which is what those changes
actually said when they were made, and `TEST_RESULTS.md`, which is what a test
run actually printed on a particular machine on a particular day.


`src/board_game_concept/test_suite.py`, run as
`python -m board_game_concept.test_suite`, is a hand-rolled harness covering the same ground as
`tests/test_basic.py`. It was not updated when `fix-combat-stalemate-hang` made
combat multi-round attrition, so its attack test still expected one round of
damage and had been failing 9/10 since. The expectation has been corrected.
Whether the harness is worth keeping alongside pytest at all is open.
