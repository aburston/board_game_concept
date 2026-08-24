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

from board_game_concept.http.app import create_app


PROGRAM = 'bgcapiserver'


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(prog=PROGRAM, exit_on_error=True)
    parser.add_argument('--host', default='127.0.0.1',
                        help='host to bind (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080,
                        help='port to bind (default: 8080)')
    parser.add_argument('--base-path', default=os.getcwd(),
                        help='where the `games/` tree lives '
                             '(default: current directory)')
    parser.add_argument('--backend', choices=('sqlite', 'yaml'), default=None,
                        help='which storage backend to serve '
                             '(default: sqlite, or $BOARD_GAME_BACKEND)')
    args = parser.parse_args(argv[1:])

    app = create_app(base_path=args.base_path, backend=args.backend)
    app.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main(sys.argv)
