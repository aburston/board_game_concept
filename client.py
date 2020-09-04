#!/usr/bin/python3

from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player
import sys
import yaml
import os
import getpass

DEBUG = True

def usage():
   print("usage, client.py <gameno>", file = sys.stdin)
   print("or, client.py <gameno> <player_name>", file = sys.stderr)

def command_help():
    print("""
add player <name> <email> - add a new player to the game, only player '0' i.e. the game admin can do this
add type <name> <symbol> <attack> <health> <energy>
add unit <type> <name> <x> <y>

set player <email> - set a player's email address to a different value - only player '0' or the player setting their own email can do this
set board <size_x> <size_y> - set the size of the board at the beginning of the game, only player '0' can do this before the start of the game

show player - show player information 
show types - show types, this includes any enemy types seen
show units - show units, this includes any enemy units that the player has seen in the last turn
show candidate - shows the current actions that will be performed on commit

show board - shows the map of the board form the player's perspective

move <unit_id/unit_name> <north|south|east|west> - move a unit in the specified direction, players can only move their own units

commit - commit actions taken, this can't be undone

help - display this information
exit - exit the game client
    """)

def main(argv):

    size_x = 0
    size_y = 0
    game_password = ""
    password = ""
    board_meta_data = {}
    new_game = False
    board = None
    players = {}

    argc = len(argv)
    if DEBUG:
        print(f"len(argv): {argc}")

    if len(argv) == 2:
        player_name = '0'
        gameno = argv[1]
    elif len(argv) == 3:
        gameno = argv[1]
        player_name = argv[2]
    else:
        usage()
        sys.exit(1)

    basePath = os.getcwd() + "/games/_" + gameno
    data_path = basePath + "/data"
    player_path = basePath + "/players"

    if DEBUG:
        print(f"Basepath: {basePath}")
    
    # try reading data file for game 
    try:
        with open(data_path + '/data.yaml') as f:
            try:
                board_meta_data = yaml.safe_load(f)
                size_x = board_meta_data['board']['size_x']
                size_y = board_meta_data['board']['size_y']
                game_password = board_meta_data['game']['password']
                board = Board(size_x, size_y)
                if DEBUG:
                    print("Finished loading game meta data")
            except yaml.YAMLError as exc:
                print(exc, file = sys.stderr)
                sys.exit(1)
    except:
        # if this is a new game request the game admin password
        if player_name == '0':
            new_game = True
            print("Set game password")
            password1 = getpass.getpass()
            password2 = getpass.getpass(prompt="Reenter password: ")
            if password1 == password2:
                game_password = password1
            else:
                print("Passwords must match", file = sys.stderr)
                sys.exit(1)
        else:
            print(f"No game with number: {gameno}", file = sys.stderr)
            sys.exit(1)

    # load all the player files
    for player_file in os.listdir(player_path):
        with open(player_path + '/' + player_file) as f:
            try:
                player_data = yaml.safe_load(f)
                obj = Player(player_data['name'], player_data['email'])
                players[player_data['name']] = {
                    'email': player_data['email'],
                    'password': player_data['password'],
                    'obj': obj
                }
            except yaml.YAMLError as exc:
                print(exc, file = sys.stderr)
                sys.exit(1)
   
    # check the player password
    if player_name != '0':
        if player_name in players.keys():
            password = getpass.getpass()
            # check password    
            if players[player_name]['password'] != password:
                print("Incorrect password", file = sys.stderr) 
                sys.exit(1)
        else:
           print(f"player {player_name} does not exist", file = sys.stderr)
           sys.exit(1)
    elif not(new_game):
        password = getpass.getpass()
        if game_password != password:
           print("Incorrect password", file = sys.stderr) 
           sys.exit(1)

    # candidate config, this should be populated from any existing files

    name = []
    symbol = []
    health = []
    attack = []
    energy = []
    utype = []
    unit_name = []
    x_location = []
    y_location = []
    
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
        if tokens[0] == 'help':
            command_help()
            continue

        # show - board
        if tokens[0]=='show':
            if DEBUG:
                print(f"len(tokens): {len(tokens)}")
            if tokens[1] == 'board':
                if board == None:
                    print("must create board - set size and commit")
                    continue
                board.print()
            if tokens[1] == 'players':
                for player in players.keys():
                    print(f"name: {player}, email: {players[player]['email']}")
            else:
                print("invalid set command")
                continue

        # set - size, player
        if tokens[0]=='set':
            if DEBUG:
                print(f"len(tokens): {len(tokens)}")
            if tokens[1] == 'size':
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
        if tokens[0] == 'add':
            if tokens[1] == 'player':
                if player_name != '0':
                    print("only the game admin (player '0') can add players")
                    continue
                if len(tokens) != 4:
                    print("must provide 2 args for player")
                    continue
                players[tokens[2]] = {}
                players[tokens[2]]["email"] = tokens[3]
                players[tokens[2]]['obj'] = Player(tokens[2], tokens[3])
                password1 = getpass.getpass()
                password2 = getpass.getpass("Reenter password: ")
                if password1 != password2:
                    print("User passwords must match")
                    continue
                else:
                    players[tokens[2]]["password"] = password1
            elif tokens[1] == 'type':
                if len(tokens) != 7:
                    print("must provide 5 args for type")
                    continue
                name.append(tokens[2])
                symbol.append(tokens[3])
                health.append(tokens[4])
                attack.append(tokens[5])
                energy.append(tokens[6])
            elif tokens[1] == 'unit':
                if len(tokens) != 6:
                    print("must provide 4 args for unit")
                    continue
                utype.append(tokens[2])
                unit_name.append(tokens[3])
                x_location.append(tokens[4])
                y_location.append(tokens[5])
            else:
                print("invalid add command")
                continue

        if tokens[0] == 'exit':
            break

        # commiting the game saves all input data to yaml for the game setup step
        if tokens[0] == 'commit':

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
                    'password': game_password
                },
            }
            with open(data_path + '/data.yaml', 'w') as file:
                yaml.safe_dump(board_meta_data, file)

            # write the individual player files
            for p in players.keys():
                player_dict = {
                    'name': p,
                    'email': players[p]['email'],
                    'password': players[p]['password'],
                }
                with open(player_path + '/'+ p + '.yaml', 'w') as file:
                    yaml.safe_dump(player_dict, file)
                    

        # use to update player yaml to include added unit types    
        if tokens[0] == 'commit_types':
            unitData = {
                'unit_types' : {
                    name[i] : {
                        'symbol' : symbol[i],
                        'health' : health[i],
                        'attack' : attack[i],
                        'energy' : energy[i]
                    }
                }        
            }

        # use to update player yaml to unclude placed units
        if tokens[0] == 'place_units':
            for i in utype:
                if i in player_data['unit_types']:
                    continue
                else:
                    print("no unit of type %s" % i)
                    utype.remove(i)

            assert len(utype) >= 1,"must place a non zero number of units"
            unitLocations = {
                'unit_locations' : {
                    unit_name[i] : {
                        'type' : utype[i],
                        'x_location' : x_location[i],
                        'y_location' : y_location[i]  
                    }
                    for i in list(range(0,len(unit_name)))
                }
            }


if __name__ == "__main__":
   main(sys.argv)
