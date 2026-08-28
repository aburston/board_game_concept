"""What a caller may ask of a game, and the rules about when.

One function per command object. Each carries out the command or refuses it by
raising, and none of them prints anything or reads a line of input: a caller
that is not a terminal gets the same rules and the same refusals.

These rules used to live inside each role's dispatch, which is why the roles
could disagree about them. They are stated once here, and the roles are left
holding only the part that is genuinely theirs - what to say, and to whom.
"""

import yaml

from ..domain import Board, Player, UnitType, budget
from . import identity
from .errors import GameError


def set_board_size(data, command):
    """Size the board, and size it again, until setup is committed.

    A board that existed could not be resized, so an administrator who typed
    the wrong number had a game to throw away and make again. Setup is a
    thing you are still deciding: the size stands when it is committed, and
    until then it can be changed like everything else in it.
    """
    if not data.getNewGame():
        raise GameError("can't resize the board once setup is committed")
    if command.size_x < 2:
        raise GameError("x must be greater than 1")
    if command.size_y < 2:
        raise GameError("y must be greater than 1")
    try:
        # the board has its own limits beyond the minimum, and states them.
        # Built and thrown away here so a refused size is refused before
        # anything standing is moved onto a board that will not exist
        Board(command.size_x, command.size_y)
    except AssertionError as e:
        raise GameError(str(e)) from e
    data.resizeBoard(command.size_x, command.size_y)


def remove_player(data, command):
    """Take a registered player out of the game, before setup is committed."""
    if data.getNewGame() is False:
        raise GameError("can't remove players from an existing game")
    if not identity.is_player(command.number):
        raise GameError(identity.out_of_range(command.number))
    data.removePlayer(command.number)


def _player(number, points=Player.DEFAULT_BUDGET):
    """A player of that number, or a refusal saying why there cannot be one.

    The range is the domain's and `Player` states it - both the number's and
    the budget's; this turns the refusal into one a caller can act on, as
    `set_board_size` does for the board's own limits. Without it the assertion
    escapes as an `AssertionError`, which the roles do not catch, and a
    mistyped number ends the session.
    """
    if not identity.is_player(number):
        raise GameError(identity.out_of_range(number))
    try:
        return Player(number, points)
    except AssertionError as e:
        raise GameError(str(e)) from e


