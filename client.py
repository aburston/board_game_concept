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
   print("usage, client.py <gameno>", file = sys.stderr)
   print("or, client.py <gameno> <playername>", file = sys.stderr)

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
        if playername=='0':
            try:
                print("Set game password")
                password1 = getpass.getpass()
                password2 = getpass.getpass(prompt="Reenter password: ")
                if password1 == password2:
                    game_password = password1
                os.makedirs(dataPath)
                os.makedirs(playerPath)

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
                    assert playerData['password']==password,'password doesnt match username'
                    xsize = data['board']['size_x']
                    ysize = data['board']['size_y']
                   
    b = Board(int(xsize),int(ysize))
    player_names = []
    emails = []
    passwords = []
    name = []
    symbol = []
    health = []
    attack = []
    energy = []
    utype = []
    unit_name = []
    x_location = []
    y_location = []
    
    
    while True:
# =============================================================================
#         print("+-+-+-+-+-+-+\n")
#         for p in ps:
#             print(p)
#         print("\n+-+-+-+-+-+-+\n")
#         print()
# =============================================================================
        b.print()
        line = sys.stdin.readline().rstrip()
        tokens = line.split()
        if len(tokens)==0:
            continue
        if tokens[0]=='add':
            assert len(tokens)>=2,"invalid add command"
            if tokens[1]=='player':
                assert len(tokens)==5,"must provide 3 args for player"
                player_names.append(tokens[2]) 
                emails.append(tokens[3]) 
                passwords.append(tokens[4])
            elif tokens[1] == 'unit_type':
                assert len(tokens)==7,"must provide 5 args for unit_type"
                name.append(tokens[2])
                symbol.append(tokens[3])
                health.append(tokens[4])
                attack.append(tokens[5])
                energy.append(tokens[6])
            elif tokens[1] == 'unit':
                assert len(tokens)==6, "must provide 4 args for unit"
                utype.append(tokens[2])
                unit_name.append(tokens[3])
                x_location.append(tokens[4])
                y_location.append(tokens[5])
            else:
                assert False,"invalid add command"#
                
# =============================================================================
#         if token[0]=='commit':
#             commit()
#         if token[0]=='move':
#             assert len(tokens)==5,"must provide 3 args for player"
# =============================================================================
        
        if tokens[0]=='exit':
            break
        
        #initialising the game savees all input data to yaml for the game setup step
        if tokens[0]=='commit':
            assert len(player_names)>=MAX_PLAYERS, "not enough players"
            
            dict_file = {'board' : {'size_x' : xsize,'size_y' : ysize},'game' : {'game' : gameno,'no_of_players' : MAX_PLAYERS}}
            with open(dataPath + '/data.yaml', 'w') as file:
                yaml.safe_dump(dict_file, file)
            for p in list(range(1,MAX_PLAYERS+1)):
                player_dict = {
                'player_name':player_names[int(p)-1],
                'email':emails[int(p)-1],
                'password':passwords[int(p)-1]                                                       
                }
                with open(playerPath + '/'+ player_names[int(p)-1] + '.yaml', 'w') as file:
                    yaml.safe_dump(player_dict, file)
            
        #use to update player yaml to include added unit types    
        if tokens[0]=='commit_types':
            unitData = {'unit_types' : {name[i] : {
            'symbol' : symbol[i],
            'health' : health[i],
            'attack' : attack[i],
            'energy' : energy[i]   
            } for i in list(range(0,len(name)))}}
            playerData.update(unitData)
            with open(playerPath + '/'+ playername + '.yaml', 'w') as file:
                    yaml.safe_dump(playerData, file)
                 
        #use to update player yaml to unclude placed units
        if tokens[0]=='place_units':
            for i in utype:
                if i in playerData['unit_types']:
                    continue
                else:
                    print("no unit of type %s" % i)
                    utype.remove(i)
            
            assert len(utype)>=1,"must place a non zero number of units"
            unitLocations = {'unit_locations' : {unit_name[i] : {
            'type' : utype[i],
            'x_location' : x_location[i],
            'y_location' : y_location[i]  
            } for i in list(range(0,len(unit_name)))}}
            playerData.update(unitLocations)
            with open(playerPath + '\\'+ playername + '.yaml', 'w') as file:
                    yaml.safe_dump(playerData, file)
            
    
if __name__ == "__main__":
   main(sys.argv)
