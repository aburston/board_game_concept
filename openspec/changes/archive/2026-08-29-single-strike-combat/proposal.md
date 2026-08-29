## Why

Combat was fought in rounds: every unit in a contested square struck every
turn, paid, and struck again, over and over, until one side was destroyed or
nobody left could pay. A single order therefore bought as many strikes as a
unit could afford. Playing a game showed what that means — a unit ordered one
square onto a wall struck it six times in the one turn, spending its whole
energy pool, because the fight ran until the unit was dry.

That is not the game intended. A unit should get **one** strike a turn: if it
can pay for it, it strikes, and then it stops. To press a fight you order the
unit back into it, turn after turn.

## What Changes

- **BREAKING**: a contest is now a single exchange, not a run of rounds. Every
  unit standing in the square strikes once, if it can pay its attack value,
  dealing that value to every other unit in the square at the same instant.
  Then the exchange is over, whoever is left standing.
- A fight no longer drains a unit's whole energy pool in one turn: a strike
  costs the attack value once, and that is the end of it until the next order.
- A contest is now usually **undecided** — both sides survive one exchange
  unless a single strike is lethal — so the movers fall back and the square is
  held by whoever already stood there. A square is cleared only when a strike
  actually destroys what is on it.
- **BREAKING**: two identical units no longer destroy each other. Each takes
  one strike and survives, unless that one strike is enough to kill. Mutual
  destruction, and the draw it can cause, now needs a strike that is lethal on
  its own.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `combat-resolution`: a contest is one simultaneous exchange rather than a
  run of rounds; the energy cost is paid once per turn rather than once per
  round; the "runs to a decision" and "attackers at the start of a round"
  requirements are replaced by a single-exchange rule.

## Impact

- `domain/unit.py`: `exchangeAttacks` loses its round loop and resolves one
  exchange. `resolveContest` and `resolveCollision` are unchanged — they
  already settle a square from whoever survives.
- `GAME_RULES.md` R5, and the two consequences it spells out (identical units,
  `ceil(health ÷ attack)`), both of which described the round model.
- Tests that asserted attrition over rounds — a sole survivor grinding down a
  crowd, a fixed round count, mutual annihilation of equals.
- No storage, contract, CLI or interface change. A running game keeps playing;
  its next turn is resolved under the new rule.
