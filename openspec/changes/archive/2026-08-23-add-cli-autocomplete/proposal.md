## Why

The three roles speak a small sentence language — `add type`, `add unit`,
`move alpha north`, `show units json` — and today you have to remember all of
it and type all of it. Nothing helps: `read_command` prints a prompt and calls
`sys.stdin.readline()` directly, so the session has no line editing at all.
There is no Tab, no history, not even a working backspace beyond what the
terminal driver gives, and a mistyped word is not a hint, it is
`invalid command` and a fresh prompt.

The cost is worst where the words are not in the grammar at all but in the
game: `move <unit>` wants a unit the player named themselves, possibly turns
ago, and `add unit <type>` wants a type they defined during setup. The only
way to see either is to stop, run `show units` or `show types`, read the name
off a table, and type it back in exactly. `help` already knows the whole
grammar — it is generated from `grammar.py` — and the session already holds
the player's own units and types. None of that reaches the person at the
prompt.

Launching a role has the same gap from the other side: `bgcclient` takes a
game number and a player number, both of which are on disk under `games/`, and
neither of which the shell will complete.

## What Changes

- Pressing Tab in a `bgcserver`, `bgcclient` or `bgcobserver` session completes
  what can be typed next: the verbs, the `show` subjects, the trailing `json`,
  the four directions, and the subjects of `set`, `add` and `load`.
- Completion is filtered by role, from the same table `help` is generated
  from. The observer is never offered `move`, and no role is offered a `show`
  subject it may not ask for — the offer and the refusal come from one place.
- Completion reaches into the game the session already holds: `move` completes
  the player's own units that are still in play, and `add unit` completes the
  type names that player has defined. Both read what the session has in memory,
  so a unit deployed a moment ago completes without a reload.
- `load board` and `load player` complete file paths from the working
  directory.
- Interactive sessions gain line editing and within-session history as a
  by-product of reading input through `readline`: arrow keys, Ctrl-A, Ctrl-R
  and up-arrow recall now work at the prompt.
- The grammar table in `grammar.py` gains a machine-readable form — each
  command as its literal words and its placeholders — and the usage strings
  `help` prints are generated from it. One description of the language now
  serves the parser's error messages, `help`, and completion.
- The package ships bash and zsh completion scripts for the three commands:
  `bgcclient <TAB>` offers the game numbers found under `games/`, a second
  `<TAB>` offers the player numbers registered in that game, and
  `bgcserver -g <TAB>` offers game numbers. The scripts are files to source,
  documented in `README.md`; no new command goes onto the path.
- Input that is not a terminal is untouched. A role reading from a pipe or a
  file still prints the same prompts, reads the same lines, and ends at end of
  input exactly as it does now — no readline, no completion, no escape
  sequences in the transcript.

Not in scope: a persistent history file across sessions, completing numeric
arguments (coordinates, statistics), suggesting names for things that do not
exist yet (`add type <name>`), Ctrl-C handling, colour, and any change to what
a command does once it has been typed.

## Capabilities

### New Capabilities

- `cli-completion`: what completes at each point in a session, where the
  candidates come from, that completing never touches the game, that
  non-interactive input behaves exactly as before, and the shell completion of
  the three launch commands.

### Modified Capabilities

- `player-client`: the client command loop states that an interactive session
  is line-edited and completes with Tab, while piped input is read as it is
  today.
- `game-server`: the same for the server's interactive setup prompt.
- `game-observer`: the same for the observer's command loop.
- `cli-installation`: "only the roles are installed" is stated precisely enough
  to cover the completion scripts — they ship as files to source, not as
  commands, so installing the package still puts exactly three names on the
  path.

## Impact

- **CLI**: `cli/grammar.py` gains the structured word list per usage and
  generates the usage strings from it; new `cli/complete.py` holds the
  completion function, the candidate sources and the `readline` wiring;
  `cli/session.py` reads interactive input through `input()` and keeps
  `sys.stdin.readline()` for everything else; `cli/help.py` and `cli/roles.py`
  share one "does this role offer this usage" predicate with completion;
  `bgcserver.py`, `bgcclient.py` and `bgcobserver.py` each install a completer
  for their role and game.
- **Packaging**: a `completions/` directory holding `bgc.bash` and `bgc.zsh`.
  `pyproject.toml` declares no new console script.
- **Tests**: new `tests/test_completion.py` over the completion function
  directly — role filtering, each position in each command, names from a game,
  paths — plus a pty-driven smoke test that Tab completes in a real session,
  skipped where a pty is not available. The existing CLI surface suites drive
  roles through pipes and must pass unchanged, which is the evidence that
  non-interactive behaviour did not move.
- **Docs**: `README.md` gains a section on completion and on sourcing the shell
  scripts; `GAME_RULES.md` is untouched — no rule changes.
- **Determinism**: none. Completion reads the game and never writes to it, and
  nothing in turn resolution is touched.
