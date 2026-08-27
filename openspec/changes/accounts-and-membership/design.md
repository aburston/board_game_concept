## Context

Five facts about the current code decide most of this design.

**The number in the path is the whole of the credential.** `http/app.py`
routes every read and every write through `/games/<gameno>/players/<int:number>/…`
and hands that number straight to `Game(repository, number)`. Nothing between
the socket and the game asks whether the caller is that number. The module's
own docstring names this as unfinished — "When authentication lands, the
identity moves to a token and the path stops carrying it" — so the intent was
always to remove the number from the path.

**But the number cannot leave the path, because one account may hold several
seats.** That is a decision taken in this change (a person should be able to
play both sides to learn the game), and it makes the number underdetermined by
the account. So the path keeps it and authorisation becomes a *check* rather
than a *lookup*. This is the smaller change as well as the necessary one:
every route in `app.py` keeps its URL, and the guard goes in front.

**`service/identity.py` already answers a different question, cleanly.** It
says what a *number* is entitled to — `sees_everything`, `may_change`,
`is_player` — and its docstring explains that the administrator and the
observer live there because they are "roles a caller takes, not things the
rules of the game know about". That is exactly the right boundary. This change
adds the question *which numbers may this account be*, and answers it in a new
module. `identity.py` is not touched, and neither is anything below it.

**Every store is scoped to one game.** `session_module.make_repository(gameno,
…)` builds a repository per game under `games/_<gameno>/`, and `app.py` builds
a fresh one per request. There is nowhere in that tree for a person to live,
because a person is not part of any one game. An account store is therefore
new state at a new level, not a table added to an existing schema.

**The HTTP client already holds a `requests.Session`.** `HttpSession.__init__`
(`cli/backend.py:209`) keeps one for the life of the session, so carrying a
credential on every CLI request is one header set once, not a change to each
of the dozen call sites that use it.

## Goals / Non-Goals

**Goals:**

- An account is who a person is; a membership is which seat they hold in which
  game. Neither is a thing the rules of the game know about.
- The numbers, and what each number is entitled to, are unchanged. A number
  now has to be proven; what it means once proven does not move.
- `visibility` becomes true of the HTTP tier, rather than true of the engine
  and unenforced above it.
- One place decides whether an account may act as a number, so the browser and
  the command line cannot come to disagree about it.
- The local file flow is untouched, including every suite that drives a role
  through a pipe.
- No new dependency.

**Non-Goals:**

- The web interface. This change makes it possible and does not begin it.
- A lobby endpoint, a game registry, or creating a game over HTTP. All three
  want the account store to exist first, which is why they are next and not
  now.
- Enforcing that a player does not also log in as the observer. Explicitly
  rejected; see the decision below.
- More than one administrator, or per-game administrators.
- E-mail, password reset by mail, rate limiting, lockout, account deletion,
  TLS.

**Invariant untouched:** nothing here is consulted while a turn resolves. The
guard runs before `Game` is built and has no part in `board.commit()`, so the
determinism `tests/test_determinism.py` enforces is unaffected by construction
rather than by care.

## Decisions

### Accounts live in their own store, beside the games tree

Not inside any `games/_<gameno>/`, because an account outlives every game it
plays in and belongs to none of them. `accounts.sqlite3` under the SQLite
backend; `accounts/` holding three YAML files under the YAML one.

It gets its own port — `storage/account_store.py`, in the shape of
`storage/repository.py` — rather than new methods on `GameRepository`. Two
reasons. A game repository is chosen per game and built per request; an
account store is one per server. And `GameRepository` has two implementations
that must stay byte-comparable for the persistence tests, which a person is
not part of.

**Both backends implement it, and one choice drives both.** This reverses an
earlier decision here that the store should be SQLite only, on the grounds
that the YAML backend exists so an operator can `cat` a game and a password
hash is the one thing that should not be sitting in a readable file.

That reasoning was about the hashes, and it missed a larger property: a
deployment is one thing. A SQLite account store beside a YAML game store makes
"which backend is this?" a question with two answers — one for the games and
one for the people — which nothing else in this project does and nothing
should have to reason about. So `make_account_store(backend, base_path)`
returns the store for the backend the games use, taking the name
`cli/session.py` already resolves from `--backend` and `BOARD_GAME_BACKEND`.
There is deliberately no way to ask for one of each.

What the earlier reasoning was right about is the cost, and it is paid rather
than argued away: under YAML the scrypt hashes sit in a file. They are not
reversible, but a file walks off more easily than a table does, so the store
directory and its files are created `0700`/`0600`, with the mode set as the
file is created rather than after it — otherwise there is a window in which
the hashes are readable by anyone. An operator who would rather not make that
trade runs SQLite, which is the default.

### The seat stays in the path; authorisation is a guard

