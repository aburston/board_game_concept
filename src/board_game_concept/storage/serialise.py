"""Writing game state out as YAML.

This is the on-disk format: what the server publishes and what a client reads
back. The roles also print it verbatim for `show units`, so the same text
serves both, and changing it changes both.
"""


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


def serialise_units(board, player=None):
    """The board's units as YAML, limited to what this player may see.

    Passing no player serialises the whole board, which is what the server
    writes as the authoritative record.
    """
    units_str = "board: {" + \
        f" size_x: {board.size_x}, size_y: {board.size_y}" + "}\n"

    if player is None:
        units_str = units_str + f"player: {player}\n"
    else:
        units_str = units_str + f"player: {player.number}\n"

    listed = ""
    for index, unit in enumerate(board.units):
        if _visible_to(unit, player):
            listed = listed + "  - { " + f"id: {index}, " + unit_fields(unit) + " }\n"

    if listed == "":
        units_str = units_str + "units: None\n"
    else:
        units_str = units_str + "units:\n" + listed

    return units_str
