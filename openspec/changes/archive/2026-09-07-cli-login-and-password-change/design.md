## Context

See proposal.md - Why. What matters for the approach is the shape already in
the code:

- `service/accounts.py` states every account rule once - registering, signing
  in, changing a password, the `must_change` gate - and takes an
  `AccountStore` as its first argument. It knows nothing of HTTP.
- `http/sessions.py` is a thin skin over those calls: `/sessions`,
  `/sessions/current`, `/accounts/current`, `/accounts/current/password`.
  `storage/account_store.py:make_account_store(backend, base_path)` opens the
  store the same calls need locally, and `ensure()` is what creates `admin`
  and `observer`.
- `cli/backend.py` already draws a seam for *the game*: `Session` names the
  operations, `LocalSession` opens a repository in process, `HttpSession`
  fetches. `cli/session.py:make_session` decides which of the two a role
  gets, and today refuses outright when an HTTP session has no token.
- `cli/grammar.py` describes the language once; `parser.py`, `help.py` and
  `complete.py` are all held to that description, and `roles.py` says which
  parts of it each role may use.

So the work is a second seam of the same shape, and four more entries in the
one grammar. Nothing below the command line changes.

## Goals / Non-Goals

**Goals:**

- One set of account operations with two implementations, chosen by the same
  fact that chooses the game session, so the command line cannot answer
  differently from the browser.
- A password never in argv, never in the history file, never echoed.
- A forced password change captured wherever an account signs in.

**Non-Goals:**

- Registering an account from the command line. The routes exist and a
  browser uses them; adding a fifth command is a separate ask, and every
  account a command line needs to reach today already exists.
- The administrator resetting *another* account's password (`reset_password`).
  Same reason.
- Minting, listing and revoking long-lived tokens from the command line. The
  `/tokens` routes stay browser-only for now; `--token` and
  `$BOARD_GAME_TOKEN` are how a script carries one.
- Keeping a token between runs. Explicitly rejected below.
- Any change to `service/`, `storage/` or `http/`.

## Decisions

### An accounts seam beside the session seam

A new `cli/accounts.py` holds `Accounts`, naming four operations -
`sign_in(username, password)`, `sign_out()`, `whoami()`,
`change_password(current, new)` - with two implementations:

- `LocalAccounts(backend, base_path)` opens a store with
  `make_account_store(...)`, calls `ensure()` the first time it is asked for
  anything, and then calls `service/accounts.py` directly.
- `HttpAccounts(url)` posts to the same four routes the browser uses.

*Why not put them on `Session`?* Because a session is a game and these are
not. A role that has not opened a game at all still has an account, and
`Session`'s contract is already the thing this change must not disturb.

*Why not always go over HTTP?* Because the local flow must work with no
server running - that is the requirement that makes the initial password
changeable at all - and because a local role reaching a server would be the
opposite of what `make_session`'s probe exists to prevent.

Which implementation a role gets follows how it reached its game: an
`HttpSession` means `HttpAccounts` against the same URL, a `LocalSession`
means `LocalAccounts` against the same backend and base path. One decision,
made once, so the access method of the game and the access method of the
account can never disagree.

### `ensure()` is called lazily, not at start-up

`LocalAccounts` opens nothing until the session asks for an account
operation. This is what keeps `The account store is not needed locally` true:
a role that plays a game locally and is never asked to sign in creates no
store. A role that *is* asked creates one, holding `admin` and `observer`,
which is how the initial password becomes changeable on a machine that has
never run a server.

### The token lives in the process, and is handed to the session

`sign_in` returns the account and the token. For an HTTP session the token
has to reach the requests: `HttpSession` gains a setter for the bearer token
it sends, and a `login` at the prompt replaces the one the session was opened
with. For a local session the token identifies nobody to anything - local
play needs no account - so it is held only so that `whoami`, `passwd` and
`logout` have something to act on.

*Alternative rejected:* a credentials file (`~/.config/...` or under
`$BOARD_GAME_HOME`). It is what most tools do, and it is more convenient. It
was rejected because it puts a bearer token on disk with a lifetime nobody
sees, needs file modes, expiry handling and an invalidation story of its own,
and none of it is needed for the problem in the proposal. `--token` and
`$BOARD_GAME_TOKEN` already carry a credential for anything unattended.

### Start-up: prompt only where there is a terminal

`cli/session.py:_http_session` is the one place that refuses for want of a
token. It gains a branch: where `sys.stdin` and `sys.stdout` are both
terminals - the same test `_read_line` already uses to decide whether there
is a person there - it prompts for a username and a password, signs in
through `HttpAccounts`, captures a forced password change, and opens the
session with the token it was issued. Where either is not a terminal it
reports and exits exactly as it does today, so every existing script, test
and bot in `matches/` is unaffected.

The sign-in happens before the session is built, because the session's first
request needs a token that works.

### Four commands in the one grammar

`login [<username>]`, `logout`, `whoami` and `passwd` are added to
`grammar.py` as usages, to `parser.py` as verbs, to `service/commands.py` as
nodes, and to all three roles in `roles.py`. `help` and completion follow from
the grammar without being touched, which is the point of that file.

The username is an optional argument; the password is never an argument, in
any position. A command line is a public thing - a history file, a process
listing - and a password in one is a password leaked.

Handling is shared rather than repeated: one `handle_account_command(command,
accounts)` in `cli/accounts.py`, called from each role's loop with the same
three lines. Three roles, one behaviour, no chance of drift.

### Reading a password

`getpass.getpass()`. It reads from the terminal without echoing and without
going through `readline`, so nothing typed at it reaches the history the
completion machinery installed. The username is read with the ordinary
prompt.

`passwd` asks for the current password, then the new one twice. In the forced
change straight after a sign-in the current password is the one just typed,
so only the new one is asked for - which is the flow the browser presents and
the one an operator meets on their first ever run.

### A refusal is reported, not fatal

Every account command reports and returns to the prompt, the way a refused
game command does. The one place a refusal still ends the process is a
start-up sign-in that fails, because a role that cannot prove itself has no
session to offer - which is what it does today with a bad token.

## Risks / Trade-offs

- [A local session's `login` is a token that identifies nobody] → Stated
  plainly in the message: locally, signing in is for reading and changing an
  account, not for playing, and playing needs no account either way.
- [Signing in at a prompt each run is less convenient than a saved token] →
  Accepted deliberately (see the decision above). `--token` and
  `$BOARD_GAME_TOKEN` are unchanged for anything that runs unattended.
- [Prompting at start-up changes what a role does with no token] → Only where
  both stdin and stdout are terminals. Anything redirected, piped or run by a
  test behaves exactly as it does today, and that is the case the existing
  scenario covers.
- [A password could reach the history file through the wrong read] → One
  reader, `getpass`, used everywhere a password is read, and a test that no
  role accepts a password-shaped argument.
- [The account store could be created where nobody expected one] → Only when
  an account command is actually used locally, and it is created at
  `$BOARD_GAME_HOME` (or the working directory), which is where a server
  would have created it. The message says where it went.
- [YAML and SQLite must answer alike] → They already must
  (`identity-and-accounts`: The two backends behave alike). The command-line
  tests run under both, as the rest of the CLI tests do.

## Migration Plan

Nothing to migrate. Existing tokens, existing account stores and existing
scripts keep working; the change only adds ways to get a token and to change
a password.
