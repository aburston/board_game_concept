"""Signing in, and passwords, from a command line.

The seam beside the one `backend.py` draws. That one hides how a *game* is
reached; this one hides how an *account* is reached, and for the same reason:
a role should ask the same four questions - who am I, sign me in, sign me out,
change my password - whether it is talking to a server or opening a game
directory itself.

`service/accounts.py` states every rule about an account once, and until now
only the HTTP tier had a way to call it. `LocalAccounts` calls it directly;
`HttpAccounts` calls the same four routes a browser calls. Neither states a
rule of its own, which is what makes the command line and the browser answer
alike.

Nothing here writes a credential to disk. A session signs in, holds its token
for as long as the process runs, and is signed in as nobody the next time -
which is what `--token` and `$BOARD_GAME_TOKEN` remain for, for anything
running unattended. A token in a file is a credential with a lifetime nobody
can see, and none of what this module is for needs one.
"""

import getpass
import sys

import requests

from ..service import accounts as account_rules
from ..service.errors import (AccountError, NotAuthenticated, NotAuthorised,
                              PasswordMustChange)
from ..storage.account_store import make_account_store


class SignedIn:
    """Who a session is signed in as, and the token that proves it."""

    def __init__(self, username, kind, token, must_change=False):
        self.username = username
        self.kind = kind
        self.token = token
        # whether this account may do nothing until its password is changed.
        # Carried here because it is the answer to the question the caller
        # asked, not a second request it has to make
        self.must_change = must_change

    def described(self):
        """This account, as one line for whoever is reading."""
        return f'{self.username} ({self.kind})'


class Accounts:
    """The four things a session may ask about its own account.

    Subclasses implement all of them. This class says what the set is and
    fails loudly rather than silently when one is missing, the way `Session`
    does for the game.
    """

    def __init__(self, on_token=None):
        # who this session is signed in as, or None
        self.signed_in = None
        # what to tell when the token changes. An HTTP session sends the
        # token with every request it makes, so signing in at the prompt has
        # to reach it; a local session has nothing to tell
        self._on_token = on_token

    def sign_in(self, username, password):
        """A token for this account, held for the life of this process."""
        raise NotImplementedError

    def sign_out(self):
        """End the token this session holds."""
        raise NotImplementedError

    def whoami(self):
        """Who this session is signed in as, or None."""
        raise NotImplementedError

    def change_password(self, current, new):
        """Change the password of the account this session is signed in as."""
        raise NotImplementedError

    # --- what every implementation shares

    def note(self):
        """What signing in this way is for, where that needs saying."""
        return None

    def _hold(self, signed_in):
        self.signed_in = signed_in
        if self._on_token is not None:
            self._on_token(signed_in.token if signed_in else None)
        return signed_in

    def _require_signed_in(self):
        if self.signed_in is None:
            raise NotAuthenticated('not signed in')
        return self.signed_in


class LocalAccounts(Accounts):
    """The in-process implementation: `service/accounts.py`, on this machine.

    The store is opened the first time it is asked for and not before, which
    is what keeps a local game that never signs in from creating an account
    store beside itself. A role that *does* sign in creates one - holding
    `admin` and `observer`, each needing its password changed - which is how
    the first password on a machine that has never run a server becomes
    changeable at all.
    """

    NOTE = ('signing in locally reads and changes an account; '
            'playing a local game needs no account')

    def __init__(self, backend=None, base_path=None, on_token=None):
        super().__init__(on_token=on_token)
        self._backend = backend
        self._base_path = base_path
        self._store = None

    def note(self):
        return self.NOTE

    def store(self):
        """The account store, opened and ensured on first use."""
        if self._store is None:
            # imported here rather than at the top: `session.py` imports this
            # module for the sign-in it does at start-up, and a module-level
            # import either way round would be a cycle
            from .session import default_backend, default_base_path
            backend = self._backend or default_backend()
            base_path = self._base_path or default_base_path()
            store = make_account_store(backend, base_path)
            store.ensure()
            self._store = store
        return self._store

    def sign_in(self, username, password):
        account, token = account_rules.authenticate(
            self.store(), username, password)
        return self._hold(SignedIn(account.username, account.kind, token,
                                   account.must_change))

    def sign_out(self):
        held = self._require_signed_in()
        account_rules.end_token(self.store(), held.token)
        self._hold(None)

    def whoami(self):
        if self.signed_in is None:
            return None
        # read back rather than reported from what was held, so that an
        # account whose password was changed elsewhere is not still described
        # as one that must change it
        account = account_rules.account_for(self.store(), self.signed_in.token)
        return SignedIn(account.username, account.kind, self.signed_in.token,
                        account.must_change)

    def change_password(self, current, new):
        held = self._require_signed_in()
        account = account_rules.account_for(self.store(), held.token)
        account_rules.change_password(self.store(), account, current, new)
        held.must_change = False


