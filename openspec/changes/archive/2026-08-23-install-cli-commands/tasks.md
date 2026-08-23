## 1. Give each role one name

See design.md — Decisions 1, 2 and 3. The suite is expected to fail between 1.1
and 1.4; task 2 is what makes it green again.

- [x] 1.1 Rename the three role entries in `[project.scripts]` to `bgcserver`,
      `bgcclient` and `bgcobserver`, keeping the same targets, and delete the
      `board-game-test-suite` entry; verify `pip install -e '.[dev]'` succeeds,
      the three commands appear in `venv/bin`, and
      `python -m board_game_concept.test_suite` still runs the harness
- [x] 1.2 Add a `PROGRAM` constant to `server.py`, `client.py` and `observer.py`
      holding that role's command name, and pass it to `read_command` in place
      of `argv[0]`; verify the installed `bgcobserver` prompts `bgcobserver> `
      rather than the path it was invoked by
- [x] 1.3 Name the command in each usage message — `bgcclient <gameno>
      <player_number>` and `usage, bgcobserver <gameno>`; verify each prints it
      when started with the wrong number of arguments
- [x] 1.4 Delete the dead `usage()` in `server.py` and construct its
      `ArgumentParser` with `prog=PROGRAM`; verify `bgcserver` with no
      arguments prints `usage: bgcserver [-h] -g GAME_NUMBER` and exits with a
      failure status, and that nothing else references the deleted function

## 2. Follow the rename through the suite

- [x] 2.1 Update the three prompt constants in `tests/cli_harness.py` to
      `bgcserver> `, `bgcclient> ` and `bgcobserver> `
- [x] 2.2 Update the usage strings asserted in
      `tests/test_cli_client_surface.py` and
      `tests/test_cli_observer_surface.py`, and the prompt literals in
      `tests/test_cli_observer_surface.py` and `tests/test_cli_server_surface.py`
- [x] 2.3 Update the prompt literals in
      `tests/test_server_client_integration.py`, which carries its own copy of
      the harness; verify `grep -rn '\.py> ' tests/` returns nothing
- [x] 2.4 Run `pytest` and verify the full suite passes again

## 3. Run what a user runs

See design.md — Decisions 4 and 5.

- [x] 3.1 Have `tests/cli_harness.py` resolve each role to the installed command
      when `shutil.which` finds it and to the module file when it does not,
      leaving the `__package__` bootstrap in the role modules in place; verify
      the CLI surface suites pass both with the package installed and with it
      uninstalled
- [x] 3.2 Add `tests/test_cli_installation.py` asserting each of the three
      commands is on the path and starts, reaching its prompt or its usage, and
      that none of the old `board-game-*` names resolves; skip the whole module
      with an instruction to `pip install -e '.[dev]'` when the commands are not
      on the path; verify it passes installed and skips uninstalled

## 4. Make installation the documented setup

- [x] 4.1 Replace the README's dependency list with the venv plus
      `pip install -e '.[dev]'` sequence, rename the three commands in its
      console scripts section, and replace the `board-game-test-suite` line with
      how to run the harness as a module; verify a reader following it from a
      fresh clone ends with the commands on their path
- [x] 4.2 Rename the commands in the `MODULE_DESCRIPTION.md` console script
      table and in the `openspec/config.yaml` context paragraph, and say in both
      that the standalone harness is run as a module rather than installed
- [x] 4.3 Rename the commands in `SPEC_COVERAGE.md` — the three capability rows
      and the reproduction commands that name `board-game-*` — and correct the
      entry that describes the harness as run by a console script
- [x] 4.4 Install the package in the CI workflow with `pip install -e '.[dev]'`;
      verify the workflow runs the installation test rather than skipping it

## 5. Verify

- [x] 5.1 Run `pytest` and verify the full suite passes with the package
      installed
- [x] 5.2 Recreate the venv from scratch, follow the README, and verify
      `bgcserver`, `bgcclient` and `bgcobserver` all run by name, that
      `venv/bin` holds no `board-game-*` and no test-suite command, and that the
      harness still runs as a module
- [x] 5.3 Play a short game from a directory other than the project root using
      the commands by name, and verify the game files appear under that
      directory's `games/_<gameno>`
- [x] 5.4 Run `pylint` and `flake8` as CI does and verify the change introduces
      no new findings
- [x] 5.5 Verify `grep -rn 'board-game-' . --exclude-dir=venv
      --exclude-dir=.git --exclude-dir=archive` returns nothing
- [ ] 5.6 Run `openspec validate install-cli-commands --strict` and verify it
      reports the change valid

## 6. One name per role in the repository too

Added after the first pass installed `bgcserver` from a file called `server.py`,
which left a role with two names again. See design.md — Decisions 1 and 1b.

- [x] 6.1 Rename `server.py`, `client.py` and `observer.py` to `bgcserver.py`,
      `bgcclient.py` and `bgcobserver.py` with `git mv`, and point the
      `[project.scripts]` targets at the renamed modules; verify
      `pip install -e '.[dev]'` succeeds and each command still starts its role
- [x] 6.2 Drop the hyphen from the command names, so the command and the file
      stem are spelled the same: `bgcserver`, `bgcclient`, `bgcobserver`, and
      the prompts `bgcserver> `, `bgcclient> `, `bgcobserver> `; verify the
      installed commands print the new prompts and usage
- [x] 6.3 Follow both renames through `tests/cli_harness.py` (the launchers,
      the prompt constants and `start_entry_point`),
      `tests/test_server_client_integration.py`, the surface tests and
      `tests/test_cli_installation.py`; verify `pytest` passes with the package
      installed and with it off the path
- [x] 6.4 Follow them through `README.md`, `MODULE_DESCRIPTION.md`,
      `openspec/config.yaml`, `SPEC_COVERAGE.md` and the CI workflow; verify no
      `bgc-` spelling and no bare `server.py`, `client.py` or `observer.py`
      reference is left outside the archive and the historical notes
- [x] 6.5 Re-run the lint and the verification from task 5; verify the findings
      still match HEAD's and a game still runs from another directory
