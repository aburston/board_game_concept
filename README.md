# board_game_concept
Board game idea based on building and programming your own units

`GAME_RULES.md` states the rules the game plays by, in one place.

 * Create your own unit types, and deploy units built from them
 * Order each unit every turn; every player's orders resolve at once
 * Units that meet fight it out, and the last player with a unit standing wins

Not built yet: programming a unit to play itself, which the concept is named
for. Units are ordered by hand, one command at a time. See "Not built yet" in
`MODULE_DESCRIPTION.md` for the rest.
 
# server idea

 * The server runs permanently, and automatically commits whenever all the players commit
 * The players should pause after their commit and wait for the server to commit
 * Currently the server runs and waits for files to be created and written into a directory on disk by the
player client.

# web service - [TODO, none of this exists yet]
 * combine server, client and observer into different roles in the API based on login
 * create "flask" based web service that exposes all the cli based commands as a RESTful API
 * backend would still be files for now, although moving to sqlite may be a thought via a common data class

# setup

On ubuntu 24.04, `pip` and `venv` come from apt:

```
sudo apt-get install python3-pip python3.12-venv
```

Then, from the project root, create a virtualenv and install the package into
it. The install is what puts the commands below on your path, so it is not
optional:

```
python3 -m venv venv
source venv/bin/activate
pip install -e '.[dev]'
```

`-e` installs in place, so the commands run the source in `src/` rather than a
copy of it. Everything the game itself needs comes with the install; `pytest` is
the one extra the test suite wants:

```
pip install pytest
pytest                        # the whole suite, from the project root
pytest tests/test_basic.py    # or one file
```

The suite runs the installed commands when they are on your path and falls back
to the module files when they are not, so it passes either way — but
`tests/test_cli_installation.py` skips unless you have installed the package,
and that is the file that proves the commands work at all.

Legacy expect-based shell tests and `test/test.sh` have been removed; the Python
tests now cover the same behavior.

# Console scripts

Installing the package puts one command on your path per role:

  * `bgcclient <gameno> <player_number>` → runs the player client interface
  * `bgcserver -g <gameno>` → runs the game server/admin interface
  * `bgcobserver <gameno>` → runs the neutral game observer

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

