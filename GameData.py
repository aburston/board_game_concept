from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player
from BoardGameConcept import Empty
import sys
import yaml
import os

DEBUG = False

class GameData:

    def __init__(self, data_path, player_path, player_name, password):

        self.player_path = player_path
        self.data_path = data_path
        self.player_name = player_name
        self.players = {}
        # XXX need a new name for this flag
        if player_name == '0':
            self.new_game = False
        else:
            self.new_game = True

        # try reading meta data file for game 
        try:
            with open(data_path + '/data.yaml') as f:
                try:
                    board_meta_data = yaml.safe_load(f)
                    size_x = board_meta_data['board']['size_x']
                    size_y = board_meta_data['board']['size_y']
                    self.game_password = board_meta_data['game']['password']
                    self.board = Board(size_x, size_y)
                    if DEBUG:
                        print("Finished loading game meta data")
                except yaml.YAMLError as e:
                    print(e, file = sys.stderr)
                    sys.exit(1)

        except Exception as e:
            print(f"No game with path: {data_path}", file = sys.stderr)
            print(e, file = sys.stderr)
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
                            self.new_game = False
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
                        self.players[name] = {
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
                                self.players[name]['types'][unit_type['name']] = unit_type

                        # if this is player '0' the moves files could exist
                        moves_file = player_path + '/' + player_data['name'] + '_units.yaml'
                        if os.path.exists(moves_file):
                            with open(moves_file) as g:
                                self.players[name]['moves'] = yaml.safe_load(g)
                                if DEBUG:
                                    print(self.players[name]['moves'])

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
                            print(self.players[p_name]['types'])
                        player = self.players[p_name]['obj']
                        unit_type = self.players[p_name]['types'][unit['type']]['obj']
                        x = unit['x']
                        y = unit['y']
                        self.board.add(player, x, y, name, unit_type, int(unit['health']), int(unit['energy']), bool(unit['destroyed']), bool(unit['on_board']))
                        if DEBUG:
                            print(f"processing unit {name} setting health {unit['health']}, destroyed {unit['destroyed']}")
                    self.board.commit()    

        # load the seen units into the visible board
        if os.path.exists(player_path + '/' + player_name + '_units_seen.yaml'):        
            self.seen_board = Board(size_x, size_y)
            if DEBUG:
                print("loading units seen")
            with open(player_path + '/' + player_name + '_units_seen.yaml') as f:
                units = yaml.safe_load(f)['units']
                if DEBUG:
                    print(units)
                if units != 'None':
                    for unit in units:
                        name = unit['name']
                        if DEBUG:
                            print(f"processing seen unit {name}")
                        p_name = unit['player']
                        if DEBUG:
                            print(players[p_name]['types'])
                        player = self.players[p_name]['obj']
                        unit_type = self.players[p_name]['types'][unit['type']]['obj']
                        x = unit['x']
                        y = unit['y']
                        self.seen_board.add(player, x, y, name, unit_type, int(unit['health']), int(unit['energy']), bool(unit['destroyed']), bool(unit['on_board']))
                        if DEBUG:
                            print(f"processing unit {name} setting health {unit['health']}, destroyed {unit['destroyed']}, on_board {unit['on_board']}")
                    self.seen_board.commit()    
       
        # check the player password
        if player_name in self.players.keys():
            # check password    
            if self.players[player_name]['password'] != password:
                print("Incorrect password", file = sys.stderr) 
                sys.exit(1)
            # set the player_obj to provide context that limits visibility on several show commands, etc    
            player_obj = self.players[player_name]['obj']
            # set the password
            self.password = password
        elif player_name == '0':    
            # check password    
            if self.game_password != password:
                print("Incorrect password", file = sys.stderr) 
                sys.exit(1)
            # set the player_obj to provide context that limits visibility on several show commands, etc    
            player_obj = None
            # set the password
            self.password = password
        else:
           print(f"player {self.player_name} does not exist", file = sys.stderr)
           sys.exit(1)
