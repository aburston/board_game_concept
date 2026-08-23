"""Turning what a `show` command has to say into the text a terminal shows.

Layout only. What there is to say is `views.py`'s answer, and this module
decides how it sits on the page: which columns, in what order, padded to what
width. Plain ASCII throughout - no colour and no box drawing - so the same
text reads in a terminal, down a pipe and in a test transcript.

The board is drawn as a grid of single character squares between rules:

    +-+-+-+
    |X|#|#|
    +-+-+-+
    |#|#|#|
    +-+-+-+
"""

from ..domain import Empty
from . import views

EMPTY_SQUARE = str(Empty())

# what a column reads when the game has no value to put in it. An empty column
# is indistinguishable from a value that happens to be blank, and `None` is
# the language talking about itself rather than about the game
MISSING = '-'

# columns are separated by whitespace rather than by rules: the alignment is
# the structure, and a `|` between every pair of columns is noise on top of it
GAP = '  '


def square_character(square, player=None):
    """The one character standing for whatever holds this square.

    A square a player may not see reads as empty, so passing a player draws
    the board as that player sees it and passing none draws all of it.
    """
    unit = views.occupant(square, player)
    return EMPTY_SQUARE if unit is None else str(unit)


def render_grid(rows, size_x):
    """A grid of already-chosen characters, as lines of text."""
    rule = '+' + '-+' * size_x
    lines = []
    for row in rows:
        lines.append(rule)
        lines.append('|' + '|'.join(row) + '|')
    lines.append(rule)
    return '\n'.join(lines)


def render_board(board, player=None):
    """The board as lines of text, without a trailing newline."""
    view = views.board_view(board, player)
    return render_grid(view['rows'], view['size_x'])


def print_board(board, player=None):
    print(render_board(board, player))


def table(headers, rows, numeric=()):
    """Rows of values under their headers, in columns that line up.

    Every column is as wide as the widest thing in it, its header included, so
    a value can be compared with the one above it without counting commas.
    Numeric columns are right-aligned, because lining up the last digit is
    what makes 10 obviously more than 3; everything else reads from the left.
    No line carries trailing whitespace, so nothing shifts when the text is
    copied out of a terminal.
    """
    headers = [str(header) for header in headers]
    body = [[MISSING if value is None else str(value) for value in row]
            for row in rows]
    widths = [max([len(header)] + [len(row[index]) for row in body])
              for index, header in enumerate(headers)]
    right = {index for index, header in enumerate(headers)
             if header in numeric}

    def line(cells):
        padded = [cell.rjust(widths[index]) if index in right
                  else cell.ljust(widths[index])
                  for index, cell in enumerate(cells)]
        return GAP.join(padded).rstrip()

    return '\n'.join([line(headers)] + [line(row) for row in body])


def _print_table(entries, headers, keys, numeric, nothing):
    """One subject as a table, or one line saying there is none of it.

    A header with no rows under it reads as a table that failed to load, which
    is not what an empty game means.
    """
    if not entries:
        print(nothing)
        return
    rows = [[entry.get(key) for key in keys] for entry in entries]
    print(table(headers, rows, numeric))


def print_types(entries):
    _print_table(
        entries,
        headers=('PLAYER', 'NAME', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY'),
        keys=('player', 'name', 'symbol', 'attack', 'health', 'energy'),
        numeric=('PLAYER', 'ATTACK', 'HEALTH', 'ENERGY'),
        nothing='no unit types yet')


def print_units(entries):
    _print_table(
        entries,
        headers=('PLAYER', 'NAME', 'TYPE', 'SYMBOL', 'ATTACK', 'HEALTH',
                 'ENERGY', 'X', 'Y', 'STATE', 'DIRECTION'),
        keys=('player', 'name', 'type', 'symbol', 'attack', 'health',
              'energy', 'x', 'y', 'state', 'direction'),
        numeric=('PLAYER', 'ATTACK', 'HEALTH', 'ENERGY', 'X', 'Y'),
        nothing='no units yet')


def print_players(entries):
    _print_table(
        entries,
        headers=('PLAYER', 'STATUS'),
        keys=('player', 'status'),
        numeric=('PLAYER',),
        nothing='no players yet')


def print_pending(entries):
    _print_table(
        entries,
        headers=('PLAYER', 'UNIT', 'ORDER', 'X', 'Y'),
        keys=('player', 'unit', 'order', 'x', 'y'),
        numeric=('PLAYER', 'X', 'Y'),
        nothing='no orders pending')


def print_board_view(view):
    """The grid, and what the symbols on it stand for.

    The legend is collected from the squares that were drawn, so a board with
    nothing visible on it has nothing to explain and gets no legend.
    """
    print(render_grid(view['rows'], view['size_x']))
    if not view['legend']:
        return
    print()
    print(table(
        ('SYMBOL', 'PLAYER', 'TYPE'),
        [[entry['symbol'], entry['player'], entry['type']]
         for entry in view['legend']],
        numeric=('PLAYER',)))
