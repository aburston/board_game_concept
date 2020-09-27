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
   print("client.py <gameno> <player_name>", file = sys.stderr)

def command_help():
    print("""
add type <name> <symbol> <attack> <health> <energy>
add unit <type> <name> <x> <y>

~~set player email <email> - set a player's email address to a different value - only player '0' or the player setting their own email can do this
~~set player password <password> - set a player's password to a different value - only player '0' or the player setting their own email can do this

show player - show player information 
show types - show types, this includes any enemy types seen
show units - show units, this includes any enemy units that the player has seen in the last turn

show board - shows the map of the board form the player's perspective

move <unit_id/unit_name> <north|south|east|west> - move a unit in the specified direction, players can only move their own units

commit - commit actions taken, this can't be undone

help - display this information
exit - exit the game client
    """)

def main(argv):

    if DEBUG:
        print(f"len(argv): {len(argv)}")

    if len(argv) == 3:
        gameno = argv[1]
        player_name = argv[2]
    else:
        usage()
        sys.exit(1)

    # initialize the data object
    data = GameData(gameno, player_name)

    # load the data 
    while True:

        # load/reload the gamedata
        data.load()

        # set the fields used in the parser
        players = data.getPlayers()
        player_obj = data.getPlayerObj(player_name)
        board = data.getBoard()
        seen_board = data.getSeenBoard()
        size_x = data.getSizeX()
        size_y = data.getSizeY()
        new_game = data.getNewGame()
        unprocessed_moves = data.getUnprocessedMoves()

        # wait 5 seconds if there are unprocessed moves and then reload
        if unprocessed_moves:
            print("waiting for turn to complete...")
            time.sleep(5)
            # restart the loop
            continue

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
                else:
                    print("invalid show command")
                    continue

            # add - player, type, unit
            elif tokens[0] == 'add':
                if len(tokens) == 1:
                    print("invalid add command")
                    continue
                elif tokens[1] == 'type':
                    if len(tokens) != 7:
                        print("must provide 5 args for type")
                        continue
                    if new_game == False:
                        print("can't add types after first turn")
                        continue
                    try:
                        type_name = tokens[2]
                        symbol = tokens[3]
                        attack = tokens[4]
                        health = tokens[5]
                        energy = tokens[6]
                        obj = UnitType(type_name, symbol, int(attack), int(health), int(energy))
                        players[player_name]['types'][type_name] = {}
                        players[player_name]['types'][type_name]['name'] = type_name
                        players[player_name]['types'][type_name]['symbol'] = symbol
                        players[player_name]['types'][type_name]['attack'] = attack
                        players[player_name]['types'][type_name]['health'] = health
                        players[player_name]['types'][type_name]['energy'] = energy
                        players[player_name]['types'][type_name]['obj'] = obj
                    except Exception as e:    
                        print(f"error adding unit type: {e}")
                        continue
                elif tokens[1] == 'unit':
                    if len(tokens) != 6:
                        print("must provide 4 args for unit")
                        continue
                    if board == None:
                        print("board must be loaded in order to place units")
                        continue
                    if new_game == False:
                        print("can't add units after first turn")
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
            elif tokens[0] == 'move':
                if len(tokens) != 3:
                    print("must provide 2 args for move")
                    continue
                elif board == None:
                    print("board must be loaded in order to move units")
                    continue
                elif new_game:
                    print("can't move units until after the first turn is complete")
                    continue
                try:
                    unit_name = tokens[1]
                    direction = tokens[2]
                    # TODO - make sure you implment rules to make this unique per player
                    unit = board.getUnitByName(unit_name)[0]
                    if player_name != unit.player.name:
                        print("can't move units belonging to other players")
                        continue
                    if unit.on_board == False:
                        print("can't move units not on the board")
                        continue
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
            elif tokens[0] == 'commit':
                if data.clientSave():
                    print("commit complete")
                    break

            # leave
            elif tokens[0] == 'exit':
                sys.exit(0)
            else:
                print("invalid command")


if __name__ == "__main__":
   main(sys.argv)
