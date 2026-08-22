#!/usr/bin/env python3

import sys
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept import GameData
from board_game_concept.cli.render import print_board
from board_game_concept.storage.serialise import serialise_units
from board_game_concept.cli import roles
from board_game_concept.cli.help import print_help
from board_game_concept.cli.parser import ParseError, parse

ROLE = roles.OBSERVER

DEBUG = False


def usage():
    print("usage, observer.py <gameno>", file=sys.stderr)


def main(argv=None):
    # the console script entry point calls this with nothing, so fall back to
    # the process arguments
    if argv is None:
        argv = sys.argv


    if DEBUG:
        print(f"len(argv): {len(argv)}")

    if len(argv) == 2:
        player_number = 0
        gameno = argv[1]
    else:
        usage()
        sys.exit(1)

    # initialize the data object
    data = GameData(gameno, player_number)

    while True:

        # load the gamedata
        data.load()

        players = data.getPlayers()
        player_obj = data.getPlayerObj(player_number)
        board = data.getBoard()
        seen_board = data.getSeenBoard()
        size_x = data.getSizeX()
        size_y = data.getSizeY()
        new_game = data.getNewGame()

        # interactive mode
        while True:
            # read a line and make sense of it
            print(f"{argv[0]}> ", flush=True, end='')
            line = sys.stdin.readline().rstrip()
            try:
                command = parse(line)
            except ParseError as error:
                print(error.message)
                continue

            # a blank line is not a command
            if command is None:
                continue

            # the observer watches; it is refused everything that writes
            if not ROLE.allows(command):
                print(ROLE.refusal(command))
                continue

            if command.kind == 'help':
                print_help(ROLE)

            elif command.kind == 'show':
                if command.subject == 'board':
                    if seen_board is not None:
                        print_board(seen_board)
                    elif board is None:
                        print("must create board - set size and commit")
                    else:
                        print_board(board, player_obj)

                elif command.subject == 'types':
                    for player in players.keys():
                        if 'types' in players[player].keys():
                            for unit_name in players[player]['types'].keys():
                                unit_type = players[player]['types'][unit_name]
                                print(
                                    f"player: {player}, name: {unit_type['name']}, symbol: {unit_type['symbol']}, attack: {unit_type['attack']}, health: {unit_type['health']}, energy: {unit_type['energy']}")

                elif command.subject == 'players':
                    for player in players.keys():
                        print(f"number: {player}")

                elif command.subject == 'units':
                    if seen_board is not None:
                        print(serialise_units(seen_board))
                    elif board is None:
                        print("must create board - set size and commit")
                    else:
                        print(serialise_units(board, player_obj))

                elif command.subject == 'pending':
                    for player in players.keys():
                        if 'moves' in players[player].keys():
                            print(f"player: {player}, moves: {players[player]['moves']}")

            elif command.kind == 'reload':
                # leave the inner loop, and the game is read again
                print("reloading")
                break

            elif command.kind == 'exit':
                sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
