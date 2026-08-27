## Why

Over the HTTP tier a session's identity is a number in a URL, and nothing
checks it. `GET /games/1/players/2/views/board` returns player 2's private
view to whoever asks for it, and `POST /games/1/players/2/commands` gives
player 2's orders on their behalf. The number is not a credential; it is a
path segment, and a person who can count can be anybody.

That is not only a security gap. **Visibility is a rule of the game**, and the
HTTP tier cannot honour it. `visibility` requires that a player sees an enemy
unit only by fighting it, and `player-numbering` requires that a session reads
only what its identity is entitled to. The engine implements both faithfully —
a client is loaded from its own published view, and `read_view` does the join —
and then the transport hands the answer to anyone who asks in another player's
name. Every guarantee in `visibility` is, over HTTP, a guarantee about who
typed the URL.

Nor is there anywhere to put a person. A game knows player numbers; it does
not know that Ada is player 1 of game 4 and player 3 of game 7, and there is
no store in which it could. Every store this project has is scoped to one
game, under `games/_<gameno>/`. So there is no lobby, no way to see which
games exist, and no way for somebody to join one — the only way to become a
player is for the administrator to type `add player 2` and for you to be
trusted to run `bgcclient 1 2` and nothing else.

This change puts a class of user above the numbers. An account is who a person
is; a membership is which seat that person holds in which game. The numbers do
not change, the rules do not change, and `service/identity.py` does not change:
what changes is that a number now has to be **proven** rather than asserted.

## What Changes

- **Accounts exist, and live outside any game.** A new server-wide store
  beside the games tree holds accounts, memberships and sessions. This is the
  first state this project has that is not scoped to one game, and it needs to
  be, because a person outlives every game they play in.

- **One backend drives the whole deployment.** The store has an implementation
  per backend, and the backend named for the games is the one the accounts are
  kept in — `accounts.sqlite3` under SQLite, `accounts/` under YAML. There is
  no arrangement where a deployment is one thing for its games and another for
  its people. Where the store is files, they are created private to the user
  running the server, because they carry password hashes.

- **Two system accounts are created on first start.** `admin` with password
  `admin`, and `observer` with password `observer`. `admin` is player 0 of
  every game and `observer` is 1000 of every game — implicitly, with no
  membership row, because the administrator and the observer are roles a
  caller takes rather than seats a game holds.

- **A system account's password must be changed before it is used for
  anything else.** Both are created needing a change; until it is made, the
  only request either account may make is the one that makes it. A default
  credential that is never changed is the failure mode this exists to close,
  and offering the change is not the same as requiring it.

- **Players register themselves.** Anyone may create an account with a
  username and a password. `admin` and `observer` are reserved and refused,
  compared without regard to case, so that the two system accounts cannot be
  impersonated by registration.

- **A player holds a seat by membership.** The administrator registers the
  seats as they always have — `add player <number> [budget]`, before the game
  starts — and a registered account claims an unclaimed one. A seat has one
  holder. Claiming one that is taken is refused, and so is claiming a seat in
  a game that has started.

- **One account may hold several seats in one game.** Deliberately permitted,
  so that one person can play both sides to learn the game — which is the only
  way to try it without a second person, and which `game-outcome` already
  calls a sandbox. The seat stays in the request path, so two browser tabs are
  two seats.

- **A request is refused unless the account may act as that number.** Player 0
  requires the administrator; 1000 requires the observer or the administrator;
  1 to 999 requires a membership for that game and that number. The routes do
  not move: authorisation is a guard in front of them, and the number they
  already carry is what the guard checks a membership against.

- **The observer sees everything, and that is honour-based.** One shared
  account, and nothing stops a player logging into it in another tab to see
  the whole board. This is a decision, not an oversight: the game is played
  among people who would rather play it than win it. What the change owes them
  is that the bargain is stated plainly where they log in, rather than
  discovered.

- **The command-line roles prove themselves with a token.** An account may
  mint a token; `BOARD_GAME_TOKEN` or `--token` carries it, and `HttpSession`
  sends it. This keeps networked CLI play working, and it is what a script or
  one of the bots in `matches/` can use without a password in its history.

- **Local play needs no account.** Without `BOARD_GAME_SERVER` the roles open
  the game directory themselves, and there is no server to prove anything to.
  Accounts govern the HTTP tier and nothing else, so every local flow and
  every suite that drives the roles through a pipe is untouched.

- **Passwords are stored hashed and are never recoverable.** Werkzeug's
  scrypt, which arrives with Flask and costs no new dependency. An account may
  change its own password; the administrator may reset anyone's.

Not in this change: the web interface itself, a lobby endpoint or any game
registry, creating a game over HTTP, e-mail, password reset by e-mail,
password composition rules beyond a minimum length, rate limiting, account
deletion, more than one administrator, per-game administrators, TLS, or
accounts for the bots in `matches/` — which this change makes possible and
does not itself do.

## Capabilities

### New Capabilities

- `identity-and-accounts`: what an account is and where accounts live, the two
  system accounts and the password change they require before use, how a
  player registers, how a seat is claimed and given up, that one account may
  hold several seats, which account may act as which number, how a session is
  held and how a token is minted, that passwords are stored hashed, and that
  the local file flow needs none of it.

### Modified Capabilities

- `player-numbering`: an identity reached through a server is proven rather
  than asserted, and one account may hold several of a game's numbers. The
  numbers themselves, and what each is entitled to, are unchanged.

## Impact

- **Domain**: `domain/account.py` — new; what an account is, its three kinds,
  the rules a username and a password must satisfy, and the reserved names.
  Pure, and knows nothing about how an account is stored or asked for.
- **Service**: `service/accounts.py` — new; one function per use case
  (`register`, `authenticate`, `change_password`, `reset_password`,
  `mint_token`, `claim_seat`, `release_seat`, `may_act_as`), refusing by
  raising the way `service/games.py` does. `service/identity.py` is
  **unchanged**: it still answers what a number is entitled to, and the new
  layer answers only which number an account may be.
- **Storage**: `storage/account_store.py` — new port, in the shape of
  `storage/repository.py`, plus `make_account_store(backend, base_path)`,
  which is the only way one is built. `storage/sqlite_account_store.py` and
  `storage/accounts.sql` — the SQLite implementation.
  `storage/yaml_account_store.py` — the YAML one: three files under
  `accounts/`, written by replacement and created `0700`/`0600`. No change to
  `GameRepository` or to either game backend; a game's own store is not where
  a person lives.
- **HTTP**: `http/auth.py` — new; the guard, and the routes for registering,
  logging in and out, changing a password, minting a token, and claiming or
  releasing a seat. `http/app.py` — the existing routes gain the guard and
  keep their paths; `create_app` takes the account store's location and
  ensures the two system accounts exist.
- **CLI**: `cli/backend.py` — `HttpSession` sends `Authorization: Bearer` on
  every request, which is one header on the `requests.Session` it already
  holds. `cli/session.py` — `BOARD_GAME_TOKEN` beside `BOARD_GAME_SERVER`.
  The three role files gain `--token`. No change to any local path.
- **Packaging**: `pyproject.toml` — no new dependency; Werkzeug arrives with
  Flask, which is already required.
- **Docs**: `README.md` — the account model, the two default passwords and
  that they must be changed, how a player registers and joins, and
  `BOARD_GAME_TOKEN`. `MODULE_DESCRIPTION.md` — the new modules and the
  account store beside the games tree. `GAME_RULES.md` is **not** touched:
  no rule of the game changes.
