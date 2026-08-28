"""What a caller may ask about an account, and the rules about when.

One function per use case, in the shape `service/games.py` has: each carries
out what it is asked or refuses it by raising, and none of them prints
anything or reads a line of input.

The question this module answers is *which numbers may this account be*.
`service/identity.py` answers a different one - what a *number* is entitled to
- and is not touched by any of this. Keeping the two apart is what lets the
numbers, and everything the rules say about them, stay exactly as they were
while the way a session comes by one changes completely.
"""

from ..domain import Kind
from ..domain import account as account_rules
from ..storage.sqlite_account_store import (
    hash_password, new_token, password_matches, session_expiry)
from . import identity
from .errors import (AccountError, NotAuthenticated, NotAuthorised,
                     PasswordMustChange)


def register(store, username, password):
    """Create an account of the player kind.

    Every refusal is `domain/account.py`'s to state; this asks rather than
    deciding, so the rule cannot be enforced differently here than it is
    wherever else a name or a password arrives.
    """
    refusal = account_rules.username_refusal(username)
    if refusal is not None:
        raise AccountError(refusal)
    refusal = account_rules.password_refusal(password)
    if refusal is not None:
        raise AccountError(refusal)
    if store.read_account_by_name(username) is not None:
        raise AccountError(f'{username.strip()} is already taken')
    try:
        return store.create_account(username, hash_password(password),
                                    Kind.PLAYER)
    except ValueError as error:
        # the store's unique index refused it, which is the same refusal
        # arriving from the other end of a race
        raise AccountError(str(error)) from error


def authenticate(store, username, password, minted=False, label=None):
    """A token for this account, or a refusal that says nothing useful.

    The refusal does not say whether the username or the password was wrong,
    and the same hashing work is done either way, so that a caller cannot
    learn which names exist by asking.
    """
    account = store.read_account_by_name(username)
    if account is None:
        # hash something anyway, so an unknown name does not answer faster
        # than a wrong password
        hash_password(password if isinstance(password, str) else '')
        raise NotAuthenticated('that username and password do not match')
    if not password_matches(account.password_hash, password):
        raise NotAuthenticated('that username and password do not match')
    token = new_token()
    store.create_session(account.account_id, token,
                         session_expiry(minted=minted), label=label)
    return account, token


def account_for(store, token):
    """The account this token identifies, or a refusal."""
    account = store.read_session(token)
    if account is None:
        raise NotAuthenticated('not signed in')
    return account


def end_token(store, token):
    """End one token."""
    store.delete_session(token)


def mint_token(store, account, label=None):
    """A long-lived token for a program to use.

    The same `sessions` row a login makes, with a label and a distant expiry.
    """
    token = new_token()
    store.create_session(account.account_id, token,
                         session_expiry(minted=True), label=label)
    return token


def change_password(store, account, current, new):
    """Change an account's own password, given the one it has now."""
    if not password_matches(account.password_hash, current):
        raise NotAuthorised('that is not the current password')
    refusal = account_rules.password_refusal(new)
    if refusal is not None:
        raise AccountError(refusal)
    store.set_password(account.account_id, hash_password(new))


def reset_password(store, caller, username, new):
    """Set another account's password. The administrator's to do."""
    if not caller.is_administrator():
        raise NotAuthorised('only the administrator may set another '
                            "account's password")
    refusal = account_rules.password_refusal(new)
    if refusal is not None:
        raise AccountError(refusal)
    target = store.read_account_by_name(username)
    if target is None:
        raise AccountError(f'there is no account named {username}')
    store.set_password(target.account_id, hash_password(new))
    return target


def require_usable(account):
    """Refuse an account that has not changed the password it was made with.

    The gate the two system accounts are held by. Stated here rather than in
    the transport, because it is a rule about an account rather than about a
    request.
    """
    if account.must_change:
        raise PasswordMustChange(
            f'{account.username} must change its password before doing '
            'anything else')


def may_act_as(store, account, gameno, number):
    """Whether this account may act as this number of this game.

    The one rule, asked by every caller:

      0        the administrator
      1000     the observer, or the administrator
      1..999   an account holding that seat of that game

    The administrator may act as the observer because it is already entitled
    to see the whole game - `identity.sees_everything` says so of both numbers
    - and refusing it would be a distinction with nothing behind it. It may
    not act as a player number without holding that seat: player 0 owns no
    units, and an administrator who wants to play claims a seat like anyone
    else.
    """
    if not identity.identifies_anyone(number):
        return False
    if number == identity.ADMINISTRATOR:
        return account.is_administrator()
    if number == identity.OBSERVER:
        return account.is_observer() or account.is_administrator()
    return store.holds_seat(gameno, number, account.account_id)


def require_may_act_as(store, account, gameno, number):
    """`may_act_as`, as a refusal rather than an answer."""
    require_usable(account)
    if not may_act_as(store, account, gameno, number):
        raise NotAuthorised(
            f'{account.username} may not act as '
            f'{identity.describe(number)} of game {gameno}')


def claim_seat(store, game_repository, account, gameno, number):
    """Take an unclaimed seat of a game that has not started.

    The game's own repository answers two of the three refusals - whether the
    number is a registered player of that game, and whether the game has
    started - and is never written to. Claiming a seat is not a way around
    `add player`.
    """
    require_usable(account)
    if not identity.is_player(number):
        raise AccountError(identity.out_of_range(number))
    if number not in game_repository.player_numbers():
        raise AccountError(
            f'game {gameno} has no player {number} to sit as')
    if _has_started(game_repository):
        raise AccountError(f'game {gameno} has started')
    try:
        store.claim_seat(gameno, number, account.account_id)
    except ValueError as error:
        raise AccountError(str(error)) from error
    return number


def release_seat(store, game_repository, account, gameno, number):
    """Give up a seat, while the game has not started."""
    require_usable(account)
    holder = store.read_membership(gameno, number)
    if holder is None:
        raise AccountError(f'seat {number} of game {gameno} is not held')
    if holder != account.account_id:
        raise NotAuthorised(
            f'seat {number} of game {gameno} is not {account.username}\'s '
            'to give up')
    if _has_started(game_repository):
        raise AccountError(
            f'game {gameno} has started; a seat cannot be given up')
    store.release_seat(gameno, number)


def _has_started(game_repository):
    """Whether a turn of this game has been resolved.

    "Started" is a turn having resolved, not setup having ended, and the
    distinction is forced by what the game actually records. `Game.new_game`
    is a per-session derived flag - `not sees_everything` at load, cleared
    when that player has committed - so it is `False` for the administrator
    before anything is set up and `True` for a player after. It answers "does
    this session still have setup to do", which is a different question from
    "may somebody still join", and it is not durable.

    What is durable is the turn number, which `R3.8` keeps at 0 through the
    administrator's setup commit because that commit is not a turn. So a seat
    may still be claimed after setup is committed and before the first turn
    resolves - which is the window a lobby exists for, when the board is set
    and nobody has moved - and cannot be claimed once play is under way.

    Read rather than tracked, so it cannot disagree with the game.
    """
    progress = game_repository.read_progress()
    if progress is None:
        return False
    return int(progress.get('turn') or 0) >= 1
