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

~~set player email <email> - set a player's email address to a different value - only player '0' or the player setting their own email can do this
~~set player password <password> - set a player's password to a different value - only player '0' or the player setting their own email can do this
set board <size_x> <size_y> - set the size of the board at the beginning of the game, only player '0' can do this before the start of the game

show player - show player information 
show types - show types, this includes any enemy types seen
show units - show units, this includes any enemy units that the player has seen in the last turn
~~show candidate - shows the current actions that will be performed on commit

show board - shows the map of the board form the player's perspective

move <unit_id/unit_name> <north|south|east|west> - move a unit in the specified direction, players can only move their own units

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
    elif len(argv) == 3:
        gameno = argv[1]
        player_name = argv[2]
        # flip the logic if this is a player connecting
        new_game = True
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
                password = board_meta_data['game']['password']
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
                password = password1
            else:
                print("Passwords must match", file = sys.stderr)
                sys.exit(1)
        else:
            print(f"No game with number: {gameno}", file = sys.stderr)
            sys.exit(1)

    # load all the player files
    for player_file in os.listdir(player_path):
        with open(player_path + '/' + player_file) as f:
            if str(f).find("_units.yaml") != -1:
                continue
            if str(f).find("commit") != -1:
                new_game = False
                continue
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
            # set the player_obj to provide context that limits visibility on several show commands, etc    
            player_obj = players[player_name]['obj']    
        else:
           print(f"player {player_name} does not exist", file = sys.stderr)
           sys.exit(1)
    elif not(new_game):
        password1 = getpass.getpass()
        if password != password1:
           print("Incorrect password", file = sys.stderr) 
           sys.exit(1)

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

        # show - board, units
        if tokens[0]=='show':
            if DEBUG:
                print(f"len(tokens): {len(tokens)}")
            if tokens[1] == 'board':
                if board == None:
                    print("must create board - set size and commit")
                    continue
                board.print(player_obj)
                
            elif tokens[1] == 'types':
                for player in players:
                    if 'types' in players[player].keys():    
                        for types in players[player]['types'].keys():
                            for unit_name in players[player]['types'].keys():
                                unit_type = players[player]['types'][unit_name]
                                print(f"player: {player}, name: {unit_type['name']}, symbol: {unit_type['symbol']}, attack: {unit_type['attack']}, health: {unit_type['health']}, energy: {unit_type['energy']}")

            elif tokens[1] == 'players':
                for player in players.keys():
                    print(f"name: {player}, email: {players[player]['email']}")
            elif tokens[1] == 'units':
                if board == None:
                    print("must create board - set size and commit")
                    continue
                print(board.listUnits(player_obj))
            else:
                print("invalid show command")
                continue

        # set - size, player
        if tokens[0]=='set':
            if DEBUG:
                print(f"len(tokens): {len(tokens)}")
            if tokens[1] == 'size':
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
                if player_name == '0':
                    print("only the players can add unit types not admin")
                    continue
                if len(tokens) != 7:
                    print("must provide 5 args for type")
                    continue
                try:
                    obj = UnitType(player_obj, tokens[3], int(tokens[4]), int(tokens[5]), int(tokens[6]))
                except Exception as e:    
                    print(f"error adding unit type: {e}")
                    continue
                type_name = tokens[2]
                symbol = tokens[3]
                attack = tokens[4]
                health = tokens[5]
                energy = tokens[6]
                players[player_name]['types'] = {}
                players[player_name]['types'][type_name] = {}
                players[player_name]['types'][type_name]['name'] = type_name
                players[player_name]['types'][type_name]['symbol'] = symbol
                players[player_name]['types'][type_name]['attack'] = attack
                players[player_name]['types'][type_name]['health'] = health
                players[player_name]['types'][type_name]['energy'] = energy
                players[player_name]['types'][type_name]['obj'] = obj
            elif tokens[1] == 'unit':
                if player_name == '0':
                    print("only the players can add units not admin")
                    continue
                if len(tokens) != 6:
                    print("must provide 4 args for unit")
                    continue
                if board == None:
                    print("board must be loaded in order to place units")
                    continue
                try:
                    type_name = tokens[2]
                    name = tokens[3]
                    x = int(tokens[4])
                    y = int(tokens[5])
                    if DEBUG:
                        print(f"{player_obj}, {x}, {y}, {name}, {players[player_name]['types'][type_name]['obj']}")
                    board.add(player_obj, x, y, name, players[player_name]['types'][type_name]['obj'])
                    board.commit()
                except Exception as e:
                    print(f"error creating new unit {e}")
                    continue
            else:
                print("invalid add command")
                continue

        # move - unit
        if tokens[0] == 'move':
            if player_name == '0':
                print("only the players can move units not admin")
                continue
            if len(tokens) != 3:
                print("must provide 2 args for move")
                continue
            if board == None:
                print("board must be loaded in order to move units")
                continue
            try:
                unit_name = tokens[1]
                direction = tokens[2]
                # TODO - make sure you implment rules to make this unique per player
                unit = board.getUnitByName(unit_name)[0]
                if direction == 'north':
                    direction = UnitType.NORTH
                elif direction == 'south':
                    direction = UnitType.SOUTH
                elif direction == 'east':
                    direction = UnitType.EAST
                elif direction == 'west':
                    direction = UnitType.WEST
                else:
                    print(f"invalid direction {direction}")
                    continue
                unit.move(direction)
                print(board.listUnits(player_obj))
            except Exception as e:
                print(f"error moving unit {e}")
                continue

        # commiting the game saves all input data to yaml for the game setup step
        if tokens[0] == 'commit':

            # check the board size has been set
            if size_x <= 1 or size_y <= 1:
                print(f"the board size is too small ({size_x}, {size_y})")
                continue

            # only admin can write to the data directory
            if player_name == '0':
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

                # TODO: pick up board files created by players and merge them into the board

                # resolve all moves and end the turn
                board.commit()

            # both admin and players can update the player info
            # write the individual player files
            if player_name == '0':
                # write all players
                for p in players.keys():
                    player_dict = {
                        'name': p,
                        'email': players[p]['email'],
                        'password': players[p]['password'],
                    }
                    with open(player_path + '/'+ p + '.yaml', 'w') as file:
                        yaml.safe_dump(player_dict, file)
            else:
                # write the logged in player file only
                p = player_name
                player_dict = {
                    'name': p,
                    'email': players[p]['email'],
                    'password': players[p]['password'],
                }
                with open(player_path + '/'+ p + '.yaml', 'w') as file:
                    yaml.safe_dump(player_dict, file)
                with open(player_path + '/'+ 'commit', 'w') as file:
                    file.write("")
                    file.close()

            # write out the units information to disk
            if player_name == '0':
                # this writes the master board units, i.e. everything
                all_units = board.listUnits()
                with open(data_path + '/units.yaml', 'w') as file:
                    file.write(player_units)
                    file.close()
            else:
                # this creates files of unit creation or unit moves
                player_units = board.listUnits(player_obj)
                with open(player_path + '/'+ p + '_units.yaml', 'w') as file:
                    file.write(player_units)
                    file.close()

            print("commit complete")    

        # leave
        if tokens[0] == 'exit':
            break


if __name__ == "__main__":
   main(sys.argv)
