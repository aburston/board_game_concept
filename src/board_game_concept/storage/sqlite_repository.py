"""Keeping a game as a SQLite database, one file per game.

The port is the same one `YamlGameRepository` implements; where that backend
writes YAML files under `games/_<gameno>/`, this one writes rows into
`games/_<gameno>/game.sqlite3`. The visible shape of a game directory does
not change - an operator still copies, backs up and deletes a directory -
but the contents are one file and a lock table rather than a dozen small
YAML files.

Two things the schema knows that the file layout could not:

- A view is a query. `read_view(n)` joins `units` against `sightings` for
  that viewer, so what a player is entitled to see is computed rather than
  materialised.
- The combat log is a table. `write_units` alone leaves `turn_events`
  untouched; a caller that wants events recorded writes them through
  `write_turn_events`.
"""

import json
import os
import sqlite3

from ..service.errors import UnreadableGame
from . import notify
from .lock import GameIsBusy
from .repository import GameRepository


# columns of `units` (and, in the same order, of `orders` after
# `player_number` and `id`). Kept as one list so any drift between the schema
# and the code is one edit rather than several
_UNIT_COLUMNS = (
    'owner', 'name', 'type_name', 'symbol',
    'attack', 'health', 'energy',
    'type_attack', 'type_health', 'type_energy',
    'x', 'y', 'state', 'direction', 'destroyed', 'on_board',
)


def _schema_path():
    return os.path.join(os.path.dirname(__file__), 'schema.sql')


