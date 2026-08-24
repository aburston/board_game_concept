"""The parts of an interactive session that all three roles share.

What each role does with a command differs, and so does the shape of its loop -
the server runs unattended once setup is over, the client waits for its turn,
the observer only ever reads. What they have in common is how a line becomes a
command, how a refusal is reported, and what happens when the game itself
cannot be read.
"""

import os
import sys

from .. import YamlGameRepository
from ..service import commands
from ..service.errors import GameDataError, GameError
from ..storage.sqlite_repository import SqliteGameRepository
from .backend import HttpSession, LocalSession
from .parser import ParseError, parse


# the compiled-in default is SQLite. `BOARD_GAME_BACKEND` overrides it so
# the test suite can run the roles under either backend without every test
# having to pass `--backend` through its subprocess call
BACKEND_ENV = 'BOARD_GAME_BACKEND'
COMPILED_DEFAULT_BACKEND = 'sqlite'


def default_backend():
    return os.environ.get(BACKEND_ENV, COMPILED_DEFAULT_BACKEND)


def make_repository(gameno, backend=None, base_path=None):
    """Which backend a role puts behind its `LocalSession`.

    The three CLI binaries call this rather than picking a class themselves,
    so a `--backend` argument added here reaches them without three edits.
    Default is SQLite; a caller who wants the YAML directory layout asks
    for it by name (or through the `BOARD_GAME_BACKEND` env var).

    `base_path` names the directory `games/` lives under; the CLI binaries
    let it default to the process working directory, and the HTTP tier
    passes the base path it was configured for.
    """
    if backend is None:
        backend = default_backend()
    if backend == 'sqlite':
        return SqliteGameRepository(gameno, base_path=base_path)
    if backend == 'yaml':
        return YamlGameRepository(gameno, base_path=base_path)
    raise ValueError(f"unknown backend: {backend}")


def add_backend_argument(parser):
    """Add `--backend {sqlite,yaml}` to a role's parser.

    The default is what `default_backend()` returns - `sqlite`, unless the
    `BOARD_GAME_BACKEND` env var says otherwise. That is how the test suite
    runs the roles under YAML while the compiled-in default is SQLite.
    """
    parser.add_argument(
        '--backend', choices=('sqlite', 'yaml'), default=None,
        help="which storage backend to use "
             f"(default: {COMPILED_DEFAULT_BACKEND}, "
             f"or ${BACKEND_ENV} when set)")


SERVER_ENV = 'BOARD_GAME_SERVER'

# where the local API server is expected to be, when the caller did not
# name one explicitly. The guard in `make_session` probes this URL for a
# live `bgcapiserver` before falling back to local storage; if a caller
# genuinely wants local mode while an API server is up they set
# `BOARD_GAME_NO_REDIRECT` to skip the probe
LOCAL_API_URL = 'http://127.0.0.1:8080'
LOCAL_API_ENV = 'BOARD_GAME_LOCAL_API'
NO_REDIRECT_ENV = 'BOARD_GAME_NO_REDIRECT'
_PROBE_TIMEOUT = 0.5


def default_server():
    return os.environ.get(SERVER_ENV)


def probe_local_api(url=None):
    """The URL of a live `bgcapiserver` on this host, or None.

    Hits `/_/health` with a short timeout and checks the JSON body
    (`{"ok": true}`). Returns the URL if the check passes, None
    otherwise. Anything else running on the port fails the JSON check
    and does not fool the guard.
    """
    if os.environ.get(NO_REDIRECT_ENV):
        return None
    if url is None:
        url = os.environ.get(LOCAL_API_ENV, LOCAL_API_URL)
    # imported inside so `requests` is not a hard requirement for a
    # process that never uses HTTP
    import requests
    try:
        response = requests.get(
            f'{url.rstrip("/")}/_/health', timeout=_PROBE_TIMEOUT)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict) or body.get('ok') is not True:
        return None
    return url


def add_server_argument(parser):
    """Add `--server URL` (default: none) to a role's parser.

    When set, the role goes over HTTP against the URL rather than reaching
    into a local game directory. `BOARD_GAME_SERVER` env var is the
    fallback so a test that has spun up a Flask thread can point every
    subprocess at it without touching argv.
    """
    parser.add_argument(
        '--server', default=None,
        help=f"URL of the game server, e.g. http://127.0.0.1:8080 "
             f"(overrides ${SERVER_ENV}); when unset the role uses local "
             f"storage")