class HttpAccounts(Accounts):
    """The HTTP implementation: the four routes a browser signs in through.

    One `requests.Session`, carrying the bearer header rather than the cookie
    the browser is given, because `http/auth.py` prefers the header and a
    command line has nowhere to keep a cookie.
    """

    def __init__(self, base_url, on_token=None, token=None):
        super().__init__(on_token=on_token)
        self.base_url = base_url.rstrip('/')
        self._session = requests.Session()
        # a token the session was started with - named on the command line,
        # taken from the environment, or issued by a sign-in at start-up. It
        # already identifies somebody, so this is signed in as them; who that
        # is is asked of the server the first time anybody wants to know,
        # rather than by a request nobody asked for
        self._carried = token
        if token:
            self._session.headers['Authorization'] = f'Bearer {token}'

    def _resolve_carried(self):
        """Who the token this session was started with identifies."""
        if self._carried is None or self.signed_in is not None:
            return
        token, self._carried = self._carried, None
        try:
            body = self._json(self._session.get(
                f'{self.base_url}/accounts/current'))
        except AccountError:
            # a token that was never issued, was ended, or is past its time.
            # The session is signed in as nobody, which is what it is
            self._session.headers.pop('Authorization', None)
            return
        # held directly rather than through `_hold`: the session this was
        # made for is already sending this token
        self.signed_in = SignedIn(body['username'], body['kind'], token,
                                  body.get('must_change_password', False))

    def sign_in(self, username, password):
        body = self._json(self._session.post(
            f'{self.base_url}/sessions',
            json={'username': username, 'password': password}))
        token = body['token']
        self._session.headers['Authorization'] = f'Bearer {token}'
        # the cookie the route also sets is dropped: one carrier, so that a
        # signed-out session cannot still be signed in by the other
        self._session.cookies.clear()
        return self._hold(SignedIn(body['username'], body['kind'], token,
                                   body.get('must_change_password', False)))

    def sign_out(self):
        self._resolve_carried()
        self._require_signed_in()
        self._json(self._session.delete(f'{self.base_url}/sessions/current'))
        self._session.headers.pop('Authorization', None)
        self._session.cookies.clear()
        self._hold(None)

    def whoami(self):
        self._resolve_carried()
        if self.signed_in is None:
            return None
        body = self._json(self._session.get(
            f'{self.base_url}/accounts/current'))
        return SignedIn(body['username'], body['kind'], self.signed_in.token,
                        body.get('must_change_password', False))

    def change_password(self, current, new):
        self._resolve_carried()
        held = self._require_signed_in()
        self._json(self._session.post(
            f'{self.base_url}/accounts/current/password',
            json={'current': current, 'new': new}))
        held.must_change = False

    @staticmethod
    def _json(response):
        """The body, or the refusal this status deserves.

        The mirror of `http/auth.py:error_response`, read back: a refusal
        arrives as the same kind of error a local refusal would have been
        raised as, so a caller cannot tell the two apart and does not have to.
        """
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code // 100 == 2:
            return body
        message = body.get('error') or response.text or 'the server refused'
        if response.status_code == 401:
            raise NotAuthenticated(message)
        if body.get('must_change_password'):
            raise PasswordMustChange(message)
        if response.status_code == 403:
            raise NotAuthorised(message)
        raise AccountError(message)


# --- reading a credential from a person
#
# A password is read with `getpass`, which does not echo it and does not go
# through `readline` - so it reaches no history file, and completion never
# sees it. It is never read any other way, and it is never a word on a
# command line: a command line is a public thing, and a password in one is a
# password leaked.

MISMATCH_MESSAGE = 'the two passwords do not match'


