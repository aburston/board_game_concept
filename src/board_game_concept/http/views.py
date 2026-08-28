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

from ..domain import Empty, UnitType, budget

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
            attack = _as_int(unit_type['attack'])
            health = _as_int(unit_type['health'])
            energy = _as_int(unit_type['energy'])
            entries.append({
                'player': number,
                'name': unit_type['name'],
                'symbol': unit_type['symbol'],
                'attack': attack,
                'health': health,
                'energy': energy,
                # what deploying one unit of this type spends, so a player can
                # read the price beside the design rather than adding it up
                'cost': attack + health + energy,
            })
    return entries


def flags_view(entries):
    """Where every flag is, as any session may read it.

    Read from what the resolution published rather than from the session's
    own board: a flag is the one thing shown without contact, so it cannot
    travel inside a view whose whole meaning is "these are units you may
    see". Three fields, and nothing about the unit carrying it.
    """
    made = []
    for entry in entries or []:
        made.append({
            'player': _as_int(entry.get('player')),
            'x': _as_int(entry.get('x')),
            'y': _as_int(entry.get('y')),
            'standing': bool(entry.get('standing')),
        })
    return sorted(made, key=lambda flag: (flag['player'] is None,
                                          flag['player']))


def types_seen_view(entries, met=True):
    """Every enemy design this session has met, as the types view shapes one.

    The same fields `types_view` gives, so a screen can draw one list from
    either, plus the turns the design was first and last met on. A session
    that sees everything is given the types it can see: it has met them all
    by definition, and keeping a second record for it would be a record that
    could disagree with the board.
    """
    made = []
    for entry in entries or []:
        attack = _as_int(entry['attack'])
        health = _as_int(entry['health'])
        energy = _as_int(entry['energy'])
        made.append({
            'player': entry['owner'] if met else entry['player'],
            'name': entry['name'],
            'symbol': entry['symbol'],
            'attack': attack,
            'health': health,
            'energy': energy,
            'cost': attack + health + energy,
            'first_seen': entry.get('first_seen'),
            'last_seen': entry.get('last_seen'),
        })
    return made


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
            # whether this unit carries its player's flag. A seat is only
            # ever given units it may see, so this says nothing it was not
            # already being told - where an enemy flag is comes from `flags`
            'flag': bool(getattr(unit, 'flag', False)),
        })
    return entries


def players_view(players, eliminated=(), board=None):
    """Every registered player, whether they are in the game, and their points.

    The three point numbers are `None` where this session is not entitled to
    know them. That is decided by whether the player's record was read at all
    - a player reads their own and nobody else's - rather than by filtering
    here, so there is nothing for a filter to be forgotten from.
    """
    entries = []
    for number in players:
        player = players[number].get('obj')
        known = player is not None and player.budget is not None
        spent = budget.spent(board, player) if known else None
        entries.append({
            'player': number,
            'status': 'eliminated' if number in eliminated else 'active',
            'budget': player.budget if known else None,
            'spent': spent,
            'left': player.budget - spent if known else None,
        })
    return entries


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
                # what the unit is, as well as what it was told to do. An
                # army that has been committed and not yet resolved is on no
                # board anywhere, so this is the only thing that can be drawn
                # for it - and a player who has just committed their setup
                # was looking at an empty board because of it
                'type': unit.get('type_name') or unit.get('type'),
                'symbol': unit.get('symbol'),
                'attack': _as_int(unit.get('attack')),
                'health': _as_int(unit.get('health')),
                'energy': _as_int(unit.get('energy')),
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


# what a flag is drawn with on a square whose unit this session cannot see.
# One character, like every other square, and not a symbol any type may use:
# a type's symbol is one character a player chose, and a player who chose
# this one would be drawing somebody else's flag
FLAG_SYMBOL = '!'


def board_view(board, player=None, flags=()):
    """The board as it may be seen: its size, its squares, and its symbols.

    The legend is collected from the squares the grid drew, so a symbol that
    was not drawn is not explained either.

    `flags` is where the flags are, which every session may know whatever it
    has met. A flag standing on a square this session cannot otherwise see is
    drawn as a flag - the square, and whose flag it is, and nothing about the
    unit holding it. Where the session can see the unit, the unit is drawn as
    it always was: it is already telling them more than the flag would.
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

    for flag in flags or []:
        x, y = _as_int(flag.get('x')), _as_int(flag.get('y'))
        if not flag.get('standing') or x is None or y is None:
            continue
        if rows[y][x] != str(Empty()):
            continue                    # a unit is drawn there already
        rows[y][x] = FLAG_SYMBOL
        legend[(FLAG_SYMBOL, _as_int(flag.get('player')), 'flag')] = None

    return {
        'size_x': board.size_x,
        'size_y': board.size_y,
        'rows': rows,
        'legend': [{'symbol': symbol, 'player': number, 'type': type_name}
                   for symbol, number, type_name in sorted(legend)],
    }
