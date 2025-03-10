#!/usr/bin/env python3

import sys
import yaml
import os
import time
import argparse

from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player
from BoardGameConcept import Empty
from GameData import GameData

DEBUG = False

def usage():
   print("usage, server.py <gameno> [<boardfile>] [<playerfile 1>] ... [<playerfile n>]", file = sys.stderr)

def command_help():
    print("""
add player <number> - add a new player to the game, only player 0 i.e. the game admin can do this
load board <board_file> - loads the board size from a file
load player <player_file> - loads the player data, player types and player units from a file
set board <size_x> <size_y> - set the size of the board at the beginning of the game, only player 0 can do this before the start of the game
show board - show the board
show player - show player information
show types - show player defined unit types
commit - commit actions taken, this can't be undone

help - display this information
exit - exit the game client
    """)

#add player <name> <email> - add a new player to the game, only player 0 i.e. the game admin can do this
def add_player(name, email):
    pass

#load board <board_file> - loads the board size from a file
def load_board(board_file):
    pass

#load player <player_file> - loads the player data, player types and player units from a file
def load_player(player_file):
    pass

#set board <size_x> <size_y> - set the size of the board at the beginning of the game, only player 0 can do this before the start of the game
def set_board(size_x, size_y):
    pass

#show board - show the board
def show_board(data, player_number):
    player_obj = data.getPlayerObj(player_number)
    seen_board = data.getSeenBoard()
    board = data.getBoard()
    if seen_board != None:
        if DEBUG:
            print("showing seen board")
        seen_board.print()
    elif board == None:
        print("must create board - set size and commit")
    else:
        board.print(player_obj)

#show player - show player information
def show_player(player_id):
    pass

#show types - show player defined unit types
def show_types():
    pass

#commit - commit actions taken, this can't be undone
def commit():
    pass

def main(argv):

    # the server is run as the administrator who is player 0
    player_number = 0

    # other arguments
    parser = argparse.ArgumentParser(exit_on_error=True)
    parser.add_argument('-g', '--game-number', required=True, help='specify the game number')
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
            elif tokens[0]=='show':
                if DEBUG:
                    print(f"len(tokens): {len(tokens)}")
                if len(tokens) == 1:
                    print("invalid show command")
                    continue
                elif tokens[1] == 'board':
                    show_board(data, player_number)
                elif tokens[1] == 'types':
                    for player in players.keys():
                        if 'types' in players[player].keys():
                            for types in players[player]['types'].keys():
                                for unit_name in players[player]['types'].keys():
                                    unit_type = players[player]['types'][unit_name]
                                    print(f"player: {player}, name: {unit_type['name']}, symbol: {unit_type['symbol']}, attack: {unit_type['attack']}, health: {unit_type['health']}, energy: {unit_type['energy']}")

                elif tokens[1] == 'players':
                    for player in players.keys():
                        print(f"name: {player}, email: {players[player]['email']}")
                elif tokens[1] == 'units':
                    if seen_board != None:
                        if DEBUG:
                            print("showing seen units")
                        print(seen_board.listUnits())
                    elif board == None:
                        print("must create board - set size and commit")
                    else:
                        print(board.listUnits(player_obj))
                elif tokens[1] == 'pending':
                    for player in players.keys():
                        if 'moves' in players[player].keys():
                            print(f"player: {player}, moves: {players[player]['moves']}")
                else:
                    print("invalid show command")
                    continue

            # set - size, player
            elif tokens[0]=='set':
                if DEBUG:
                    print(f"len(tokens): {len(tokens)}")
                if len(tokens) == 1:
                    print("invalid set command")
                    continue
                elif tokens[1] == 'board':
                    if player_number != 0:
                        print("only the game admin (player 0) can set board size")
                        continue
                    if board != None:
                        print("can't resize an existing board")
                        continue
                    if len(tokens) != 4:
                        print("must provide x and y for size")
                        continue
                    try:
                        size_x = int(tokens[2])
                        size_y = int(tokens[3])
                        # immediately create the board object
                        board = Board(size_x, size_y)
                        data.setBoard(board)
                    except:
                        print("x and y must be a numbers")
                        continue
                    if size_x < 2:
                        print("x must be greater than 1")
                    if size_y < 2:
                        print("y must be greater than 1")
                else:
                    print("invalid set command")
                    continue

            # add - player, type, unit
            elif tokens[0] == 'add':
                if len(tokens) == 2:
                    print("invalid add command")
                    continue
                elif tokens[1] == 'player':
                    if len(tokens) != 3:
                        print("must provide 1 arg for player")
                    elif new_game == False:
                        print("can't add players to an existing game")
                    else:
                        number = tokens[2]
                        players[number] = {
                            'obj': Player(tokens[2]),
                            'types': {}
                        }
                else:
                    print("invalid add command")
                    continue

            # load - player
            elif tokens[0] == 'load':
                if len(tokens) == 2:
                    print("invalid load command")
                    continue
                elif tokens[1] == 'player':
                    if len(tokens) != 3:
                        print("must provide 1 args for load player")
                    elif new_game == False:
                        print("can't add players to an existing game")
                    else:
                        player_data = {}
                        try:
                            with open(tokens[2]) as f:
                                    player_data = yaml.safe_load(f)
                                    if DEBUG:
                                        print("finished player data")
                        except Exception as e:
                            print(f"Error loading player file {tokens[2]} {e}")
                            continue
                        players[player_data['number']] = {
                            'obj': Player(player_data['number']),
                            'types': player_data['types'],
                            'units': player_data['units']
                        }
                elif tokens[1] == 'board':
                    if len(tokens) != 3:
                        print("must provide 1 args for load board")
                    else:
                        board_data = {}
                        try:
                            with open(tokens[2]) as f:
                                    board_data = yaml.safe_load(f)
                                    if DEBUG:
                                        print("finished player data")
                        except Exception as e:
                            print(f"Error loading player file {tokens[2]} {e}")
                            continue
                        size_x = int(board_data['board']['size_x'])
                        size_y = int(board_data['board']['size_y'])
                        # immediately create the board object
                        board = Board(size_x, size_y)
                        data.setBoard(board)

                else:
                    print("invalid load command")
                    continue

            # committing the game saves all input data to yaml for the game setup step
            elif tokens[0] == 'commit':
                # do all the commit actions for the first commit
                if data.serverSave():
                    print("commit complete")
                    break
                else:
                    # commit failed, go back to interactive prompt to resolve problems
                    continue
            # leave
            elif tokens[0] == 'exit':
                sys.exit(0)
            else:
                print("invalid command")

        # do all the commit actions, this will be run when the server is non-interactive
        if new_game:
            # clear the new game flag, this suppresses interactive mode for the server
            data.setNewGame(False)
        elif data.serverSave():
            print("commit complete")
        else:
            print("internal server error saving game data")
            sys.exit(1)

        # wait for player commits before restarting the load and commit cycle
        data.waitForPlayerCommit()

        # log board + units
        board.print()
        print(board.listUnits())

# run main()
if __name__ == "__main__":
   main(sys.argv)
