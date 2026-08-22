"""The parts of an interactive session that all three roles share.

What each role does with a command differs, and so does the shape of its loop -
the server runs unattended once setup is over, the client waits for its turn,
the observer only ever reads. What they have in common is how a line becomes a
command, how a refusal is reported, and what happens when the game itself
cannot be read.
"""

import sys

from ..service.errors import GameDataError, GameError
from .parser import ParseError, parse


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


def read_command(prompt, role):
    """The next command from this role, or None if there is nothing to do.

    Blank lines, lines that are not commands, and commands this role may not
    run are all reported here and come back as None, so a caller only ever
    sees a command it is allowed to act on.
    """
    print(f"{prompt}> ", flush=True, end='')
    line = sys.stdin.readline().rstrip()
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


__all__ = ['GameError', 'load_game', 'read_command', 'report']
