# board_game_concept
Board game idea based on building and programming your own units

`GAME_RULES.md` states the rules the game plays by, in one place.

 * Create your own unit types, and deploy units built from them
 * Order each unit every turn; every player's orders resolve at once
 * Units that meet fight it out, and the last player with a unit standing wins

Not built yet: programming a unit to play itself, which the concept is named
for. Units are ordered by hand, one command at a time. See "Not built yet" in
`MODULE_DESCRIPTION.md` for the rest.

# Install

From the project root:

```
python3 -m venv venv
source venv/bin/activate
pip install .
```

That's it. Every dependency comes with the install, and four console
scripts land on your `$PATH`: `bgcapiserver`, `bgcserver`, `bgcclient`,
`bgcobserver`. On Ubuntu, `sudo apt-get install python3-pip
python3.12-venv` first if you don't have them.

For working on the code, use `pip install -e '.[dev]'` — the `-e`
installs in place, `[dev]` pulls in the linter.

# Run over HTTP

The three CLI roles talk to a REST server (`bgcapiserver`); with no
`--server` and no `BOARD_GAME_SERVER` set, the roles probe for one on
`http://127.0.0.1:45678`. Naming a `--backend` or `--server` explicitly
skips the probe.

```
$ bgcapiserver &
$ export BOARD_GAME_SERVER=http://127.0.0.1:45678
$ bgcserver -g 1               # admin: sets the board, registers players
                               # commits and exits
$ bgcclient 1 1                # player 1
$ bgcclient 1 2                # player 2
$ bgcobserver 1                # observer
```

Without `BOARD_GAME_SERVER` (or `--server URL` on a role), each binary
opens the game directory itself and runs its own local flow — the CLI
behaviour that pre-dated the HTTP tier is unchanged. The storage backend
is chosen by `BOARD_GAME_BACKEND` (or `--backend`); SQLite is the
default, YAML is the readable-file alternative.

## Storage backends

Two backends behind the same `GameRepository` port:

- **SQLite** (default) — one file per game at
  `games/_<gameno>/game.sqlite3`. Real tables; `held()` is a
  transaction; `read_view` runs the visibility join. This is what a
  real deployment uses.
- **YAML** — the readable-file backend. One YAML file per thing under
  `games/_<gameno>/data/` and `games/_<gameno>/players/`. Available
  for tests (byte-diff coverage), or for an operator who wants to
  `cat` the game state. Pick with `--backend yaml` or
  `BOARD_GAME_BACKEND=yaml`.

Pick one at startup and stay with it: a game written by one backend is
not readable by the other, and there is no migration between them.

## Point budgets

Each player is registered with a point budget, which is what bounds the
army they may deploy. The administrator names it as an optional second
argument:

```
bgcserver> add player 1 150     # 150 points to spend
bgcserver> add player 2         # the default: 100
```

A budget is an integer from 1 to 1000 and is fixed for the life of the
game. A type costs the sum of its statistics — `add type Cross X 1 10
10` costs 21 — and every unit deployed from it costs that again, so a
100-point budget buys four Crosses and refuses a fifth. Defining a type
is free; deploying is what spends, and a destroyed unit is not refunded.
`show types` prints each type's `COST` and `show players` prints your
`BUDGET`, `SPENT` and `LEFT`.

A player file handed to `load player` may carry a `budget:` key; one
that leaves it out gets the default.

**A game saved before budgets existed cannot be opened.** A stored
player record with no budget is refused rather than defaulted, because
defaulting one would play the game by rules it was not set up under.
Delete the game directory and start a new one.

# The web interface

Install it and start it. That is the whole of the setup:

```
$ pip install .
$ bgcapiserver
bgcapiserver: http://127.0.0.1:45678/
  games and accounts in /home/you/games
    /home/you/games/games/
    /home/you/games/accounts.sqlite3
  set $BOARD_GAME_HOME to keep them somewhere else
  sign in as admin / admin, or observer / observer - each must change its
  password before it can do anything
```

It says where it is serving, where it put your games and accounts, and how to
get in, because a person who has just installed something should not have to
read the source to find any of that out.

## Where it keeps things

**The directory you start it in**, unless you say otherwise — `games/` and
either `accounts.sqlite3` or `accounts/` beside each other.

That is fine when you run it in a directory you keep games in, and a trap when
you don't: an installed command is run from wherever you happen to be, so
starting it somewhere else tomorrow gives you a **different, empty server**,
handing out the default passwords again. Set `$BOARD_GAME_HOME` and it stops
mattering where you were:

```
$ export BOARD_GAME_HOME=~/board-games
$ bgcapiserver
```

