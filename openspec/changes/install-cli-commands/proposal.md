## Why

The command-line roles do not agree with themselves about what they are called,
and nothing checks that they can be run at all once installed.

`pyproject.toml` declares `board-game-server`, `board-game-client` and
`board-game-observer`, but every role builds its prompt from `sys.argv[0]`. Run
from the installed script, the server prompts

```
/home/user/src/board_game_concept/venv/bin/board-game-server>
```

— the whole invocation path, on every line of the session. Run as a file it
prompts `server.py> `, which is what the tests expect and what
`test_server_client_integration.py` matches on, so the identity the suite pins
is the one nobody installing the package ever sees. The usage messages name
`client.py` and `observer.py`, files a user of an installed command has no
reason to know exist, and `server.py` carries a third name in a dead `usage()`
function that describes arguments `argparse` does not accept.

Nothing installs the package either. The README documents a virtualenv, `pip
install` of individual libraries, and running `pytest`; CI installs
`requirements.txt` and never installs the package. So the console scripts are
never exercised anywhere — which is how they came to be broken once already
(`SPEC_COVERAGE.md` — 9: every one of them raised `TypeError` and stopped, and
only launching the module files directly worked).

## What Changes

- Each interactive role SHALL be installed under a name unique to this project
  and short enough to type: `bgcserver`, `bgcclient` and `bgcobserver`,
  replacing the `board-game-*` names. No alias for the old names is kept; the
  package has no consumer outside this repository.
- `board-game-test-suite` SHALL be removed from `[project.scripts]` rather than
  renamed. It runs a developer test harness, which is not something an installed
  game needs a permanent command for; `src/board_game_concept/test_suite.py`
  stays and remains runnable as a module.
- Each role SHALL name itself by its installed command name — in its prompt, its
  usage line and its argument errors — rather than by `sys.argv[0]`. The prompt
  becomes `bgcserver> `, `bgcclient> ` and `bgcobserver> `, and is the same
  whether the command was found on the path, run by an explicit path, or run as
  a module file.
- The file implementing a role SHALL carry the command's name, so a role has one
  name and not two: `server.py`, `client.py` and `observer.py` become
  `bgcserver.py`, `bgcclient.py` and `bgcobserver.py`. A command whose name
  appears nowhere in the repository is the same confusion this change is
  removing from the prompt, one level further out.
- The commands SHALL be installed onto the path by installing the package, and
  `pip install -e .` SHALL be the documented setup step. The README and
  `MODULE_DESCRIPTION.md` follow, and CI installs the package so the console
  scripts are exercised by the suite rather than only declared.
- The CLI test harness SHALL drive the installed commands when they are on the
  path, falling back to the module files when they are not, so the suite tests
  what a user runs without requiring an install to pass.
- A test SHALL assert that the three commands are on the path and start, and
  that no `board-game-*` command is declared, skipped with an instruction when
  the package is not installed. This is the check that was missing when the
  console scripts were dead.
- The dead `usage()` in `server.py`, which names arguments `argparse` rejects,
  SHALL be removed, and `argparse` SHALL be told the program name so its own
  usage and error output names the command.
- Where a game's files live SHALL be stated: a game is resolved relative to the
  working directory the command is run in. This is what the code does today and
  what running from the path makes worth saying out loud.

Explicitly out of scope: deleting `src/board_game_concept/test_suite.py`, which
duplicates `tests/test_basic.py` in a hand-rolled harness. Losing its console
script is not a judgement on the module, and whether the module earns its place
is a separate question. Also out of scope: installing outside a virtualenv
(pipx, `--user`), any new command or subcommand, any change to what a role can
do, and the `requirements.txt` / `pyproject.toml` duplication.

## Capabilities

### New Capabilities

- `cli-installation`: what the command-line roles are called, how they get onto
  the path, and where they look for a game.

### Modified Capabilities

- `game-server`: Server Invocation names the installed command and fixes the
  identity the server presents.
- `player-client`: Client Invocation, as above.
- `game-observer`: Observer Invocation, as above.

## Impact

- `pyproject.toml`: three `[project.scripts]` entries are renamed, and point at
  the renamed modules; the `board-game-test-suite` entry is deleted. No new
  dependency.
- `src/board_game_concept/cli/server.py`, `client.py`, `observer.py`: renamed to
  `bgcserver.py`, `bgcclient.py` and `bgcobserver.py`. Each gains a program-name
  constant used for the prompt and usage; `read_command(argv[0], ROLE)` becomes
  `read_command(PROGRAM, ROLE)`; the server's dead `usage()` goes and its
  `ArgumentParser` gets `prog`.
- `tests/cli_harness.py`: resolves each role's executable, preferring the
  installed command; the three prompt constants and the module file names
  change.
- `tests/test_cli_client_surface.py`, `tests/test_cli_observer_surface.py`,
  `tests/test_cli_server_surface.py`, `tests/test_server_client_integration.py`:
  the prompt and usage strings they assert on change.
- `tests/test_cli_installation.py`: new — the three commands are on the path and
  start, and nothing else is installed under the old names.
- `README.md`: an install step, the renamed console scripts, and how to run the
  standalone harness now that it has no command of its own.
- `MODULE_DESCRIPTION.md`: the console script table, the `cli` module list, and
  the paragraph on the standalone harness.
- `openspec/config.yaml`: the context paragraph naming the modules and the
  console scripts.
- `SPEC_COVERAGE.md`: the three capability rows and the reproduction commands
  that name `board-game-*`.
- `.github/workflows/*.yml`: installs the package.
