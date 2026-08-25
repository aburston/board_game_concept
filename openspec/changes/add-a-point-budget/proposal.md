## Why

Nothing today bounds an army. A player defines types during setup and then
deploys as many units of them as there are free squares: `add unit` is refused
for an unknown type, a square that is taken, or coordinates off the board, and
for nothing else. On a 10x10 board that is up to a hundred units, and the
player who types fastest during setup wins before a turn is resolved.

There is no cost to designing well either. `attack 10 health 10 energy 100` is
strictly better than `attack 1 health 1 energy 10` and costs the same, which
is to say nothing, so there is exactly one type worth defining and every game
converges on it. The three statistics are meant to be a trade — a fast cheap
scout against a slow expensive brawler — and a trade needs a currency.

A point budget is that currency. Each player is given a pool of points when
they are registered; a type costs the sum of its statistics; deploying a unit
of that type spends its cost out of the pool; and a deployment the pool cannot
pay for is refused. The interesting decision — many cheap units or few strong
ones — becomes the decision the setup phase is about.

## What Changes

- **A player is registered with a budget.** `add player <number> [budget]`
  takes an optional point budget; omitting it gives the default of 100. A
  player file read by `load player` may carry an optional `budget:` key,
  defaulting the same way. The budget is fixed at registration and never
  changes for the life of the game.

- **A unit type costs the sum of its statistics.** `attack + health + energy`,
  the type as designed — so `attack 1 health 10 energy 10` costs 21, and every
  unit deployed from that type costs 21 again. The cheapest type a player can
  define costs 3; the dearest costs 120, which no default budget can afford,
  and that is the trade the currency exists to make visible.

- **Deploying spends the budget.** `add unit` is refused when the type's cost
  is more than the player has left, naming the cost, what is left, and the
  budget it is left out of. An exact fit is allowed; a deployment that would
  take the pool below zero is not.

- **What is spent is derived, never counted.** A player's spend is the sum of
  the costs of every unit the board holds for them, destroyed ones included.
  There is no running total to drift out of step with the board, and there is
  no refund: a destroyed unit's points stay spent.

- **The server enforces it too.** The rule is applied again when a turn is
  resolved, so a deployment published by something other than the client — a
  hand-written order file, a loaded player file with more units than the
  budget buys — is refused through the existing rejection channel rather than
  quietly landing on the board. Where a player's deployments in one turn
  cannot all be afforded, they are charged in unit-name order, so which ones
  survive is decided by the rules and not by the order a file happened to list
  them in.

- **A budget is part of a saved game.** Each player's stored record carries
  the budget it was registered with, in both backends. A stored record without
  one is a game this version cannot read, and opening it fails the way any
  other malformed game data does, rather than being silently defaulted into a
  game that plays by different rules than it was set up under.

- **The numbers are visible.** `show players` gains `BUDGET`, `SPENT` and
  `LEFT`; `show types` gains `COST`. A session is shown the numbers for the
  players whose records it is entitled to read — its own, and every player's
  for the administrator and the observer — and `-` for the rest, so the
  columns leak nothing a player could not already read.

Not in this change: spending points on anything but deploying units, a budget
that changes during play, refunds for losses, reinforcement after setup, or
costing a type by anything other than the sum of its three statistics.

## Capabilities

### New Capabilities

- `point-budget`: what a budget is and when it is fixed, what a type costs,
  how a player's spend is derived from the board, when a deployment is
  refused, that both the client and the turn resolution enforce it, and the
  settled order deployments are charged in.

### Modified Capabilities

- `game-server`: `add player` takes an optional budget, and `load player`
  reads an optional `budget:` key; both are refused when the number is out of
  range or the budget is not a number in its permitted range.
- `game-persistence`: a player's stored record carries their budget, and a
  stored record without one is malformed game data.
- `player-client`: deploying is refused when the budget cannot pay for it, and
  the session continues.
- `cli-output`: `players` gains `BUDGET`, `SPENT` and `LEFT`; `types` gains
  `COST`; an unknown budget reads `-`.

## Impact

- **Domain**: `domain/player.py` — `Player` carries a budget, its permitted
  range, and its default; a budget the session may not know is `None`.
  `domain/unit.py` — `UnitType` gains the cost of its design.
  `domain/budget.py` — new; what a player has spent on a board, what they have
  left, and whether they can afford a type. One module both the client's
  refusal and the server's rejection ask.
- **Service**: `service/games.py` — `add_player` takes the budget through,
  `load_player` reads it from the file, `deploy_unit` refuses what cannot be
  paid for. `service/game.py` — `_load_players` builds a `Player` with the
  budget from their record, and fails the game when a record has none.
  `service/turn.py` — deployment orders are charged and refused at resolution.
  `service/commands.py` — `AddPlayer` gains a `budget` field with a default,
  so a draft written before this change still replays.
- **CLI**: `cli/grammar.py` — `add player` gains an optional argument, which
  needs a grammar word for an optional slot rather than an optional literal.
  `cli/parser.py` — `_parse_add_player` accepts one argument or two.
  `cli/complete.py` — nothing new to complete; a budget is a number the person
  chooses.
- **Storage**: `storage/repository.py` — `write_player` takes the budget.
  `storage/yaml_repository.py` — `budget:` beside `number:` and `types:`.
  `storage/sqlite_repository.py`, `storage/schema.sql` — `memberships` gains
  a budget column. Both refuse a record that has none.
- **HTTP**: `http/views.py` — `players_view` carries the three numbers;
  `types_view` carries the cost. The command endpoint needs no change: an
  `AddPlayer` record carries its budget through `as_record`.
- **Docs**: `GAME_RULES.md` — the budget, the cost of a type, and what
  deploying spends. `MODULE_DESCRIPTION.md` — `domain/budget.py`.
  `README.md` — the budget argument on `add player`.
