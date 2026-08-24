"""What a `show` command has to say, before anyone has decided how to say it.

One function per subject, each returning plain data - lists of dicts, and for
the board a dict of dimensions and rows. Nothing here prints, and nothing here
knows whether the answer is going out as a table or as JSON. That is the whole
point: the two formats are two renderings of one value, so they cannot come to
disagree about what is on the board the way three hand-written `show` ladders
did.

Visibility is not decided here either. A role's game already holds only what
that role may see - a client is loaded from its own published view - so a view
built from it is already limited to what may be shown.

The words are also chosen here rather than in the renderer: a state of 1 is
`moving` in a table and in JSON alike, because that is content, not layout.
"""

from ..domain import Empty, UnitType

# what the stored numbers mean, said the way a player says them
DIRECTION_WORDS = {
    UnitType.NONE: None,
    UnitType.NORTH: 'north',
    UnitType.EAST: 'east',
    UnitType.SOUTH: 'south',
    UnitType.WEST: 'west',
}

STATE_WORDS = {
    UnitType.INITIAL: 'waiting',
    UnitType.MOVING: 'moving',
    UnitType.NOP: 'holding',
}


def direction_word(direction):
    """Which way an order points: `north`, `east`, `south`, `west`, or None.

    This is the order's direction, not a heading the unit keeps. A unit is not
    facing anywhere: resolving a turn consumes the order and clears it, so a
    unit that is not under orders has no direction at all.
    """
    return DIRECTION_WORDS.get(_as_int(direction))


def state_word(state, destroyed=False):
    """What a unit is doing: destroyed first, since it is doing nothing else."""
    if destroyed:
        return 'destroyed'
    return STATE_WORDS.get(_as_int(state), 'holding')


def order_word(state, direction):
    """The order a published unit carries: a move, a deployment, or nothing."""
    state = _as_int(state)
    if state == UnitType.MOVING:
        heading = direction_word(direction)
        return f"move {heading}" if heading else 'hold'
    if state == UnitType.INITIAL:
        return 'deploy'
    return 'hold'


def _as_int(value):
    """A stored value as the number it means, or None if it is not one.

    Orders are read back from YAML a player's client wrote, so a value that
    should be a number can arrive as text.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _on_board(unit):
    """Whether this unit is standing somewhere, rather than gone or waiting."""
    return (unit.on_board
            and not unit.destroyed
            and unit.state != UnitType.INITIAL)


def types_view(players):
    """Every unit type these players hold, one entry each."""
    entries = []
    for number in players:
        for type_name in players[number].get('types', {}):
            unit_type = players[number]['types'][type_name]
            entries.append({
                'player': number,
                'name': unit_type['name'],
                'symbol': unit_type['symbol'],
                'attack': _as_int(unit_type['attack']),
                'health': _as_int(unit_type['health']),
                'energy': _as_int(unit_type['energy']),
            })
    return entries


def units_view(board):
    """Every unit this board holds, with the values play has left it.

    A unit's statistics are its own, not its type's: a unit that has been
    fought has less health than it was built with, and that is what a player
    needs to see.
    """
    entries = []
    for unit in board.units:
        placed = _on_board(unit)
        entries.append({
            'player': unit.player.number,
            'name': unit.name,
            'type': unit.type_name,
            'symbol': unit.symbol,
            'attack': unit.attack,
            'health': unit.health,
            'energy': unit.energy,
            'x': unit.x if placed else None,
            'y': unit.y if placed else None,
            'state': state_word(unit.state, unit.destroyed),
            'direction': direction_word(unit.direction) if placed else None,
        })
    return entries


def players_view(players, eliminated=()):
    """Every registered player, and whether they are still in the game."""
    return [{
        'player': number,
        'status': 'eliminated' if number in eliminated else 'active',
    } for number in players]


def _is_deployment(board, owner, name):
    """Whether this order asks for a unit the board does not hold yet.

    The same rule the turn resolves by: a published unit its owner's board has
    never heard of is being deployed, whatever else its order says.
    """
    if board is None or owner is None:
        return False
    return board.findUnit(name, owner) is None


def pending_view(players, board=None):
    """The orders published for the coming turn, flattened across players.

    A player publishes their orders as the units they hold; each carries the
    order it was given in its state and direction. Passing the board lets a
    unit that is not on it yet be named as the deployment it is, rather than
    as the standing still its order technically asks for.
    """
    entries = []
    for number in players:
        moves = players[number].get('moves')
        if not moves:
            continue
        units = moves.get('units')
        # a player holding no units publishes "units: None", which reads back
        # as the string rather than as null
        if not units or units == 'None':
            continue
        for unit in units:
            name = unit.get('name')
            order = order_word(unit.get('state'), unit.get('direction'))
            if order == 'hold' and _is_deployment(
                    board, players[number].get('obj'), name):
                order = 'deploy'
            entries.append({
                'player': _as_int(unit.get('player')),
                'unit': name,
                'order': order,
                'x': _as_int(unit.get('x')),
                'y': _as_int(unit.get('y')),
            })
    return entries


def occupant(square, player=None):
    """The unit this square shows, or None if it shows nothing.

    The rule is the one the grid is drawn by: a square a player may not see
    holds nothing as far as they are concerned, and a contested square shows
    the player their own unit before anyone else's.
    """
    if type(square) is Empty:
        return None
    if type(square) is list:
        occupants = [unit for unit in square if not unit.destroyed]
        if not occupants:
            return None
        if player is None:
            return occupants[0]
        for unit in occupants:
            if unit.player == player:
                return unit
        return None
    if player is None or square.player == player:
        return square
    return None


def board_view(board, player=None):
    """The board as it may be seen: its size, its squares, and its symbols.

    The legend is collected from the squares the grid drew, so a symbol that
    was not drawn is not explained either.
    """
    rows = []
    legend = {}
    for row in board.rows():
        drawn = []
        for square in row:
            unit = occupant(square, player)
            if unit is None:
                drawn.append(str(Empty()))
                continue
            drawn.append(str(unit))
            legend[(str(unit), unit.player.number, unit.type_name)] = None
        rows.append(drawn)
    return {
        'size_x': board.size_x,
        'size_y': board.size_y,
        'rows': rows,
        'legend': [{'symbol': symbol, 'player': number, 'type': type_name}
                   for symbol, number, type_name in sorted(legend)],
    }