def at_a_terminal():
    """Whether there is a person typing at this session.

    Both streams, for the reason `session._read_line` asks about both: a
    prompt is written to one and read from the other, so a terminal on stdin
    with a pipe on stdout is not somebody typing.
    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def ask_username(prompt='username: '):
    """A username, read the ordinary way. It is not a secret."""
    return input(prompt).strip()


def ask_password(prompt='password: '):
    """A password, read without echoing it and without touching history.

    Two ways of reading, for the two kinds of caller `session._read_line`
    already distinguishes. A person at a terminal gets `getpass`, which turns
    the echo off and does not go through `readline`. Anything else - a pipe, a
    test, a script - gets the prompt and a line of its own input, because
    there is no terminal to turn the echo off on and `getpass` reaching for
    `/dev/tty` would read from a terminal the caller is not typing at.
    """
    if at_a_terminal():
        return getpass.getpass(prompt)
    print(prompt, end='', flush=True)
    line = sys.stdin.readline()
    if line == '':
        raise EOFError
    return line.rstrip('\n')


def ask_new_password(prompt='new password: '):
    """A new password, typed twice, or None if the two did not match.

    Asked twice because it is being set rather than checked: nothing will
    tell the person they mistyped it until the next time they try to sign in.
    """
    first = ask_password(prompt)
    again = ask_password('new password again: ')
    if first != again:
        print(MISMATCH_MESSAGE)
        return None
    return first


def _asked(reader, *args, **kwargs):
    """One credential, or None where there was nobody there to type it.

    End of input is not an error here: a session that is asked for a password
    and has none to give has declined, and is told what that leaves it as
    rather than dying of it.
    """
    try:
        return reader(*args, **kwargs)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


# --- the commands themselves


def sign_in_at_prompt(accounts, username=None, strict=False):
    """Sign in, asking for what was not given, and capture a forced change.

    `strict` is the difference between the two callers. At a prompt, an
    account that declines to change its password is left signed in and
    refused by everything else, which is what the browser leaves it as. At
    start-up there is nothing yet to be refused by - the session has not been
    opened - so declining is the end of it.
    """
    if username is None:
        username = _asked(ask_username)
    if not username:
        raise AccountError('a username is needed to sign in')
    password = _asked(ask_password)
    if password is None:
        raise AccountError('a password is needed to sign in')
    signed_in = accounts.sign_in(username, password)
    print(f'signed in as {signed_in.described()}')
    note = accounts.note()
    if note:
        print(note)
    if signed_in.must_change:
        changed = capture_password_change(accounts, signed_in, password)
        if not changed and strict:
            raise PasswordMustChange(
                f'{signed_in.username} must change its password before '
                'doing anything else')
    return signed_in


def capture_password_change(accounts, signed_in, current):
    """Ask for a new password where the account may do nothing without one.

    The token the sign-in just issued is what the change is made with, which
    is what the browser does too - the password change is the one thing an
    account in this state may reach.
    """
    print(f'{signed_in.username} must change its password before doing '
          'anything else')
    new = _asked(ask_new_password)
    if new is None:
        print('password unchanged; this session may do nothing else '
              'until it is')
        return False
    try:
        accounts.change_password(current, new)
    except AccountError as error:
        _report(error)
        return False
    print('password changed')
    return True


def handle_account_command(command, accounts):
    """Carry out one of the account commands, or say this was not one.

    Called by each role's loop before its own dispatch, so the four commands
    behave identically in all three roles rather than three times over. Every
    refusal is reported and the prompt comes back, the way a refused game
    command is: being told the wrong password is not a reason to end
    somebody's session.
    """
    handler = {
        'login': lambda: sign_in_at_prompt(accounts, command.username),
        'logout': lambda: _sign_out(accounts),
        'whoami': lambda: _whoami(accounts),
        'passwd': lambda: _change_password(accounts),
    }.get(command.kind)
    if handler is None:
        return False
    try:
        handler()
    except AccountError as error:
        _report(error)
    except requests.RequestException as error:
        print(f'the server could not be reached: {error}')
    return True


def _sign_out(accounts):
    username = accounts.signed_in.username if accounts.signed_in else None
    accounts.sign_out()
    print(f'signed out{f" of {username}" if username else ""}')


def _whoami(accounts):
    who = accounts.whoami()
    if who is None:
        print('not signed in')
        return
    print(f'signed in as {who.described()}')
    if who.must_change:
        print(f'{who.username} must change its password before doing '
              'anything else')


def _change_password(accounts):
    held = accounts.whoami()
    if held is None:
        raise NotAuthenticated('not signed in')
    if held.must_change:
        # the account may reach nothing but this, so ask for the current
        # password and then walk exactly the flow a sign-in would have
        current = _asked(ask_password, 'current password: ')
        if current is None:
            return
        capture_password_change(accounts, held, current)
        return
    current = _asked(ask_password, 'current password: ')
    if current is None:
        return
    new = _asked(ask_new_password)
    if new is None:
        return
    accounts.change_password(current, new)
    print('password changed')


def _report(error):
    """Say why an account command was refused."""
    for line in error.lines():
        print(line)
