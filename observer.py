#!/usr/bin/python3

from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player
from BoardGameConcept import Empty
import sys
import yaml
import os
from getpass import getpass
import time
from GameData import GameData

DEBUG = False

def usage():
   print("usage, client.py <gameno>", file = sys.stderr)

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

def main(argv):

    if DEBUG:
        print(f"len(argv): {len(argv)}")

    if len(argv) == 2:
        player_name = '0'
        gameno = argv[1]
    else:
        usage()
        sys.exit(1)

    basePath = os.getcwd() + "/games/_" + gameno
    data_path = basePath + "/data"
    player_path = basePath + "/players"

    if DEBUG:
        print(f"Basepath: {basePath}")

    # get the password
    if os.path.exists(basePath):
        password = getpass()
   
    # initialize the data object
    data = GameData(data_path, player_path, player_name, password)

    while True:

        # load the gamedata
        data.load()

        players = data.getPlayers()
        player_obj = data.getPlayerObj(player_name)
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
            elif tokens[0]=='show':
                if DEBUG:
                    print(f"len(tokens): {len(tokens)}")
                if len(tokens) == 1:
                    print("invalid show command")
                    continue
                elif tokens[1] == 'board':
                    if seen_board != None:
                        if DEBUG:
                            print("showing seen board")
                        seen_board.print()
                    elif board == None:
                        print("must create board - set size and commit")
                    else:
                        board.print(player_obj)

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

            # commiting the game saves all input data to yaml for the game setup step
            elif tokens[0] == 'reload':
                # relaod the data
                print("reloading")
                break
            # leave
            elif tokens[0] == 'exit':
                sys.exit(0)
            else:
                print("invalid command")

if __name__ == "__main__":
   main(sys.argv)
