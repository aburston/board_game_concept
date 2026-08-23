"""Writing game state out as YAML.

This is the on-disk format: what the server publishes and what a client reads
back. The roles also print it verbatim for `show units`, so the same text
serves both, and changing it changes both.
"""

from ..service.commands import as_record, from_record


def unit_fields(unit):
    """One unit as the body of a YAML flow mapping, without the braces."""
    # numbers are written as numbers. They used to be quoted, so everything
    # reading a unit back had to convert it again, and a player number that
    # went out as text came back as text and no longer matched the integer the
    # rest of the game knew the player by
    return (
        f'player: {unit.player.number}, '
        f'type: "{unit.type_name}", '
        f'name: "{unit.name}", '
        f'symbol: "{unit.symbol}", '
        f'attack: {unit.attack}, '
        f'health: {unit.health}, '
        f'energy: {unit.energy}, '
        # the design, so that a type learned by contact is the type as its
        # owner built it and not the state the unit was in when it was met
        f'type_attack: {unit.type_attack}, '
        f'type_health: {unit.type_health}, '
        f'type_energy: {unit.type_energy}, '
        f'x: {unit.x}, y: {unit.y}, '
        f'state: {unit.state}, direction: {unit.direction}, '
        f'destroyed: {unit.destroyed}, on_board: {unit.on_board}'
    )


def _visible_to(unit, player):
    """Whether this player is entitled to be told about this unit."""
    if player is None or unit.player == player:
        return True
    # a unit seen by several of the player's units is still one unit, so it
    # is listed once
    return any(player.number == seen.player.number for seen in unit.seen_by)


def serialise_orders(board, player):
    """This player's orders for the turn: their units that are still in play.

    A destroyed unit is not an order. It used to be published like any other,
    in the state that means "waiting to be deployed", and the server dutifully
    tried to deploy it again every turn for the rest of the game.
    """
    return serialise_units(board, player, in_play_only=True)


def serialise_units(board, player=None, in_play_only=False, turn=None):
    """The board's units as YAML, limited to what this player may see.

    Passing no player serialises the whole board, which is what the server
    writes as the authoritative record. Passing `in_play_only` leaves out
    destroyed units, which is what a player publishes as their orders.
    """
    units_str = "board: {" + \
        f" size_x: {board.size_x}, size_y: {board.size_y}" + "}\n"
    if turn is not None:
        units_str = units_str + f"turn: {turn}\n"

    if player is None:
        units_str = units_str + f"player: {player}\n"
    else:
        units_str = units_str + f"player: {player.number}\n"

    listed = ""
    for index, unit in enumerate(board.units):
        if in_play_only and unit.destroyed:
            continue
        if _visible_to(unit, player):
            listed = listed + "  - { " + f"id: {index}, " + unit_fields(unit) + " }\n"

    if listed == "":
        units_str = units_str + "units: None\n"
    else:
        units_str = units_str + "units:\n" + listed

    return units_str


def serialise_draft(commands, turn):
    """A session's uncommitted commands, as the document a draft is kept as.

    The turn is written with them because a draft belongs to one turn. A draft
    found under a turn the game has moved past is work left behind by a session
    that ended while the turn was being resolved, and is discarded rather than
    replayed into a turn it was never meant for.
    """
    return {
        'turn': turn,
        'commands': [as_record(command) for command in commands],
    }


def restore_draft(draft, turn):
    """The commands a draft holds, or none if it is not for this turn.

    Reading a draft that is absent, empty, or stamped with another turn is
    ordinary rather than an error: all three mean there is no work to restore.
    """
    if not draft or draft.get('turn') != turn:
        return []
    records = draft.get('commands') or []
    return [from_record(record) for record in records]
