## Why

`unit-movement` requires every resolved move to be charged for: the cost is
`E // 100 + 1` and the unit's energy is reduced by it. One kind of move was
never charged. Moving onto a square somebody is standing on — the move that
starts a fight — checked that the unit had the energy to attack and then moved
it for nothing.

So a unit crossing open ground paid for every step, while a unit that kept
meeting opponents advanced for free. Two units walking toward each other along
a row ended up having paid different amounts for the same journey, decided by
which of them the turn happened to resolve first.

This was found by playing a game rather than by reading, when the two sides of
an even exchange finished with different energy.

## What Changes

- Moving onto a square held by a standing unit SHALL be charged the movement
  cost, like every other move.
- The move SHALL be refused if the unit cannot pay it, as every other move is,
  in addition to the existing requirement that it have at least its attack
  value in energy to start a fight.
- `unit-movement` gains a scenario stating that engaging is charged for, since
  the requirement covering it was general enough to be read as not applying.

Combat itself is unchanged: an attack still costs the attacker its attack
value, each round, exactly as before. What changes is that arriving now costs
what arriving anywhere else costs.

A unit with just enough energy to attack but not to move no longer engages.
That is the existing rule about paying for a move, applied where it was not
being applied.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `unit-movement`: the requirement that a move is charged for is stated to
  cover moving onto an occupied square, and the move is refused when the unit
  cannot pay.

## Impact

- `src/board_game_concept/domain/unit.py`: `UnitType.preCommit`, the branch
  that engages a standing unit.
- `tests/test_turn_events.py`: that engaging costs a move, that it costs the
  same as crossing open ground, and that a unit which cannot pay does not
  engage.
- No change to the on-disk format, and none to any command surface.