class SqliteGameRepository(GameRepository):

    def __init__(self, gameno, base_path=None):
        if base_path is None:
            base_path = os.getcwd()
        self.gameno = gameno
        self.root = os.path.join(base_path, 'games', f'_{gameno}')
        # `data_path` is what Game reads for the notifier and for error
        # messages that name where a game lives. The FIFOs still land under
        # it, the same as with the YAML backend
        self.data_path = os.path.join(self.root, 'data')
        self.db_path = os.path.join(self.root, 'game.sqlite3')
        self._connection = None
        # nested `held()` calls increment the depth rather than opening a
        # second transaction. That is what the YAML backend's advisory lock
        # does, and this matches
        self._depth = 0

    # --- the game itself

    def ensure(self):
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        self._connect()
        # apply the schema once per connection, not once per write. Running
        # `executescript` mid-transaction would commit the transaction the
        # caller is inside; and the sentinel row is written by the same
        # first-time-only path, so ensure() called on an already-set-up
        # database does not take a write lock
        if not self._has_schema():
            self._apply_schema()
            self._connection.execute(
                'INSERT OR IGNORE INTO games (id) VALUES (1)')

    def _connect(self):
        if self._connection is not None:
            return
        # isolation_level=None puts the connection in autocommit mode and
        # lets `held()` open the transaction it wants; the default would open
        # one implicitly on the first data statement and get in the way
        self._connection = sqlite3.connect(self.db_path, isolation_level=None,
                                           timeout=0)
        self._connection.row_factory = sqlite3.Row
        # WAL so a reader does not block a writer, foreign keys so the schema
        # is trustworthy
        self._connection.execute('PRAGMA journal_mode=WAL')
        self._connection.execute('PRAGMA foreign_keys=ON')

    def _apply_schema(self):
        with open(_schema_path(), encoding='utf-8') as file:
            self._connection.executescript(file.read())

    # --- holding a game while it is used

    def held(self, read=False):
        # matches the YAML backend: `ensure` is what makes the schema exist
        # at all, so `held()` calling it first means the transaction is
        # opened over a database that has tables
        self.ensure()
        return _Transaction(self, read)

    # the transaction owns the connection; nested `held()` re-enters the
    # same one
    def _enter(self, read):
        if self._depth == 0:
            try:
                if read:
                    self._connection.execute('BEGIN DEFERRED')
                else:
                    self._connection.execute('BEGIN IMMEDIATE')
            except sqlite3.OperationalError as error:
                if 'locked' in str(error) or 'busy' in str(error):
                    raise GameIsBusy(
                        f"the game at {self.data_path} is in use") from error
                raise
        self._depth += 1

    def _leave(self, failed):
        self._depth -= 1
        if self._depth != 0:
            return
        if failed:
            self._connection.execute('ROLLBACK')
        else:
            self._connection.execute('COMMIT')

    def _has_schema(self):
        row = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='games'").fetchone()
        return row is not None

    # --- the board

    def read_board(self):
        if not self._db_ready():
            return None
        row = self._get(
            'SELECT size_x, size_y FROM games WHERE id=1').fetchone()
        if row is None or row['size_x'] is None:
            return None
        return row['size_x'], row['size_y']

    def write_board(self, size_x, size_y):
        self.ensure()
        connection = self._get()
        connection.execute(
            'INSERT INTO games (id, size_x, size_y) VALUES (1, ?, ?) '
            'ON CONFLICT(id) DO UPDATE SET size_x=excluded.size_x, '
            'size_y=excluded.size_y',
            (int(size_x), int(size_y)))

    # --- progress

    def read_progress(self):
        if not self._db_ready():
            return None
        row = self._get(
            'SELECT turn_no, outcome FROM games WHERE id=1').fetchone()
        if row is None:
            return None
        # a game with no turns resolved has never had its progress written;
        # returning None matches what the YAML backend did
        if row['turn_no'] == 0 and row['outcome'] is None and \
                self._eliminated() == []:
            return None
        progress = {
            'turn': row['turn_no'] or 0,
            'eliminated': self._eliminated(),
        }
        if row['outcome'] is not None:
            # `outcome` is a dict `{decided, winner, turn}`, kept as JSON in
            # the column so the schema does not have to describe it
            progress['outcome'] = json.loads(row['outcome'])
        return progress

    def _eliminated(self):
        rows = self._get(
            'SELECT player_number FROM eliminated '
            'ORDER BY player_number').fetchall()
        return [row['player_number'] for row in rows]

    def write_progress(self, progress):
        self.ensure()
        turn = int(progress.get('turn', 0))
        outcome = progress.get('outcome')
        connection = self._get()
        connection.execute(
            'UPDATE games SET turn_no=?, outcome=? WHERE id=1',
            (turn, None if outcome is None else json.dumps(outcome)))
        connection.execute('DELETE FROM eliminated')
        for number in progress.get('eliminated') or []:
            connection.execute(
                'INSERT INTO eliminated (player_number) VALUES (?)',
                (int(number),))

    # --- units (the authoritative board)

    def read_units(self):
        if not self._db_ready():
            return []
        return [_unit_row_to_dict(row) for row in self._get(
            f"SELECT id, {', '.join(_UNIT_COLUMNS)} "
            "FROM units ORDER BY id").fetchall()]

    def write_units(self, document):
        self.ensure()
        units = document.get('units') or []
        connection = self._get()
        # a fresh list per write, so nothing left over from a turn ago
        # can outlive the turn that ends here. `sightings` cascades on
        # `units.id`
        connection.execute('DELETE FROM units')
        for unit in units:
            _insert_unit(connection, unit)

    # --- players

    def player_numbers(self):
        if not self._db_ready():
            return []
        rows = self._get(
            'SELECT player_number FROM memberships '
            'ORDER BY player_number').fetchall()
        return [row['player_number'] for row in rows]

    def read_player(self, number):
        if not self._db_ready():
            return None
        rows = self._get(
            'SELECT name, symbol, attack, health, energy '
            'FROM unit_types WHERE player_number=? ORDER BY name',
            (int(number),)).fetchall()
        row = self._get(
            'SELECT player_number FROM memberships WHERE player_number=?',
            (int(number),)).fetchone()
        if row is None and not rows:
            return None
        types = {}
        for r in rows:
            types[r['name']] = {
                'name': r['name'], 'symbol': r['symbol'],
                'attack': r['attack'], 'health': r['health'],
                'energy': r['energy'],
            }
        return {'number': int(number), 'types': types}

    def write_player(self, number, types):
        self.ensure()
        connection = self._get()
        connection.execute(
            'INSERT OR IGNORE INTO memberships (player_number) '
            'VALUES (?)', (int(number),))
        connection.execute(
            'DELETE FROM unit_types WHERE player_number=?',
            (int(number),))
        for name, type_data in (types or {}).items():
            connection.execute(
                'INSERT INTO unit_types (player_number, name, symbol, '
                'attack, health, energy) VALUES (?, ?, ?, ?, ?, ?)',
                (int(number), name, type_data['symbol'],
                 int(type_data['attack']), int(type_data['health']),
                 int(type_data['energy'])))

    # --- what a player can see

    def read_view(self, number):
        # `_restore` treats None and [] the same (both mean "nothing to
        # restore"), so the SQLite backend does not carry a "has ever had a
        # view" bit. The join is what a caller was reading from the
        # materialised file, produced fresh from the source every read
        if not self._db_ready():
            return []
        return [_unit_row_to_dict(row) for row in self._get(
            f"SELECT units.id, {', '.join('units.' + c for c in _UNIT_COLUMNS)} "
            "FROM units JOIN sightings ON sightings.seen_unit_id=units.id "
            "WHERE sightings.viewer=? ORDER BY units.id",
            (int(number),)).fetchall()]

    def write_view(self, number, document):
        self.ensure()
        connection = self._get()
        connection.execute('DELETE FROM sightings WHERE viewer=?',
                           (int(number),))
        for unit in document.get('units') or []:
            # `id` in the document is the caller's index; on the SQLite
            # side, sightings reference `units.id`, which is the same
            # index because `write_units` inserts them in that order
            # into a table whose primary key follows that order
            connection.execute(
                'INSERT OR IGNORE INTO sightings '
                '(viewer, seen_unit_id) VALUES (?, ?)',
                (int(number), int(unit['id'])))

    # --- orders and the commit barrier

    def has_orders(self, number):
        if not self._db_ready():
            return False
        row = self._get(
            'SELECT 1 FROM orders WHERE player_number=? LIMIT 1',
            (int(number),)).fetchone()
        return row is not None

    def read_orders(self, number):
        if not self._db_ready():
            return None
        rows = self._get(
            f"SELECT id, {', '.join(_UNIT_COLUMNS)} FROM orders "
            "WHERE player_number=? ORDER BY id",
            (int(number),)).fetchall()
        if not rows:
            return None
        return {'units': [_unit_row_to_dict(row) for row in rows]}

    def write_orders(self, number, document):
        self.ensure()
        units = document.get('units') or []
        connection = self._get()
        connection.execute('DELETE FROM orders WHERE player_number=?',
                           (int(number),))
        for index, unit in enumerate(units):
            _insert_order(connection, int(number), index, unit)

    def clear_orders(self):
        connection = self._get()
        connection.execute('DELETE FROM orders')

    def committed_players(self, turn=None):
        if not self._db_ready():
            return []
        if turn is None:
            rows = self._get(
                'SELECT player_number FROM commits '
                'ORDER BY player_number').fetchall()
        else:
            rows = self._get(
                'SELECT player_number FROM commits WHERE turn_no=? '
                'ORDER BY player_number',
                (int(turn),)).fetchall()
        return [row['player_number'] for row in rows]

    def mark_committed(self, number, turn=None):
        self.ensure()
        connection = self._get()
        connection.execute(
            'INSERT INTO commits (player_number, turn_no) VALUES (?, ?) '
            'ON CONFLICT(player_number) DO UPDATE SET '
            'turn_no=excluded.turn_no',
            (int(number), None if turn is None else int(turn)))

    def has_committed(self, number):
        if not self._db_ready():
            return False
        row = self._get(
            'SELECT 1 FROM commits WHERE player_number=?',
            (int(number),)).fetchone()
        return row is not None

    def clear_commits(self):
        connection = self._get()
        # matches the YAML backend: the marker survives, only the turn is
        # spent. `has_committed` still answers True after this
        connection.execute('UPDATE commits SET turn_no=NULL')

    # --- drafts

    def read_draft(self, number):
        if not self._db_ready():
            return None
        row = self._get(
            'SELECT turn_no, commands FROM drafts WHERE player_number=?',
            (int(number),)).fetchone()
        if row is None:
            return None
        try:
            commands = json.loads(row['commands'])
        except (TypeError, ValueError) as error:
            raise UnreadableGame(
                f"the draft held by session {number} could not be read: "
                f"{error}") from error
        return {'turn': row['turn_no'], 'commands': commands}

    def write_draft(self, number, draft):
        self.ensure()
        connection = self._get()
        connection.execute(
            'INSERT INTO drafts (player_number, turn_no, commands) '
            'VALUES (?, ?, ?) ON CONFLICT(player_number) DO UPDATE SET '
            'turn_no=excluded.turn_no, commands=excluded.commands',
            (int(number), int(draft.get('turn', 0)),
             json.dumps(draft.get('commands') or [])))

    def clear_draft(self, number):
        connection = self._get()
        connection.execute('DELETE FROM drafts WHERE player_number=?',
                           (int(number),))

    # --- rejections

    def read_rejections(self, number):
        if not self._db_ready():
            return []
        rows = self._get(
            'SELECT unit, type_name, x, y, reason FROM rejections '
            'WHERE player_number=? ORDER BY rowid',
            (int(number),)).fetchall()
        return [{'unit': row['unit'], 'type': row['type_name'],
                 'x': row['x'], 'y': row['y'], 'reason': row['reason']}
                for row in rows]

    def write_rejections(self, number, rejected, turn=None):
        self.ensure()
        connection = self._get()
        connection.execute(
            'DELETE FROM rejections WHERE player_number=?',
            (int(number),))
        for record in rejected or []:
            connection.execute(
                'INSERT INTO rejections (player_number, turn_no, unit, '
                'type_name, x, y, reason) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (int(number),
                 0 if turn is None else int(turn),
                 record.get('unit'), record.get('type'),
                 record.get('x'), record.get('y'), record.get('reason')))

    # --- combat log: written, not yet read

    def write_turn_events(self, turn, events):
        """Record the events one resolution produced.

        Not on the port. A caller that wants events recorded reaches here;
        `service/turn.py` does not yet. Kept here so the table is on the
        schema and reachable for whichever step wires it up.
        """
        self.ensure()
        connection = self._get()
        connection.execute('DELETE FROM turn_events WHERE turn_no=?',
                           (int(turn),))
        for seq, event in enumerate(events):
            connection.execute(
                'INSERT INTO turn_events (turn_no, seq, kind, payload) '
                'VALUES (?, ?, ?, ?)',
                (int(turn), seq,
                 getattr(event, 'kind', None) or event.get('kind'),
                 json.dumps(getattr(event, 'detail', None)
                            or event.get('detail') or {})))

    # --- the bus, still over FIFOs until step 5

    def wake(self, name):
        return notify.signal(notify.wake_path(self.data_path, str(name)))

    def waiter(self, name):
        return notify.Waiter(notify.wake_path(self.data_path, str(name)))

    # --- private helpers

    def _db_ready(self):
        """Whether the database has been opened and its schema applied.

        A caller may `read_*` a game that does not exist yet; the answer is
        "nothing", not an error, the same way it was on the YAML backend.
        """
        if self._connection is None:
            if not os.path.exists(self.db_path):
                return False
            self._connect()
        return self._has_schema()

    def _get(self, *args):
        """The connection, with a query passed through when one is given.

        A statement outside a `held()` block still needs a connection, and
        every read reaches here rather than `self._connection` so that the
        connection is opened lazily.
        """
        if self._connection is None:
            self._connect()
        if not args:
            return self._connection
        return self._connection.execute(*args)


