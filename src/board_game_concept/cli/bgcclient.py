#!/usr/bin/env python3

import sys
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept import Game, YamlGameRepository
from board_game_concept.cli import complete, roles
from board_game_concept.cli.show import perform_show, show_units
from board_game_concept.cli.help import print_help
from board_game_concept.cli.render import print_dropped
from board_game_concept.cli.session import (describe_outcome, load_game,
                                            read_command, report)
from board_game_concept.service import games, identity
from board_game_concept.service.errors import GameError

ROLE = roles.CLIENT

# what this role calls itself, wherever it was launched from. The prompt and
# the usage both come from here rather than from `argv[0]`, which is the path
# the process happened to be started by
PROGRAM = 'bgcclient'

DEBUG = False


def usage():
    print(f"{PROGRAM} <gameno> <player_number>", file=sys.stderr)


def main(argv=None):
    # the console script entry point calls this with nothing, so fall back to
    # the process arguments
    if argv is None:
        argv = sys.argv

    if DEBUG:
        print(f"len(argv): {len(argv)}")

    if len(argv) == 3:
        gameno = argv[1]
        try:
            player_number = int(argv[2])
        except ValueError:
            usage()
            sys.exit(1)
        # checked before the game is opened, so that a caller who cannot be
        # this player is told so rather than opened as one and then refused
        # by every command they try
        if not identity.is_player(player_number):
            print(identity.out_of_range(player_number), file=sys.stderr)
            usage()
            sys.exit(1)
    else:
        usage()
        sys.exit(1)

    # initialize the data object
    data = Game(YamlGameRepository(gameno), player_number)

    # let a person at a terminal complete what they are typing. The names come
    # from this game object, which is the same one the loop below reloads into,
    # so a unit deployed during the session completes without a reload
    complete.install(ROLE, complete.GameNames(data, player_number))

    # load the data
    while True:

        # load/reload the gamedata
        load_game(data)

        # what this session shows is read where it is shown, so that a unit
        # deployed or ordered since the game was loaded is in it
        unprocessed_moves = data.getUnprocessedMoves()

        # wait 5 seconds if there are unprocessed moves and then reload
        if unprocessed_moves:
            print("waiting for turn to complete...")
            # blocks until the server has taken the orders, rather than
            # sleeping and looking again
            data.waitForTurn()
            # restart the loop
            continue

        # a decided game, or one this player has been wiped out of, takes no
        # more orders. Everything that only displays still works
        outcome = data.getOutcome()
        out_of_it = outcome is not None or data.isEliminated(player_number)
        if outcome is not None:
            print(describe_outcome(outcome))
        elif out_of_it:
            print(f"player {player_number} is out of the game")

        # anything of this player's own that could not be put back when their
        # draft was restored, said before they are asked for anything else
        print_dropped(data.getDropped())

        # report anything the server refused when it resolved the last turn
        rejected = data.getRejected()
        if rejected:
            print(f"{len(rejected)} order(s) rejected last turn:")
            for order in rejected:
                print(f"  - {order['unit']} at "
                      f"({order['x']},{order['y']}): {order['reason']}")

        # interactive mode
        while True:

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

            if out_of_it and command.kind in ('commit', 'move', 'add_type',
                                              'add_unit'):
                print("the game is over" if outcome is not None
                      else "you are out of the game")
                continue

            if command.kind == 'commit':
                if data.clientSave():
                    print("commit complete")
                    break
                continue

            # everything else is the service layer's to carry out or refuse,
            # and to remember: an order that is not committed yet is written
            # down as it is given, so ending the session does not lose it
            try:
                games.perform(data, command)
            except GameError as error:
                report(error)
                continue
            if command.kind == 'move':
                # the order is read back so the player can see it took, as the
                # same table `show units` would have given them
                show_units(data)


if __name__ == "__main__":
    main(sys.argv)
