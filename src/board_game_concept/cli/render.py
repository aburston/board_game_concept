"""Turning game state into the text a terminal shows.

The board is drawn as a grid of single character squares between rules:

    +-+-+-+
    |X|#|#|
    +-+-+-+
    |#|#|#|
    +-+-+-+
"""

from ..domain import Empty

EMPTY_SQUARE = str(Empty())


def square_character(square, player=None):
    """The one character standing for whatever holds this square.

    A square a player may not see reads as empty, so passing a player draws
    the board as that player sees it and passing none draws all of it.
    """
    if type(square) is Empty:
        return EMPTY_SQUARE
    if type(square) is list:
        # a contested square holds several units: show one of them rather
        # than the repr of the list
        occupants = [unit for unit in square if not unit.destroyed]
        if not occupants:
            return EMPTY_SQUARE
        if player is None:
            return str(occupants[0])
        for unit in occupants:
            if unit.player == player:
                return str(unit)
        return EMPTY_SQUARE
    if player is None or square.player == player:
        return str(square)
    return EMPTY_SQUARE


def render_board(board, player=None):
    """The board as lines of text, without a trailing newline."""
    rule = '+' + '-+' * board.size_x
    lines = []
    for row in board.rows():
        lines.append(rule)
        lines.append(
            '|' + '|'.join(square_character(square, player) for square in row) + '|')
    lines.append(rule)
    return '\n'.join(lines)


def print_board(board, player=None):
    print(render_board(board, player))
