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
add player <name> <email> - add a new player to the game, only player '0' i.e. the game admin can do this
set board <size_x> <size_y> - set the size of the board at the beginning of the game, only player '0' can do this before the start of the game
show board - show the board
show player - show player information 
commit - commit actions taken, this can't be undone

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
    
    while True:
        # try reading meta data file for game 
        try:
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

        except:
            # if this is a new game request the game admin password
            new_game = True
            print("Set game password")
            password1 = getpass.getpass()
            password2 = getpass.getpass(prompt="Reenter password: ")
            if password1 == password2:
                password = password1
            else:
                print("Passwords must match", file = sys.stderr)
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
                        board.add(player, x, y, name, unit_type, int(unit['health']), bool(unit['destroyed']), bool(unit['on_board']))
                        if DEBUG:
                            print(f"processing unit {name} setting health {unit['health']}, destroyed {unit['destroyed']}")
                    board.commit()    

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

            # set - size, player
            elif tokens[0]=='set':
                if DEBUG:
                    print(f"len(tokens): {len(tokens)}")
                if len(tokens) == 1:
                    print("invalid set command")
                    continue
                elif tokens[1] == 'board':
                    if player_name != '0':
                        print("only the game admin (player '0') can set board size")
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
                if len(tokens) == 1:
                    print("invalid add command")
                    continue
                elif tokens[1] == 'player':
                    if len(tokens) != 4:
                        print("must provide 2 args for player")
                    elif new_game == False:
                        print("can't add players to an existing game")
                    else:    
                        name = tokens[2]
                        players[name] = {
                            "email": tokens[3],
                            'obj': Player(tokens[2], tokens[3]),
                            'types': {}
                        }
                        password1 = getpass.getpass()
                        password2 = getpass.getpass("Reenter password: ")
                        if password1 != password2:
                            print("User passwords must match")
                            continue
                        else:
                            players[name]["password"] = password1
                else:
                    print("invalid add command")
                    continue

            # commiting the game saves all input data to yaml for the game setup step
            elif tokens[0] == 'commit':
                break
            # leave
            elif tokens[0] == 'exit':
                sys.exit(0)
            else:
                print("invalid command")    

        # do all the commit actions and then wait for player commits

        # check the board size has been set
        if size_x <= 1 or size_y <= 1:
            print(f"the board size is too small ({size_x}, {size_y})")
            continue

        # add required directories
        if not(os.path.exists(data_path)):
            os.makedirs(data_path)
        if not(os.path.exists(player_path)):
            os.makedirs(player_path)

        # write the data file for the board
        board_meta_data = {
            'board' : {
                'size_x' : size_x,
                'size_y' : size_y
            },
            'game' : {
                'game' : gameno,
                'no_of_players' : len(players.keys()),
                'password': password
            },
        }
        with open(data_path + '/data.yaml', 'w') as file:
            yaml.safe_dump(board_meta_data, file)

        # pick up board files created by players and merge them into the board
        for player in players.keys():
            if 'moves' in players[player].keys():
                print(f"player: {player}, moves: {players[player]['moves']}")
                units = players[player]['moves']['units']
                if units == None:
                    continue
                for unit in units:
                    name = unit['name']
                    p_name = unit['player']
                    x = unit['x']
                    y = unit['y']
                    state = unit['state']
                    direction = unit['direction']
                    print(f"processing unit {name} belonging to {p_name} at ({x},{y}) {str(direction)}")
                    player = players[p_name]['obj']
                    #print(players[p_name]['types'])
                    unit_type = players[p_name]['types'][unit['type']]['obj']
                    if state == UnitType.INITIAL:
                        board.add(player, x, y, name, unit_type)
                    elif state == UnitType.MOVING:
                        actual_unit = board.getUnitByCoords(x, y)
                        actual_unit.move(direction)
                        print(f"moving unit at ({x},{y}) {str(direction)}")
                    elif state == UnitType.NOP:
                        actual_unit = board.getUnitByCoords(x, y)
                        print(type(actual_unit))
                        if isinstance(actual_unit, Empty):
                            board.add(player, x, y, name, unit_type)
                        print(f"NOP unit at ({x},{y}) {str(direction)}")
                    else:    
                        assert False, f"Invalid unit state {str(state)} provided by player"

        # resolve all moves and end the turn
        board.commit()
        for player_file in os.listdir(player_path):
                if player_file.find("_units.yaml") != -1:
                    os.remove(player_path + "/" + player_file)

        # both admin and players can update the player info
        # write the individual player files
        # write all players the first time
        for p in players.keys():
            types = players[p]['types']
            for type_name in types.keys():
                del types[type_name]['obj']
            player_dict = {
                'name': p,
                'email': players[p]['email'],
                'password': players[p]['password'],
                'types': types
            }
            with open(player_path + '/'+ p + '.yaml', 'w') as file:
                yaml.safe_dump(player_dict, file)

        # write out the units information to disk
        # this writes the master board units, i.e. everything
        all_units = board.listUnits()
        with open(data_path + '/units.yaml', 'w') as file:
            file.write(all_units)
            file.close()

        print("commit complete")

        print("updating player units seen based on the commit outcome")
        for p in players.keys():
            player_obj = players[p]['obj']
            player_units = board.listUnits(player_obj)
            if DEBUG:
                print("write moves/changes")
                print(player_units)
            with open(player_path + '/'+ p + '_units_seen.yaml', 'w') as file:
                file.write(player_units)
                file.close()

        # output board + units
        board.print()
        print(board.listUnits())
        
        # wait for player commits before restarting the load and commit cycle
        print("wait for player commit")
        while True:
            commit_count = 0
            for player_file in os.listdir(player_path):
                if player_file.find("_units.yaml") != -1:
                    commit_count = commit_count + 1
            if commit_count == len(players.keys()):
                break
            time.sleep(10)

        # clear the new game flag
        new_game = False

# run main()
if __name__ == "__main__":
   main(sys.argv)
