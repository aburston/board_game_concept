## Why

A browser can do the whole of an account's life: sign in with a username and a
password, be told the password must be changed, change it, and carry on. A
command line can do none of it. `--token` and `$BOARD_GAME_TOKEN` are the only
credentials a role accepts, and nothing on the command line issues a token - so
the first thing a new deployment asks its operator to do, change `admin`'s
password from `admin`, can only be done by starting `bgcapiserver` and opening
a browser at it. An operator who runs the roles against local storage, or over
SSH with no browser, is locked out of their own account store.

Authentication belongs to who is asking, not to how they reached the game.
`service/accounts.py` already states every rule once; only the HTTP tier has
been given a way to call it.

## What Changes

- Every role - `bgcserver`, `bgcclient`, `bgcobserver` - gains four account
  commands in the shared grammar: `login`, `logout`, `whoami` and `passwd`.
  They are offered by all three roles, since who you are is not a thing one
  role may ask and another may not.
- `login` takes a username and a password, reading the password without
  echoing it, and holds the token it is given for the life of the process.
  Nothing is written to disk: a role signs in each run, which is what
  `--token` and `$BOARD_GAME_TOKEN` remain for when a script needs a
  credential it does not type.
- An account that must change its password is told so and asked for a new one
  there and then, exactly as the browser does - the token it was issued is
  what it changes the password with, and the change lifts the refusal for the
  rest of the session.
- A role talking to a server with no token no longer refuses to start when
  there is a person at the terminal: it prompts for a username and a password,
  captures a forced password change if there is one, and opens the session
  with the token it was issued. With no terminal - a pipe, a script, a bot in
  `matches/` - it reports that a token is needed and exits as it does today.
- The four commands work under every access method. Over HTTP they are the
  `/sessions`, `/accounts/current` and `/accounts/current/password` routes the
  browser uses. Against local storage they are the same
  `service/accounts.py` calls, made directly against the account store under
  `$BOARD_GAME_HOME`, so the initial password can be changed with no server
  running at all.
- Playing locally still needs no account. The local file flow opens a game
  with no username, no password and no token, as it always has; the account
  commands are something a local session may do, not something it must.

## Capabilities

### New Capabilities

None. Everything here is the command line reaching rules that
`identity-and-accounts` already states.

### Modified Capabilities

- `identity-and-accounts`: what a command-line role may do about its own
  account. The requirement that a role proves itself with a token is widened
  to let it sign in for one; the requirement that the local file flow needs no
  account is narrowed to say that is true of *playing*, and that the account
  commands still work there; and requirements are added for signing in from a
  role, for capturing a forced password change from a role, and for what a
  role without a terminal does.

## Impact

- `cli/grammar.py`, `cli/parser.py`, `cli/roles.py`, `cli/help.py`,
  `cli/complete.py`: four new commands in the one grammar the three roles
  share, offered to all three roles.
- `cli/session.py`: `make_session` no longer refuses an HTTP session outright
  for want of a token when there is a terminal to ask at.
- `cli/backend.py`: a seam for the account operations beside the game seam
  `LocalSession`/`HttpSession` already draw - local calls
  `service/accounts.py` against an account store, HTTP calls the account
  routes.
- `cli/bgcserver.py`, `cli/bgcclient.py`, `cli/bgcobserver.py`: each role's
  loop handles the new command kinds.
- `service/accounts.py`, `storage/*_account_store.py`, `http/sessions.py`:
  unchanged. The rules and the routes are already there.
- A password read from a terminal must not be echoed and must not reach a
  history file, a log line or an argument list.
