## Context

See proposal.md - Why.

Three facts about the current code shape this design.

**Defining a type spends nothing; deploying a unit spends.** `budget.remaining`
derives spend from the units standing on the board, not from the type
catalogue. So a catalogue of eight types can be given to every player for
nothing, and only the array has to be paid for.

**Setup decisions are recorded as commands and replayed.** A player session
holds a draft of the commands they have issued but not committed; opening the
seat again replays it. `add-a-take-back` made deployment take-backable by the
same route. This is what makes a *seeded* deployment editable rather than
magic: the seed can be the same commands a player would have typed.

**The board and the seat count are not settled until the setup is committed.**
`set_board_size` and `add_player` both refuse only once `getNewGame()` is
false. So at the moment a player is registered, we do not yet know the board
size or how many players there will be - and `placement-zones` gives a player
their half only in a two-player game.

## Goals / Non-Goals

**Goals:**

- A created game can be committed and played without a single setup decision.
- Everything seeded is reachable by ordinary commands, so it can be edited,
  taken back, and reasoned about with the rules already written.
- The seeding is backend-only: no client learns a new concept.

**Non-Goals:**

- More than one array. The structure should not forbid a second, but only one
  is defined here.
- Arrays for three or more players.
- Migration of existing games. See proposal.md - What Changes.
- Any change to how types, budgets, placement or combat work. The default army
  is made of the rules as they stand; if the catalogue needs a new rule to be
  good, the catalogue is wrong.

## Decisions

### The catalogue and the array are data in `domain/`, not code

The eight types and the fifteen placements are declared as plain data and run
through the ordinary `UnitType` constructor and the ordinary deployment path.
Nothing about them bypasses a check.

*Why*: a default that skipped validation could hold a type no player could
have designed, and the first sign of it would be a game that cannot be
committed. Running the catalogue through the constructor means a mistake in
the table is caught by the type's own assertions, in a test, at once.

*Alternative considered*: writing the units straight onto the board. Faster,
and wrong - it would produce units that are not charged, not placement
checked, and not take-backable.

### The catalogue is seeded at registration; the array is seeded at the seat

These two are separated because they depend on different things.

```
   add_player ──────────▶ catalogue        depends on nothing:
                                           a type is legal on any board,
                                           in any game, at any player count

   seat opened,  ───────▶ array            depends on the board size, the
   draft empty                             player count and the budget -
                                           none of which are settled when
                                           the player is registered
```

*Why*: seeding the array at registration would place units before the board
size is known, so an administrator resizing to 5x5 afterwards would leave
fifteen units off the board. Seeding at the seat means the array is placed
against the board as it then is, and `placement-zones` can be consulted.

*Alternative considered*: seeding both at the setup commit. Rejected - the
player would never see the army in the client before committing, which is the
whole point of it.

*Residual hole*: the administrator can still resize the board or add a third
player after a seat has been seeded. That is not a new hazard - a hand-placed
unit has the same exposure today - and the recovery already exists: the clash
refusal leaves the setup open and the player takes units back. Worth a note in
the rules, not a new mechanism.

### "Has made no setup decision" means the draft is empty

The seed fires when a player's draft holds no commands. Seeding then writes
its own commands into that draft, so it never fires twice, and a player who
takes the whole array back does not get it again.

*Why*: it needs no new state and no new record. The draft already answers
"has this player touched their setup".

*Alternative considered*: a `seeded` flag on the player record. A second thing
to keep in step with the draft, for an answer the draft already holds.

### The array is expressed as depth from the player's own edge

Depth 0 is the row at the player's edge, depth 1 the row in front. The lower
numbered player's depth 0 is row 0; the other's is the last row. Columns are
not mirrored, as in chess.

*Why*: it makes the array independent of board size and of which seat holds
which half, and it means one table describes both players.

### Slow units go in front and fast units behind

The array inverts chess. Pawns and Heavies stand at depth 1, Runners and the
Lance at depth 0.

*Why*: a unit's reach is its energy divided by its move fare. A Heavy has
5 moves in it and a strike costs 5 more, so a Heavy deployed at the back of a
half arrives at the fighting line unable to strike. A Runner has 10 moves and
a strike costs 2. The fast units are the ones that can afford to travel, so
they are the ones that can start further back.

*Consequence for the catalogue*: this is why the Heavy's energy is not raised
to make it mobile. Its immobility is what makes deployment depth a decision.

### The Wall and the Scout are in the array on purpose

Both are units the rules allow and nobody builds: attack 0 with no energy, and
attack 0 with energy. Putting one of each in the default array is the cheapest
way to teach that they exist.

*Note*: contact is recorded only inside the strike loop, and only for units
that can pay for a strike. So the Scout reveals itself by drawing fire and
learns nothing from a Wall or a spent unit. It is a probe, not a detector. A
unit that sees without fighting would be a new mechanic and is out of scope.

## Risks / Trade-offs

**Both players start with the identical army, so the first turns are
symmetric and the type-disclosure rule tells nobody anything.** → Accepted,
and turned around: the catalogue is common knowledge, so a *custom* design is
the thing that carries information when it is met. A player who wants secrecy
edits, which is what the feature is for.

**Redefining a catalogue type after deploying units of it leaves two different
things under one name** - the deployed units keep the design they were copied
from, while the catalogue entry holds the new one. → Correct behaviour (you
get the unit you paid for) but newly reachable, because a default catalogue
invites edits where an invented one did not. Out of scope here; worth a
follow-up that says plainly what happened.

**Fifteen units per side is a lot of orders per turn.** → Real, and the reason
a second, smaller array is worth having later. Not a reason to ship no array:
a player who wants fewer units takes some back, and gets the points.

**Raising the default budget to 250 and giving every created game a board
changes what a great many tests start from.** → The blast radius is the main
cost of this change. Tests that register a player and assert on an empty
catalogue, an unsized board, or a budget of 100 all move. Most take a named
budget or an explicit board already; the ones that do not are the work.

**A game created for three players still gets no array, and its players may
not notice why.** → The catalogue is still given, so the game is not worse off
than today. Saying so where the placement area is published would be a small
kindness; it is not required by the specs here.

## Migration Plan

None. Games created before this change keep the board, budget and empty
catalogue they were created with, and no code reads a default retrospectively.
Rollback is reverting the change; games created while it was in force keep
their board and their units, which remain ordinary boards and ordinary units.

## Open Questions

- Whether a second, smaller array (around eight units) should follow, and
  whether choosing between arrays belongs to the administrator at creation or
  to the player at the seat. Deferring this does not change the specs here:
  one array is defined, and the seam that seeds it takes a name.
