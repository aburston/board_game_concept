## Why

All three roles read a line, and treat "nothing was typed" and "there is
nothing left to read" as the same thing. `read_command` calls
`sys.stdin.readline()`, which returns the empty string at end of input; that
parses as a blank line, which is reported as nothing to do, and the session
loops round and prompts again — forever, at whatever speed the terminal can
print.

Interactively this never shows: a person types `exit`, and Ctrl-D is rare
enough to look like a hang rather than a bug. It bites the moment a role is
driven from anything but a keyboard. Piping a script of commands into
`board-game-client` runs them and then spins, filling the pipe with prompts and
never exiting, so the game cannot be scripted, demonstrated from a shell, or
driven by a wrapper that closes its end. It was found while playing a game
through the console scripts to check the `fix-rules-defects` change.

## What Changes

End of input ends the session, exactly as `exit` does. The three roles already
handle `exit`; the reader hands them the same command when its input runs out,
so nothing else changes and the roles are not touched.

This is a small behavioural addition, not a fix to a rule of the game: no
capability said what should happen at end of input, so the loop was free to do
the wrong thing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `player-client`: the client's command loop ends the session at end of input.
- `game-server`: the server's interactive setup ends at end of input.
- `game-observer`: the observer's command loop ends the session at end of input.

## Impact

- **CLI**: `cli/session.py` — `read_command` alone. `server.py`, `client.py`
  and `observer.py` are unchanged: each already ends on the command it is
  given.
- **Tests**: one scenario per role in the three CLI surface suites, driving a
  role with its input closed and asserting it exits rather than spinning.
- **Docs**: `GAME_RULES.md` R8, which describes what each role accepts.
