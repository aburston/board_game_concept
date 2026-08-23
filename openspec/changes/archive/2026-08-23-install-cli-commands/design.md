## Context

See `proposal.md` — Why. The constraints that shape the approach:

- **Printed output is contract, and the prompt is printed on every line.**
  `tests/cli_harness.py` and `tests/test_server_client_integration.py` drive the
  roles over stdin and read until a prompt appears. Changing what the prompt is
  changes what a large part of the suite waits for, so the prompt has to be
  changed in one place and the waits changed with it.
- **The prompt is currently whatever `argv[0]` happens to be.** Each role calls
  `read_command(argv[0], ROLE)` and `session.read_command` prints `f"{prompt}> "`.
  Every role therefore has as many identities as there are ways to launch it,
  and the tests pass only because `read_until` matches a substring: the absolute
  path the harness passes ends in `server.py> `. Renaming the files (Decision
  1b) breaks even that coincidence, so the constant is what has to carry the
  identity.
- **The console scripts have been dead before.** `SPEC_COVERAGE.md` — 9 records
  all four raising `TypeError` when installed, because nothing ran them. Any fix
  that leaves them untested is the same fix.
- **`pytest` on a fresh clone currently passes without installing anything.**
  the three role modules put `src` on `sys.path` themselves
  when `__package__ is None`, and the harness launches them by file path. That
  property is worth keeping: a change about installation that makes the suite
  fail unless you install first trades one obstacle for another.
- **No consumer outside this repository.** Nothing imports the package and no
  script anywhere calls `board-game-*`, so the old names can go rather than be
  kept as aliases.

## Goals / Non-Goals

**Goals:**

- One command per interactive role, none of the names shared with another
  project and none of them the name of a source file. Nothing else installed.
- One identity per role, printed the same way however the role was launched.
- Installing the package puts the commands on the path, and that is the
  documented setup.
- The suite runs the installed commands when they exist, and says so when they
  do not.

**Non-Goals:**

- Keeping `board-game-*` working, under an alias or otherwise.
- Deleting `src/board_game_concept/test_suite.py`, or reconciling it with
  `tests/test_basic.py`. It loses its console script and keeps everything else.
- Installing outside a virtualenv — pipx, `pip install --user`, a system
  package. `pip install -e .` into the project's venv is what this change
  documents.
- Any new command, subcommand, flag or argument. `bgcserver -g <gameno>`,
  `bgcclient <gameno> <player>` and `bgcobserver <gameno>` take exactly the
  arguments they take today.
- Removing the `pyaml` entry in `requirements.txt` that duplicates
  `pyproject.toml`'s `PyYAML` dependency. Adjacent, and a separate decision.

## Decisions

### 1. `bgc` as the prefix, and the old names go

`bgcserver`, `bgcclient`, `bgcobserver`. Unique to this project, short enough
to type repeatedly, and each says which role it is.

No separator inside the name — not `bgc-server`, not `bgc_server`. A hyphen
cannot appear in a module file name, since an entry point names a module
(`import bgc-server` is a syntax error), and an underscore would leave the
command and the file spelled differently. Running the words together is the one
spelling a file and a command can share exactly, which is what Decision 1b is
for.

No alias for `board-game-*`. An alias is only worth its confusion when someone
is depending on the old name, and nobody is: the names are three months old,
they were unusable for most of that time (`SPEC_COVERAGE.md` — 9), and the only
references are this repository's own documentation, which this change updates.

### 1a. The test harness loses its command rather than gaining a new one

`board-game-test-suite` is deleted from `[project.scripts]`. An installed game
does not need a permanent command for a developer test harness, and naming it
`bgctestsuite` would put a fourth executable on every user's path to run
something only someone working on this repository ever wants.

`src/board_game_concept/test_suite.py` stays where it is and keeps its
`if __name__ == '__main__'` block, so it runs as
`python -m board_game_concept.test_suite` for anyone who wants it. This is a
packaging decision, not a verdict on the module: whether it should exist beside
`tests/test_basic.py` at all is still the open question it was.

### 1b. The file is named for the command

`server.py`, `client.py` and `observer.py` become `bgcserver.py`,
`bgcclient.py` and `bgcobserver.py`, and the entry points follow them to
`board_game_concept.cli.bgcserver:main` and its siblings.

Decision 2 stops a role having one name in the prompt and another on the path.
This stops it having a third in the repository. A reader who runs `bgcserver`
and then goes looking for it should find a file called `bgcserver.py`, and
`grep -r bgcserver` should reach the code rather than only the packaging.

The names in `cli/` stay distinct from the other modules there — `grammar.py`,
`parser.py`, `session.py` are shared machinery, and the three `bgc*` files are
the things you can actually run, which is now visible from the file listing.

Alternative considered: leaving the files alone and installing `server`,
`client` and `observer`. The names would match, but they would stop being
unique to this project, which is where this change started.

### 2. Each role names itself with a constant

Each role module gains

```python
PROGRAM = 'bgcserver'   # 'bgcclient', 'bgcobserver'
```

used for the prompt (`read_command(PROGRAM, ROLE)`), the usage line, and the
server's `ArgumentParser(prog=PROGRAM)`. `sys.argv[0]` stops being read for
anything but arguments.

