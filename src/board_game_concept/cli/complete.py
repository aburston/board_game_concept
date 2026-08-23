"""Completing a line that is being typed.

Everything here answers one question - given what has been typed so far, what
words could come next - and answers it from the same two places the session
answers every other question from: the grammar in `grammar.py`, and the role's
table in `roles.py`. A word is offered only where the grammar allows it and
only if the role may run the command it forms, so what is offered before a
line is entered cannot disagree with what is accepted after it.

`candidates` is a function of a string, which is what makes it testable
without a terminal. `install` is the thin shell that hands `readline` the same
function; it is the only part that needs a terminal, and it does nothing at
all where `readline` cannot be imported.

Completion never changes anything. It reads the game the session already holds
in memory - so a unit deployed a moment ago completes - and it never loads,
saves, commits or asks the repository for anything.
"""

import os
import glob

from .grammar import (DIRECTION, DIRECTIONS, Optional, PATH, Slot, TYPE, UNIT)
from .help import usages_for
from . import views


def candidates(line, role, source=None):
    """The words that could follow what has been typed, sorted and unique.

    `line` is the text to the left of the cursor. A line ending in a space is
    a new word starting; anything else is the last word being completed, and
    only candidates beginning with it come back.
    """
    typed = line.split()
    if line == '' or line[-1:].isspace():
        prefix = ''
    else:
        prefix = typed[-1]
        typed = typed[:-1]
    offered = set()
    for usage in usages_for(role):
        element = _next_element(usage, typed)
        if element is None:
            continue
        offered.update(_for_element(element, prefix, source))
    return sorted(word for word in offered if word.startswith(prefix))


def _next_element(usage, typed):
    """What this usage expects after these words, or None if it does not fit.

    A literal must be the word that was typed, a slot takes whatever was
    typed, and an optional is either the word or not there at all - in which
    case the word is offered to the element after it.
    """
    index = 0
    for word in typed:
        while index < len(usage.words):
            element = usage.words[index]
            index += 1
            if isinstance(element, str):
                if element == word:
                    break
                return None
            if isinstance(element, Optional):
                if element.word == word:
                    break
                continue
            # a slot takes any one word
            break
        else:
            # the usage ran out of room while there were still words
            return None
    if index < len(usage.words):
        return usage.words[index]
    return None


def _for_element(element, prefix, source):
    """The candidates one element of a usage contributes."""
    if isinstance(element, str):
        return (element,)
    if isinstance(element, Optional):
        return (element.word,)
    if isinstance(element, Slot):
        return _for_slot(element.kind, prefix, source)
    return ()


def _for_slot(kind, prefix, source):
    """The candidates for a slot, by what it stands for."""
    if kind == DIRECTION:
        return tuple(DIRECTIONS)
    if kind == PATH:
        return _paths(prefix)
    if source is not None:
        if kind == UNIT:
            return tuple(source.units())
        if kind == TYPE:
            return tuple(source.types())
    # a number, a symbol, or a name being invented: nothing to offer, because
    # only the person typing it knows what it is
    return ()


def _paths(prefix):
    """The paths a partly typed one could be, directories marked as such.

    A directory comes back with a separator on the end so that completing it
    once leaves the cursor inside it and the next completion lists it. The
    completer's delimiters are whitespace only, which is what keeps a path
    with a separator in it one word rather than several.
    """
    found = []
    for path in glob.glob(prefix + '*'):
        found.append(path + os.sep if os.path.isdir(path) else path)
    return found


class GameNames:
    """The names of things this session holds that a command can name.

    Read from the views `show` prints, rather than from the board directly, so
    the names offered are the names the player has just been shown. Nothing
    here reads the game again: the session's own game object is already only
    what this role may see, and it already holds everything done this session.
    """

    def __init__(self, data, player_number):
        self.data = data
        self.player_number = player_number

    def _mine(self, entry):
        return _as_int(entry.get('player')) == _as_int(self.player_number)

    def units(self):
        """This player's own units, less the ones that have been destroyed."""
        board = self.data.getBoard()
        if board is None:
            return []
        return sorted({entry['name'] for entry in views.units_view(board)
                       if self._mine(entry) and entry['state'] != 'destroyed'})

    def types(self):
        """The unit types this player has defined."""
        players = self.data.getPlayers()
        if not players:
            return []
        return sorted({entry['name'] for entry in views.types_view(players)
                       if self._mine(entry)})


def _as_int(value):
    """A player number as a number, however it was stored."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def install(role, source=None):
    """Let `readline` complete this role's grammar, if it can.

    Returns whether completion was installed. `readline` is absent on some
    systems and is `libedit` on others, and a session that cannot complete is
    still a session, so neither case is worth a word to the player.
    """
    try:
        # imported here rather than at the top: a session on a system without
        # it is still a session, and this is the one place that would fail
        import readline  # pylint: disable=import-outside-toplevel
    except ImportError:
        return False

    state = {'matches': []}

    def complete(text, index):  # pylint: disable=unused-argument
        # `readline` passes the word being completed and asks for one match at
        # a time. The word is not enough to know which word it is, so the line
        # is read from `readline` itself and `text` goes unused
        if index == 0:
            # the callback is given the current word, not the line, and the
            # line is what says which word this is
            line = readline.get_line_buffer()[:readline.get_endidx()]
            try:
                state['matches'] = candidates(line, role, source)
            except Exception:  # pylint: disable=broad-except
                # a completer that raises is swallowed by readline and leaves
                # the terminal in a state nobody can explain; an empty list is
                # the honest answer for "no idea"
                state['matches'] = []
        if index < len(state['matches']):
            return state['matches'][index]
        return None

    readline.set_completer(complete)
    # whitespace only. The default set includes `/`, which would make
    # `games/bo` complete as the word `bo` and paste the answer over the
    # directory that was already typed
    readline.set_completer_delims(' \t\n')
    if 'libedit' in (readline.__doc__ or ''):
        readline.parse_and_bind('bind ^I rl_complete')
    else:
        readline.parse_and_bind('tab: complete')
    return True
