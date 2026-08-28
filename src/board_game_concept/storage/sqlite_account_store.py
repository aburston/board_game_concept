"""Keeping accounts, seats and tokens as a SQLite database.

One file, `accounts.sqlite3`, beside the games tree rather than inside any
game. The connection and transaction handling match `SqliteGameRepository`:
autocommit with an explicit `BEGIN`, WAL so a reader does not block a writer,
and foreign keys on.

Passwords are hashed with Werkzeug's scrypt, which arrives with Flask and so
costs no dependency this project did not already have. Nothing here ever
holds, logs or returns a password.
"""

import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from ..domain import account as account_rules
from ..domain.account import Account, Kind
from ..cli.session import default_base_path
from .account_store import AccountStore
from .lock import GameIsBusy


# the file the store is kept in, beside `games/` rather than inside it
STORE_FILENAME = 'accounts.sqlite3'

# how long a writer waits for another writer before giving up
BUSY_WAIT = 5.0

# how long a token from a login is accepted for, and how long one minted for a
# program is. The second is not forever: a token that never expires is one
# that cannot be forgotten about
SESSION_DAYS = 30
MINTED_DAYS = 3650


def _schema_path():
    return os.path.join(os.path.dirname(__file__), 'accounts.sql')


def _now():
    return datetime.now(timezone.utc)


def _stamp(moment):
    return moment.isoformat()


def hash_password(password):
    """The stored form of a password. Never reversible."""
    return generate_password_hash(password)


def password_matches(password_hash, password):
    """Whether this password is the one that hash was made from."""
    if not password_hash or not isinstance(password, str):
        return False
    return check_password_hash(password_hash, password)


def new_token():
    """A token nobody can guess."""
    return secrets.token_urlsafe(32)


