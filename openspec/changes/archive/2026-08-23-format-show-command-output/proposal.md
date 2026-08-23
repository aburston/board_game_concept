## Why

The three roles answer `show` in three different accidental formats, none of
them designed. `show units` prints `serialise_units()` verbatim — the YAML the
server writes to disk — so a player reading their own board gets a wire format
with `type_attack`, `on_board` and an internal list index in it. `show types`
and `show players` print comma-separated `key: value` runs that have to be read
word by word to find the one number you wanted, and nothing lines up between
rows. `show pending` prints the repr of a Python dict straight out of the
loaded game file. There is no way to compare two units at a glance, and no way
for anything other than a person to consume the output either: the one format
that is machine-readable, `show units`, is machine-readable by accident and
carries fields that only mean something to storage.

## What Changes

- `show board`, `show types`, `show units`, `show players` and `show pending`
  print aligned, headed tables — one row per thing, columns of a fixed width,
  numbers right-aligned, headers naming each column. `show board` keeps its
  existing ASCII grid, gained a legend of the symbols on it.
- Every `show` subject gains a JSON form: `show <subject> json` prints the same
  content as a single JSON document on stdout, for a caller that is not a
  person. The tables and the JSON are rendered from one shared view of the
  game, so the two can never disagree about what is on the board.
- **BREAKING** `show units` no longer prints storage YAML. The table shows the
  fields a player acts on; the JSON form shows the same fields under stable
  names. `serialise_units()` is untouched and remains the on-disk and
  server-to-client format — display and transport simply stop being the same
  string.
- **BREAKING** `show <subject> <anything>` where the trailing word is not
  `json` is now reported as an invalid show command. Trailing words after a
  subject were silently ignored; a mistyped `show units jsno` must not quietly
  print a table instead.
- `help` lists the `json` form alongside each `show` subject, since it is
  generated from the same grammar table.
- **BREAKING** the client reads a player's units back to them after a `move`,
  to show the order took. That read-back was the same storage YAML and becomes
  the same table `show units` gives, written by the same code.

Not in scope: prompts, error and refusal messages, `usage:` lines, commit and
turn status lines, and the outcome report. They are worth the same treatment
and are left for a follow-up so this change stays one thing.

## Capabilities

### New Capabilities

- `cli-output`: how a role renders what a `show` command asked for — the table
  layout every role shares, the columns each subject has, the JSON form of each
  subject, and the rule that both are rendered from the same view of the game.

### Modified Capabilities

- `game-server`: server display commands gain the `json` form and are stated in
  terms of the shared table and JSON formats, rather than "listed".
- `player-client`: client display commands gain the `json` form, still limited
  to what the player has seen — the JSON form publishes no more than the table
  does.
- `game-observer`: observer display commands gain the `json` form.

## Impact

- **CLI**: `cli/render.py` gains a table renderer and per-subject views;
  `cli/grammar.py` and `cli/parser.py` gain the optional `json` word on `show`;
  `service/commands.py` — `Show` gains a `format` field; the `show` dispatch in
  `bgcserver.py`, `bgcclient.py` and `bgcobserver.py` is replaced by one call
  per subject into the shared renderer, removing the three copies of it; the
  client's read-back after `move` calls the same renderer.
- **Storage**: none. `storage/serialise.py` keeps the format it has, and the
  server keeps publishing it; only the roles stop printing it as display.
- **Tests**: `tests/test_parser.py` for the new `show` grammar, and the three
  CLI surface suites, which assert on `number: 1` and other old-format lines
  today.
- **Docs**: `GAME_RULES.md` R8 and `README.md`, which describe what each role
  accepts and shows.
