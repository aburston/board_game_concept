"""Which games exist, and what state each is in.

Derived by reading the games, never written down. A registry that is kept
would be a fourth thing to hold in step with the board, and its failure mode
is a lobby that lists a game which is not there or hides one that is. This is
the pattern `turn.py` already uses for elimination - "derived from the board
every turn rather than tracked, so that who is out cannot drift out of step
with what is standing" - and `domain/budget.py` for a player's spend.

The cost is that listing n games opens n games. At the scale this runs at that
is cheaper than the class of bug it avoids; if it ever stops being true, the
answer is a cache with the directory as its source of truth, not a table.
"""

import os

from ..cli import session as session_module
from .errors import GameError


# what a game is doing, in the order a lobby sorts them by
SETTING_UP = 'setting up'
BEING_PLAYED = 'being played'
DECIDED = 'decided'
UNREADABLE = 'unreadable'

# how a game's directory is named under `games/`
PREFIX = '_'


def game_numbers(base_path=None):
    """The numbers of the games under this tree, in order.

    The directory listing is the registry. A game made by a command-line role
    is here without anything having been told about it, and a game that has
    been removed is not.
    """
    root = os.path.join(base_path or session_module.default_base_path(),
                        'games')
    try:
        entries = os.listdir(root)
    except FileNotFoundError:
        return []
    return sorted(entry[len(PREFIX):] for entry in entries
                  if entry.startswith(PREFIX))


def describe(gameno, backend=None, base_path=None):
    """One game as plain data, or as unreadable where it cannot be read.

    A game whose storage is broken is reported rather than raised, so that one
    bad directory does not make the whole lobby unusable.
    """
    try:
        repository = session_module.make_repository(
            gameno, backend=backend, base_path=base_path)
        size = repository.read_board()
        progress = repository.read_progress() or {}
        numbers = repository.player_numbers()
    except Exception as error:            # pylint: disable=broad-except
        return {
            'gameno': gameno,
            'state': UNREADABLE,
            'error': str(error),
            'size_x': None,
            'size_y': None,
            'turn_number': 0,
            'outcome': None,
            'players': [],
        }

    turn_number = int(progress.get('turn') or 0)
    outcome = progress.get('outcome') or None
    return {
        'gameno': gameno,
        'state': _state(turn_number, outcome),
        'size_x': size[0] if size else None,
        'size_y': size[1] if size else None,
        'turn_number': turn_number,
        'outcome': outcome,
        'players': list(numbers),
        'eliminated': list(progress.get('eliminated') or []),
    }


def _state(turn_number, outcome):
    """What a game is doing, decided the way everything else here is.

    A game is being played once a turn has resolved, which is the same line
    `service/accounts.py` draws for whether a seat may still be claimed - the
    administrator's commit that ends setup is not a turn and does not number
    one, so a game whose board is set but which nobody has moved in is still
    being set up.
    """
    if outcome:
        return DECIDED
    if turn_number >= 1:
        return BEING_PLAYED
    return SETTING_UP


def games(backend=None, base_path=None):
    """Every game under this tree, described."""
    return [describe(gameno, backend=backend, base_path=base_path)
            for gameno in game_numbers(base_path)]


def exists(gameno, base_path=None):
    """Whether a game of this number is already there."""
    return gameno in game_numbers(base_path)


def create(gameno, backend=None, base_path=None):
    """Make a new, empty game: no board, no players, nothing played.

    Refuses a number a game already has, leaving the existing game untouched.
    """
    if not str(gameno).strip():
        raise GameError('a game needs a number')
    if exists(gameno, base_path):
        raise GameError(f'game {gameno} already exists')
    repository = session_module.make_repository(
        gameno, backend=backend, base_path=base_path)
    repository.ensure()
    return describe(gameno, backend=backend, base_path=base_path)