def add_player(data, command):
    """Register a player, with their point budget, before the game starts."""
    if data.getNewGame() is False:
        raise GameError("can't add players to an existing game")
    player = _player(command.number, command.budget)
    data.getPlayers()[command.number] = {
        'obj': player,
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
    # a file is written by hand, so its number is checked here at the edge the
    # same way one typed at the prompt is - and so is its budget. A file with
    # no `budget:` is a budget the author did not choose, which is what the
    # default is for; a *stored* record with none is a different thing and
    # `game-persistence` refuses it
    points = player_data.get('budget', Player.DEFAULT_BUDGET)
    try:
        points = int(points)
    except (TypeError, ValueError) as e:
        raise GameError(f"budget must be a number in {command.path}") from e
    player = _player(number, points)
    data.getPlayers()[number] = {
        'obj': player,
        'types': player_data['types'],
        'units': player_data['units'],
    }


def _setup_is_closed(data, what):
    """Why nothing more may be added, said as it actually is.

    Setup closes when this session commits it, which is before the first turn
    is resolved rather than after it. Telling a player who has just committed
    that they cannot deploy "after first turn" describes a turn that has not
    happened, on a board that is showing them nothing of theirs - so it reads
    as a defect rather than as the rule it is.
    """
    if data.getTurnNumber() == 0:
        return (f"your setup is committed, so no more {what} can be added - "
                "the game begins when every player has committed")
    return f"can't add {what} after first turn"


def define_type(data, command):
    """Define a unit type for the player whose session this is."""
    if not data.getNewGame():
        raise GameError(_setup_is_closed(data, 'types'))
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
        raise GameError(_setup_is_closed(data, 'units'))
    player_obj = data.getPlayerObj(data.player_number)
    try:
        unit_type = (data.getPlayers()[data.player_number]
                     ['types'][command.type_name]['obj'])
    except Exception as e:
        raise GameError(f"error creating new unit {e}") from e

    # what the budget will not pay for is refused before anything is placed,
    # so a refusal leaves the game exactly as it was and `perform` records
    # nothing. The board asked is the client's own view, which holds all of
    # this player's own units - including one deployed a moment ago - so the
    # spend it is judged against is complete
    refusal = budget.refusal(board, player_obj, unit_type)
    if refusal is not None:
        raise GameError(refusal)

    try:
        # the client holds one board, which is the view it was published, so a
        # unit deployed this turn goes into it and is visible to its owner at
        # once. It used to hold a second, fuller board as well, which had to be
        # kept in step with the view and was the reason a just-deployed unit
        # could not be seen
        board.add(player_obj, command.x, command.y, command.name, unit_type)
        board.commit()
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
    # scoped to this player, so that an opponent holding a unit of the same
    # name cannot make a player's own order unanswerable. `board-model` allows
    # two players to reuse a name, and the unscoped lookup returned whichever
    # was registered first
    player_obj = data.getPlayerObj(data.player_number)
    try:
        unit = board.getUnitByName(command.unit, player_obj)[0]
    except Exception as e:
        raise GameError(f"error moving unit {e}") from e
    if data.player_number != unit.player.number:
        raise GameError("can't move units belonging to other players")
    if not unit.on_board:
        raise GameError("can't move units not on the board")
    unit.move(command.direction)


def set_flag(data, command):
    """Designate which of this player's units carries their flag.

    Made during setup and fixed by the commit that ends it. It may be moved
    from one of the player's units to another until then - designating is a
    setup decision like the board's size or a seat, and every other one can be
    taken back until it is committed.
    """
    board = data.getBoard()
    if board is None:
        raise GameError("board must be loaded in order to carry a flag")
    if not data.getNewGame():
        raise GameError(
            "the flag is fixed for the game: it is designated during setup "
            "and cannot be moved once that setup is committed")
    player_obj = data.getPlayerObj(data.player_number)
    unit = board.findUnit(command.unit, player_obj)
    if unit is None:
        raise GameError(
            f"there is no unit of yours called {command.unit} to carry the "
            f"flag")
    # exactly one, enforced where the designation is made rather than
    # reconciled later: a board that holds two carriers for one player is a
    # state nothing else in the game knows how to read
    for held in board.units:
        if held.player is not None and held.player.number == data.player_number:
            held.flag = False
    unit.flag = True


# which function carries out which command. Named here rather than by building
# a function name from the kind, so that a helper in this module cannot become
# a command by accident - the same reason `parser.py` names its verbs one by
# one instead of looking them up
def set_new_game(data, command):
    """End the setup phase. Only the administrator sends this; over HTTP it
    is a command like any other so the wire has one shape."""
    data.setNewGame(bool(command.new_game))


ACTIONS = {
    'set_board': set_board_size,
    'add_player': add_player,
    'remove_player': remove_player,
    'load_board': load_board,
    'load_player': load_player,
    'add_type': define_type,
    'add_unit': deploy_unit,
    'set_flag': set_flag,
    'move': order_move,
    'set_new_game': set_new_game,
}


def carries_out(command):
    """Whether this is a command that does something to a game."""
    return command.kind in ACTIONS


def carry_out(data, command):
    """Do what this command asks, recording nothing.

    Replaying a draft comes through here: the rules are applied again, but the
    commands are already written down and must not be written down twice.
    """
    action = ACTIONS.get(command.kind)
    if action is None:
        raise GameError(f"{command.kind} is not something to do to a game")
    action(data, command)


def perform(data, command):
    """Do what this command asks, and remember that it was asked.

    The one way a caller changes a game. Recording here rather than in each
    caller is what stops a session's work being lost when the session ends -
    and stops a caller added later from quietly not recording, which would
    look like working code and lose somebody's army.

    A command that is refused is not recorded: the draft holds what was done,
    not what was attempted.

    Whether the caller may change a game at all is decided here, from its
    identity. `cli/roles.py` decides it too, by not offering the observer a
    command that writes - which is enough for a person at a prompt and nothing
    at all for a caller that does not go through one.
    """
    if not identity.may_change(data.player_number):
        raise GameError(
            f"{identity.describe(data.player_number)} may not change a game")
    carry_out(data, command)
    data.recordDraft(command)