One setting moves games and accounts together — a deployment with its games in
one place and its people in another would be worse than either. `--base-path`
overrides both.

One page, and it is a client of the same JSON API the command-line roles use
— there is no route that exists only for the browser. Sign in, take a seat
from the lobby, design your units, and play.

**No build step and no package manager.** Everything under
`src/board_game_concept/http/static/` is a plain file served as it was
written: the board is one `<svg>` and a unit moves by a change of `transform`,
so the animation is a CSS transition rather than a library. The repository
stays one language with one toolchain.

The interface shows three things the command line leaves you to find out the
hard way: what a move will cost before you commit it, that a unit given no
order recovers a point (so holding is a choice, not an empty row), and that an
enemy vanishing from your board is contact lost rather than a defect.

It is playable from the keyboard: arrow keys move about the board, `Enter`
selects the unit under the cursor, an arrow key then orders it that way, and
`c` commits.

## Serving it properly

`bgcapiserver` runs Flask's development server, which is fine for a laptop or
a club and not for anything else. Each player waiting for a turn holds a
server thread for the length of the long-poll budget, so a host serving more
than a few people wants `gunicorn` or `uwsgi` in front of the same app — and
TLS, as below.

# Accounts

The three CLI roles talk to a game by naming a number. A **server** does not
take anybody's word for it: over HTTP an account signs in, and what it may do
is decided by which seats it holds.

An account is who somebody is; a seat is which player number they hold in
which game. The numbers themselves are unchanged — 0 is still the
administrator, 1 to 999 the players, 1000 the observer — and what each is
entitled to is unchanged too. What changed is that a number now has to be
proved rather than asserted.

Accounts live beside the `games/` tree rather than inside any game, because a
person outlives every game they play in. **They are kept in the same backend
the games are**, chosen by the same `--backend` or `BOARD_GAME_BACKEND`: a
SQLite deployment keeps them in `accounts.sqlite3`, a YAML one in three files
under `accounts/`. A deployment is one thing or the other; there is no mixture.

Under the YAML backend the password hashes are in a readable file. They are
scrypt and are not reversible, but a file walks off more easily than a table
does, so `accounts/` is created `0700` and its files `0600` — keep them that
way, or run the SQLite backend, which is the default.

## First run

```
$ bgcapiserver &                  # creates accounts.sqlite3 if it is absent
```

The store is created with two accounts: **`admin`** with the password
`admin`, and **`observer`** with the password `observer`. **Both must change
their password before they can do anything else** — until they do, every
request is refused except the one that changes it. That is the whole point of
shipping with a known password: it is a way in, once.

```
# sign in, and change the password the account was created with
$ curl -s -X POST localhost:45678/sessions     -H 'Content-Type: application/json'     -d '{"username":"admin","password":"admin"}'
{"kind":"admin","must_change_password":true,"token":"...","username":"admin"}

$ curl -s -X POST localhost:45678/accounts/current/password     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json'     -d '{"current":"admin","new":"something-better"}'
```

A password is at least 8 characters and nothing else is required of it. The
administrator can set anybody's password without knowing it
(`POST /accounts/<name>/password`); an account changes its own by giving the
one it has now.

## Joining a game

The administrator sets a game up as it always did — `set board`, then
`add player <number> [budget]` for each seat. Anyone else registers an
account and takes an open seat:

```
$ curl -s -X POST localhost:45678/accounts     -d '{"username":"ada","password":"secret12"}' -H 'Content-Type: application/json'
$ curl -s localhost:45678/games/1/seats -H "Authorization: Bearer $TOKEN"
$ curl -s -X POST localhost:45678/games/1/seats/2 -H "Authorization: Bearer $TOKEN"
```

`admin` and `observer` are reserved and cannot be registered, in any case.

A seat can be taken until a turn of that game has resolved — so a game that
has been set up but not yet played is still joinable, which is when somebody
looking for a game to join would arrive. It can be given up in that same
window and not after.

**One account may hold several seats in one game.** That is deliberate: it is
how one person plays both sides to try the game out without needing a second
person. Each seat stays a separate identity — its own army, its own orders,
its own view, and its own place at the commit barrier — so holding both is no
way round the fog of war. Because a seat is not implied by the account, it
stays in the address: `/games/1/players/2/...` is seat 2, and two browser tabs
can be two seats.

## Playing over HTTP from the command line

A role talking to a server carries a token. Mint one with `POST /tokens` and
give it to the role:

```
$ export BOARD_GAME_SERVER=http://127.0.0.1:45678
$ export BOARD_GAME_TOKEN=...        # or bgcclient --token ...
$ bgcclient 1 2
```

