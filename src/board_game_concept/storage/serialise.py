"""Building the plain-data documents storage holds.

Documents are what the port takes now. The YAML backend still writes today's
bytes; anything that used to compose those bytes here composes the document
here and lets the backend turn it into bytes.
"""

from ..service.commands import as_record, from_record


def _visible_to(unit, player):
    """Whether this player is entitled to be told about this unit."""
    if player is None or unit.player == player:
        return True
    # a unit seen by several of the player's units is still one unit, so it
    # is listed once
    return any(player.number == seen.player.number for seen in unit.seen_by)


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

def units_document(board, player=None, in_play_only=False, turn=None):
    """The plain-data document a units file holds.

    Same shape as the file, and what `serialise_units` was implicitly encoding
    as text: `{board, turn, player, units}`. Returned so the port can take
    data and the backend can serialise it however it likes - the YAML backend
    still emits the current bytes, and a database backend can insert rows.
    """
    return {
        'board': {'size_x': board.size_x, 'size_y': board.size_y},
        'turn': turn,
        'player': None if player is None else player.number,
        'units': [
            {'id': index, **_unit_record(unit)}
            for index, unit in enumerate(board.units)
            if not (in_play_only and unit.destroyed)
            and _visible_to(unit, player)
        ],
    }


def _unit_record(unit):
    """One unit as its record fields, less the `id`. Same fields the emitter
    puts in `unit_fields`, in the same order."""
    return {
        'player': unit.player.number,
        'type': unit.type_name,
        'name': unit.name,
        'symbol': unit.symbol,
        'attack': unit.attack,
        'health': unit.health,
        'energy': unit.energy,
        'type_attack': unit.type_attack,
        'type_health': unit.type_health,
        'type_energy': unit.type_energy,
        'x': unit.x, 'y': unit.y,
        'state': unit.state, 'direction': unit.direction,
        'destroyed': unit.destroyed, 'on_board': unit.on_board,
        # whether this unit carries its player's flag. A record written before
        # flags existed has no such field and reads back as carrying nothing,
        # which is what keeps an older game playing under the rules it was set
        # up under
        'flag': unit.flag,
    }
