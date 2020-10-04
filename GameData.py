from BoardGameConcept import UnitType
from BoardGameConcept import Board
from BoardGameConcept import Player
from BoardGameConcept import Empty
import sys
import yaml
import os
from getpass import getpass
import time

DEBUG = False

class GameData:

    def getUnprocessedMoves(self):
        return self.unprocessed_moves

    def getGamePassword(self):
        return self.game_password

    def getPlayerObj(self, player_name):
        if self.player_name == '0':
            player_obj = None
        else:
            player_obj = self.players[player_name]['obj']
        return player_obj

    def getPlayers(self):
        return self.players

    def getNewGame(self):
        return self.new_game

    def setNewGame(self, new_game):
        self.new_game = new_game

    def getBoard(self):
        return self.board

    def setBoard(self, board):
        self.board = board

    def getSeenBoard(self):
        return self.seen_board

    def getSizeX(self):
        if self.board != None:
            return self.board.size_x
        else:
            return 0

    def getSizeY(self):
        if self.board != None:
            return self.board.size_y
        else:
            return 0

    def __init__(self, gameno, player_name):

        self.gameno = gameno

        # set the paths for the game db
        base_path = os.getcwd() + "/games/_" + gameno
        if DEBUG:
            print(f"Basepath: {base_path}")
        self.data_path = base_path + "/data"
        self.player_path = base_path + "/players"

        # get the password if this game already exists
        if os.path.exists(self.data_path + '/data.yaml'):
            password = getpass()
        else:
            password = ""

        self.player_name = player_name
        self.password = password

        self.players = {}
        self.seen_board = None
        self.board = None
        self.game_password = None
        self.unprocessed_moves = False
        # XXX need a new name for this flag
        if player_name == '0':
            self.new_game = False
        else:
            self.new_game = True

    def load(self):

        # reset unprocessed_moves
        self.unprocessed_moves = False

        # if the game directory does not exist, create it    
        if not(os.path.exists(self.data_path)):
            os.makedirs(self.data_path)
            os.makedirs(self.player_path)

        # try reading meta data file for game 
        try:
            with open(self.data_path + '/data.yaml') as f:
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
            if self.player_name == '0':
                # if this is a new game request the game admin password
                self.new_game = True
                print("Set game password")
                password1 = getpass()
                password2 = getpass(prompt="Reenter password: ")
                if password1 == password2:
                    self.game_password = password1
                    # set the blank password to the newly acquired password
                    self.password = password1
                    self.game_password = password1
                else:
                    print("Passwords must match", file = sys.stderr)
                    sys.exit(1)
            else:
                print(f"No game with path: {self.data_path}", file = sys.stderr)
                print(e, file = sys.stderr)
                sys.exit(1)

        # load all the player files
        if os.path.exists(self.player_path):
            for player_file in os.listdir(self.player_path):
                with open(self.player_path + '/' + player_file) as f:
                    if str(f).find("_units.yaml") != -1:
                        if str(f).find(self.player_name + "_units.yaml") != -1:
                            if DEBUG:
                                print("unprocessed player moves, " +
                                    "waiting for game to complete the turn", 
                                    file = sys.stderr)
                            self.unprocessed_moves = True
                        continue   
                    if str(f).find("commit_") != -1:
                        if str(f).find("commit_" + self.player_name) != -1:
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
                        moves_file = self.player_path + '/' + player_data['name'] + '_units.yaml'
                        if os.path.exists(moves_file):
                            with open(moves_file) as g:
                                self.players[name]['moves'] = yaml.safe_load(g)
                                if DEBUG:
                                    print(self.players[name]['moves'])

                    except yaml.YAMLError as exc:
                        print(exc, file = sys.stderr)
                        sys.exit(1)

        # load the units into the board                
        if os.path.exists(self.data_path + '/units.yaml'):        
            if DEBUG:
                print("loading units")
            with open(self.data_path + '/units.yaml') as f:
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
                        self.board.add(
                            player,
                            x, y,
                            name,
                            unit_type,
                            int(unit['health']),
                            int(unit['energy']),
                            bool(unit['destroyed']),
                            bool(unit['on_board'])
                        )
                        if DEBUG:
                            print(f"processing unit {name} setting " +
                                "health {unit['health']}, " +
                                "destroyed {unit['destroyed']}")
                    self.board.commit()    

        # load the seen units into the visible board
        if os.path.exists(self.player_path + '/' + self.player_name + '_units_seen.yaml'):        
            self.seen_board = Board(self.board.size_x, self.board.size_y)
            if DEBUG:
                print("loading units seen")
            with open(self.player_path + '/' + self.player_name + '_units_seen.yaml') as f:
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
                            print(self.players[p_name]['types'])
                        player = self.players[p_name]['obj']
                        unit_type = self.players[p_name]['types'][unit['type']]['obj']
                        x = unit['x']
                        y = unit['y']
                        self.seen_board.add(
                            player, 
                            x, y,
                            name,
                            unit_type,
                            int(unit['health']),
                            int(unit['energy']),
                            bool(unit['destroyed']),
                            bool(unit['on_board'])
                        )
                        if DEBUG:
                            print(f"processing unit {name} setting " +
                                f"health {unit['health']}, " +
                                f"destroyed {unit['destroyed']}, " +
                                f"on_board {unit['on_board']}")
                    self.seen_board.commit()    
       
        # check the player password
        if self.player_name in self.players.keys():
            # check password    
            if self.players[self.player_name]['password'] != self.password:
                print("Incorrect password", file = sys.stderr) 
                sys.exit(1)
            # set the player_obj to provide context that limits visibility on
            # several show commands, etc
            player_obj = self.players[self.player_name]['obj']
        elif self.player_name == '0':    
            # check password    
            if self.game_password != self.password:
                print("Incorrect password", file = sys.stderr) 
                sys.exit(1)
            # set the player_obj to provide context that limits visibility on
            # several show commands, etc
            self.player_obj = None
        else:
           print(f"player {self.player_name} does not exist", file = sys.stderr)
           sys.exit(1)


    def clientSave(self):
        # check the board size has been set
        if self.board.size_x <= 1 or self.board.size_y <= 1:
            print(f"the board size is too small ({self.board.size_x}, " +
            f"{self.board.size_y})")
            return(False)

        # write the logged in player file only
        p = self.player_name
        types = self.players[p]['types']
        for type_name in types.keys():
            del types[type_name]['obj']
        player_dict = {
            'name': p,
            'email': self.players[p]['email'],
            'password': self.players[p]['password'],
            'types': types
        }
        with open(self.player_path + '/'+ p + '.yaml', 'w') as file:
            yaml.safe_dump(player_dict, file)
        with open(self.player_path + '/'+ 'commit_' + self.player_name, 'w') as file:
            file.write("")
            file.close()

        # this creates files of unit creation or unit moves
        player_units = self.board.listUnits(self.getPlayerObj(self.player_name))
        if DEBUG:
            print("write moves/changes")
            print(player_units)
        with open(self.player_path + '/'+ p + '_units.yaml', 'w') as file:
            file.write(player_units)
            file.close()

        if DEBUG:
            print("save complete")

        return(True)    

    def serverSave(self):

        # check the board size has been set
        if self.getSizeX() <= 1 or self.getSizeY() <= 1:
            print(f"the board size is too small ({self.getSizeX()}, {self.getSizeY()})")
            return(False)

        # add required directories
        if not(os.path.exists(self.data_path)):
            os.makedirs(self.data_path)
        if not(os.path.exists(self.player_path)):
            os.makedirs(self.player_path)

        # write the data file for the board
        board_meta_data = {
            'board' : {
                'size_x' : self.board.size_x,
                'size_y' : self.board.size_y
            },
            'game' : {
                'game' : self.gameno,
                'no_of_players' : len(self.players.keys()),
                'password': self.game_password
            },
        }
        with open(self.data_path + '/data.yaml', 'w') as file:
            yaml.safe_dump(board_meta_data, file)

        # pick up board files created by players and merge them into the board
        for player in self.players.keys():
            if 'moves' in self.players[player].keys():
                if DEBUG:
                    print(f"player: {player}, moves: {self.players[player]['moves']}")
                units = self.players[player]['moves']['units']
                if units == None:
                    continue
                for unit in units:
                    name = unit['name']
                    p_name = unit['player']
                    x = unit['x']
                    y = unit['y']
                    state = unit['state']
                    direction = unit['direction']
                    if DEBUG:
                        print(f"processing unit {name} belonging to {p_name} " +
                            f"at ({x},{y}) {str(direction)}")
                    player = self.players[p_name]['obj']
                    #print(players[p_name]['types'])
                    unit_type = self.players[p_name]['types'][unit['type']]['obj']
                    if state == UnitType.INITIAL:
                        self.board.add(player, x, y, name, unit_type)
                    elif state == UnitType.MOVING:
                        actual_unit = self.board.getUnitByCoords(x, y)
                        actual_unit.move(direction)
                        if DEBUG:
                            print(f"moving unit at ({x},{y}) {str(direction)}")
                    elif state == UnitType.NOP:
                        actual_unit = self.board.getUnitByCoords(x, y)
                        if DEBUG:
                            print(type(actual_unit))
                        if isinstance(actual_unit, Empty):
                            self.board.add(player, x, y, name, unit_type)
                        print(f"NOP unit at ({x},{y}) {str(direction)}")
                    else:    
                        assert False, (f"Invalid unit state {str(state)} " + 
                            "provided by player")

        # resolve all moves and end the turn
        self.board.commit()
        for player_file in os.listdir(self.player_path):
                if player_file.find("_units.yaml") != -1:
                    os.remove(self.player_path + "/" + player_file)

        # both admin and players can update the player info
        # write the individual player files
        # write all players the first time
        for p in self.players.keys():
            types = self.players[p]['types']
            for type_name in types.keys():
                del types[type_name]['obj']
            player_dict = {
                'name': p,
                'email': self.players[p]['email'],
                'password': self.players[p]['password'],
                'types': types
            }
            with open(self.player_path + '/'+ p + '.yaml', 'w') as file:
                yaml.safe_dump(player_dict, file)

        # write out the units information to disk
        # this writes the master board units, i.e. everything
        all_units = self.board.listUnits()
        with open(self.data_path + '/units.yaml', 'w') as file:
            file.write(all_units)
            file.close()

        if DEBUG:
            print("updating player units seen based on the commit outcome")
        for p in self.players.keys():
            player_obj = self.players[p]['obj']
            player_units = self.board.listUnits(player_obj)
            if DEBUG:
                print("write moves/changes")
                print(player_units)
            with open(self.player_path + '/'+ p + '_units_seen.yaml', 'w') as file:
                file.write(player_units)
                file.close()

        return(True)        

    def waitForPlayerCommit(self):
        print("wait for player commit")
        while True:
            commit_count = 0
            for player_file in os.listdir(self.player_path):
                if player_file.find("_units.yaml") != -1:
                    commit_count = commit_count + 1
            if commit_count == len(self.players.keys()):
                break
            time.sleep(10)

