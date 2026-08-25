## Context

See `proposal.md`. The defect is one argument — the number a `Game` is opened
as — and the fix is the other number. What is worth designing is not the line
but where the rule lives, because the line was written by somebody who knew
both facts it depends on and still got it wrong: that a player's session is
built from that player's own view, and that resolving a turn republishes the
board it holds.

## Goals / Non-Goals

**Goals:**
- A two-player game played over the API is undecided until it is decided by
  play.
- The rule about which session may resolve a turn is stated where a turn is
  resolved, not in each caller.
- A player still gets an answer to their own commit that is theirs to read.
- The scenario is covered on both storage backends, and CI actually runs both.

**Non-Goals:**
- Changing what a player's session is given. Its half-sightedness is
  `visibility` working, not the defect.
- The administrator branch of `POST /commit`. It resolves without asking the
  barrier, which is right for the setup commit that ends setup and is what
  `resolve_pending` reaches over HTTP; whether those two should be one endpoint
  is a separate question and is noted below.
- Retiring the `@pytest.mark.backend('sqlite')` pins. Some of them are about
  SQLite; the ones that are merely inherited from a module-level pin are for
  somebody to look at once the matrix means both jobs run.

## Decisions

### 1. The endpoint resolves as the administrator

```
   game.load(); game.clientSave()                       # publish as the player
   resolver = Game(_repository(gameno),
                   identity.ADMINISTRATOR)              # resolve as the game
   resolved = resolver.resolveWhenReady()
   game.load()                                          # answer as the player
```

Three sessions where there were two, and each is opened as the identity whose
act it is. Publishing is the player's: it is their orders and their draft. The
resolution is nobody's in particular, which in this game means the
administrator's — the identity `identity.py` calls "the game's administrator
and commit authority, who owns no units".

`identity.ADMINISTRATOR` rather than `0`, for the reason that module exists.

### 2. The answer is read as the player who asked

The old code chose between the two sessions (`resolver if resolved else game`)
and reloaded whichever it picked. Both read the same repository, so the choice
never mattered to the values — but with the resolver now the administrator's
session, choosing it would have built a player's response from a session
entitled to the whole game. `_commit_payload` reads only the turn number, the
outcome and who is awaited, none of which is secret; the point is that a
response to a player should not be assembled from a session that can see more
than they can, whatever it happens to read today.

So the payload is always built from the player's own session, reloaded after
the resolve.

### 3. The refusal lives in `resolve`, not in the endpoint

Fixing the endpoint alone would leave the next caller to get it right by
knowing two facts about a layer below it. `turn.resolve` is where the damage
would be done — it is the function that republishes the board it was given —
so it is where the question is asked.

It raises rather than returning `False`. `False` means "the turn could not be
resolved", which `bgcserver` exits on and which a caller may reasonably print;
this is not a state of the game but a caller asking for something it may not
have. `GameError` is what the service layer raises for that everywhere else,
and the HTTP tier already maps it.

The guard is the first thing in the function, before the board-size check and
before anything is written. Under `resolve_when_ready` it raises inside the
hold; both repositories roll back and release on the way out, and there is
nothing to roll back.

### 4. Entitled to the whole game *and* allowed to change it

`sees_everything` is true of the observer as well as the administrator, and an
observer resolving a turn would be a read that wrote. `may_change` is false of
the observer and true of everyone else. The pair is the administrator today,
and stays correct if another identity is added that is both.

Asked as two identity questions rather than as `player_number == 0`, which is
what `identity.py`'s own docstring asks callers not to do.

### 5. One test file for the scenario, run on both backends

The scenario is a game, not a backend, so `tests/test_two_player_commit.py`
takes the backend from `game_harness.DEFAULT_BACKEND` and is not pinned. It
plays the same game twice — over the endpoint and against the service layer —
because the second is the control: it passed before the fix and after it, which
is what makes the file evidence about the defect rather than about the fix.

The end-to-end coverage through two `bgcclient` subprocesses goes in
`tests/test_client_over_http.py` beside the one-player test that missed this,
and is pinned to SQLite with the rest of that module.

### 6. CI runs the suite once per backend

A matrix over `yaml` and `sqlite`, with `BOARD_GAME_BACKEND` set from it on the
pytest step. `fail-fast: false`, so one backend failing still reports the
other. Lint runs in both jobs, which is duplicated work and not worth a
separate job to avoid.

The alternative — one job running pytest twice — hides which backend failed
behind one red tick.

## Risks / Trade-offs

- **The SQLite job is new work in CI, and new work can be flaky.** The HTTP
  tests start a Flask thread and drive subprocesses; they are the least
  hermetic thing in the suite. Both jobs were run locally with the package
  installed the way CI installs it before the matrix was proposed: 658 passed
  under YAML, 630 under SQLite.

- **The guard could refuse a caller that ought to be allowed.** Only three
  callers resolve turns — `bgcserver` through `LocalSession`, the commit
  endpoint, and the tests — and all now do so as the administrator. A fourth
  that wanted to would be asking to resolve a turn from part of a game.

- **The administrator branch of `POST /commit` still resolves without asking
  the barrier.** `HttpSession.resolve_pending` posts to it as player 0 and gets
  an unconditional `serverSave`, which is not what `resolve_when_ready` means.
  Nothing reaches it today — `bgcserver` exits after setup in HTTP mode — and
  it cannot decide a game wrongly, because the board it republishes is the
  whole board. Recorded here rather than fixed, so that whoever gives the
  endpoint a barrier-checking admin path knows it was seen.

## Migration Plan

1. `service/turn.py`: the guard, and the docstring that says why.
2. `http/app.py`: resolve as the administrator, answer as the player.
3. `tests/test_two_player_commit.py`: the scenario, both transports.
4. `tests/test_client_over_http.py`, `tests/test_turn_publication.py`: end to
   end, and the refusal.
5. `openspec/specs/turn-commit/spec.md` and `SPEC_COVERAGE.md`.
6. `.github/workflows/python-app.yml`: the backend matrix.

## Open Questions

None.
