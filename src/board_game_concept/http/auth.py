"""Who is asking, over HTTP, and whether they may act as the number they name.

Three checks, in this order, in front of every route that names a player
number:

  1. a token that is accepted, or 401
  2. an account whose password has been changed, or 403
  3. `may_act_as` for the number in the path, or 403

The number stays in the path. `app.py` was written expecting authentication to
move the identity into a token and take the number out of the URL, and that is
not possible once one account may hold several seats of one game: the account
no longer says which seat it is acting as. So the path keeps the number and
this checks it, which leaves every route exactly where it was.

The rule itself is not here. `service/accounts.may_act_as` states it once, and
this module is only the part that knows about headers, cookies and status
codes.
"""

import functools

from flask import current_app, g, jsonify, request

from ..service import accounts
from ..service.errors import (AccountError, NotAuthenticated, NotAuthorised,
                              PasswordMustChange)


# where a browser keeps its token. `HttpOnly` so a script on the page cannot
# read it; a command-line role sends the same token as a bearer header instead
SESSION_COOKIE = 'bgc_session'

AUTHORIZATION_HEADER = 'Authorization'
BEARER = 'Bearer '


def store():
    """This request's account store.

    Built per request and cached on `g`, for the same reason `app.py` builds
    a repository per request: a SQLite connection belongs to the thread that
    opened it, and the app is served threaded. Opening one is cheap.
    """
    if 'account_store' not in g:
        g.account_store = current_app.config['ACCOUNT_STORE_FACTORY']()
    return g.account_store


def presented_token():
    """The token this request carries, from either carrier, or None.

    The header is preferred over the cookie so that a command-line role
    talking to a server it has also browsed is the account it named.
    """
    header = request.headers.get(AUTHORIZATION_HEADER, '')
    if header.startswith(BEARER):
        return header[len(BEARER):].strip() or None
    return request.cookies.get(SESSION_COOKIE) or None


def current_account():
    """The account this request is from, or None.

    Cached on `g` for the request, so a route that asks twice does not read
    the store twice.
    """
    if 'account' not in g:
        try:
            g.account = accounts.account_for(store(), presented_token())
        except NotAuthenticated:
            g.account = None
    return g.account


def require_account():
    """The account this request is from, or a refusal."""
    account = current_account()
    if account is None:
        raise NotAuthenticated('not signed in')
    return account


def error_response(error):
    """One refusal, as the status it deserves.

    `NotAuthenticated` is 401 because the caller has not said who it is.
    Everything else about an account is 403: the caller has said, and the
    answer is no. A refusal returns nothing of the game - not a board, not a
    view, not a turn number - because a refusal that leaked what it was
    protecting would be no refusal at all.
    """
    if isinstance(error, NotAuthenticated):
        return jsonify({'error': str(error)}), 401
    if isinstance(error, PasswordMustChange):
        return jsonify({'error': str(error),
                        'must_change_password': True}), 403
    if isinstance(error, NotAuthorised):
        return jsonify({'error': str(error)}), 403
    return jsonify({'error': str(error)}), 400


def authenticated(view):
    """A route that needs an account, whatever number it names."""
    @functools.wraps(view)
    def guarded(*args, **kwargs):
        try:
            account = require_account()
            accounts.require_usable(account)
        except AccountError as error:
            return error_response(error)
        return view(*args, **kwargs)
    return guarded


def acts_as_number(view):
    """A route that names a player number and must prove entitlement to it.

    The number is taken from the route's own `number` argument and the game
    from its `gameno`, so nothing has to be repeated at each route. The check
    runs before the view, which is what keeps a refused request from opening
    a repository or building a `Game` at all - so a refusal cannot leak
    through an error about game data.
    """
    @functools.wraps(view)
    def guarded(*args, **kwargs):
        try:
            account = require_account()
            accounts.require_may_act_as(
                store(), account, str(kwargs.get('gameno')),
                int(kwargs.get('number')))
        except AccountError as error:
            return error_response(error)
        return view(*args, **kwargs)
    return guarded
