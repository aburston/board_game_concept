"""Answering a `show` command, once, for whichever role asked.

The three roles used to hold a copy each of the same ladder of subjects, and
the copies had drifted: two of them printed pending orders by interpolating a
raw dictionary, and all three printed the storage YAML as though it were
display. There is one ladder now, and `roles.py` still decides which subjects
a role may ask for, so the observer is no more able to see a player's hand
than it was.

The format is chosen here and nowhere else: the same view is either drawn as a
table or written as JSON, so the two cannot describe different games.
"""

import json

from ..service.errors import GameError
from . import render

# what to say when the record is asked for before there is one
NOT_RESOLVED = "the game has not been resolved"

# what to say when a subject needs a board and the game has not been given one
# yet. It is a refusal rather than an answer, so it is said in words even when
# JSON was asked for - as `invalid show command` is
NO_BOARD = "must create board - set size and commit"

# the subjects that have nothing to say until the board exists
NEEDS_BOARD = ('board', 'units', 'placement')


def _view(data, subject):
    """What this subject has to say, as plain data.

    The session builds it: `LocalSession` computes from live objects,
    `HttpSession` fetches from the server. Either way the value is the same
    JSON the terminal renders below.
    """
    return data.getView(subject)


def _print_table(subject, view):
    if subject == 'board':
        render.print_board_view(view)
    elif subject == 'units':
        render.print_units(view)
    elif subject == 'types':
        render.print_types(view)
    elif subject == 'players':
        render.print_players(view)
    elif subject == 'events':
        render.print_events(view)
    elif subject == 'designs':
        render.print_designs(view)
    elif subject == 'flags':
        render.print_flags(view)
    elif subject == 'placement':
        render.print_placement(view)
    else:
        render.print_pending(view)


def show_units(data):
    """The units table, printed without having been asked for by name.

    The client reads a player's units back to them after an order, so that
    they can see it took. That read-back is the same listing `show units`
    gives and is written by the same code, rather than being the storage YAML
    it used to be.
    """
    render.print_units(data.getView('units'))


def perform_show(data, command, replay=None):
    """Print what this `show` command asked for, as it asked for it.

    `replay` is the session's place in the record, for a `show turn`: the
    turn shown becomes the one `next` and `prev` step from.
    """
    subject = command.subject
    if subject == 'program':
        try:
            view = data.getProgram(command.name)
        except GameError as error:
            for line in error.lines():
                print(line)
            return
        if command.format == 'json':
            print(json.dumps({subject: view}, indent=2))
            return
        render.print_program(view)
        return
    if subject == 'turn':
        if replay is None:
            replay = Replay(data)
        if command.format == 'json':
            view, refusal = replay.view(command.turn, known=command.known)
            if view is None:
                print(refusal)
                return
            replay.current = int(command.turn)
            print(json.dumps({subject: view}, indent=2))
            return
        replay.show(command.turn, known=command.known)
        return
    if subject in NEEDS_BOARD and data.getBoard() is None:
        print(NO_BOARD)
        return
    view = _view(data, subject)
    if command.format == 'json':
        # one document, named for its subject, so a reader can tell what it is
        # holding and a later field can be added beside it
        print(json.dumps({subject: view}, indent=2))
        return
    _print_table(subject, view)


class Replay:
    """Where a session is in the record, and how it moves through it.

    Every role reads the record the same way - a turn at a time, forwards
    and back - and refuses to read it while any setup is outstanding: a game
    is resolved to its end the moment the last setup is committed, so a game
    without an outcome has no record to show.
    """

    def __init__(self, data):
        self.data = data
        self.current = None

    def refusal(self):
        """Why the record cannot be read now, or None if it can."""
        if self.data.getOutcome() is not None:
            return None
        waiting = self.data.waitingOn()
        if waiting:
            who = ', '.join(str(number) for number in waiting)
            return (f"{NOT_RESOLVED}: waiting for player(s) {who} to "
                    f"commit their setup")
        return f"{NOT_RESOLVED} yet"

    def view(self, turn, known=False):
        """One turn's view, or None and why not."""
        refusal = self.refusal()
        if refusal is not None:
            return None, refusal
        view = self.data.getTurn(turn, known=known)
        if view is None:
            turns = self.data.turnNumbers()
            held = (f"turns {turns[0]} to {turns[-1]}" if turns
                    else "no turns")
            return None, f"the record has no turn {turn}; it holds {held}"
        return view, None

    def show(self, turn, known=False):
        view, refusal = self.view(turn, known=known)
        if view is None:
            print(refusal)
            return False
        self.current = int(turn)
        render.print_turn(view)
        return True

    def final(self, known=False):
        """The last turn of the record, which is where a resolved game
        opens."""
        turns = self.data.turnNumbers()
        if not turns:
            return False
        return self.show(turns[-1], known=known)

    def step(self, by):
        if self.current is None:
            refusal = self.refusal()
            if refusal is not None:
                print(refusal)
                return False
            print("no turn is being shown; `show turn <n>` first")
            return False
        return self.show(self.current + by)
