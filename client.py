#!/usr/bin/python

from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player
import sys
import yaml
import os

def main(argv):
    xsize = 2
    ysize = 2
    MAX_PLAYERS = 2
    
    #2 startup modes, player 0 or non-0 player
    assert len(argv)>=3, "usage, client.py <gameno> <playername> <xsize> <ysize>\nor, client.py <gameno> <playername> <password>"
    if argv[1]=='0':
        playername = argv[1]
        gameno = argv[0]
        xsize = argv[2]
        ysize = argv[3]
    elif argv[1]:
        gameno = argv[0]
        playername = argv[1]
        password = argv[2]
    else:
        assert False, "usage, client.py <gameno> <playerno> <xsize> <ysize>\nor, client.py <gameno> <playerno> <password>"
    
    dataPath = os.getcwd() + "\games\_" + gameno + "\data"
    playerPath = os.getcwd() + "\games\_" + gameno + "\players"
    
    #try reading data file for game 
    #except to create the directory for the game data file
    try:
        with open(dataPath + '\\data.yaml') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print(exc)
    except:
        if playername=='0':
            try:
                os.makedirs(dataPath)
                os.makedirs(playerPath)
            except OSError:
                print ("Creation of the directories for game %s failed" % gameno)
            else:
                print ("Successfully created the directories for game %s" % gameno)
        else:
            print("no such game")
          
    if playername != '0':
        try:
            with open(playerPath + '\\'+ playername + '.yaml') as f:
                try:
                    playerData = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    print(exc)
        except:
            print('no player with name %s' % playername)
            sys.exit()
 

    directory = os.fsencode(playerPath)
    
    
    
    #if player, retrieve data, check password
    if playername != '0':
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
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
        if tokens[0]=='initialise':
            assert len(player_names)>=MAX_PLAYERS, "not enough players"
            
            dict_file = {'board' : {'size_x' : xsize,'size_y' : ysize},'game' : {'game' : gameno,'no_of_players' : MAX_PLAYERS}}
            with open(dataPath + '\\data.yaml', 'w') as file:
                yaml.safe_dump(dict_file, file)
            for p in list(range(1,MAX_PLAYERS+1)):
                player_dict = {
                'player_name':player_names[int(p)-1],
                'email':emails[int(p)-1],
                'password':passwords[int(p)-1]                                                       
                }
                with open(playerPath + '\\'+ player_names[int(p)-1] + '.yaml', 'w') as file:
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
            with open(playerPath + '\\'+ playername + '.yaml', 'w') as file:
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
   main(sys.argv[1:])
