## Why

The observer is player 0, and so is the administrator. `bgcobserver.py` hardcodes
`player_number = 0`, and `Game` decides what a session may see with
`sees_everything = player_number == 0`. Two roles that differ in the most
important way — one may change the game and one may not — are the same identity
to everything below the CLI.

The command line gets away with it because they are different binaries with
different grammars: `cli/roles.py` simply does not give the observer the
commands that write. Nothing else enforces it. One API cannot work that way,
because a single endpoint has to decide from the caller's identity whether a
request may change anything, and today's identity cannot tell it.

It is not only a future problem. Drafting made the shared identity visible:

```
    administrator sets board 6 7, adds player 1, does NOT commit
    observer opens the same game
      → observer board size: (6, 7)
      → observer holds a draft of: ['set_board', 'add_player']
```

The observer reads the administrator's uncommitted setup and holds it as its
own draft. It sees work nobody has published, and a session that is supposed to
write nothing is one recorded command away from writing into somebody else's
draft.

Three more defects sit alongside it, all from the same root — that no rule
anywhere says which numbers mean what:

- **`add player 0` is accepted**, registering the administrator as a player of
  the game they are running. Nothing refuses it.
- **`add player 1000` is accepted**, which becomes a direct collision the moment
  1000 means the observer.
- **`add player -1` raises `AssertionError`**, not `GameError`. The roles catch
  `GameError`, so this escapes and **kills the server** — the same class of
  defect as number 4 in `SPEC_COVERAGE.md`, which was fixed for a bare `add`
  and is still live for a negative number.

`game-observer` already claims the observer is bound to a game "with no player
affiliation". That is not true today. This change makes it true by giving the
observer an affiliation of its own.

## What Changes

**The three roles get three identities, and the numbering is stated once.**

- **The observer is player 1000.** A reserved number, never registered as a
  player and never waited for by the commit barrier. It is entitled to see the
  whole game, as it is today, and entitled to change nothing.

- **A player is numbered 1 to 999.** `add player` refuses anything outside that
  range, and refuses it as a refusal the session reports rather than an error
  that ends it. A client cannot be launched for a number outside it either.

- **0 stays the administrator.** Unchanged, except that it is now stated rather
  than assumed, and `add player 0` is refused.

- **A session reads only its own draft.** Falls out of the split: the observer
  stops reading the administrator's, because it is no longer the administrator.
  The observer drafts nothing, having no command that writes.

- **Being entitled to see everything stops meaning "is player 0".** Two
  identities are now entitled to the whole game, so the question a session
  answers becomes *may this identity see everything* rather than *is this
  identity zero*.

**BREAKING**: a game whose player list includes 0 or a number above 999 can no
longer have been made by `add player`, and one made by hand or by `load player`
is refused when it is loaded rather than opening into an unclear state. No game
made by the commands as shipped is affected, because a player number has only
ever come from `add player` or a loaded player file.

Not in this change: accounts, credentials, sessions or bearer tokens; any change
to what a player may see; any change to the roles' command surfaces beyond the
refusals above. The observer's grammar is what it already is.

## Capabilities

### New Capabilities
- `player-numbering`: who the numbers in a game belong to — the administrator,
  the observer, and the players — and which numbers a player may take. Stated
  once here rather than four times over, because `game-server` enforces it when
  registering, `player-client` and `game-observer` each depend on it to know
  who they are, and `game-persistence` refuses a session whose number the game
  does not have.

### Modified Capabilities
- `game-observer`: the observer is player 1000 and no longer shares the
  administrator's identity; its claim to have "no player affiliation" becomes a
  reserved affiliation of its own. It reads no other session's uncommitted work.
- `game-server`: `add player` refuses a number outside 1 to 999, and refuses a
  reserved one, reporting it rather than ending the session.
- `player-client`: a client may only be launched for a player number in 1 to
  999, and says so rather than opening a session that can never be a player.

## Impact

- **Domain**: `domain/player.py` — `Player` asserts only that a number is a
  non-negative integer. The range belongs here or in the service layer, and
  which is a design question rather than a scope one.
- **Service**: `service/game.py` — seven places test `player_number == 0` or
  `!= 0`; each becomes a question about the identity's entitlements rather than
  about the number. `service/games.py` — `add_player` gains the range check and
  stops letting an `AssertionError` escape as one.
- **CLI**: `cli/bgcobserver.py` — the hardcoded 0 becomes the observer's number.
  `cli/bgcclient.py` — the number taken from `argv` is checked before a session
  is opened. `cli/complete.py` takes a player number and may need the same.
- **Tests**: the observer surface suite, which asserts what an observer sees;
  `tests/test_cli_server_surface.py` for the new refusals; a new file for the
  numbering rules themselves. The shared-identity leak demonstrated above is
  worth a test of its own, since it is the thing that showed the defect.
- **Docs**: `MODULE_DESCRIPTION.md` and `README.md` both describe the observer
  as player 0. `SPEC_COVERAGE.md` gains the three defects above.
