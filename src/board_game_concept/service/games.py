"""What a caller may ask of a game, and the rules about when.

One function per command object. Each carries out the command or refuses it by
raising, and none of them prints anything or reads a line of input: a caller
that is not a terminal gets the same rules and the same refusals.

These rules used to live inside each role's dispatch, which is why the roles
could disagree about them. They are stated once here, and the roles are left
holding only the part that is genuinely theirs - what to say, and to whom.
"""

import yaml

from ..domain import Board, Player, UnitType
from .errors import GameError


def set_board_size(data, command):
    """Size the board, before the game starts."""
    if data.getBoard() is not None:
        raise GameError("can't resize an existing board")
    if command.size_x < 2:
        raise GameError("x must be greater than 1")
    if command.size_y < 2:
        raise GameError("y must be greater than 1")
    try:
        # the board has its own limits beyond the minimum, and states them
        board = Board(command.size_x, command.size_y)
    except AssertionError as e:
        raise GameError(str(e)) from e
    data.setBoard(board)


def add_player(data, command):
    """Register a player, before the game starts."""
    if data.getNewGame() is False:
        raise GameError("can't add players to an existing game")
    data.getPlayers()[command.number] = {
        'obj': Player(command.number),
        'types': {},
    }


def _read_yaml(path, what):
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise GameError(f"Error loading {what} file {path} {e}") from e


def load_board(data, command):
    """Take the board size from a file."""
    board_data = _read_yaml(command.path, 'player')
    size_x = int(board_data['board']['size_x'])
    size_y = int(board_data['board']['size_y'])
    data.setBoard(Board(size_x, size_y))


def load_player(data, command):
    """Take a player, their types and their units from a file."""
    if data.getNewGame() is False:
        raise GameError("can't add players to an existing game")
    player_data = _read_yaml(command.path, 'player')
    number = int(player_data['number'])
    data.getPlayers()[number] = {
        'obj': Player(number),
        'types': player_data['types'],
        'units': player_data['units'],
    }


def define_type(data, command):
    """Define a unit type for the player whose session this is."""
    if not data.getNewGame():
        raise GameError("can't add types after first turn")
    try:
        obj = UnitType(command.name, command.symbol, command.attack,
                       command.health, command.energy)
    except Exception as e:
        raise GameError(f"error adding unit type: {e}") from e
    data.getPlayers()[data.player_number]['types'][command.name] = {
        'name': command.name,
        'symbol': command.symbol,
        'attack': command.attack,
        'health': command.health,
        'energy': command.energy,
        'obj': obj,
    }


def deploy_unit(data, command):
    """Place one of this player's units on the board."""
    board = data.getBoard()
    if board is None:
        raise GameError("board must be loaded in order to place units")
    if not data.getNewGame():
        raise GameError("can't add units after first turn")
    player_obj = data.getPlayerObj(data.player_number)
    seen_board = data.getSeenBoard()
    try:
        unit_type = (data.getPlayers()[data.player_number]
                     ['types'][command.type_name]['obj'])
        board.add(player_obj, command.x, command.y, command.name, unit_type)
        board.commit()
        # the view the server published is what the player is shown, so a unit
        # deployed this turn has to be put there too or it stays invisible to
        # its own owner until the turn resolves. Only this player's own unit is
        # added, so nothing the server has not revealed becomes visible.
        if seen_board is not None:
            seen_board.add(player_obj, command.x, command.y, command.name,
                           unit_type)
            seen_board.commit()
    except Exception as e:
        raise GameError(f"error creating new unit {e}") from e


def order_move(data, command):
    """Order one of this player's units to move."""
    board = data.getBoard()
    if board is None:
        raise GameError("board must be loaded in order to move units")
    if data.getNewGame():
        raise GameError(
            "can't move units until after the first turn is complete")
    try:
        unit = board.getUnitByName(command.unit)[0]
    except Exception as e:
        raise GameError(f"error moving unit {e}") from e
    if data.player_number != unit.player.number:
        raise GameError("can't move units belonging to other players")
    if not unit.on_board:
        raise GameError("can't move units not on the board")
    unit.move(command.direction)
