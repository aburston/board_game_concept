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

from . import render

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


def perform_show(data, command):
    """Print what this `show` command asked for, as it asked for it."""
    subject = command.subject
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
