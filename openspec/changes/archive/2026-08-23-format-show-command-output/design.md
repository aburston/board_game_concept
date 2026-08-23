## Context

`show` is answered in three places. `bgcserver.py`, `bgcclient.py` and
`bgcobserver.py` each hold their own `if command.subject == ...` ladder, and
the three ladders have drifted: the server and the observer print pending
orders by interpolating a raw dict, the client has no `show pending` at all,
and all three print `serialise_units()` — the YAML the repository writes — as
though it were display. `render.py` holds the board grid and two list printers
that build strings by f-string concatenation, one line at a time, with no
notion of a column.

Two facts about the current code shape this design. The first is that a role's
`Game` already holds only what that role may see: a client is loaded from its
own published view, which is why `bgcclient` calls `print_board(board)` with no
player argument. Visibility is therefore not the renderer's job — it is already
done by the time a view is built, and one dispatch can serve all three roles.
The second is that `serialise_units()` is doing two jobs at once, and its
docstring says so: it is the on-disk format, the server-to-client transport,
and the text `show units` prints. Only the third job moves.

## Goals / Non-Goals

**Goals:**

- One table renderer, one view per subject, one `show` dispatch shared by the
  three roles.
- Tables that can be read across a row and compared down a column.
- A JSON form of every subject, named for what a caller acts on rather than for
  how the game is stored.
- The table and the JSON provably the same content, because they are rendered
  from the same structure.

**Non-Goals:**

- Changing the storage or transport format. `storage/serialise.py` is not
  touched, and the server keeps publishing exactly what it publishes now.
- Reformatting anything that is not a listing: prompts, `usage:` lines, parse
  errors, refusals, `commit complete`, the waiting and rejected-order reports,
  and the outcome line all stay as they are. They deserve the same pass; doing
  it here would double the change and the test churn. The read-back after
  `move` is in, because it is a listing of units and nothing else.
- Colour, cursor control, paging, terminal-width detection, or a table library.
- A non-interactive `--json` process flag. The roles are interactive sessions,
  so the format belongs on the command, not on the process.

## Decisions

### A view layer between the game and the output

New `cli/views.py` builds one plain-data structure per subject —
`board_view`, `types_view`, `units_view`, `players_view`, `pending_view` —
each a list of dicts (or, for the board, a dict of dimensions plus rows) using
lower-case, stable field names. Nothing in it prints, and nothing in it knows
whether the answer is going out as a table or as JSON.

The table renderer and `json.dumps` then both consume that structure. This is
the whole reason the spec can promise the two formats agree: they are not two
renderers reading the game, they are two renderers reading one value. The
alternative — a `to_json` next to each existing print function — is how the
current drift happened, and would let the JSON gain a field the table never
shows.

The views also do the translation from stored numbers to words: `state` 1
becomes `moving`, `direction` 2 becomes `east`, an eliminated player becomes
`eliminated`. That translation is content, not layout, so both formats get it.

The column is `DIRECTION`, not `FACING`. A unit does not face anywhere: the
value is the direction of the order it is holding, and `Board._move` clears it
as the turn resolves, whether the move happened or not. Calling it a facing
would describe a rule the game does not have.

### A minimal table renderer, not a dependency

`render.py` gains `table(headers, rows, numeric=())`: measure each column
against its header and every cell, pad, join with two spaces, right-align the
columns named as numeric, and `rstrip` each line. That is roughly twenty lines
and no new dependency. `tabulate` or `rich` would each pull a package into a
project whose only runtime dependency is PyYAML, and would style output this
project has deliberately kept plain ASCII — the board grid is drawn with `+-|`
and Unicode borders elsewhere would look imported.

Two spaces between columns rather than a `|` separator: the columns are the
structure, and vertical rules add noise a person does not read. Right-aligned
numbers because comparing `10` against `3` down a column is the thing these
tables exist for.

Empty results print one plain sentence (`no units yet`) rather than a bare
header row, which reads as a table that failed to load.

