"""Who a session is, and what that entitles it to.

Every session opens a game as a number, and that number is the whole of who the
session is. Three kinds of session share the numbering: the administrator who
sets a game up, the players who own units, and the observer who watches.

The reserved numbers live here rather than in the domain because the
administrator and the observer are roles a caller takes, not things the rules of
the game know about - the engine resolves turns for players and has never heard
of an administrator. What a *player's* number may be is the domain's, and is
taken from `Player` rather than restated.

These functions exist because the questions used to be asked as `player_number
== 0`, which was three different questions wearing one test: may this session
see everything, does it own units, and must its number be a registered player.
Widening that test to cover a second privileged number would have broken each of
them differently.
"""

from ..domain import Player

# the game's administrator and commit authority, who owns no units
ADMINISTRATOR = 0

# the neutral, read-only view, which owns no units and changes nothing
OBSERVER = 1000

RESERVED = (ADMINISTRATOR, OBSERVER)


def is_player(number):
    """Whether this number is one a player of a game may have."""
    return isinstance(number, int) and Player.FIRST <= number <= Player.LAST


def identifies_anyone(number):
    """Whether a session may be opened as this number at all."""
    return number in RESERVED or is_player(number)


def sees_everything(number):
    """Whether this identity is entitled to the whole game.

    Two identities are, which is the reason this is a question rather than a
    comparison with zero.
    """
    return number in RESERVED


def may_change(number):
    """Whether this identity may change a game.

    Not the same as being a player: the administrator sets a game up and commits
    it. What this excludes is the observer, which the command line already
    excludes by not offering it a command that writes - and which nothing
    excluded below the command line.
    """
    return number != OBSERVER


def describe(number):
    """What this identity is called, for a message a person reads."""
    if number == ADMINISTRATOR:
        return 'the administrator'
    if number == OBSERVER:
        return 'the observer'
    if is_player(number):
        return f'player {number}'
    return f'{number}'


def out_of_range(number):
    """Why this number is not a player's, as a message naming the range."""
    if number in RESERVED:
        return (f'{number} is reserved for {describe(number)} '
                f'and cannot be a player')
    return (f"a player's number must be from {Player.FIRST} "
            f'to {Player.LAST}')