class SqliteAccountStore(AccountStore):
    """The account store, as one SQLite file."""

    def __init__(self, base_path=None):
        self.base_path = base_path or default_base_path()
        self.db_path = os.path.join(self.base_path, STORE_FILENAME)
        self._connection = None
        self._depth = 0
        self._system_accounts_ensured = False

    # --- the store itself

    def ensure(self):
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        self._connect()
        if not self._has_schema():
            self._apply_schema()
        # once per store object, not once per query. `_get` calls `ensure`
        # before every statement, and re-running the insert each time would
        # take a write lock inside a caller's read transaction
        if not self._system_accounts_ensured:
            self._ensure_system_accounts()
            self._system_accounts_ensured = True

    def _connect(self):
        if self._connection is not None:
            return
        # a short wait rather than `timeout=0`: two genuine writers - two
        # people claiming a seat at the same moment - should queue for a
        # moment rather than one of them failing outright. `held()` is still
        # what a caller uses when it wants the refusal
        self._connection = sqlite3.connect(self.db_path, isolation_level=None,
                                           timeout=BUSY_WAIT)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute('PRAGMA journal_mode=WAL')
        self._connection.execute('PRAGMA foreign_keys=ON')

    def _apply_schema(self):
        with open(_schema_path(), encoding='utf-8') as file:
            self._connection.executescript(file.read())

    def _has_schema(self):
        row = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='accounts'").fetchone()
        return row is not None

    def _ensure_system_accounts(self):
        """`admin` and `observer`, created once and never reset.

        Read before write. `INSERT OR IGNORE` alone is idempotent in its
        effect but not in its cost: it takes a write lock every time, and this
        runs on the first use of every per-request store, so a page that
        fetches several views at once had every one of those requests
        contending for the same lock and one of them losing with "database is
        locked". Under WAL a read blocks nothing, so asking first is what
        makes the common case - they are already there - cost nothing.

        The insert stays `INSERT OR IGNORE` for the case two processes find
        them missing together: the unique `username_key` decides, and neither
        resets a password somebody has changed.
        """
        wanted = ((account_rules.ADMINISTRATOR_NAME, Kind.ADMINISTRATOR),
                  (account_rules.OBSERVER_NAME, Kind.OBSERVER))
        keys = [account_rules.normalise(name) for name, _kind in wanted]
        held = {
            row['username_key'] for row in self._connection.execute(
                'SELECT username_key FROM accounts WHERE username_key IN '
                f'({", ".join("?" * len(keys))})', keys)}
        missing = [(name, kind) for name, kind in wanted
                   if account_rules.normalise(name) not in held]
        if not missing:
            return
        for name, kind in missing:
            self._connection.execute(
                'INSERT OR IGNORE INTO accounts '
                '(username, username_key, password_hash, kind, must_change, '
                ' created_at) VALUES (?, ?, ?, ?, 1, ?)',
                (name, account_rules.normalise(name), hash_password(name),
                 kind, _stamp(_now())))

    # --- holding the store while it is used

    def held(self, read=False):
        self.ensure()
        return _Transaction(self, read)

    def _enter(self, read):
        if self._depth == 0:
            try:
                self._connection.execute(
                    'BEGIN DEFERRED' if read else 'BEGIN IMMEDIATE')
            except sqlite3.OperationalError as error:
                if 'locked' in str(error) or 'busy' in str(error):
                    raise GameIsBusy(
                        f'the account store at {self.db_path} is in use'
                    ) from error
                raise
        self._depth += 1

    def _leave(self, failed):
        self._depth -= 1
        if self._depth != 0:
            return
        self._connection.execute('ROLLBACK' if failed else 'COMMIT')

    def _get(self, statement=None, parameters=()):
        self.ensure()
        if statement is None:
            return self._connection
        return self._connection.execute(statement, parameters)

    # --- accounts

    def create_account(self, username, password_hash, kind, must_change=False):
        key = account_rules.normalise(username)
        try:
            cursor = self._get(
                'INSERT INTO accounts (username, username_key, password_hash, '
                'kind, must_change, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (username.strip(), key, password_hash, kind,
                 1 if must_change else 0, _stamp(_now())))
        except sqlite3.IntegrityError as error:
            raise ValueError(f'{username} is already taken') from error
        return self.read_account(cursor.lastrowid)

    def read_account(self, account_id):
        row = self._get('SELECT * FROM accounts WHERE id=?',
                        (account_id,)).fetchone()
        return _account_from(row)

    def read_account_by_name(self, username):
        row = self._get('SELECT * FROM accounts WHERE username_key=?',
                        (account_rules.normalise(username),)).fetchone()
        return _account_from(row)

    def set_password(self, account_id, password_hash):
        self._get(
            'UPDATE accounts SET password_hash=?, must_change=0 WHERE id=?',
            (password_hash, account_id))

    def accounts(self):
        rows = self._get(
            'SELECT * FROM accounts ORDER BY username_key').fetchall()
        return [_account_from(row) for row in rows]

    # --- tokens

    def create_session(self, account_id, token, expires_at, label=None):
        self._get(
            'INSERT INTO sessions (token, account_id, label, created_at, '
            'expires_at) VALUES (?, ?, ?, ?, ?)',
            (token, account_id, label, _stamp(_now()), _stamp(expires_at)))
        return token

    def read_session(self, token, now=None):
        if not token:
            return None
        row = self._get('SELECT * FROM sessions WHERE token=?',
                        (token,)).fetchone()
        if row is None:
            return None
        if _stamp(now or _now()) >= row['expires_at']:
            # past its time is not distinguished from never issued: a caller
            # learns only that the token is not accepted
            return None
        return self.read_account(row['account_id'])

    def delete_session(self, token):
        self._get('DELETE FROM sessions WHERE token=?', (token,))

    def delete_sessions_of(self, account_id):
        self._get('DELETE FROM sessions WHERE account_id=?', (account_id,))

    def sessions_of(self, account_id):
        rows = self._get(
            'SELECT token, label, created_at, expires_at FROM sessions '
            'WHERE account_id=? ORDER BY created_at', (account_id,)).fetchall()
        return [dict(row) for row in rows]

    # --- seats

    def claim_seat(self, gameno, number, account_id):
        try:
            self._get(
                'INSERT INTO memberships (gameno, number, account_id, '
                'claimed_at) VALUES (?, ?, ?, ?)',
                (str(gameno), int(number), account_id, _stamp(_now())))
        except sqlite3.IntegrityError as error:
            # the primary key refused it, which is what makes two claims
            # arriving together unable to both succeed
            raise ValueError(
                f'seat {number} of game {gameno} is already held') from error
        return True

    def release_seat(self, gameno, number):
        self._get('DELETE FROM memberships WHERE gameno=? AND number=?',
                  (str(gameno), int(number)))

    def read_membership(self, gameno, number):
        row = self._get(
            'SELECT account_id FROM memberships WHERE gameno=? AND number=?',
            (str(gameno), int(number))).fetchone()
        return row['account_id'] if row else None

    def holds_seat(self, gameno, number, account_id):
        return self.read_membership(gameno, number) == account_id

    def seats_of_game(self, gameno):
        rows = self._get(
            'SELECT number, account_id FROM memberships WHERE gameno=? '
            'ORDER BY number', (str(gameno),)).fetchall()
        return {row['number']: row['account_id'] for row in rows}

    def seats_of_account(self, account_id):
        rows = self._get(
            'SELECT gameno, number FROM memberships WHERE account_id=? '
            'ORDER BY gameno, number', (account_id,)).fetchall()
        return [(row['gameno'], row['number']) for row in rows]


class _Transaction:
    """The context manager `held()` returns."""

    def __init__(self, store, read):
        self._store = store
        self._read = read

    def __enter__(self):
        self._store._enter(self._read)
        return self

    def __exit__(self, kind, value, traceback):
        self._store._leave(failed=kind is not None)
        return False


def _account_from(row):
    if row is None:
        return None
    return Account(username=row['username'],
                   password_hash=row['password_hash'],
                   kind=row['kind'],
                   must_change=bool(row['must_change']),
                   account_id=row['id'])


def session_expiry(minted=False):
    """When a token issued now stops being accepted."""
    return _now() + timedelta(days=MINTED_DAYS if minted else SESSION_DAYS)
