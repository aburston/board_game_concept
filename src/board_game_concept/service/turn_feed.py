"""What each seat is told the turn did.

`Board.commit` has always reported what it did - a move, an engagement, every
attack with its damage, a destruction - and every one of those reports was
thrown away as soon as the refusals had been picked out of it. A player was
left to work out from the board what had happened to them, and could not: a
unit that lost eight health looks exactly like a unit that lost none, and a
square that was fought over looks exactly like a square that was not.

This turns those events into a feed, one entry per thing that happened, and
decides which of them each seat is entitled to read. Two rules do that
deciding, and they are the whole of the visibility policy here:

  - a seat is told about anything one of its own units did or had done to it;
  - a seat is told about other people's units only where it could see every
    unit involved, which is what `visibility` already grants it.

An entry that names no unit - a square being contested, emptied or shared - is
told to a seat only where that seat was already told about something else at
the same square, so it reads as context for a fight the seat can see rather
than as news of one it cannot.

The engine does not put coordinates on an attack or a destruction, because it
reports them from inside the contest that already said where it was. The feed
does, by carrying the square of the contest onto the entries that follow it:
what a player wants to know is where they were hit, and "somewhere" is not an
answer a board can draw.
"""

from ..domain.events import Event, players_in, record

# the kinds that open a fight at a square. Everything reported until the next
# one of these belongs to that square
CONTESTS = ('contested', 'collided')

# the kinds that carry their own square
PLACED = ('deployed', 'moved', 'joined', 'engaged', 'refused', 'retreated',
          'held', 'undecided', 'emptied', 'shared')

# the kinds reported from inside a contest, which is where they happened.
# `removed` is not one of them: every destroyed unit is taken off the board
# together at the end of the turn, by which time the contest being spoken of
# is whichever was fought last, and that is somebody else's square
INSIDE = ('attacked', 'destroyed')

# what a square came to rather than what one player did to another. These are
# told to everyone who was in the fight, whoever they name: a unit falling is
# the square's outcome, and a seat that struck it is entitled to know it fell
OUTCOMES = ('destroyed', 'removed')


def entries(events):
    """Every event as a plain record, with the square it happened on.

    The order is the order it happened in, which is the order a person reads
    it back in. `text` is the domain's own wording, so the browser, the CLI
    and a log all say the same thing about the same event.
    """
    made = []
    at_x = at_y = None
    for event in events:
        detail = dict(event.detail)
        if event.kind in CONTESTS or event.kind in PLACED:
            if detail.get('x') is not None:
                at_x, at_y = detail['x'], detail['y']
        elif event.kind in INSIDE and at_x is not None and 'x' not in detail:
            # an attack or a destruction inside the contest just announced
            detail['x'] = at_x
            detail['y'] = at_y
        made.append(record(event.kind, detail))
    return made


def names_in(entry):
    """Every unit this entry names.

    `units` is a count in some kinds and a list of names in others, which is
    the engine's shape rather than a choice made here: a value that is not a
    string is a number of contestants and names nobody.
    """
    detail = entry.get('detail') or {}
    found = set()
    for key in ('unit', 'target'):
        if detail.get(key):
            found.add(str(detail[key]))
    listed = detail.get('units')
    if isinstance(listed, str):
        found.update(name for name in listed.split(',') if name)
    return found


def for_seat(made, number):
    """The entries one seat may read, in the order they happened.

    `number` is that seat's player number, and it is the whole of the rule: an
    entry reaches a seat where one of its own units is named in it.

    It used to reach a seat where every unit named was one that seat could
    see, which meant a player standing beside a contest they took no part in
    read every blow struck in it. Being able to see two units is not being in
    their fight, and what they did to each other is theirs. A seat in a
    three-way contest is told what it struck and what struck it, and not what
    the other two did to one another.

    Whose units an entry names is read from the entry rather than matched
    against a list of names. It used to be matched: a seat held the names of
    its own units and kept an entry that mentioned one of them. A name only
    has to be unique within one player's own units, though, so two players who
    both called a unit `scout` each read the other's entries about it - and
    two players handed the same default army did it every game.
    """
    number = int(number)
    kept = []
    squares = set()
    for index, entry in enumerate(made):
        named = names_in(entry)
        if not named:
            continue                       # square-only, decided below
        if entry['kind'] in OUTCOMES:
            continue                       # the square's, decided below too
        if number not in players_in(entry.get('detail')):
            continue
        kept.append(index)
        square = _square(entry)
        if square is not None:
            squares.add(square)

    # what the square itself came to, kept where the seat was in the fight: a
    # square it had a unit in is one it may be told was contested, and one
    # where it may be told a unit fell. A unit falling in front of you is not
    # a thing that can be kept from you, and being told you killed something
    # is the whole point of having struck it - `destroyed` names the unit that
    # fell and nobody else, so the rule above would otherwise withhold a
    # player's own kill from them
    for index, entry in enumerate(made):
        if names_in(entry) and entry['kind'] not in OUTCOMES:
            continue
        square = _square(entry)
        if square is not None and square in squares:
            kept.append(index)

    return [made[index] for index in sorted(kept)]


def _square(entry):
    detail = entry.get('detail') or {}
    if detail.get('x') is None or detail.get('y') is None:
        return None
    return (detail['x'], detail['y'])


def as_events(made):
    """The records back as `Event`s, for a caller that wants the domain type."""
    return [Event(entry['kind'], **entry['detail']) for entry in made]
