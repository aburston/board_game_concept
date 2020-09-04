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
   print("or, client.py <gameno> <playername>", file = sys.stderr)

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

    xsize = 2
    ysize = 2
    MAX_PLAYERS = 2
    game_password = ""
    password = ""

    argc = len(argv)
    if DEBUG:
        print(f"len(argv): {argc}")

    if len(argv) == 2:
        playername = '0'
        gameno = argv[1]
    elif len(argv) == 3:
        gameno = argv[1]
        playername = argv[2]
    else:
        usage()
        sys.exit(1)

    basePath = os.getcwd() + "/games/_" + gameno
    dataPath = basePath + "/data"
    playerPath = basePath + "/players"

    if DEBUG:
        print(f"Basepath: {basePath}")
    
    # try reading data file for game 
    # except to create the directory for the game data file
    try:
        with open(dataPath + '/data.yaml') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print(exc)
    except:
        if playername == '0':
            try:
                print("Set game password")
                password1 = getpass.getpass()
                password2 = getpass.getpass(prompt="Reenter password: ")
                if password1 == password2:
                    game_password = password1
                else:
                    print("Passwords must match", file = sys.stderr)
                    sys.exit(1)

            except OSError:
                print (f"Creation of the directories for game {gameno} failed", file = sys.stderr)
                sys.exit(1)
            else:
                print (f"Successfully created the directories for game {gameno}")
        else:
            print(f"No game with number: {gameno}", file = sys.stderr)
            sys.exit(1)
    
    if playername != '0':
        password = getpass.getpass()
        try:
            with open(playerPath + '/'+ playername + '.yaml') as f:
                try:
                    playerData = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    print(exc)
        except:
            print(f"no player with name {playername}", file = sys.stderr)
            sys.exit(1)
 
    #if player, retrieve data, check password
    if playername != '0':
        for filename in os.listdir(playerPath):
            if filename.endswith(".yaml"):
                filename = os.path.splitext(filename)[0] 
                if filename==playername:
                    assert playerData['password']==password, "password doesn't match username"
                    xsize = data['board']['size_x']
                    ysize = data['board']['size_y']

    # candidate config, this should be populated from any existing files
    players = {}
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

        # add - player, type, unit
        if tokens[0]=='add':
            assert len(tokens)>=2,"invalid add command"
            if tokens[1] == 'player':
                if playername != '0':
                    print("only the game admin (player '0') can add players")
                    continue
                if len(tokens) != 4:
                    print("must provide 2 args for player")
                    continue
                players[tokens[2]] = {}
                players[tokens[2]]["email"] = tokens[3]
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

# =============================================================================
#         if token[0]=='commit':
#             commit()
#         if token[0]=='move':
#             assert len(tokens)==5,"must provide 3 args for player"
# =============================================================================

        if tokens[0] == 'exit':
            break

        #initialising the game savees all input data to yaml for the game setup step
        if tokens[0] == 'commit':

            # check there are enough players
            if len(players.keys())<MAX_PLAYERS:
                print ("not enough players")
                continue

            # add required directories
            if not(os.path.exists(dataPath)):
                os.makedirs(dataPath)
            if not(os.path.exists(playerPath)):
                os.makedirs(playerPath)

            # write the data file for the board
            dict_file = {'board' : {'size_x' : xsize,'size_y' : ysize},'game' : {'game' : gameno,'no_of_players' : MAX_PLAYERS}}
            with open(dataPath + '/data.yaml', 'w') as file:
                yaml.safe_dump(dict_file, file)

            # write the individual player files
            for p in players.keys():
                player_dict = {
                    'name': p,
                    'email': players[p]['email'],
                    'password': players[p]['password']
                }
                with open(playerPath + '/'+ p + '.yaml', 'w') as file:
                    yaml.safe_dump(player_dict, file)

        #use to update player yaml to include added unit types    
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

        #use to update player yaml to unclude placed units
        if tokens[0] == 'place_units':
            for i in utype:
                if i in playerData['unit_types']:
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
