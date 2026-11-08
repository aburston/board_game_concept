"""Reading the record back: a turn as a seat may see it, and a type's program.

A game is resolved to its end the moment the last setup is committed, and
every turn is written as it goes. This is what turns one of those records
into something a person can be shown, for whichever role is asking: the
board after the turn, what the turn did, what it would not do for the
player, and what their controllers thought.

Entitlement is decided here and nowhere else. The board after a turn is
drawn whole for everyone, because a replay is watched once the game is over
and nothing on it can still be acted on. A controller's trace is its owner's
and the observer's: contact discloses a type's attack, health and energy and
nothing of how it thinks, so a seat is given its own traces and nobody
else's. The same goes for a program.
"""

from ..domain.events import players_in
from ..domain.program import Program, ProgramError, TICKS_PER_COMPUTE, cap
from ..domain.square import Empty
from ..http.views import FLAG_SYMBOL, _as_int
from . import turn_feed
from .errors import GameError
from .turn import _survivors


# what a square of an army's map is drawn with when the map is all the army
# knows of it. A friend is drawn with its own symbol, as on the board
UNKNOWN_SYMBOL = '?'
ENEMY_SYMBOL = 'E'


def program_view(record):
    """A type's program, line by line with the ticks each line costs.

    `record` is the type as a player's file holds it. The listing says the
    type's compute, how many ticks an energy buys it, the per-turn cap and
    the total of a straight run - which is how a player sees whether the
    program fits its type before a turn tells them it did not.
    """
    compute = _as_int(record.get('compute')) or 0
    text = record.get('program') or ''
    lines = []
    total = 0
    if text:
        try:
            program = Program(text)
        except ProgramError as e:
            raise GameError(f"the stored program is refused at {e}") from e
        for number, raw, ticks in program.listing():
            lines.append({'line': number, 'text': raw, 'ticks': ticks})
        total = program.ticks
    return {
        'type': record.get('name'),
        'compute': compute,
        'program': text or None,
        'lines': lines,
        'total': total,
        'ticks_per_energy': cap(compute),
        'cap': cap(compute),
        'ticks_per_compute': TICKS_PER_COMPUTE,
    }


def turn_view(record, player_number, sees_everything, known=False,
              seat=None):
    """One turn of the record, as this seat may read it.

    The board is drawn from the record's units and flags, whole; or, when
    `known` is asked for, from the seat's own army map as it stood after the
    turn - what the army knew, which is the thing its controllers were
    reading. A session that sees everything has no army of its own and names
    whose knowledge it wants with `seat`. The events, the rejections and the
    traces are the seat's own unless the seat sees everything.
    """
    units = record.get('units') or []
    turn = record.get('turn')
    army = None
    if known:
        army = seat if (sees_everything and seat is not None) else (
            None if sees_everything else player_number)
    if army is not None:
        board = known_board(record, army)
        army_map = (record.get('maps') or {}).get(str(army)) or {}
    else:
        board = record_board(record)
        army_map = None
    events = record.get('events') or []
    traces = record.get('traces') or []
    if not sees_everything:
        events = turn_feed.for_seat(events, player_number)
        traces = [trace for trace in traces
                  if _as_int(trace.get('player')) == int(player_number)]
    progress = record.get('progress') or {}
    return {
        'turn': turn,
        'board': board,
        'known': army,
        'map': army_map,
        'units': [_unit_entry(unit) for unit in units
                  if not unit.get('destroyed')],
        'events': [{'turn': turn, **entry} for entry in events],
        'rejected': rejections_in(record, player_number, sees_everything),
        'traces': traces,
        'outcome': progress.get('outcome'),
        'eliminated': progress.get('eliminated') or [],
    }


def record_board(record):
    """The board after a turn, drawn from the record: every standing unit,
    and a flag where its carrier stands."""
    size = record.get('board') or {}
    size_x, size_y = int(size.get('size_x')), int(size.get('size_y'))
    empty = str(Empty())
    rows = [[empty] * size_x for _ in range(size_y)]
    legend = {}
    for unit in record.get('units') or []:
        if unit.get('destroyed') or not unit.get('on_board'):
            continue
        x, y = _as_int(unit.get('x')), _as_int(unit.get('y'))
        if x is None or y is None or not (0 <= x < size_x and 0 <= y < size_y):
            continue
        symbol = str(unit.get('symbol'))
        rows[y][x] = symbol
        legend[(symbol, _as_int(unit.get('player')), unit.get('type'))] = None
    for flag in record.get('flags') or []:
        x, y = _as_int(flag.get('x')), _as_int(flag.get('y'))
        if not flag.get('standing') or x is None or y is None:
            continue
        if rows[y][x] != empty:
            continue
        rows[y][x] = FLAG_SYMBOL
        legend[(FLAG_SYMBOL, _as_int(flag.get('player')), 'flag')] = None
    return _board(size_x, size_y, empty, rows, legend)


