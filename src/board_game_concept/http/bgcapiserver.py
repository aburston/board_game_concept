#!/usr/bin/env python3
"""The HTTP tier's console-script entry point.

Local-only by default. A real deployment binds where its operator wants and
uses a proper WSGI server (gunicorn, uwsgi); Flask's dev server is fine for
a laptop or a test.
"""

import argparse
import os
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept.cli.session import HOME_ENV, default_base_path
from board_game_concept.http.app import create_app


PROGRAM = 'bgcapiserver'

# where the server binds when its operator does not say. The same
# number `cli/session.py` probes for a running server on: a role that
# looked somewhere else would open the game files a server is already
# serving, which is the collision the probe exists to prevent
DEFAULT_PORT = 45678


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(prog=PROGRAM, exit_on_error=True)
    parser.add_argument('--host', default='127.0.0.1',
                        help='host to bind (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'port to bind '
                             f'(default: {DEFAULT_PORT})')
    parser.add_argument('--base-path', default=None,
                        help=f'where `games/` and the account store live '
                             f'(default: ${HOME_ENV}, or the current '
                             f'directory)')
    parser.add_argument('--backend', choices=('sqlite', 'yaml'), default=None,
                        help='which storage backend to serve '
                             '(default: sqlite, or $BOARD_GAME_BACKEND)')
    args = parser.parse_args(argv[1:])

    base_path = args.base_path or default_base_path()
    app = create_app(base_path=base_path, backend=args.backend)
    _announce(app, base_path, args.host, args.port)
    app.run(host=args.host, port=args.port)


def _announce(app, base_path, host, port):
    """Say where to go, where the state is, and how to get in.

    Somebody who has just installed this should not have to read the source
    to find out which port it took, where it put their games, or that the
    administrator's password is the word `admin` once. Printed before the
    server binds so it is the first thing on the screen rather than buried
    under request logs.
    """
    store = os.path.join(base_path, 'accounts.sqlite3')
    if app.config.get('BACKEND') == 'yaml':
        store = os.path.join(base_path, 'accounts') + os.sep
    print(f'{PROGRAM}: http://{host}:{port}/', file=sys.stderr)
    print(f'  games and accounts in {base_path}', file=sys.stderr)
    print(f'    {os.path.join(base_path, "games") + os.sep}', file=sys.stderr)
    print(f'    {store}', file=sys.stderr)
    print(f'  set ${HOME_ENV} to keep them somewhere else',
          file=sys.stderr)
    if _is_new(store):
        print('  sign in as admin / admin, or observer / observer - '
              'each must change its password before it can do anything',
              file=sys.stderr)
    print(file=sys.stderr)


def _is_new(store):
    """Whether this looks like a store nobody has signed into yet."""
    try:
        return os.path.getsize(store) < 100_000 if os.path.isfile(store) \
            else True
    except OSError:
        return True


if __name__ == '__main__':
    main(sys.argv)
