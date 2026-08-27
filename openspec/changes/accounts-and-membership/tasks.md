## 1. What an account is

- [x] 1.1 Add `domain/account.py`: an `Account` carrying a username, a password
      hash, a kind and whether it must change its password. `Kind` is
      `ADMINISTRATOR`, `OBSERVER` and `PLAYER`, and an account is exactly one
      of them. Pure — it neither stores nor hashes, so it can be tested with no
      database at all, the way `Player` and `UnitType` are.
- [x] 1.2 State the username rules there: `RESERVED = ('admin', 'observer')`,
      a `normalise(name)` that lower-cases for comparison, and a
      `refusal(name)` returning the one sentence a caller reports or `None`.
      The stored form keeps the case that was typed (design.md — "Reserved
      names are compared without regard to case").
- [x] 1.3 State the password rule there too: `MIN_PASSWORD = 8`, and a refusal
      naming the minimum. No composition rule.
- [x] 1.4 Export what the layer above needs from `domain/__init__.py`, matching
      how `Board`, `Player` and `UnitType` are exported today.
- [x] 1.5 Add `tests/test_account_domain.py`: the three kinds are distinct,
      `admin`/`Admin`/`ADMIN` are all reserved, a name differing only in case
      collides, a 7-character password is refused and an 8-character one is
      not.

## 2. The account store

- [ ] 2.1 Add `storage/accounts.sql`: `accounts` (id, username, username_key
      UNIQUE, password_hash, kind, must_change, created_at), `memberships`
      (gameno, number, account_id, claimed_at, PRIMARY KEY (gameno, number)),
      `sessions` (token PRIMARY KEY, account_id, label, expires_at). Note in a
      comment that `memberships` has **no** unique constraint on (gameno,
      account_id), and why (design.md — "One account may hold several seats").
      Verify: `sqlite3 :memory: < accounts.sql` reports no error.
- [x] 2.2 Add `storage/account_store.py` — the port, in the shape of
      `storage/repository.py`: `ensure`, `held`, `create_account`,
      `read_account`, `read_account_by_name`, `set_password`,
      `create_session`, `read_session`, `delete_session`, `claim_seat`,
      `release_seat`, `read_membership`, `seats_of_game`, `seats_of_account`.
      Docstrings say what each must guarantee; the abstract class raises.
- [x] 2.3 Add `storage/sqlite_account_store.py` implementing it, one file at
      `<base_path>/accounts.sqlite3`. SQLite only — no YAML implementation,
      because a password hash should not be sitting in a readable file
      (design.md — "Accounts live in their own store"). `ensure()` runs the
      schema and creates the two system accounts as task 2.5 describes.
- [x] 2.4 Hash with `werkzeug.security.generate_password_hash` /
      `check_password_hash`. Verify: two accounts registered with the same
      password have different stored hashes, and no stored column holds the
      password in a readable form. No change to `pyproject.toml` — Werkzeug
      arrives with Flask, which is already required.
- [x] 2.5 `ensure()` creates `admin`/`admin` (administrator kind) and
      `observer`/`observer` (observer kind), both with `must_change` set, only
      when they are absent. Verify: opening an existing store does not reset a
      password that has been changed, and does not clear `must_change` on one
      that has not.
- [x] 2.6 `claim_seat` is refused when the seat is held, by the primary key
      rather than by a read-then-write, so two simultaneous claims cannot both
      succeed. Verify against a store held open by two connections.
- [ ] 2.7 Add `tests/test_account_store.py`: an account round-trips, a seat is
      claimed once and refused the second time, one account claims two seats in
      one game, a released seat is claimable again, a session is created, read
      and deleted, and an expired session does not read back.

## 3. What a caller may ask about an account

- [ ] 3.1 Add `service/accounts.py` with one function per use case —
      `register`, `authenticate`, `change_password`, `reset_password`,
      `mint_token`, `end_token`, `claim_seat`, `release_seat`, `may_act_as` —
      each carrying it out or refusing by raising, and none of them printing or
      reading input. The shape `service/games.py` already has.
- [ ] 3.2 `may_act_as(account, gameno, number)` is the one rule: 0 needs the
      administrator kind, 1000 needs the observer or the administrator, 1 to
      999 needs a membership for that game and that number (design.md — "The
      seat stays in the path; authorisation is a guard"). It asks
      `service/identity.py` what a number *is* and never restates it.
- [ ] 3.3 `service/identity.py` is **not** changed. Verify by diff: this change
      adds no line to it.
- [ ] 3.4 `register` refuses a reserved or taken username and a short password,
      by asking `domain/account.py` rather than by testing strings itself, and
      always creates the player kind.
- [ ] 3.5 `authenticate` returns a token, and its refusal does not say whether
      the username or the password was wrong.
- [ ] 3.6 `change_password` requires the account's current password;
      `reset_password` requires the caller to be the administrator and does
      not. Both clear `must_change`.
- [ ] 3.7 `claim_seat` refuses a number the game has not registered as a
      player, a seat already held, and a game that has started — reading the
      game's own repository to answer the first and the third, and never
      writing to it. `release_seat` refuses once the game has started and
      refuses a caller that is not the holder.
- [ ] 3.8 Add `tests/test_account_service.py` covering each refusal above
      against a real store and a real game directory.

## 4. The guard over HTTP

- [ ] 4.1 Add `http/auth.py`: read the token from an `Authorization: Bearer`
      header or from the session cookie, resolve it to an account, and refuse
      with 401 when there is none or it is not accepted. One token kind, two
      carriers (design.md — "One kind of credential, carried two ways").
- [ ] 4.2 Add the `must_change` gate: an account needing a password change is
      refused with 403 on everything except the password-change route, and the
      body says the password must be changed.
- [ ] 4.3 Add the `may_act_as` guard and put it in front of every existing
      route in `http/app.py` that names a player number. **The route paths do
      not change** — `/games/<gameno>/players/<int:number>/…` stays exactly as
      it is, and the guard checks the number the path already carries.
- [ ] 4.4 Refuse with 403 and return nothing of the game: verify that a refused
      request neither builds a `Game` nor opens a repository, so a refusal
      cannot leak through an error message about game data.
- [ ] 4.5 `create_app` takes where the account store lives (defaulting beside
      the games tree) and calls `ensure()` once at startup.
- [ ] 4.6 Add `tests/test_http_auth.py`: no token is 401; a made-up token is
      401; an ended token is 401; a player asking for another seat's view is
      403 and the body carries no board; a player asking for 0 or 1000 is 403;
      the administrator asking for 1000 is allowed; an account holding a seat
      in another game is 403 here.

## 5. Registering, logging in, and passwords over HTTP

- [ ] 5.1 `POST /accounts` — register. `POST /sessions` — authenticate, set the
      cookie and return the token. `DELETE /sessions/current` — end it.
- [ ] 5.2 `POST /accounts/current/password` — change your own, giving the
      current one. `POST /accounts/<name>/password` — the administrator sets
      another's without it.
- [ ] 5.3 `POST /tokens` — mint a labelled, long-lived token for a program;
      `DELETE /tokens/<id>` — revoke it. Same `sessions` row as a login token,
      with a label and a distant expiry.
- [ ] 5.4 The response to a failed authentication does not distinguish an
      unknown username from a wrong password, and takes the same time to a
      reasonable approximation — the same scrypt work is done either way.
- [ ] 5.5 Extend `tests/test_http_auth.py`: registering a reserved name is
      refused; registering a taken name in another case is refused; a changed
      password authenticates and the old one does not; a player cannot reset
      another account; a minted token works on a game route and survives a
      logout of the login token.

## 6. Seats

- [ ] 6.1 `GET /games/<gameno>/seats` — the registered player numbers of that
      game, each with its budget and the username holding it or nothing. Any
      authenticated account may read it; it names no account's private state.
- [ ] 6.2 `POST /games/<gameno>/seats/<int:number>` — claim.
      `DELETE /games/<gameno>/seats/<int:number>` — give up.
- [ ] 6.3 Verify a claim of an unregistered number is refused and adds no
      player to the game: `add player` stays the administrator's, and claiming
      is not a way around it.
- [ ] 6.4 Add `tests/test_seats.py`: claim, double-claim refused, two seats in
      one game by one account allowed, release before the game starts, release
      after it refused, release by a non-holder refused, claim after the game
      starts refused.
- [ ] 6.5 Add `tests/test_two_seats_one_account.py` driving a whole two-seat
      game through HTTP as one account: each seat deploys its own army, each
      commits separately, the barrier waits for both, and each seat's view
      holds only what that number may see.

## 7. The command-line roles carry a token

- [ ] 7.1 `cli/session.py`: `TOKEN_ENV = 'BOARD_GAME_TOKEN'`, read beside
      `BOARD_GAME_SERVER`.
- [ ] 7.2 `cli/backend.py`: `HttpSession.__init__` takes the token and sets
      `Authorization: Bearer` on the `requests.Session` it already holds — one
      header, not a change to each call site.
- [ ] 7.3 The three role files gain `--token`, overriding the environment. A
      role talking to a server with no token reports that one is needed and
      exits with a failure status rather than opening a session.
- [ ] 7.4 A refusal from the server is reported as what it is — "that account
      may not act as player 2" — rather than as a transport error.
- [ ] 7.5 **No change to any local path.** Verify by running
      `tests/test_cli_client_surface.py`, `test_cli_server_surface.py`,
      `test_cli_observer_surface.py`, `test_full_game.py` and
      `test_cli_eof.py` unchanged and green.
- [ ] 7.6 Add `tests/test_token_cli.py`: a role with a good token plays over
      HTTP; a role with none is refused before opening a session; a role with a
      token for the wrong seat reports the server's refusal.

## 8. The suites that drive the HTTP tier

- [ ] 8.1 Add a `conftest.py` fixture that creates an account store, registers
      an account, claims a seat and returns an authenticated test client — so
      each existing suite changes by the fixture it asks for rather than by a
      rewrite (design.md — "Seven suites drive the HTTP tier and all of them
      break").
- [ ] 8.2 Move each of `test_http_api.py`, `test_client_over_http.py`,
      `test_server_over_http.py`, `test_observer_over_http.py`,
      `test_wait_over_http.py`, `test_two_player_commit.py` and
      `test_local_api_guard.py` onto it. Where a suite drives two players, it
      needs two accounts holding one seat each — which is what the two-player
      commit barrier is now testing.
- [ ] 8.3 Add to each of those suites one case that the request is refused
      without the fixture, so every HTTP surface is shown to be guarded rather
      than only the ones `test_http_auth.py` names.

## 9. The whole flow

- [ ] 9.1 Add `tests/test_accounts_end_to_end.py`: start with an empty base
      path; `ensure()` creates the two system accounts; the administrator
      authenticates with `admin`/`admin`, is refused everything, changes its
      password, then sizes a board and registers two players; two people
      register accounts and claim a seat each; both play a turn to resolution
      over HTTP; the observer authenticates, is refused until it changes its
      password, then sees both armies.
- [ ] 9.2 Verify in that test that each player's board holds only what
      `visibility` entitles them to — which is the guarantee this change exists
      to make true of the HTTP tier.
- [ ] 9.3 Run `tests/test_determinism.py` and confirm it is untouched: nothing
      added here is consulted while a turn resolves.
- [ ] 9.4 Run the whole suite against both storage backends
      (`BOARD_GAME_BACKEND=yaml` and `sqlite`), since the account store is the
      same either way and the games are not.
- [ ] 9.5 `pylint` clean, to the settings in `.pylintrc`.

## 10. Documentation

- [ ] 10.1 `README.md`: the account model in a section of its own — the two
      default passwords, that both must be changed before anything else works,
      how a player registers and claims a seat, that one account may hold
      several seats, and `BOARD_GAME_TOKEN`.
- [ ] 10.2 `README.md`: the first-run sequence, and a line that
      `accounts.sqlite3` sits beside `games/` and is worth backing up with it —
      losing it makes every game unreachable over HTTP while leaving the games
      themselves intact.
- [ ] 10.3 `README.md`: state plainly that the observer account is shared and
      sees every unit of every player, that nothing enforces the distinction,
      and that this is deliberate. Move "Authentication and TLS" out of "what's
      next" and leave TLS there, naming it as still needed for a deployment
      beyond a trusted network.
- [ ] 10.4 `MODULE_DESCRIPTION.md`: `domain/account.py`, `service/accounts.py`,
      `storage/account_store.py`, `storage/sqlite_account_store.py`,
      `http/auth.py`, and the account store beside the games tree. Correct the
      "Not built yet" line, which still says an HTTP API is not built.
- [ ] 10.5 `GAME_RULES.md` is **not** touched. Verify by diff: no rule of the
      game changes, and R8's table of what each role may type is unaffected.
- [ ] 10.6 `ARCHITECTURE_OPTIONS.md`: mark step 4 done in the status table —
      it landed before this change and the table still says "Not started" —
      and note that §5's identity sketch is what this change implements, with
      the seat kept in the path rather than removed from it.
