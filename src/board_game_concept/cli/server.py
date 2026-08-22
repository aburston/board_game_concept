#!/usr/bin/env python3

import sys
import yaml
import argparse
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept import Board, Player, GameData
from board_game_concept.cli.render import print_board
from board_game_concept.storage.serialise import serialise_units
from board_game_concept.cli import roles
from board_game_concept.cli.help import print_help
from board_game_concept.cli.parser import ParseError, parse

ROLE = roles.SERVER

DEBUG = False


def usage():
    print(
        "usage, server.py <gameno> [<boardfile>] [<playerfile 1>] ... [<playerfile n>]",
        file=sys.stderr)


# load board <board_file> - loads the board size from a file


def load_board(board_file):
    pass

# load player <player_file> - loads the player data, player types and
# player units from a file


def load_player(player_file):
    pass

# set board <size_x> <size_y> - set the size of the board at the beginning
# of the game, only player 0 can do this before the start of the game


def set_board(size_x, size_y):
    pass

# show board - show the board


def show_board(data, player_number):
    player_obj = data.getPlayerObj(player_number)
    seen_board = data.getSeenBoard()
    board = data.getBoard()
    if seen_board is not None:
        if DEBUG:
            print("showing seen board")
        print_board(seen_board)
    elif board is None:
        print("must create board - set size and commit")
    else:
        print_board(board, player_obj)

# show player - show player information


def show_player(player_id):
    pass

# show types - show player defined unit types


def show_types():
    pass

# commit - commit actions taken, this can't be undone


def commit():
    pass


def main(argv=None):
    # the console script entry point calls this with nothing, so fall back to
    # the process arguments
    if argv is None:
        argv = sys.argv


    # the server is run as the administrator who is player 0
    player_number = 0

    # other arguments
    parser = argparse.ArgumentParser(exit_on_error=True)
    parser.add_argument(
        '-g',
        '--game-number',
        required=True,
        help='specify the game number')
    args = parser.parse_args()

    # initialize data object
    data = GameData(args.game_number, player_number)

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
        while new_game:
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

            if not ROLE.allows(command):
                print(ROLE.refusal(command))
                continue

            if command.kind == 'help':
                print_help(ROLE)

            elif command.kind == 'show':
                if command.subject == 'board':
                    show_board(data, player_number)

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

            elif command.kind == 'set_board':
                if board is not None:
                    print("can't resize an existing board")
                    continue
                size_x = command.size_x
                size_y = command.size_y
                if size_x < 2:
                    print("x must be greater than 1")
                    continue
                if size_y < 2:
                    print("y must be greater than 1")
                    continue
                # the board has its own limits beyond the minimum, and
                # reports them itself
                try:
                    board = Board(size_x, size_y)
                except AssertionError as e:
                    print(e)
                    continue
                data.setBoard(board)

            elif command.kind == 'add_player':
                if new_game is False:
                    print("can't add players to an existing game")
                    continue
                players[command.number] = {
                    'obj': Player(command.number),
                    'types': {}
                }

            elif command.kind == 'load_player':
                if new_game is False:
                    print("can't add players to an existing game")
                    continue
                try:
                    with open(command.path) as f:
                        player_data = yaml.safe_load(f)
                except Exception as e:
                    print(f"Error loading player file {command.path} {e}")
                    continue
                number = int(player_data['number'])
                players[number] = {
                    'obj': Player(number),
                    'types': player_data['types'],
                    'units': player_data['units']
                }

            elif command.kind == 'load_board':
                try:
                    with open(command.path) as f:
                        board_data = yaml.safe_load(f)
                except Exception as e:
                    print(f"Error loading player file {command.path} {e}")
                    continue
                size_x = int(board_data['board']['size_x'])
                size_y = int(board_data['board']['size_y'])
                board = Board(size_x, size_y)
                data.setBoard(board)

            elif command.kind == 'commit':
                # do all the commit actions for the first commit
                if data.serverSave():
                    print("commit complete")
                    break
                # commit failed, go back to the prompt to resolve the problem
                continue

            elif command.kind == 'exit':
                sys.exit(0)

        # do all the commit actions, this will be run when the server is
        # non-interactive
        if new_game:
            # clear the new game flag, this suppresses interactive mode for the
            # server
            data.setNewGame(False)
        elif data.serverSave():
            print("commit complete")
        else:
            print("internal server error saving game data")
            sys.exit(1)

        # wait for player commits before restarting the load and commit cycle
        data.waitForPlayerCommit()

        # log board + units
        print_board(board)
        print(serialise_units(board))


# run main()
if __name__ == "__main__":
    main(sys.argv)