def known_board(record, player_number):
    """The board as one army knew it after a turn: its own units where they
    stand, the enemies it has met where it met them, the squares it has
    walked on as empty, and everything else unknown."""
    size = record.get('board') or {}
    size_x, size_y = int(size.get('size_x')), int(size.get('size_y'))
    empty = str(Empty())
    rows = [[UNKNOWN_SYMBOL] * size_x for _ in range(size_y)]
    legend = {(UNKNOWN_SYMBOL, None, 'unknown'): None}
    army_map = (record.get('maps') or {}).get(str(player_number)) or {}
    for x, y, _turn in army_map.get('visited') or []:
        rows[int(y)][int(x)] = empty
    for x, y, _turn, _attack, _health in army_map.get('enemies') or []:
        rows[int(y)][int(x)] = ENEMY_SYMBOL
        legend[(ENEMY_SYMBOL, None, 'enemy')] = None
    for unit in record.get('units') or []:
        if unit.get('destroyed') or not unit.get('on_board'):
            continue
        if _as_int(unit.get('player')) != int(player_number):
            continue
        x, y = _as_int(unit.get('x')), _as_int(unit.get('y'))
        if x is None or y is None:
            continue
        symbol = str(unit.get('symbol'))
        rows[y][x] = symbol
        legend[(symbol, _as_int(unit.get('player')), unit.get('type'))] = None
    return _board(size_x, size_y, empty, rows, legend)


def _board(size_x, size_y, empty, rows, legend):
    return {
        'size_x': size_x,
        'size_y': size_y,
        'empty': empty,
        'rows': rows,
        'legend': [{'symbol': symbol, 'player': number, 'type': type_name}
                   for symbol, number, type_name
                   in sorted(legend, key=lambda key: (key[1] is None,
                                                      key[1] or 0, key[0]))],
    }


def rejections_in(record, player_number, sees_everything=False):
    """What a turn would not do for this player, read from the record.

    The same refusals the resolution reported when it ran - an order refused
    while it was applied, a move not carried out for want of energy or
    because it would leave the board, a contest that ended undecided - each
    naming the unit, its square and the reason, and each the player's own
    unit and nobody else's of the same name. A seat that sees everything is
    given every player's.
    """
    units = {}
    for unit in record.get('units') or []:
        units[(_as_int(unit.get('player')), unit.get('name'))] = unit
    wanted = None if sees_everything else int(player_number)
    made = []

    def add(owner, name, reason):
        if wanted is not None and owner != wanted:
            return
        unit = units.get((owner, name))
        if unit is None:
            return
        made.append({
            'player': owner,
            'unit': name,
            'type': unit.get('type'),
            'x': _as_int(unit.get('x')),
            'y': _as_int(unit.get('y')),
            'reason': reason,
        })

    for entry in record.get('events') or []:
        detail = entry.get('detail') or {}
        if entry.get('kind') == 'refused':
            for owner in players_in(detail):
                add(owner, detail.get('unit'), detail.get('reason'))
        elif entry.get('kind') == 'undecided':
            where = f"({detail.get('x')}, {detail.get('y')})"
            for owner, name in _survivors(detail):
                add(owner, name, f"the contest at {where} was undecided")
    return made


def _unit_entry(unit):
    """A unit of the record as the units table shows one."""
    return {
        'player': _as_int(unit.get('player')),
        'name': unit.get('name'),
        'type': unit.get('type'),
        'symbol': unit.get('symbol'),
        'attack': _as_int(unit.get('attack')),
        'health': _as_int(unit.get('health')),
        'energy': _as_int(unit.get('energy')),
        'x': _as_int(unit.get('x')),
        'y': _as_int(unit.get('y')),
        'flag': bool(unit.get('flag')),
        # the design, so a unit can be drawn against what it was built with
        'type_attack': _as_int(unit.get('type_attack')),
        'type_health': _as_int(unit.get('type_health')),
        'type_energy': _as_int(unit.get('type_energy')),
    }