A role started against a server with no token says so and exits rather than
opening a session it cannot act through. A token is also what a script or a
bot uses, since it keeps a password out of a shell history.

**Playing locally needs no account at all.** Without `BOARD_GAME_SERVER` the
roles open the game directory themselves, and there is no server to prove
anything to.

## What the observer sees

The observer account sees **every unit of every player**, on every game —
that is what the rules grant the observer, and it is what makes watching a
game worth doing.

It is one shared account, and **nothing stops somebody who holds a seat in a
game from also signing in as the observer to see the whole board**. That is
deliberate rather than an oversight: the enforcement that would work costs
live spectating, and this is a game played among people who would rather play
it than win it. Change the observer password to whatever your group is
comfortable sharing, and tell people what it shows.

## Keeping it

The account store — `accounts.sqlite3` or `accounts/`, depending on the
backend — sits beside `games/` and is worth backing up with it. Losing it
makes every game unreachable over HTTP while leaving the games themselves
perfectly intact — a membership names a seat rather than being part of one —
so the recovery is to recreate the accounts and claim the seats again.

## Web service - what's next
 * TLS. Tokens and passwords cross the wire in clear, and `bgcapiserver`
   binds `127.0.0.1` by default. Anything reachable beyond a trusted network
   wants TLS in front of it, and a real WSGI server rather than Flask's
   development one.

# Working on the code

For an editable install (the commands run the source in `src/` rather than
a copy of it) plus the linter used in CI:

```
pip install -e '.[dev]'
```

The test suite wants `pytest`:

```
pip install pytest
pytest                          # whole suite (YAML backend by default)
BOARD_GAME_BACKEND=sqlite pytest   # same suite over SQLite
pytest tests/test_basic.py      # or one file
```

The suite runs the installed commands when they are on your path and falls
back to the module files when they are not, so it passes either way — but
`tests/test_cli_installation.py` skips unless you have installed the package,
and that is the file that proves the commands work at all.

**Install editable, not plain, while you are working.** A `pip install .`
copies the source into `site-packages`, and the suites that drive the roles
as subprocesses — `tests/test_cli_*_surface.py` and
`tests/test_server_client_integration.py` — then run that copy rather than
what you have just edited. They go green against the code you replaced, which
looks exactly like passing. `pip install -e` points them at `src/`.

# Console scripts

Installing the package puts one command on your path per role:

  * `bgcclient <gameno> <player_number>` → runs the player client interface
  * `bgcserver -g <gameno>` → runs the game server/admin interface
  * `bgcobserver <gameno>` → runs the neutral game observer

The three roles are three identities: 0 is the administrator, 1 to 999
are the players, and 1000 is the observer. `bgcclient` takes a player's
number and refuses one outside that range.

Each resolves a game against the directory you run it in, as `games/_<gameno>`.

Inside a session, `show board`, `show types`, `show units`, `show players` and
`show pending` print tables. Ending the command in `json` — `show units json` —
prints the same thing as one JSON document instead, so a session can be driven
by something other than a person:

```
bgcclient> show units
PLAYER  NAME  TYPE   SYMBOL  ATTACK  HEALTH  ENERGY  X  Y  STATE    DIRECTION
     1  x1    Cross  X            1       1      10  0  0  holding  -
```

# Completion

Inside a session, Tab completes what can be typed next. That is the commands
the role you are running accepts, the `show` subjects it may ask for, the
trailing `json`, the four directions — and the names only the game knows: your
own units for `move`, and the types you have defined for `add unit`. A unit you
deployed a moment ago completes without a reload. `load board` and `load
player` complete paths.

You get line editing and within-session history with it: arrow keys, Ctrl-A,
and up-arrow to recall what you typed before.

None of this happens when a session's input is not a terminal. Driven by a pipe
or a file — which is how the test suite drives every role — a session prompts
and answers exactly as it always has, with no editing and nothing but its own
output in the transcript.

For completing the commands themselves, source the script for your shell:

```
source completions/bgc.bash            # bash
source completions/bgc.zsh             # zsh, after compinit
```

Then `bgcclient <TAB>` offers the game numbers under `games/`, a second `<TAB>`
offers the players registered in that game, and `bgcserver -g <TAB>` offers
game numbers. They are files to source; installing the package still puts three
commands on your path and nothing else.

The standalone test harness has no command of its own — it is developer tooling
rather than something an installed game needs, so run it as a module:

```
python -m board_game_concept.test_suite
```

# TODO

  * add and `initgame.py` script to do the initial setup of the game, strip that    out of the server
  * separate all the DB storage out of the `GameData.py` class and rename,
    create dedicated objects for data returned from the DB.

  
Note to check my clone... -R

