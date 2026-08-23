## 1. The grammar as words

- [x] 1.1 Add `Slot(display, kind)` and `Optional(word)` to `cli/grammar.py`,
  with the closed set of slot kinds: `UNIT`, `TYPE`, `PATH`, `DIRECTION`,
  `NUMBER`, `NAME`, `SYMBOL`
- [x] 1.2 Give `Usage` a `words` tuple — literals, slots and optionals in the
  order they are typed — and generate `usage` from it: a literal as itself, a
  slot as `<display>`, an optional as `[word]`
- [x] 1.3 Rewrite every entry of `USAGES` in the new form, keeping the direction
  slot's display built from `DIRECTIONS` so `move` still reads
  `move <unit> <north|east|south|west>`
- [x] 1.4 Add a test that the generated `usage` string of every entry equals the
  string it had before this change, so `help` output is provably unmoved
- [x] 1.5 Add a test that every `Usage` parses as its own `kind` when its slots
  are filled with plausible words, holding the table and the parser together

## 2. One predicate for what a role offers

- [x] 2.1 Add `Role.offers(usage)` to `cli/roles.py` — the kind is in `kinds`,
  and a `show` usage's subject is in `show_subjects`
- [x] 2.2 Have `cli/help.py` filter with `role.offers(usage)` instead of its own
  copy of the condition
- [x] 2.3 Add a test that for every role and every usage, `offers()` agrees with
  `allows()` on the command that usage describes

## 3. The completion function

- [x] 3.1 Add `cli/complete.py` with `candidates(line, role, source)`: split the
  text left of the cursor, decide whether a new word is starting or the last one
  is being completed, and return the words that could come next, sorted and
  deduplicated
- [x] 3.2 Walk the usages the role offers: literals must match what was typed,
  slots consume one word each, and the element past the typed words contributes
  the candidates
- [x] 3.3 Return the fixed words for literal and optional elements, and the four
  directions for a `DIRECTION` slot
- [x] 3.4 Return nothing for `NUMBER`, `NAME` and `SYMBOL` slots, and nothing
  once a usage is complete
- [x] 3.5 Complete a `PATH` slot with `glob`, relative to the working directory,
  appending `/` to directories so the next completion descends
- [x] 3.6 Filter every candidate by the prefix being completed and return an
  empty list when none match

## 4. Names from the game

- [x] 4.1 Add `GameNames(data, player_number)` to `cli/complete.py` with
  `units()` and `types()`, built from `views.units_view` and `views.types_view`
- [x] 4.2 Filter `units()` to that player's own units that are still in play,
  excluding destroyed units and every other player's
- [x] 4.3 Filter `types()` to that player's own type names
- [x] 4.4 Read only what the session holds — no `load()`, no `save()`, no call
  into the repository — so completing cannot change or re-read the game
- [x] 4.5 Have `candidates()` ask the source for `UNIT` and `TYPE` slots, and
  answer nothing when the source has nothing

## 5. Wiring readline into a session

- [x] 5.1 Add `install(role, source)` to `cli/complete.py`: import `readline`
  inside a `try`, return silently if it is unavailable, set the completer, set
  the delimiters to whitespace only, and bind both `tab: complete` and
  `bind ^I rl_complete` for `libedit`
- [x] 5.2 Write the callback: on `state == 0` read
  `readline.get_line_buffer()[:readline.get_endidx()]`, call `candidates()` and
  cache the list; on later states index into it
- [x] 5.3 Fork the read in `session.read_command`: `input(f"{prompt}> ")` when
  both stdin and stdout are terminals, catching `EOFError` and returning `Exit`
  after printing the blank line the current code prints; otherwise the existing
  `print` plus `sys.stdin.readline()` path, unchanged
- [x] 5.4 Extend the `read_command` docstring to record why there are two paths
  and why `EOFError` and `''` both mean `exit`
- [x] 5.5 Install a completer in `bgcclient.py` for `roles.CLIENT` with a source
  over its game and player number
- [x] 5.6 Install a completer in `bgcserver.py` for `roles.SERVER` before the
  setup loop, and in `bgcobserver.py` for `roles.OBSERVER`
- [x] 5.7 Check that the server's unattended cycle reads no commands and is not
  touched by any of this

## 6. Tests for completion

- [x] 6.1 Add `tests/test_completion.py` covering the verbs on an empty line,
  the subjects after `show`, `json` after a subject, the subjects after `set`,
  `add` and `load`, and the directions after a unit name in `move`
- [x] 6.2 Test the role filter: the observer is offered no `move`, `add` or
  `commit`; the client is not offered `show pending`; the server is
- [x] 6.3 Test names from a small built game — own units offered for `move`,
  own types for `add unit`
- [x] 6.4 Test that another player's unit of a similar name and a destroyed unit
  of the player's own are both absent
- [x] 6.5 Test path completion in a temporary directory, including descending
  into a directory and treating a path with a separator as one word
- [x] 6.6 Test that nothing is offered for a coordinate, a statistic, a name
  being invented, or after a complete `commit`
- [x] 6.7 Test that completing repeatedly writes nothing to the game directory
  and leaves the loaded game unchanged
- [x] 6.8 Add a pty-driven test that a real `bgcclient` session completes `sh`
  to `show`, skipped when a pty cannot be allocated
- [x] 6.9 Add a test that a piped session's captured output holds no escape
  sequence, and run the existing CLI surface suites unchanged as the evidence
  that non-interactive behaviour did not move

## 7. Shell completion

- [x] 7.1 Add `completions/bgc.bash`: complete a game number for `bgcclient` and
  `bgcobserver` from `games/_*` with the `_` stripped, a player number for
  `bgcclient`'s second argument from `games/_<gameno>/players/<n>.yaml`, and
  `bgcserver`'s options plus a game number after `-g`/`--game-number`
- [x] 7.2 Add `completions/bgc.zsh` covering the same three commands
- [x] 7.3 Offer nothing, and fail nothing, in a directory with no `games/`
- [x] 7.4 Add a test that the paths the scripts glob still match what
  `YamlGameRepository` writes, so the two cannot drift apart silently
- [x] 7.5 Confirm `pyproject.toml` declares no new console script and the three
  installed commands are unchanged

## 8. Documentation

- [x] 8.1 Add a completion section to `README.md`: what Tab does in a session,
  what it completes from the game, and the line to source for bash and for zsh
- [x] 8.2 Note in `README.md` that piped sessions are unchanged, since the test
  suite drives roles that way
- [x] 8.3 Record any divergence this change leaves behind in `SPEC_COVERAGE.md`
- [x] 8.4 Run the full suite and `pylint` over `src/`, and fix what this change
  broke
