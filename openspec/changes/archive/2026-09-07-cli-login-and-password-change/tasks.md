## 1. The accounts seam

- [x] 1.1 Add `cli/accounts.py` with an `Accounts` base class naming
      `sign_in(username, password)`, `sign_out()`, `whoami()` and
      `change_password(current, new)`, each raising `NotImplementedError`, in
      the shape `cli/backend.py:Session` has; verify with a unit test that the
      base class refuses every operation.
- [x] 1.2 Implement `LocalAccounts(backend, base_path)`: open the store with
      `storage/account_store.make_account_store`, call `ensure()` the first
      time an operation is asked for and not before, and answer each operation
      by calling `service/accounts.py`; verify with a test that signing in
      against a temporary base path returns the account and a token, and that
      constructing it and never using it creates no store on disk.
- [x] 1.3 Implement `HttpAccounts(url)` over `POST /sessions`,
      `DELETE /sessions/current`, `GET /accounts/current` and
      `POST /accounts/current/password`, raising the same
      `service/errors.py` types a local refusal raises; verify against a live
      app fixture that a wrong password, a short new password and a
      `must_change` account produce the same error types as `LocalAccounts`.
- [x] 1.4 Add `make_accounts(session, ...)` in `cli/session.py` returning
      `HttpAccounts` for an `HttpSession` and `LocalAccounts` for a
      `LocalSession`, with the same URL, backend and base path the session was
      built with; verify with a test that each session kind yields the
      matching implementation.

## 2. Reading credentials

- [x] 2.1 Add credential prompts in `cli/accounts.py`: a username read with
      the ordinary prompt and a password read with `getpass.getpass()`, plus a
      new-password prompt that asks twice and refuses a mismatch; verify with
      a test that patches the reader and asserts the password prompt never
      goes through `input()`.
- [x] 2.2 Add a test asserting no role accepts a password as a command-line
      argument, and that a password typed at a prompt is not added to the
      `readline` history.

## 3. The four commands in the grammar

- [x] 3.1 Add `Login`, `Logout`, `Whoami` and `ChangePassword` nodes to
      `service/commands.py`, with `login` carrying an optional username and no
      node carrying a password; verify with a unit test of each node's fields.
- [x] 3.2 Add the usages `login [<username>]`, `logout`, `whoami` and `passwd`
      to `cli/grammar.py` and the matching verbs to `cli/parser.py`; verify
      `tests/test_grammar.py` passes, including its check that every usage
      parses as the command it names.
- [x] 3.3 Offer all four commands in `SERVER`, `CLIENT` and `OBSERVER` in
      `cli/roles.py`; verify with a test that each role allows each of the four
      and that `help` lists them for all three.

## 4. Handling the commands

- [x] 4.1 Add `handle_account_command(command, accounts)` to `cli/accounts.py`
      carrying out sign-in, sign-out, whoami and password change, reporting a
      refusal and returning to the prompt rather than exiting; verify with unit
      tests over a fake `Accounts` covering success and each refusal.
- [x] 4.2 Capture the forced change inside `handle_account_command`: a sign-in
      as an account whose password must change says so, asks for a new
      password using the one just typed as the current, and reports what
      happens when the caller gives none; verify with a test that a session
      signing in as `admin`/`admin` and giving a new password is afterwards
      answered, and one that declines is refused with the must-change message.
- [x] 4.3 Call the handler from `bgcserver.py`, `bgcclient.py` and
      `bgcobserver.py` before each loop's own dispatch, and give an
      `HttpSession` the token a `login` returned; verify with a CLI harness
      test per role that `login`, `whoami`, `passwd` and `logout` work at each
      role's prompt.

## 5. Start-up sign-in against a server

- [x] 5.1 Change `cli/session.py:_http_session` so that with no token, and
      with both stdin and stdout terminals, it prompts for a username and
      password, captures a forced password change, and opens the session with
      the token it was issued; verify with a test driving a pseudo-terminal
      that a role with no token opens a session after signing in.
- [x] 5.2 Keep the no-terminal path exactly as it is - report that a token is
      needed and exit with a failure status without opening a session; verify
      the existing test for that scenario still passes unchanged.
- [x] 5.3 Verify with a test that a start-up sign-in for a number the account
      may not act as reports the server's refusal and does not open a session.

## 6. Every access method answers the same

- [x] 6.1 Add an end-to-end test that changes a password at a command line
      against local storage with no server running, then signs in over HTTP
      with the new password and finds the old one refused.
- [x] 6.2 Add the mirror test: change the password over HTTP, then sign in at
      a command line with the new one and confirm no change is asked for.
- [x] 6.3 Run the command-line account tests under both the SQLite and the
      YAML backend, as the rest of the CLI tests are run, and verify the
      refusals and messages are identical under each.

## 7. Documentation and coverage

- [x] 7.1 Document the four commands and the start-up sign-in in `README.md`
      where the roles and `--token` are documented, and say that a password is
      never a command-line argument; verify by reading the section back
      against the delta spec.
- [x] 7.2 Update `bgcapiserver`'s first-run message so it says the initial
      password can also be changed from any role's prompt, not only in a
      browser; verify by running it against a fresh base path.
- [x] 7.3 Update `SPEC_COVERAGE.md` for the `identity-and-accounts`
      requirements this change adds and modifies; verify `openspec validate
      cli-login-and-password-change --strict` passes and the coverage table
      names the new scenarios.
