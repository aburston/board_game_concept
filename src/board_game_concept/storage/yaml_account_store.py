"""Keeping accounts, seats and tokens as YAML files under a directory.

The same port `SqliteAccountStore` implements, so that one backend choice
drives the whole deployment: a YAML game is served by a YAML account store
and a SQLite game by a SQLite one, and there is no arrangement where the two
disagree about what a deployment is.

Three files under `accounts/`, matching the grain of `YamlGameRepository` -
one file per thing, written by replacement so a reader sees the previous
contents or the new ones and never half of either.

**The password hashes are in a readable file.** They are scrypt and are not
reversible, but a file is easier to walk off with than a table, so the
directory and its files are created private to the user running the server
and the README says to keep them that way. That is the trade this backend
makes; `SqliteAccountStore` is the one that does not make it.
"""

import os

import yaml

from ..domain import account as account_rules
from ..domain.account import Account, Kind
from ..service.errors import UnreadableGame
from . import lock
from ..cli.session import default_base_path
from .account_store import AccountStore
from .sqlite_account_store import _now, _stamp, hash_password


# the directory the three files live in, beside `games/` rather than inside
# any game - an account outlives every game it plays in
STORE_DIRNAME = 'accounts'

ACCOUNTS_FILE = 'accounts.yaml'
MEMBERSHIPS_FILE = 'memberships.yaml'
SESSIONS_FILE = 'sessions.yaml'

# owner-only, because these files carry password hashes
DIR_MODE = 0o700
FILE_MODE = 0o600


