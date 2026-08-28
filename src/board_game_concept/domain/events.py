"""What happened while a turn was resolved.

Resolution used to narrate itself to stdout behind a debug flag, which meant
the only way to find out what a turn had done was to edit the source and run
it again. It reports these instead: `Board.commit` returns them in the order
they happened, and the caller decides whether to show them, log them, or throw
them away.
"""


class Event:
    """One thing that happened, with whatever describes it."""

    def __init__(self, kind, **detail):
        self.kind = kind
        self.detail = detail

    def __eq__(self, other):
        return (isinstance(other, Event)
                and self.kind == other.kind
                and self.detail == other.detail)

    def __repr__(self):
        described = ', '.join(f'{k}={v!r}' for k, v in sorted(self.detail.items()))
        return f'Event({self.kind!r}{", " if described else ""}{described})'

    def __str__(self):
        return DESCRIPTIONS.get(self.kind, _fallback)(self.detail)


def _fallback(d):
    return d.get('kind', '') or ', '.join(f'{k}: {v}' for k, v in sorted(d.items()))


# how each kind reads when it is shown to a person
DESCRIPTIONS = {
    'deployed': lambda d: f"{d['unit']} is placed at ({d['x']}, {d['y']})",
    'moved': lambda d: f"{d['unit']} moves to ({d['x']}, {d['y']})",
    'joined': lambda d: f"{d['unit']} joins the contest at ({d['x']}, {d['y']})",
    'engaged': lambda d: f"{d['unit']} engages {d['target']} at ({d['x']}, {d['y']})",
    'contested': lambda d: f"({d['x']}, {d['y']}) is contested by {d['units']} units",
    'attacked': lambda d: f"{d['unit']} attacks {d['target']} for {d['damage']}",
    'destroyed': lambda d: f"{d['unit']} is destroyed",
    'retreated': lambda d: f"{d['unit']} falls back to ({d['x']}, {d['y']})",
    'refused': lambda d: (f"{d['unit']} stays at ({d['x']}, {d['y']}): "
                          f"{d['reason']}"),
    'collided': lambda d: (f"{d['unit']} and {d['target']} collide between "
                           f"({d['x']}, {d['y']}) and ({d['to_x']}, {d['to_y']})"),
    'undecided': lambda d: (f"the contest at ({d['x']}, {d['y']}) is undecided "
                            f"between {d['units']}"),
    'held': lambda d: f"{d['unit']} holds ({d['x']}, {d['y']})",
    'shared': lambda d: f"({d['x']}, {d['y']}) is left shared by {d['units']} units",
    'emptied': lambda d: f"({d['x']}, {d['y']}) is left empty",
    'removed': lambda d: f"{d['unit']} leaves the board",
    'rested': lambda d: f"{d['unit']} rests and recovers to {d['energy']} energy",
}


# the kinds that say a blow was struck. A board marks these squares, and
# what counts as fighting is the domain's to say rather than a browser's
FIGHTING = frozenset((
    'contested', 'collided', 'attacked', 'destroyed', 'undecided', 'engaged'))


def record(kind, detail):
    """One event as the plain record every layer above passes around.

    The wording is worked out here rather than stored beside the event, so a
    log written last week reads the way the game reads today, and the CLI, the
    browser and a stored feed cannot come to describe the same event
    differently.
    """
    detail = dict(detail or {})
    return {
        'kind': kind,
        'detail': detail,
        'text': str(Event(kind, **detail)),
        'fighting': kind in FIGHTING,
    }


def describe(events):
    """The events as lines of text, in the order they happened."""
    return '\n'.join(str(event) for event in events)
