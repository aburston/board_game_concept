#!/usr/bin/env python3
"""The HTTP tier's console-script entry point.

Local-only by default. A real deployment binds where its operator wants and
uses a proper WSGI server (gunicorn, uwsgi); Flask's dev server is fine for
a laptop, a club, a phone or a test.

Bound wide (`--host 0.0.0.0`), the banner gives out an address another
device on the network can reach, and draws it as a QR code on the terminal:
the host is looking at this screen the moment after typing the command, and
it is the screen a guest's phone scans. The code is here rather than on the
web page because the page does not know the server's network address any
better than this file does, and giving it one would be a route for one
screen's benefit on a page the spec holds to the shared contract.
"""

import argparse
import os
import socket
import sys
from pathlib import Path

import segno

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

# the hosts that mean "every interface". Given one of these, the banner has
# to go and find an address a guest can type, because the wildcard is not one
WILDCARDS = ('0.0.0.0', '::', '')

# the loopback addresses. Nothing off this machine can reach one, so there
# is no point drawing a code for it
LOOPBACK = ('127.0.0.1', '::1', 'localhost')

# what a UDP socket is connected to in order to learn our own address. The
# TEST-NET-3 block is reserved for documentation and never routed, so nothing
# ever answers; it only has to be somewhere the default route applies to
_SOMEWHERE_OUT_THERE = ('203.0.113.1', 9)


def reachable_address():
    """The address another machine on the network would use to reach us.

    A UDP socket `connect`ed to an address off this machine sends nothing -
    UDP has no handshake, and `connect` only asks the kernel which interface
    it would go out of - so this needs no reachability and no permission,
    and works under Termux, where a fresh install has no `ifconfig` and
    `/proc/net` is closed to apps. The socket's own address is then the one
    on the interface with the default route: on a home Wi-Fi, the one the
    guests are on.

    `None` when there is no route out at all - a phone that is the hotspot
    and has no upstream - and the banner says where to look instead.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(_SOMEWHERE_OUT_THERE)
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def addresses_to_announce(host):
    """The addresses the banner prints for a bind to `host`.

    A specific host is what to print, loopback or not: the operator named it.
    A wildcard is not an address anybody can type, so it becomes the one
    `reachable_address()` finds, or nothing when it cannot.
    """
    if host not in WILDCARDS:
        return [host]
    found = reachable_address()
    return [found] if found else []


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(prog=PROGRAM, exit_on_error=True)
    parser.add_argument('--host', default='127.0.0.1',
                        help='host to bind (default: 127.0.0.1; 0.0.0.0 to '
                             'be reached from other devices on the network)')
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
    to find out which address to give out, where it put their games, or that
    the administrator's password is the word `admin` once. Printed before the
    server binds so it is the first thing on the screen rather than buried
    under request logs.

    "Where to go" is an address a browser can reach, which is not always the
    one bound: `0.0.0.0` means every interface and is not somewhere anybody
    can type, so for a wildcard the banner finds the machine's network
    address and prints that. When the address is one another device could
    reach, it is also drawn as a QR code, so a guest scans this screen
    instead of typing.
    """
    addresses = addresses_to_announce(host)
    if addresses:
        for address in addresses:
            print(f'{PROGRAM}: {_url(address, port)}', file=sys.stderr)
    else:
        print(f'{PROGRAM}: bound to every interface on port {port}, but '
              f'could not tell which address to give out', file=sys.stderr)
        print(f'  find it under Wi-Fi or hotspot in the phone\'s settings, '
              f'or with `ip addr` on a laptop, and open '
              f'http://<that address>:{port}/', file=sys.stderr)
    store = os.path.join(base_path, 'accounts.sqlite3')
    if app.config.get('BACKEND') == 'yaml':
        store = os.path.join(base_path, 'accounts') + os.sep
    print(f'  games and accounts in {base_path}', file=sys.stderr)
    print(f'    {os.path.join(base_path, "games") + os.sep}', file=sys.stderr)
    print(f'    {store}', file=sys.stderr)
    print(f'  set ${HOME_ENV} to keep them somewhere else',
          file=sys.stderr)
    if _is_new(store):
        print('  sign in as admin / admin, or observer / observer - '
              'each must change its password before it can do anything',
              file=sys.stderr)
        print('  change it here in a browser, or with `login` at the prompt '
              'of any of bgcserver, bgcclient and bgcobserver',
              file=sys.stderr)
    print(file=sys.stderr)
    if addresses and addresses[0] not in LOOPBACK:
        if len(addresses) > 1:
            print(f'  scan to open {_url(addresses[0], port)}',
                  file=sys.stderr)
        _qr(_url(addresses[0], port))


def _url(address, port):
    """The address as a browser wants it: scheme, port and trailing slash.

    The whole thing goes into the QR code, so that a phone's camera offers
    it as a link to open rather than as text to copy.
    """
    if ':' in address and not address.startswith('['):
        address = f'[{address}]'
    return f'http://{address}:{port}/'


def _qr(url):
    """Draw `url` as a QR code on the terminal, with room around it.

    `compact=True` draws two rows of modules per line with half-block
    characters, so a `http://192.168.1.23:45678/` code is about fifteen
    lines: small enough for a phone's own terminal. The blank lines and the
    quiet zone `segno` draws are what a camera needs to find the edges.
    """
    print(file=sys.stderr)
    segno.make(url).terminal(out=sys.stderr, compact=True)
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
