#!/usr/bin/env python3

import sys
import yaml
import os
from getpass import getpass
import time
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept import UnitType, Board, Player, Empty, GameData
from board_game_concept.cli.render import print_board
from board_game_concept.storage.serialise import serialise_units

DEBUG = False


def usage():
    print("usage, observer.py <gameno>", file=sys.stderr)


def command_help():
    print("""
reload - reload game data
show players - show player information
show types - show types, this includes any enemy types seen
show units - show units, this includes any enemy units that the player has seen in the last turn
show pending - shows the current actions that will be performed on commit

show board - shows the map of the board form the player's perspective

help - display this information
exit - exit the game client
    """)


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
            # read line from stdin + tokenize it
            print(f"{argv[0]}> ", flush=True, end='')
            line = sys.stdin.readline().rstrip()
            tokens = line.split()

            # ignore empty lines
            if len(tokens) == 0:
                continue

            # command help
            elif tokens[0] == 'help':
                command_help()
                continue

            # show - board, units
            elif tokens[0] == 'show':
                if DEBUG:
                    print(f"len(tokens): {len(tokens)}")
                if len(tokens) == 1:
                    print("invalid show command")
                    continue
                elif tokens[1] == 'board':
                    if seen_board is not None:
                        if DEBUG:
                            print("showing seen board")
                        print_board(seen_board)
                    elif board is None:
                        print("must create board - set size and commit")
                    else:
                        print_board(board, player_obj)

                elif tokens[1] == 'types':
                    for player in players.keys():
                        if 'types' in players[player].keys():
                            for types in players[player]['types'].keys():
                                for unit_name in players[player]['types'].keys(
                                ):
                                    unit_type = players[player]['types'][unit_name]
                                    print(
                                        f"player: {player}, name: {unit_type['name']}, symbol: {unit_type['symbol']}, attack: {unit_type['attack']}, health: {unit_type['health']}, energy: {unit_type['energy']}")

                elif tokens[1] == 'players':
                    for player in players.keys():
                        print(f"number: {player}")
                elif tokens[1] == 'units':
                    if seen_board is not None:
                        if DEBUG:
                            print("showing seen units")
                        print(serialise_units(seen_board))
                    elif board is None:
                        print("must create board - set size and commit")
                    else:
                        print(serialise_units(board, player_obj))
                elif tokens[1] == 'pending':
                    for player in players.keys():
                        if 'moves' in players[player].keys():
                            print(f"player: {player}, moves: {players[player]['moves']}")
                else:
                    print("invalid show command")
                    continue

            # committing the game saves all input data to yaml for the game
            # setup step
            elif tokens[0] == 'reload':
                # reload the data
                print("reloading")
                break
            # leave
            elif tokens[0] == 'exit':
                sys.exit(0)
            else:
                print("invalid command")


if __name__ == "__main__":
    main(sys.argv)