class _Transaction:
    """The context manager `held()` returns."""

    def __init__(self, repository, read):
        self._repository = repository
        self._read = read

    def __enter__(self):
        self._repository._enter(self._read)
        return self

    def __exit__(self, kind, value, traceback):
        self._repository._leave(failed=kind is not None)
        return False


def _unit_row_to_dict(row):
    """One `units` (or `orders`) row as the dict the service layer expects."""
    return {
        'id': row['id'],
        'player': row['owner'],
        'type': row['type_name'],
        'name': row['name'],
        'symbol': row['symbol'],
        'attack': row['attack'],
        'health': row['health'],
        'energy': row['energy'],
        'type_attack': row['type_attack'],
        'type_health': row['type_health'],
        'type_energy': row['type_energy'],
        'x': row['x'], 'y': row['y'],
        'state': row['state'], 'direction': row['direction'],
        'destroyed': bool(row['destroyed']),
        'on_board': bool(row['on_board']),
    }


def _insert_unit(connection, unit):
    connection.execute(
        f"INSERT INTO units (id, {', '.join(_UNIT_COLUMNS)}) "
        f"VALUES ({', '.join(['?'] * (1 + len(_UNIT_COLUMNS)))})",
        (int(unit['id']), int(unit['player']),
         unit['name'], unit['type'], unit['symbol'],
         int(unit['attack']), int(unit['health']), int(unit['energy']),
         int(unit['type_attack']), int(unit['type_health']),
         int(unit['type_energy']),
         int(unit['x']), int(unit['y']),
         int(unit['state']), int(unit['direction']),
         int(bool(unit['destroyed'])), int(bool(unit['on_board']))))


def _insert_order(connection, player_number, index, unit):
    connection.execute(
        f"INSERT INTO orders (player_number, id, {', '.join(_UNIT_COLUMNS)}) "
        f"VALUES ({', '.join(['?'] * (2 + len(_UNIT_COLUMNS)))})",
        (player_number, index, int(unit['player']),
         unit['name'], unit['type'], unit['symbol'],
         int(unit['attack']), int(unit['health']), int(unit['energy']),
         int(unit['type_attack']), int(unit['type_health']),
         int(unit['type_energy']),
         int(unit['x']), int(unit['y']),
         int(unit['state']), int(unit['direction']),
         int(bool(unit['destroyed'])), int(bool(unit['on_board']))))