class YamlAccountStore(AccountStore):
    """The account store, as YAML files."""

    def __init__(self, base_path=None):
        if base_path is None:
            base_path = default_base_path()
        self.base_path = base_path
        self.root = os.path.join(base_path, STORE_DIRNAME)
        self.accounts_path = os.path.join(self.root, ACCOUNTS_FILE)
        self.memberships_path = os.path.join(self.root, MEMBERSHIPS_FILE)
        self.sessions_path = os.path.join(self.root, SESSIONS_FILE)
        # the lock lives on the holding rather than beside it: nothing else
        # asks where it is, and one fewer thing to keep in step with `root`
        self._holding = lock.Holding(os.path.join(self.root, '.lock'))
        self._system_accounts_ensured = False

    # --- the store itself

    def ensure(self):
        if not os.path.exists(self.root):
            os.makedirs(self.root, mode=DIR_MODE)
        else:
            # an existing directory is tightened too, so a store made before
            # this backend set a mode does not stay world-readable
            _restrict(self.root, DIR_MODE)
        if not self._system_accounts_ensured:
            self._ensure_system_accounts()
            self._system_accounts_ensured = True

    def _ensure_system_accounts(self):
        """`admin` and `observer`, created once and never reset.

        Written only when one of them is absent, so opening an existing store
        neither resets a password somebody has changed nor clears
        `must_change` on one they have not.
        """
        with self._holding.take():
            records = self._read(self.accounts_path)
            held = {record['username_key'] for record in records}
            missing = [
                (name, kind)
                for name, kind in ((account_rules.ADMINISTRATOR_NAME,
                                    Kind.ADMINISTRATOR),
                                   (account_rules.OBSERVER_NAME,
                                    Kind.OBSERVER))
                if account_rules.normalise(name) not in held]
            if not missing:
                return
            next_id = max((record['id'] for record in records), default=0) + 1
            for name, kind in missing:
                records.append({
                    'id': next_id,
                    'username': name,
                    'username_key': account_rules.normalise(name),
                    'password_hash': hash_password(name),
                    'kind': kind,
                    'must_change': True,
                    'created_at': _stamp(_now()),
                })
                next_id += 1
            self._write(self.accounts_path, records)

    # --- holding the store while it is used

    def held(self, read=False):
        self.ensure()
        return self._holding.take(read=read)

    # --- the files

    def _read(self, path):
        """One file's records, or an empty list where there are none."""
        try:
            with open(path, encoding='utf-8') as file:
                loaded = yaml.safe_load(file)
        except FileNotFoundError:
            return []
        except yaml.YAMLError as error:
            raise UnreadableGame(
                f'the account store at {path} cannot be read', error) from error
        return list(loaded or [])

    def _write(self, path, records):
        """Replace one file, atomically and privately."""
        temporary = f'{path}.writing-{os.getpid()}'
        # opened through `os.open` so the mode is set as the file is created
        # rather than after it, which would leave a window where the hashes
        # were readable by anybody
        descriptor = os.open(temporary,
                             os.O_WRONLY | os.O_CREAT | os.O_TRUNC, FILE_MODE)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as file:
                yaml.safe_dump(list(records), file, sort_keys=True)
        except BaseException:
            if os.path.exists(temporary):
                os.remove(temporary)
            raise
        os.replace(temporary, path)
        _restrict(path, FILE_MODE)

    # --- accounts

    def create_account(self, username, password_hash, kind, must_change=False):
        key = account_rules.normalise(username)
        with self._holding.take():
            records = self._read(self.accounts_path)
            if any(record['username_key'] == key for record in records):
                raise ValueError(f'{username} is already taken')
            account_id = max((record['id'] for record in records),
                             default=0) + 1
            records.append({
                'id': account_id,
                'username': username.strip(),
                'username_key': key,
                'password_hash': password_hash,
                'kind': kind,
                'must_change': bool(must_change),
                'created_at': _stamp(_now()),
            })
            self._write(self.accounts_path, records)
        return self.read_account(account_id)

    def read_account(self, account_id):
        self.ensure()
        for record in self._read(self.accounts_path):
            if record['id'] == account_id:
                return _account_from(record)
        return None

    def read_account_by_name(self, username):
        self.ensure()
        key = account_rules.normalise(username)
        for record in self._read(self.accounts_path):
            if record['username_key'] == key:
                return _account_from(record)
        return None

    def set_password(self, account_id, password_hash):
        with self._holding.take():
            records = self._read(self.accounts_path)
            for record in records:
                if record['id'] == account_id:
                    record['password_hash'] = password_hash
                    record['must_change'] = False
            self._write(self.accounts_path, records)

    def accounts(self):
        self.ensure()
        return [_account_from(record)
                for record in sorted(self._read(self.accounts_path),
                                     key=lambda r: r['username_key'])]

    # --- tokens

    def create_session(self, account_id, token, expires_at, label=None):
        with self._holding.take():
            records = self._read(self.sessions_path)
            records.append({
                'token': token,
                'account_id': account_id,
                'label': label,
                'created_at': _stamp(_now()),
                'expires_at': _stamp(expires_at),
            })
            self._write(self.sessions_path, records)
        return token

    def read_session(self, token, now=None):
        if not token:
            return None
        self.ensure()
        moment = _stamp(now or _now())
        for record in self._read(self.sessions_path):
            if record['token'] != token:
                continue
            if moment >= record['expires_at']:
                # past its time is not distinguished from never issued
                return None
            return self.read_account(record['account_id'])
        return None

    def delete_session(self, token):
        with self._holding.take():
            records = [record for record in self._read(self.sessions_path)
                       if record['token'] != token]
            self._write(self.sessions_path, records)

    def delete_sessions_of(self, account_id):
        with self._holding.take():
            records = [record for record in self._read(self.sessions_path)
                       if record['account_id'] != account_id]
            self._write(self.sessions_path, records)

    def sessions_of(self, account_id):
        self.ensure()
        return [{'token': record['token'], 'label': record['label'],
                 'created_at': record['created_at'],
                 'expires_at': record['expires_at']}
                for record in self._read(self.sessions_path)
                if record['account_id'] == account_id]

    # --- seats

    def claim_seat(self, gameno, number, account_id):
        """Take a seat, refusing one that is held.

        Read and write happen inside one exclusive hold, which is what makes
        two claims arriving together unable to both succeed - the same
        guarantee the SQLite backend gets from its primary key.
        """
        with self._holding.take():
            records = self._read(self.memberships_path)
            for record in records:
                if (record['gameno'] == str(gameno)
                        and record['number'] == int(number)):
                    raise ValueError(
                        f'seat {number} of game {gameno} is already held')
            records.append({
                'gameno': str(gameno),
                'number': int(number),
                'account_id': account_id,
                'claimed_at': _stamp(_now()),
            })
            self._write(self.memberships_path, records)
        return True

    def release_seat(self, gameno, number):
        with self._holding.take():
            records = [
                record for record in self._read(self.memberships_path)
                if not (record['gameno'] == str(gameno)
                        and record['number'] == int(number))]
            self._write(self.memberships_path, records)

    def read_membership(self, gameno, number):
        self.ensure()
        for record in self._read(self.memberships_path):
            if (record['gameno'] == str(gameno)
                    and record['number'] == int(number)):
                return record['account_id']
        return None

    def holds_seat(self, gameno, number, account_id):
        return self.read_membership(gameno, number) == account_id

    def seats_of_game(self, gameno):
        self.ensure()
        return {record['number']: record['account_id']
                for record in sorted(self._read(self.memberships_path),
                                     key=lambda r: r['number'])
                if record['gameno'] == str(gameno)}

    def seats_of_account(self, account_id):
        self.ensure()
        return [(record['gameno'], record['number'])
                for record in sorted(self._read(self.memberships_path),
                                     key=lambda r: (r['gameno'], r['number']))
                if record['account_id'] == account_id]


def _restrict(path, mode):
    """Keep a path private to the user running the server.

    Best effort: a filesystem that does not carry modes is not a reason to
    refuse to serve, and the README is what says to check.
    """
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def _account_from(record):
    if record is None:
        return None
    return Account(username=record['username'],
                   password_hash=record['password_hash'],
                   kind=record['kind'],
                   must_change=bool(record['must_change']),
                   account_id=record['id'])
