## 1. Price a type, and give a player a budget

- [x] 1.1 Add a `cost` property to `UnitType` in `domain/unit.py`, returning
      `type_attack + type_health + type_energy` (design.md — "The price of a
      type is a property of the type"). Read from the preserved design, never
      from the worn values. Verify: a type with attack 1, health 10, energy 10
      costs 21, and a unit of that type still costs 21 after losing health and
      spending energy.
- [x] 1.2 Give `Player` a budget in `domain/player.py`: `DEFAULT_BUDGET = 100`,
      `MIN_BUDGET = 1`, `MAX_BUDGET = 1000`, and `__init__(self, number,
      budget=DEFAULT_BUDGET)` asserting the range the way `number` is asserted
      (design.md — "`Player.budget` is `None` when the session may not know
      it"). `budget=None` is permitted and means unknown; every other
      non-integer, and any integer outside the range, fails construction.
- [x] 1.3 Add `domain/budget.py` with `spent(board, player)`,
      `remaining(board, player)` and `refusal(board, player, unit_type)`.
      `spent` sums `cost` over every unit the board holds for that player,
      consulting neither `destroyed` nor `on_board` — that absence is the
      no-refund rule. `remaining` raises when the player's budget is unknown.
      `refusal` returns the one sentence both enforcers report, or `None` when
      the type is affordable.
- [x] 1.4 Export what the layer above needs from `domain/__init__.py`, matching
      how `Board`, `Player` and `UnitType` are exported today.
- [x] 1.5 Add `tests/test_point_budget.py` covering the arithmetic against a
      board directly: cost of the cheapest (3) and dearest (120) definable
      types, spend as the sum over deployed units, a destroyed unit still
      counted, an exact fit affordable, one point over refused, and
      `remaining` raising for an unknown budget.

## 2. Storage carries the budget

- [x] 2.1 Change `write_player(number, types)` to
      `write_player(number, types, budget)` on `storage/repository.py`, and
      state in its docstring that a stored record must carry a budget
      (design.md — "A stored record must carry a budget").
- [x] 2.2 `storage/yaml_repository.py`: write `budget:` beside `number:` and
      `types:`. Verify the file is still the same shape otherwise, so the
      byte-diff tests move by one line and no more.
- [x] 2.3 `storage/schema.sql`: add `budget INTEGER NOT NULL` to
      `memberships`. `storage/sqlite_repository.py`: write it and read it
      back. Verify `sqlite3 :memory: < schema.sql` reports no error.
- [x] 2.4 Both backends: a stored record with no budget raises
      `UnreadableGame` naming the player, rather than returning a record
      without one. On SQLite that includes an existing database whose
      `memberships` table has no such column — `CREATE TABLE IF NOT EXISTS`
      will not add it, and the failed read becomes the same error.
- [x] 2.5 Update every caller of `write_player`: `turn.publish` and
      `turn.resolve` pass the player's budget from their `Player` object.
- [x] 2.6 Extend `tests/test_repository.py` and `tests/test_sqlite_repository.py`:
      a budget round-trips through `write_player`/`read_player` on each
      backend, and a record written without one is refused.

## 3. Registering a player with a budget

- [x] 3.1 `cli/grammar.py`: widen `Optional` to wrap either a fixed word or a
      `Slot`, render `[<budget>]` from it, and change the `add_player` usage to
      `('add', 'player', Slot('number', NUMBER), Optional(Slot('budget',
      NUMBER)))` (design.md — "The grammar needs an optional slot"). Verify
      `help` renders `add player <number> [<budget>]`.
- [x] 3.2 `cli/parser.py`: `_parse_add_player` accepts one argument or two,
      reading the second with `_integer` so a non-number is a parse error
      naming the budget. Wrong argument counts still report what is required.
- [x] 3.3 `cli/complete.py`: confirm an optional slot completes exactly as a
      required one does, and that a `NUMBER` slot offers nothing. Extend the
      grammar test that every usage in the table parses as the command it
      names, so it covers a usage holding an optional slot — with the optional
      present and absent.
- [x] 3.4 `service/commands.py`: `AddPlayer` gains `fields = ('number',
      'budget')` with the default filled in by `__init__`, the way `Show` does
      for `format` (design.md — "`AddPlayer` gains a defaulted field"). Verify
      a draft record holding only `number` still rebuilds.
- [x] 3.5 `service/games.py`: `add_player` builds the `Player` with the budget
      and turns the range assertion into a `GameError`, the way `_player`
      already does for the number. `load_player` reads an optional `budget:`
      key, defaulting to `DEFAULT_BUDGET`, through the same construction.
- [x] 3.6 `service/game.py`: `_load_players` builds each `Player` with the
      budget from their record where it read one, and with `None` where it did
      not — a player another player is not entitled to read. A record it did
      read that carries no budget ends the session as `UnreadableGame`.
- [x] 3.7 Add tests: registering with and without a budget, a budget out of
      range refused with no player registered, a non-numeric budget refused at
      the parser, a loaded player file with and without `budget:`, and a
      budget that survives being saved and opened again.

## 4. Refusing a deployment the budget cannot pay for

- [x] 4.1 `service/games.py`: `deploy_unit` asks `budget.refusal` before it
      places anything, and raises the returned sentence as a `GameError`
      (design.md — "`domain/budget.py` is the one place the rule lives").
      Nothing is placed and nothing is recorded in the draft when it refuses,
      since `perform` records only what was carried out.
- [x] 4.2 Verify the check runs against the client's own board, and that a
      unit deployed a moment ago is already counted — the client's board is
      its own view, which holds all of that player's own units.
- [x] 4.3 Add tests to `tests/test_point_budget.py`: a deployment that fits, a
      deployment that spends exactly what is left, a deployment one point over
      refused with the game unchanged, and every further deployment refused
      once nothing is left.
- [x] 4.4 Add a CLI test that the refusal is reported at the prompt naming the
      cost, what is left, and the budget, and that the session takes further
      commands afterwards.

## 5. The turn resolution enforces it too

- [x] 5.1 `service/turn.py`: in `_apply_orders`, charge each deployment
      through `budget.refusal` against the authoritative board before
      `board.add`, and refuse it through the existing `reject(p_number, unit,
      reason)` channel (design.md — "Both enforcers, one rule"). Both the
      `INITIAL` and the `NOP` deployment paths go through it; a `MOVING` order
      is not a deployment and is not charged.
- [x] 5.2 Sort each player's deployment orders by unit name before charging
      them (design.md — "Deployments are charged in unit-name order"). A
      player's non-deployment orders keep the order they are applied in today.
- [x] 5.3 Add a determinism test to `tests/test_determinism.py`'s neighbourhood:
      the same over-budget deployments published in two different orders
      resolve to the same units placed and the same ones rejected.
- [x] 5.4 Add tests: an over-budget deployment rejected with the reason
      reaching that player's rejections, that player's other orders still
      carried out, and a loaded player file with more units than the budget
      buys deploying the ones that fit and rejecting the rest.
- [x] 5.5 Confirm `tests/test_turn_publication.py`'s list of what is published
      still holds — `write_player` gained an argument, not a call site.

## 6. What the surfaces show

- [x] 6.1 `http/views.py`: `types_view` carries each type's cost;
      `players_view` carries `budget`, `spent` and `left`, each `None` where
      the session is not entitled to know it.
- [x] 6.2 `cli/render.py` (or wherever the tables are drawn): `types` gains a
      `COST` column, `players` gains `BUDGET`, `SPENT` and `LEFT`, and a
      `None` draws as `-`. Column order is what `cli-output` names.
- [x] 6.3 Verify the JSON form writes an unknown number as `null` and not as
      `-`, and that the table and the JSON come from the one view.
- [x] 6.4 Update `tests/test_cli_tables.py` and `tests/test_cli_views.py` for
      the new columns, and add a test that a player sees `-` for another
      player's three columns while the administrator and the observer see
      numbers.
- [x] 6.5 Confirm the HTTP tier needs no route change: an `AddPlayer` record
      carries its budget through `as_record`, and `show players` over HTTP is
      the same `players_view`. Extend `tests/test_http_api.py` to post an
      `add_player` command with a budget and read it back.

## 7. The whole flow

- [x] 7.1 Add an end-to-end test: register two players with different budgets,
      define types of different costs, deploy until one player's budget is
      spent, confirm the next deployment is refused, commit, and confirm the
      board holds exactly the units that were paid for.
- [x] 7.2 Run the full suite against both backends —
      `BOARD_GAME_BACKEND=yaml pytest` and `BOARD_GAME_BACKEND=sqlite pytest` —
      and fix what this change broke.
- [x] 7.3 Run `pylint` over `src/` and fix what this change introduced.

## 8. Documentation

- [x] 8.1 `GAME_RULES.md`: a player is registered with a point budget, a type
      costs the sum of its statistics, deploying spends that cost, there are no
      refunds, and a deployment the budget cannot pay for is refused.
- [x] 8.2 `MODULE_DESCRIPTION.md`: `domain/budget.py` in the `domain/` layer,
      and `Player` carrying a budget.
- [x] 8.3 `README.md`: the optional budget argument on `add player`, and the
      `budget:` key a player file may carry.
- [x] 8.4 Note in `README.md` that a game saved before this change cannot be
      opened, and that the fix is to start a new one.
- [x] 8.5 Record any divergence this change leaves behind in `SPEC_COVERAGE.md`.
