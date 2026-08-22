#!/usr/bin/env python3

import sys
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept import Game, YamlGameRepository
from board_game_concept.cli.render import (print_board, print_players,
                                           print_types)
from board_game_concept.storage.serialise import serialise_units
from board_game_concept.cli import roles
from board_game_concept.cli.help import print_help
from board_game_concept.cli.session import load_game, read_command, report
from board_game_concept.service import games
from board_game_concept.service.errors import GameError

ROLE = roles.CLIENT

DEBUG = False


def usage():
    print("client.py <gameno> <player_number>", file=sys.stderr)


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
    else:
        usage()
        sys.exit(1)

    # initialize the data object
    data = Game(YamlGameRepository(gameno), player_number)

    # load the data
    while True:

        # load/reload the gamedata
        load_game(data)

        # what this session shows; the rules are the service layer's, and
        # it reads the game for itself
        players = data.getPlayers()
        player_obj = data.getPlayerObj(player_number)
        board = data.getBoard()
        seen_board = data.getSeenBoard()
        unprocessed_moves = data.getUnprocessedMoves()

        # wait 5 seconds if there are unprocessed moves and then reload
        if unprocessed_moves:
            print("waiting for turn to complete...")
            # blocks until the server has taken the orders, rather than
            # sleeping and looking again
            data.waitForTurn()
            # restart the loop
            continue

        # report anything the server refused when it resolved the last turn
        rejected = data.getRejected()
        if rejected:
            print(f"{len(rejected)} order(s) rejected last turn:")
            for order in rejected:
                print(f"  - {order['unit']} at "
                      f"({order['x']},{order['y']}): {order['reason']}")

        # interactive mode
        while True:

            command = read_command(argv[0], ROLE)
            if command is None:
                continue

            if command.kind == 'help':
                print_help(ROLE)
                continue

            if command.kind == 'exit':
                sys.exit(0)

            if command.kind == 'show':
                if command.subject == 'board':
                    if seen_board is not None:
                        print_board(seen_board)
                    elif board is None:
                        print("must create board - set size and commit")
                    else:
                        print_board(board, player_obj)

                elif command.subject == 'types':
                    print_types(players)

                elif command.subject == 'players':
                    print_players(players)

                elif command.subject == 'units':
                    if seen_board is not None:
                        print(serialise_units(seen_board))
                    elif board is None:
                        print("must create board - set size and commit")
                    else:
                        print(serialise_units(board, player_obj))
                continue

            if command.kind == 'commit':
                if data.clientSave():
                    print("commit complete")
                    break
                continue

            # everything else is the service layer's to carry out or refuse
            try:
                if command.kind == 'add_type':
                    games.define_type(data, command)
                elif command.kind == 'add_unit':
                    games.deploy_unit(data, command)
                elif command.kind == 'move':
                    games.order_move(data, command)
                    # the order is read back so the player can see it took
                    print(serialise_units(data.getBoard(), player_obj))
            except GameError as error:
                report(error)
                continue


if __name__ == "__main__":
    main(sys.argv)