### `show board` keeps its grid and gains a legend

The grid is the one piece of current output that is already good, and it is
what the game looks like. What it lacks is any way to know what `X` is. A
legend table under it — `SYMBOL`, `PLAYER`, `TYPE`, one row per distinct symbol
actually drawn — answers that without touching the grid. Symbols are collected
from the same squares the grid drew, so a symbol a player may not see is not in
the legend either.

### `show <subject> [json]`, not a flag

`_parse_show` currently takes a subject and ignores everything after it. It
gains one optional word, `json`, and `commands.Show` gains a `format` field
defaulting to `'table'`. A flag spelling (`show units --json`) would be the
first `-`-prefixed token in a grammar that has none, and this grammar is a
sentence language, not an argv one.

Trailing words stop being ignored. `show units wibble` is an invalid show
command, because silently printing a table for a line the player did not type
is exactly the failure mode the `_verbs()` comment in `parser.py` describes
already. This is a behaviour change on a line nothing sensible relies on.

`grammar.py`'s `USAGES` grows the `json` form in each `show` usage string, so
`help` stays generated rather than maintained.

### One dispatch, in `cli/show.py`

A single `perform_show(data, command)` replaces the three ladders: it picks the
view for the subject, then prints it as a table or as JSON. It returns without
printing for a subject the role does not hold, which cannot happen — `roles.py`
already refuses those before dispatch. The roles keep only `if command.kind ==
'show': perform_show(data, command)`.

This is where the client quietly gains nothing and the server and observer lose
their copies of the pending-orders loop. `roles.py` still decides which
subjects each role may ask for, so the client still has no `show pending`.

### The read-back after `move` is the same listing

Ordering a unit prints that player's units back to them, so they can see the
order took. It is not a `show`, but it is the same listing, and printing it a
second way would leave the client with two formats for one thing — which is
the drift this change exists to remove. `show.py` exposes `show_units(data)`
for it: the same view, the same table, no second code path. The client is the
only role that has it, because it is the only role that gives orders.

### JSON shape

A single object keyed by subject, printed with `indent=2`:

```
{
  "units": [
    { "player": 1, "name": "alpha", "type": "tank", "symbol": "T",
      "attack": 3, "health": 5, "energy": 2,
      "x": 1, "y": 1, "state": "moving", "direction": "north" }
  ]
}
```

Keyed by subject rather than a bare array so that a document says what it is
and can later carry a sibling field (a turn number, say) without breaking a
reader. Indented rather than one line per record: the volumes here are a
handful of units, `jq` reads either, and a person debugging a client reads the
indented form. `x` and `y` are `null` for a unit that is not on the board,
where the table prints `-`; JSON has a way to say "no value" and should use it.

## Risks / Trade-offs

- **`show units` no longer prints the wire format, and something may be parsing
  it.** → Nothing in the repository does: the roles print it, and the server
  and clients exchange it through `storage/`, which is untouched. Anyone
  scripting against the old text has a better answer in `show units json`, and
  the proposal marks the change breaking.
- **Two formats can drift.** → They are rendered from one view, and the spec
  states that as a requirement. A test asserts the JSON and the table describe
  the same units for the same game.
- **Rejecting trailing words could break an existing habit.** → Only a line
  that was already meaningless. It is called out as breaking.
- **The CLI surface tests assert on the old strings** (`number: 1`,
  `player: 1, moves:`). → They are rewritten as part of this change, not left
  to be discovered; the tasks list them.
- **Wide unit rows on a narrow terminal will wrap.** → Eleven columns of short
  values fit in about 70 characters, and the alternative — width detection and
  column dropping — is a great deal of machinery for a board game. Left out
  deliberately.

## Open Questions

None. The scope was settled with the user: tables for the `show` commands, plus
a JSON option on the same commands. Plain ASCII with no colour, and the field
names above, are the assumptions taken; both are cheap to revisit.