Every route keeps `/games/<gameno>/players/<int:number>/…`. In front of each
one:

```
  n == 0        → account.kind == 'admin'
  n == 1000     → account.kind in ('observer', 'admin')
  n in 1..999   → a membership exists for (account, gameno, n)
```

The administrator may act as the observer because it is already entitled to
see the whole game — `identity.sees_everything` says so of both numbers — and
refusing it would be a distinction with nothing behind it. The administrator
may **not** act as a player number without a membership: player 0 owns no
units, and an administrator who wants to play claims a seat like anyone else.

This is one function, `accounts.may_act_as(account, gameno, number)`, asked by
the HTTP guard and by nothing else today. It is stated once so that the web
interface and the command line cannot drift, which is the same reason
`domain/budget.py` holds the affordability rule for two enforcers.

### The two system accounts are implicit in every game; players are explicit

`admin` is player 0 of every game and `observer` is 1000 of every game, with
no membership row. Players get one row per seat.

The alternative — a membership row for every account in every game, written
for `admin` when a game is created — is more uniform and buys exactly one
thing: per-game administrators, so that different people could run different
games. That is a non-goal, and the row-per-game would have to be written by
something that noticed a game had been created, which is a thing that does not
exist yet (games are directories). Asymmetry now, uniformity if a second
administrator is ever wanted.

### A system account cannot be used until its password is changed

`must_change` on the account row, set on both at creation. While it is set,
every request from that account is refused except the one that changes the
password. Not a suggestion in an interface, because an interface is not what
the guard consults, and the credential is `admin`/`admin`.

The two are created by the store's `ensure()`, the way `GameRepository.ensure`
creates a game's tables — first start makes them, later starts find them. A
password already changed is never reset by a restart.

### One account may hold several seats; a seat has one holder

`PRIMARY KEY (gameno, number)` on `memberships` — a seat has one holder, which
is what stops two people ordering one army. No unique constraint on `(gameno,
account_id)` — one account may hold several seats.

This is deliberate and it is the reason the number stays in the path. It buys
the only way to try the game without a second person: claim both seats, play
both sides. `game-outcome` already says a game with fewer than two players is
a sandbox, so the rules are relaxed about solo play; this makes a two-seat
sandbox reachable.

The cost is that "which seat am I" is no longer answerable from the session,
which is a question the web interface has to answer in its URL. It already
has to, because the seat is in the path.

### "Started" is a turn having resolved, not setup having ended

A seat may be claimed until one of the game's turns has resolved. Not until
setup is committed, which is what the wording first suggested and what the
game cannot answer.

`Game.new_game` looks like the flag for this and is not. It is set to `not
sees_everything` at load and cleared once that player has committed, so it is
`False` for the administrator before anything has been set up at all and
`True` for a player after setup is over. It answers "does this session still
have setup to do" - a per-session question, and not a durable one; nothing
writes it down.

What is durable is the turn number in the game's progress, and `R3.8` keeps it
at 0 through the administrator's setup commit, because that commit is not a
turn. Reading it gives a definition that cannot disagree with the game, needs
no new column, and holds to this change's rule that no game storage changes.

It also turns out to be the better rule rather than merely the available one.
Between the setup commit and the first resolved turn, the board is set and
nobody has moved - which is exactly when somebody browsing a lobby would want
to join. Refusing them there would close the window the lobby exists for.

### The observer is honour-based, and the login page says so

One shared `observer` account, whose password the administrator can change.
Nothing stops a player opening a second tab, logging in as the observer, and
seeing the whole board — `visibility` R6.5 grants the observer exactly that.

Three enforcement options were considered and rejected. Per-game spectator
grants and a finished-games-only observer both work and both cost the live
spectating that makes an observer worth having. Refusing the observer view to
an account that holds a seat in that game does **not** work, and is the
dangerous one, because the shared account is nobody's account in particular —
there is no account identity for the check to key on, so it would look like
enforcement while enforcing nothing.

So: no enforcement, and the bargain is stated where somebody logs in, because
an honour system depends on people knowing what the honourable thing is. If
this is ever revisited, per-game spectator grants is the option to take, and
it composes with the shared account rather than replacing it.

### One kind of credential, carried two ways

A `sessions` row is a token: an opaque string, an account, an expiry, and an
optional label. A browser receives it in an `HttpOnly` cookie; a command-line
role sends the same string as `Authorization: Bearer`. One table, one
verification path, two carriers.

A minted token is the same row with a label and a distant expiry, which is
what a script or one of the bots in `matches/` uses. Splitting session tokens
from API tokens would mean two tables, two expiry rules and two revocation
paths to answer one question.

