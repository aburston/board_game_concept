## Why

The first two-player game played over the API ended on turn 1. Two players were
registered, each designed a type and deployed a unit, and they committed one
after the other. The second commit was answered with `{"decided": true,
"winner": 2, "turn": 1}` — a game decided before an order had been given, in
favour of whoever happened to commit last.

`post-commit-with-inline-resolve` made the commit that closes the barrier
resolve the turn during the request, which is what lets an HTTP game run with
no unattended `bgcserver`. It opened the resolving session as the committing
player:

```
   published = game.clientSave()                       # publish as the player
   resolver = Game(_repository(gameno), int(number))   # ← and resolve as them
   resolved = resolver.resolveWhenReady()
```

A player's session is not the whole game with parts hidden as it is drawn. It
is built from that player's own published view — `visibility` requires exactly
that — so it holds only the units that player may see, and `_load_players`
reads no other player's orders. Resolving a turn from one therefore:

- applies a single player's orders, and none of anybody else's;
- publishes that half-sighted board as `units`, the record of the game, so
  every other player's units are not moved and not fought but erased;
- judges elimination from what is left, finds everybody but the committer
  holding nothing that is standing, and decides the game in their favour.

Nothing about it is a race or a rare interleaving: it is what every two-player
commit over HTTP did. The suite was green because the endpoint's tests used a
one-player game — where the only player sees all of their own units, so the
board they resolve from is the whole board — or stopped at the commit before
the one that resolves.

It survived CI for a second reason. Every test of the HTTP tier is pinned to
the SQLite backend with `@pytest.mark.backend('sqlite')`, and CI ran `pytest`
with no `BOARD_GAME_BACKEND` set, which is YAML. Some fifty tests — the whole
HTTP tier, the SQLite repository and its safety suite — were skipped on every
run. Nothing was failing; nothing was running.

## What Changes

**A turn is resolved from the whole game, whoever asked for it.**

- **The commit endpoint resolves as the administrator.** The publish stays the
  committing player's, because it is their orders being published. The
  resolution is the administrator's, because it is the whole game's turn. The
  answer is still read back through the asking player's own session, so a
  player is told what they are entitled to be told.

- **A session that is not entitled to the whole game may not resolve a turn.**
  `service/turn.py` refuses it, so which session resolves is a rule of the game
  rather than something each caller is trusted to get right. The observer is
  refused too: it sees the whole game and changes nothing, so a turn resolved
  from one would be a read that wrote.

- **CI runs the suite once per storage backend.** A matrix over `yaml` and
  `sqlite` passes the backend through the environment variable
  `tests/conftest.py` already reads, so a pinned test is run by the job it is
  pinned to rather than by neither.

**BREAKING**: nothing. The local file transport and the command line roles
already resolved as the administrator, which is why a game played through
`bgcserver` was never affected.

## Capabilities

### Modified Capabilities
- `turn-commit`: a new requirement states that a turn is resolved only from a
  session entitled to the whole game and allowed to change it, whatever
  transport carried the commit that closed the barrier, and that a session
  which is not is refused rather than allowed to resolve from part of the game.

## Impact

- **HTTP**: `http/app.py` — the player branch of `POST /commit` resolves as
  `identity.ADMINISTRATOR` and builds its payload from the player's own
  reloaded session.
- **Service**: `service/turn.py` — `resolve` refuses a session that is not
  entitled to the whole game and allowed to change it, before anything is
  written.
- **Tests**: `tests/test_two_player_commit.py` plays the scenario over the
  endpoint and against the service layer and holds both to one answer, on
  whichever backend the run is for. `tests/test_client_over_http.py` plays it
  end to end through two `bgcclient` subprocesses.
  `tests/test_turn_publication.py` covers the refusal itself.
- **CI**: `.github/workflows/python-app.yml` — the job becomes a matrix over
  the two backends.
- **Docs**: `SPEC_COVERAGE.md`, as divergence 30.
