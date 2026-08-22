#!/usr/bin/env python3

import sys
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept import UnitType, GameData
from board_game_concept.cli.render import print_board
from board_game_concept.storage.serialise import serialise_units
from board_game_concept.cli import roles
from board_game_concept.cli.help import print_help
from board_game_concept.cli.parser import ParseError, parse

ROLE = roles.CLIENT

DEBUG = False


def usage():
    print("client.py <gameno> <player_number>", file=sys.stderr)


def main(argv=None):
    # the console script entry point calls this with nothing, so fall back to
    # the process arguments
    if argv is None:
        argv = sys.argv


    if DEBUG:
        print(f"len(argv): {len(argv)}")

    if len(argv) == 3:
        gameno = argv[1]
        try:
            player_number = int(argv[2])
        except ValueError:
            usage()
            sys.exit(1)
    else:
        usage()
        sys.exit(1)

    # initialize the data object
    data = GameData(gameno, player_number)

    # load the data
    while True:

        # load/reload the gamedata
        data.load()

        # set the fields used in the parser
        players = data.getPlayers()
        player_obj = data.getPlayerObj(player_number)
        board = data.getBoard()
        seen_board = data.getSeenBoard()
        size_x = data.getSizeX()
        size_y = data.getSizeY()
        new_game = data.getNewGame()
        unprocessed_moves = data.getUnprocessedMoves()

        # wait 5 seconds if there are unprocessed moves and then reload
        if unprocessed_moves:
            print("waiting for turn to complete...")
            # blocks until the server has taken the orders, rather than
            # sleeping and looking again
            data.waitForTurn()
            # restart the loop
            continue

        # report anything the server refused when it resolved the last turn
        rejected = data.getRejected()
        if rejected:
            print(f"{len(rejected)} order(s) rejected last turn:")
            for order in rejected:
                print(f"  - {order['unit']} at "
                      f"({order['x']},{order['y']}): {order['reason']}")

        # interactive mode
        while True:

            # read a line and make sense of it
            print(f"{argv[0]}> ", flush=True, end='')
            line = sys.stdin.readline().rstrip()
            try:
                command = parse(line)
            except ParseError as error:
                print(error.message)
                continue

            # a blank line is not a command
            if command is None:
                continue

            if not ROLE.allows(command):
                print(ROLE.refusal(command))
                continue

            if command.kind == 'help':
                print_help(ROLE)

            elif command.kind == 'show':
                if command.subject == 'board':
                    if seen_board is not None:
                        print_board(seen_board)
                    elif board is None:
                        print("must create board - set size and commit")
                    else:
                        print_board(board, player_obj)

                elif command.subject == 'types':
                    for player in players.keys():
                        if 'types' in players[player].keys():
                            for unit_name in players[player]['types'].keys():
                                unit_type = players[player]['types'][unit_name]
                                print(
                                    f"player: {player}, name: {unit_type['name']}, symbol: {unit_type['symbol']}, attack: {unit_type['attack']}, health: {unit_type['health']}, energy: {unit_type['energy']}")

                elif command.subject == 'players':
                    for player in players.keys():
                        print(f"number: {player}")

                elif command.subject == 'units':
                    if seen_board is not None:
                        print(serialise_units(seen_board))
                    elif board is None:
                        print("must create board - set size and commit")
                    else:
                        print(serialise_units(board, player_obj))

            elif command.kind == 'add_type':
                if not new_game:
                    print("can't add types after first turn")
                    continue
                try:
                    obj = UnitType(command.name, command.symbol, command.attack,
                                   command.health, command.energy)
                except Exception as e:
                    print(f"error adding unit type: {e}")
                    continue
                players[player_number]['types'][command.name] = {
                    'name': command.name,
                    'symbol': command.symbol,
                    'attack': command.attack,
                    'health': command.health,
                    'energy': command.energy,
                    'obj': obj,
                }

            elif command.kind == 'add_unit':
                if board is None:
                    print("board must be loaded in order to place units")
                    continue
                if not new_game:
                    print("can't add units after first turn")
                    continue
                try:
                    unit_type = players[player_number]['types'][command.type_name]['obj']
                    board.add(player_obj, command.x, command.y, command.name,
                              unit_type)
                    board.commit()
                    # the view published by the server is what the player is
                    # shown, so a unit deployed this turn has to be put there
                    # too or it stays invisible to its own owner until the turn
                    # resolves. Only the player's own unit is added, so nothing
                    # the server has not revealed becomes visible.
                    if seen_board is not None:
                        seen_board.add(player_obj, command.x, command.y,
                                       command.name, unit_type)
                        seen_board.commit()
                except Exception as e:
                    print(f"error creating new unit {e}")
                    continue

            elif command.kind == 'move':
                if board is None:
                    print("board must be loaded in order to move units")
                    continue
                if new_game:
                    print("can't move units until after the first turn is complete")
                    continue
                try:
                    unit = board.getUnitByName(command.unit)[0]
                    if player_number != unit.player.number:
                        print("can't move units belonging to other players")
                        continue
                    if not unit.on_board:
                        print("can't move units not on the board")
                        continue
                    unit.move(command.direction)
                    print(serialise_units(board, player_obj))
                except Exception as e:
                    print(f"error moving unit {e}")
                    continue

            elif command.kind == 'commit':
                if data.clientSave():
                    print("commit complete")
                    break

            elif command.kind == 'exit':
                sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