def make_session(gameno, player_number, server=None, backend=None,
                 base_path=None):
    """Which session backend a role puts behind its REPL.

    Anything the caller named explicitly wins over the guard: `--server`
    or `BOARD_GAME_SERVER` picks HTTP; `--backend` or
    `BOARD_GAME_BACKEND` picks local with that backend. The guard only
    fires when the caller named nothing - then a probe checks whether
    `bgcapiserver` is running here, redirects to it if so (with a
    warning to stderr), and falls back to local storage otherwise.

    Two processes writing the same storage would step on each other's
    holds; the guard is what prevents a caller from opening a game
    file that a running API server is already serving.

    `BOARD_GAME_NO_REDIRECT=1` skips the probe unconditionally.
    """
    if server is not None or default_server():
        # explicit HTTP: use whichever URL the caller named
        return HttpSession(server or default_server(),
                           gameno, player_number)
    if backend is not None or os.environ.get(BACKEND_ENV):
        # explicit local: the caller told us which backend, no probe
        return LocalSession(
            make_repository(gameno, backend=backend, base_path=base_path),
            player_number)
    # neither named: probe for a running API server before touching the
    # local files
    probed = probe_local_api()
    if probed is not None:
        print(
            f"warning: `bgcapiserver` is running at {probed}; "
            f"using HTTP instead of local storage. Set "
            f"${NO_REDIRECT_ENV}=1 to override.",
            file=sys.stderr)
        return HttpSession(probed, gameno, player_number)
    return LocalSession(
        make_repository(gameno, backend=backend, base_path=base_path),
        player_number)


def load_game(data):
    """Read the game, or report why it cannot be read and stop.

    A session that cannot open its game has nothing to offer, so this is the
    one place a role still exits. The service layer raises; only here does
    anything die of it.
    """
    try:
        data.load()
    except GameDataError as error:
        for line in error.lines():
            print(line, file=sys.stderr)
        sys.exit(1)


def _read_line(prompt):
    """One line of input, and whether there was one at all.

    Two ways of reading, because there are two kinds of caller. A person gets
    `input()`, which is the only call `readline` decorates - line editing,
    history and the completion `complete.py` installed all hang off it. Anything
    else gets the prompt and `sys.stdin.readline()` it has always got, so a
    session driven by a pipe or a file reads exactly as it did before
    completion existed and its transcript holds no terminal escape sequence.

    Both conditions are checked before taking the first path: `readline` draws
    the prompt and its edits on stdout, so a terminal on stdin with a pipe on
    stdout is not a person and must take the plain path.

    End of input is the case the two disagree about - `input()` raises
    `EOFError`, `sys.stdin.readline()` returns the empty string - and both mean
    the same thing here, which is `exit`. Stripping made the empty string and a
    blank line the same, and a role reading from a pipe that had run dry was
    told there was nothing to do, and prompted again, forever.
    """
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            return input(f"{prompt}> "), True
        except EOFError:
            return None, False
    print(f"{prompt}> ", flush=True, end='')
    line = sys.stdin.readline()
    if line == '':
        return None, False
    return line, True


def read_command(prompt, role):
    """The next command from this role, or None if there is nothing to do.

    Blank lines, lines that are not commands, and commands this role may not
    run are all reported here and come back as None, so a caller only ever
    sees a command it is allowed to act on.

    Running out of input comes back as `exit`, which every role already ends
    on.
    """
    line, read = _read_line(prompt)
    if not read:
        # the prompt has already been written, so leave the cursor on a line of
        # its own the way a terminal does for Ctrl-D
        print()
        return commands.Exit()
    line = line.rstrip()
    try:
        command = parse(line)
    except ParseError as error:
        print(error.message)
        return None
    if command is None:
        return None
    if not role.allows(command):
        print(role.refusal(command))
        return None
    return command


def report(error):
    """Say why a command was refused."""
    for line in error.lines():
        print(line)


__all__ = ['COMPILED_DEFAULT_BACKEND', 'GameError', 'add_backend_argument',
           'add_server_argument', 'default_backend', 'default_server',
           'describe_outcome', 'load_game', 'make_repository',
           'make_session', 'read_command', 'report']


def describe_outcome(outcome):
    """How the game ended, as one line for whoever is watching."""
    if outcome.get('winner') is None:
        return f"game over: a draw on turn {outcome['turn']}"
    return (f"game over: player {outcome['winner']} wins "
            f"on turn {outcome['turn']}")