This is what makes the identity stable across launch methods, and it is what
makes Decision 4 cheap: because the prompt no longer varies with how the role
was started, the harness can run the installed command or the module file and
expect the same output either way.

`session.read_command` keeps taking the name as its first parameter rather than
looking it up — it serves three roles and should not have to know which one is
calling.

Alternative considered: deriving the name from `Path(sys.argv[0]).name`. It
gives `bgcserver` for the installed command and `bgcserver.py` for the module
file
— two identities again, and a prompt that tells a user how the process was
started rather than what it is.

### 3. The server's usage text is `argparse`'s, and the dead one goes

`bgcserver.py` defines `usage()` describing
`server.py <gameno> [<boardfile>] [<playerfile 1>] ...` — positional arguments
`argparse` rejects, in a function nothing calls. It is deleted rather than
corrected. `ArgumentParser(prog=PROGRAM)` then makes `argparse` print
`usage: bgcserver [-h] -g GAME_NUMBER`, which is both accurate and generated
from the arguments actually accepted.

`bgcclient.py` and `bgcobserver.py` keep their hand-written `usage()`, since
neither
uses `argparse`; only the name inside changes.

### 4. The harness prefers the installed command, and falls back

`tests/cli_harness.py` resolves each role once:

```python
SERVER = shutil.which('bgcserver') or [PYTHON, CLI_DIR / 'bgcserver.py']
```

— the installed command when it is on the path, the module file when it is not.
The `if __package__ is None` bootstrap in each role stays, because it is what
makes the fallback work.

So `pytest` on a fresh clone still passes without an install, and `pytest` after
`pip install -e .` tests what a user actually runs. Decision 2 is what lets both
assert the same prompts and the same usage text.

Alternative considered: requiring the install and skipping the CLI suites
without it. Honest, but it turns a fresh clone from ~200 passing tests into ~140
passing and ~60 skipped, and the skip is easy to stop noticing.

Alternative considered: keeping the harness on module files only. Then nothing
ever runs the installed command, which is the hole this change exists to close.

### 5. One test that installation is what it claims

`tests/test_cli_installation.py`: for each of the three commands, assert
`shutil.which(name)` finds it and that running it starts the role — reaching its
prompt or its usage. One further assertion that none of the four `board-game-*`
names resolves, which catches both a half-finished rename and a stale script
left in a venv. Skipped, with "install the package with `pip install -e .` to
run these", when the commands are not on the path.

This is deliberately the one place that skips. It is the only assertion that
cannot be made without an install, and CI installs the package (Decision 6) so
it runs on every push.

### 6. CI installs the package

The workflow's install step becomes `pip install -e '.[dev]'` alongside the
`pytest` and `flake8` it already installs. That is what turns Decision 5 from a
test that could quietly skip forever into one that runs.

`requirements.txt` keeps its `pyaml` line and CI keeps installing it. Redundant
once the package is installed, but removing it is a separate question about
which file declares dependencies, and this change is already touching enough.

### 7. `pip install -e .`, editable, into the project venv

The README's setup becomes:

```
python3 -m venv venv
source venv/bin/activate
pip install -e '.[dev]'
```

Editable, because everyone installing this repository today is working on it: a
non-editable install leaves the commands running a copy, which is exactly the
kind of "which one am I running" confusion this change is trying to end.

No `setup.sh`. The three lines above are the standard Python setup, they are
already most of what the README says, and a wrapper script would be a fifth
executable in a change about there being too many names for things.

### 8. Where a game lives is stated, not changed

The storage layer resolves `games/_<gameno>` against the working directory. Once
the commands are on the path this stops being obvious — a user can run
`bgcserver` from anywhere, and where the game turns up matters. The new
`cli-installation` requirement writes down what the code already does. No code
changes for it; the tests it needs are the harness's existing `cwd` handling.

## Risks / Trade-offs

- **A prompt string is missed and a test hangs until it times out** → The three
  prompt constants live in `tests/cli_harness.py` and are changed there once;
  `test_server_client_integration.py` carries its own copies, which is the file
  to sweep. Grep for `.py> ` when done: no match should remain.

- **The harness falls back silently and CI never runs the installed command**
  (Decision 4) → Decision 5's test does not fall back — it skips loudly — and
  Decision 6 makes CI install the package so it cannot skip there.

- **Someone's shell has a stale `board-game-*` on the path after the rename** →
  `pip install -e .` leaves the old scripts behind in `venv/bin`. Called out in
  the tasks: remove them, or recreate the venv, and check `bgcserver` is what
  runs.

- **The rename touches five documentation files and one of them keeps the old
  name** → They are enumerated in `proposal.md` — Impact, and the final task
  greps the working tree for `board-game-` with the archive excluded.

## Migration Plan

No data migration: no game file, board file or player file names an executable.
Anyone with a venv from before the change reinstalls, or deletes
`venv/bin/board-game-*` by hand.

Sequenced so the suite is green at each step: rename the entry points and give
each role its constant first (the suite still passes, because the harness
matches prompts by substring only after its constants are updated in the same
step), then the harness, then the new installation test, then documentation and
CI.

## Open Questions

None that change the approach. One noted for later, unchanged from
`split-into-layers`: `src/board_game_concept/test_suite.py` duplicates
`tests/test_basic.py` in a hand-rolled harness. This change takes away its
console script (Decision 1a) and keeps the module runnable; whether the module
should exist at all is still open.
