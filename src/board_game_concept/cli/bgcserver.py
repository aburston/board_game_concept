#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept import YamlGameRepository
from board_game_concept.cli.render import print_board, print_dropped
from board_game_concept.cli.backend import LocalSession
from board_game_concept.storage.serialise import units_document
from board_game_concept.storage.yaml_repository import dump_units
from board_game_concept.cli import complete, roles
from board_game_concept.cli.show import perform_show
from board_game_concept.cli.help import print_help
from board_game_concept.cli.session import (describe_outcome, load_game,
                                            read_command, report)
from board_game_concept.service.errors import GameError

ROLE = roles.SERVER

# what this role calls itself, wherever it was launched from. The prompt comes
# from here rather than from `argv[0]`, which is the path the process happened
# to be started by, and `argparse` is told the same name so its usage agrees
PROGRAM = 'bgcserver'

DEBUG = False


def main(argv=None):
    # the console script entry point calls this with nothing, so fall back to
    # the process arguments
    if argv is None:
        argv = sys.argv

    # the server is run as the administrator who is player 0
    player_number = 0

    # other arguments
    parser = argparse.ArgumentParser(prog=PROGRAM, exit_on_error=True)
    parser.add_argument(
        '-g',
        '--game-number',
        required=True,
        help='specify the game number')
    args = parser.parse_args(argv[1:])

    # a session hides how the game is reached. Today it is in-process; a
    # later change swaps LocalSession for an HTTP-backed one and the rest
    # of this file does not notice
    data = LocalSession(YamlGameRepository(args.game_number), player_number)

    # completion for the setup prompt. The server owns no units and defines no
    # types, so what it gains is the grammar and the paths `load` wants
    complete.install(ROLE, complete.GameNames(data, player_number))

    while True:

        # load the gamedata
        load_game(data)

        # anything the administrator drafted that could not be put back
        print_dropped(data.getDropped())

        new_game = data.getNewGame()

        # a decided game has no turn left to resolve, and waiting for commits
        # that will never come is how the cycle used to run forever
        outcome = data.getOutcome()
        if outcome is not None:
            print(describe_outcome(outcome))
            sys.exit(0)

        # interactive mode
        while new_game:
            command = read_command(PROGRAM, ROLE)
            if command is None:
                continue

            if command.kind == 'help':
                print_help(ROLE)
                continue

            if command.kind == 'exit':
                sys.exit(0)

            if command.kind == 'show':
                perform_show(data, command)
                continue

            if command.kind == 'commit':
                # commit as this role commits - the session knows which
                # meaning by the identity it was opened as (ending setup, here)
                if data.commit():
                    print("commit complete")
                    break
                # commit failed, go back to the prompt to resolve the problem
                continue

            # everything else is the service layer's to carry out or refuse,
            # and to remember: setup that is not committed yet is written down
            # as it is done, so ending the session does not lose it
            try:
                data.perform(command)
            except GameError as error:
                report(error)
                continue

        # do all the commit actions, this will be run when the server is
        # non-interactive
        if new_game:
            # clear the new game flag, this suppresses interactive mode for the
            # server
            data.setNewGame(False)
        else:
            # asked here rather than acted on from the waiting: the question
            # that authorises a resolution and the resolution itself are one
            # act, holding the game, so another caller cannot resolve the turn
            # in between and leave this one resolving a game with no orders
            resolved = data.resolve_pending()
            if resolved is None:
                # somebody else resolved it first, which is the barrier doing
                # its work rather than a failure. Wait to be told again -
                # looping straight back would be a spin
                data.waitForPlayerCommit()
                continue
            if not resolved:
                print("internal server error saving game data")
                sys.exit(1)
            print("commit complete")

        # the turn just resolved may have decided the game
        outcome = data.getOutcome()
        if outcome is not None:
            print_board(data.getBoard())
            print(dump_units(units_document(data.getBoard())))
            print(describe_outcome(outcome))
            sys.exit(0)

        # wait for player commits before restarting the load and commit cycle
        data.waitForPlayerCommit()

        # log board + units. The board is read back rather than kept in a
        # local: setting or loading a board during setup replaces it, and the
        # local would still be the old one
        resolved = data.getBoard()
        print_board(resolved)
        print(dump_units(units_document(resolved)))


# run main()
if __name__ == "__main__":
    main(sys.argv)
