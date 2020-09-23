#!/usr/bin/python3

from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player
from BoardGameConcept import Empty
import sys
import yaml
import os
import getpass
import time

DEBUG = False

def usage():
   print("usage, client.py <gameno>", file = sys.stderr)

def command_help():
    print("""
reload - reload game data    
show player - show player information 
show types - show types, this includes any enemy types seen
show units - show units, this includes any enemy units that the player has seen in the last turn
show pending - shows the current actions that will be performed on commit

show board - shows the map of the board form the player's perspective

help - display this information
exit - exit the game client
    """)

def main(argv):

    # the password of the user connecting to this client (could be a player or admin)
    password = ""
    # assume this isn't a new game until admin can't load the game files
    new_game = False
    # the board starts out not existing, if the file is there it will be created
    board = None
    seen_board = None
    board_meta_data = {}
    size_x = 0
    size_y = 0
    # for the game admin player_obj is set to None
    player_obj = None
    # empty players dict
    players = {}

    argc = len(argv)
    if DEBUG:
        print(f"len(argv): {argc}")

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
    if os.path.exists(data_path + '/data.yaml'):
        password1 = getpass.getpass()
    
    while True:
        # try reading meta data file for game 
        with open(data_path + '/data.yaml') as f:
            try:
                board_meta_data = yaml.safe_load(f)
                size_x = board_meta_data['board']['size_x']
                size_y = board_meta_data['board']['size_y']
                password = board_meta_data['game']['password']
                board = Board(size_x, size_y)
                if DEBUG:
                    print("Finished loading game meta data")
            except yaml.YAMLError as exc:
                print(exc, file = sys.stderr)
                sys.exit(1)

        if password != password1:
            print("Incorrect password", file = sys.stderr) 
            sys.exit(1)
        
        # load all the player files
        if os.path.exists(player_path):
            for player_file in os.listdir(player_path):
                with open(player_path + '/' + player_file) as f:
                    if str(f).find("_units.yaml") != -1:
                        if str(f).find(player_name + "_units.yaml") != -1:
                            print("unprocessed player moves, waiting for game to complete the turn, try again later", file = sys.stderr)
                            sys.exit(1)
                        continue   
                    if str(f).find("commit_") != -1:
                        if str(f).find("commit_" + player_name) != -1:
                            new_game = False
                        continue
                    if str(f).find("_units_seen.yaml") != -1:
                        # skip these files
                        continue
                    try:
                        player_data = yaml.safe_load(f)
                        if DEBUG:
                            print(player_data)
                        name = player_data['name']
                        obj = Player(name, player_data['email'])
                        players[name] = {
                            'name': name,
                            'email': player_data['email'],
                            'password': player_data['password'],
                            'obj': obj,
                            'types': {}
                        }
                        if 'types' in player_data.keys():
                            for unit_type_name in player_data['types'].keys():
                                unit_type = player_data['types'][unit_type_name]
                                if DEBUG:
                                    print(unit_type)
                                unit_type_obj = UnitType(
                                    unit_type['name'],
                                    unit_type['symbol'],
                                    int(unit_type['attack']),
                                    int(unit_type['health']),
                                    int(unit_type['energy']))
                                unit_type['obj'] = unit_type_obj
                                players[name]['types'][unit_type['name']] = unit_type

                        # if this is player '0' the moves files could exist
                        moves_file = player_path + '/' + player_data['name'] + '_units.yaml'
                        if os.path.exists(moves_file):
                            with open(moves_file) as g:
                                players[name]['moves'] = yaml.safe_load(g)
                                if DEBUG:
                                    print(players[name]['moves'])

                    except yaml.YAMLError as exc:
                        print(exc, file = sys.stderr)
                        sys.exit(1)

        # load the units into the board                
        if os.path.exists(data_path + '/units.yaml'):        
            if DEBUG:
                print("loading units")
            with open(data_path + '/units.yaml') as f:
                units = yaml.safe_load(f)['units']
                if DEBUG:
                    print(units)
                if units != 'None':
                    for unit in units:
                        name = unit['name']
                        if DEBUG:
                            print(f"processing unit {name}")
                        p_name = unit['player']
                        if DEBUG:
                            print(players[p_name]['types'])
                        player = players[p_name]['obj']
                        unit_type = players[p_name]['types'][unit['type']]['obj']
                        x = unit['x']
                        y = unit['y']
                        board.add(player, x, y, name, unit_type, int(unit['health']), int(unit['energy']), bool(unit['destroyed']), bool(unit['on_board']))
                        if DEBUG:
                            print(f"processing unit {name} setting health {unit['health']}, destroyed {unit['destroyed']}")
                    board.commit()    

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
