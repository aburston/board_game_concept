#!/usr/bin/env python3

import sys
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept.cli import complete, roles
from board_game_concept.cli.backend import LocalSession
from board_game_concept.service import identity
from board_game_concept.cli.show import perform_show
from board_game_concept.cli.help import print_help
from board_game_concept.cli.session import (describe_outcome, load_game,
                                            make_repository, read_command)

ROLE = roles.OBSERVER

# what this role calls itself, wherever it was launched from. The prompt and
# the usage both come from here rather than from `argv[0]`, which is the path
# the process happened to be started by
PROGRAM = 'bgcobserver'

DEBUG = False


def usage():
    print(f"usage, {PROGRAM} <gameno>", file=sys.stderr)


def main(argv=None):
    # the console script entry point calls this with nothing, so fall back to
    # the process arguments
    if argv is None:
        argv = sys.argv

    if DEBUG:
        print(f"len(argv): {len(argv)}")

    if len(argv) == 2:
        # the observer is its own identity, not the administrator's. Both are
        # entitled to the whole game and only one may change it, which nothing
        # below the command line could tell while they shared a number
        player_number = identity.OBSERVER
        gameno = argv[1]
    else:
        usage()
        sys.exit(1)

    # a session hides how the game is reached. Today it is in-process; a
    # later change swaps LocalSession for an HTTP-backed one and the rest
    # of this file does not notice
    data = LocalSession(make_repository(gameno), player_number)

    # the observer completes what it may run, which is the reading half of the
    # grammar; `roles.OBSERVER` is what decides that, here as everywhere else
    complete.install(ROLE, complete.GameNames(data, player_number))

    while True:

        # load the gamedata
        load_game(data)

        outcome = data.getOutcome()
        if outcome is not None:
            print(describe_outcome(outcome))
        else:
            print(f"turn: {data.getTurnNumber()}")

        # interactive mode
        while True:
            # the observer watches; read_command refuses it everything
            # that writes
            command = read_command(PROGRAM, ROLE)
            if command is None:
                continue

            if command.kind == 'help':
                print_help(ROLE)

            elif command.kind == 'show':
                perform_show(data, command)

            elif command.kind == 'reload':
                # leave the inner loop, and the game is read again
                print("reloading")
                break

            elif command.kind == 'exit':
                sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