Server-side rows rather than a signed cookie, chiefly so that logging out
actually revokes — which matters more than usual here, because the observer
password is shared and "sign everyone out" is the only lever after it leaks.
It also removes the need for a `SECRET_KEY` that survives restart, which is a
thing that would otherwise have to be generated, stored and kept out of the
repository.

### Werkzeug's scrypt, so there is no new dependency

`werkzeug.security.generate_password_hash` / `check_password_hash`. Werkzeug
arrives with Flask, which `pyproject.toml` already requires, so this costs
nothing and is correct by default. `hashlib.scrypt` is the stdlib fallback if
Flask is ever dropped, and would need its own salt and encoding handling —
which is exactly the code worth not writing.

A password is refused below 8 characters, and no composition rule beyond that:
length is the property that helps, and the rest teaches people to write
`Passw0rd!`.

### Reserved names are compared without regard to case

`admin` and `observer` are refused at registration, matched case-insensitively,
and usernames are unique case-insensitively. Otherwise `Admin` registers, and
every list of who holds what seat becomes a place to be deceived. The stored
form keeps the case that was typed; the comparison ignores it.

### Local play needs no account, and this is stated rather than assumed

Without `BOARD_GAME_SERVER` the roles open the game directory themselves.
There is no server, so there is nothing to prove anything to, and requiring an
account would mean requiring one to play alone on a laptop. Accounts govern
the HTTP tier only.

This is what keeps the change small: `tests/test_cli_*_surface.py`,
`test_full_game.py` and every other suite that drives a role through a pipe
runs against the local path and needs no credential.

## Risks / Trade-offs

**Seven suites drive the HTTP tier and all of them break.**
`test_http_api.py`, `test_client_over_http.py`, `test_server_over_http.py`,
`test_observer_over_http.py`, `test_wait_over_http.py`,
`test_two_player_commit.py` and `test_local_api_guard.py` all issue
unauthenticated requests today, and after this change every one of them is a
401. This is the bulk of the work and it is not incidental — each of those
tests becomes the place where "does this account may-act-as this number" is
actually exercised. Mitigation: a `conftest.py` fixture that creates an
account, claims a seat and hands back an authenticated client, so the change
to each test is the fixture it asks for rather than a rewrite.

**Tokens and passwords cross the wire in clear.** There is no TLS here and it
is a non-goal; `bgcapiserver` binds `127.0.0.1` by default and its docstring
already says a real deployment uses a proper WSGI server. The honest position
is that this change makes authentication *possible*, and a deployment beyond a
trusted network still needs TLS in front. Named in the README rather than
solved here.

**No rate limiting.** `admin`/`admin` is guessable and the forced change is
what answers that; beyond it, an attacker on the network can try passwords as
fast as scrypt lets them, which is slow but not nothing. Acceptable at the
scale this runs at — one box, people who know each other — and the place to
fix it if that stops being true.

**A lost password cannot be recovered, only reset by the administrator.** No
e-mail, so no self-service reset. If the administrator's own password is lost,
the recovery is a row in `accounts.sqlite3` — which is a real operational
sharp edge and worth documenting rather than hiding.

**The account store is a new single point of failure.** Lose
`accounts.sqlite3` and every game becomes unreachable over HTTP while the
games themselves are intact. Recovery is to recreate accounts and re-claim
seats; the games are untouched because memberships name a seat rather than
being part of it. Worth a line in the README about backing it up beside
`games/`.

## Migration Plan

1. The account store is created on first start with the two system accounts.
   Nothing else is created and no game is touched.
2. Existing games keep their registered seats; those seats are simply
   unclaimed. An account claims one the way it would in a new game, so a game
   in progress can be picked up rather than abandoned.
3. Existing games remain fully playable through the local file flow
   throughout, with no account and no change.
4. The HTTP tier stops serving unauthenticated requests. This is a breaking
   change to anything driving it today, and there is no compatibility flag:
   an opt-out would be a way to turn the fog of war back off, which is what
   the change exists to fix.
5. `README.md` gains the first-run sequence — start the server, log in as
   `admin`/`admin`, change the password, register the seats, tell people to
   register — and the note that `accounts.sqlite3` is worth backing up.

## Open Questions

1. **Should registration be open, or gated by an invite code the administrator
   sets?** Open is assumed here. A code is a small addition later — one column
   on a settings row and one check at registration — and the answer probably
   depends on whether the server is ever reachable beyond a trusted network.
2. **Should a seat be releasable after the game starts?** Released before
   setup commits, yes; after, no, because the army is deployed and the barrier
   waits for that number. Whether an abandoned seat should instead be
   *transferable* by the administrator is a real question for long games and
   is not answered here.
3. **Do the bots in `matches/` get accounts?** The token path makes it
   possible and this change does not do it. It is what would make a seat read
   `reaper-bot` instead of `open`, and it is the shortest route to the first
   user story in `design.md` — "play a simple game against a basic bot".
