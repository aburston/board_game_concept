"""Keeping a game as YAML files under a directory.

The layout `game-persistence` describes: shared game data under `data`,
per-player files under `players`, one directory per game number. This is the
only module that knows any of those names.
"""

import os

import yaml

from ..service.errors import UnreadableGame
from . import lock
from .repository import GameRepository


class YamlGameRepository(GameRepository):

    def __init__(self, gameno, base_path=None):
        # where games live is given, not discovered: reading it from the
        # process working directory made the caller's current directory part
        # of the storage contract
        if base_path is None:
            # imported here rather than at the top: `cli.session` imports
            # this module, so a module-level import would be a cycle
            from ..cli.session import default_base_path
            base_path = default_base_path()
        self.gameno = gameno
        self.root = os.path.join(base_path, 'games', f'_{gameno}')
        self.data_path = os.path.join(self.root, 'data')
        self.player_path = os.path.join(self.root, 'players')
        # in the game's root rather than beside the files that are listed:
        # `player_numbers`, `committed_players` and `clear_orders` all classify
        # by name, and the root is listed by nothing at all
        self.lock_path = os.path.join(self.root, '.lock')
        self._holding = lock.Holding(self.lock_path)

    # --- the game itself

    def ensure(self):
        for path in (self.data_path, self.player_path):
            if not os.path.exists(path):
                os.makedirs(path)

    # --- holding a game while it is used

    def held(self, read=False):
        self.ensure()
        return self._holding.take(read=read)

    # --- writing

    def _replace(self, path):
        """Write a file by replacing it, rather than by emptying and refilling.

        A reader sees the previous contents or the new ones and never part of
        either, and a process that dies part way through leaves the previous
        contents readable rather than a half-written file.

        The temporary lives in the same directory as its target, because a
        rename is only atomic within one filesystem. Its name carries a suffix
        after the extension so that the three places which classify a game's
        files by name - `player_numbers`, `committed_players` and
        `clear_orders` - all skip it.
        """
        return _Replacement(path)

    def _read_yaml(self, path, what):
        try:
            with open(path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return None
        except yaml.YAMLError as e:
            raise UnreadableGame(f"could not read {what} at {path}", e) from e

    def read_board(self):
        board_meta_data = self._read_yaml(
            os.path.join(self.data_path, 'board.yaml'), 'the board')
        if board_meta_data is None:
            return None
        return (board_meta_data['board']['size_x'],
                board_meta_data['board']['size_y'])

    def write_board(self, size_x, size_y):
        self.ensure()
        with self._replace(os.path.join(self.data_path, 'board.yaml')) as file:
            yaml.safe_dump({'board': {'size_x': size_x, 'size_y': size_y}}, file)

    def read_progress(self):
        return self._read_yaml(
            os.path.join(self.data_path, 'progress.yaml'), 'the game progress')

    def write_progress(self, progress):
        self.ensure()
        with self._replace(os.path.join(self.data_path, 'progress.yaml')) as file:
            yaml.safe_dump(progress, file)

    def read_units(self):
        units = self._read_yaml(
            os.path.join(self.data_path, 'units.yaml'), 'the units')
        if units is None:
            return []
        # a board holding no units is written as the string, not as null
        listed = units['units']
        return [] if listed == 'None' or not listed else listed

    def write_units(self, document):
        with self._replace(os.path.join(self.data_path, 'units.yaml')) as file:
            file.write(dump_units(document))

    # --- players

    def _player_file(self, number):
        return os.path.join(self.player_path, f'{number}.yaml')

    def player_numbers(self):
        if not os.path.exists(self.player_path):
            return []
        numbers = []
        for name in os.listdir(self.player_path):
            stem, extension = os.path.splitext(name)
            if extension == '.yaml' and stem.isdigit():
                numbers.append(int(stem))
        return sorted(numbers)

    def read_player(self, number):
        record = self._read_yaml(self._player_file(number),
                                 f'the file for player {number}')
        if record is None:
            return None
        if record.get('budget') is None:
            # a record this repository wrote always carries one, so a record
            # without one was written by another version or edited by hand.
            # Either way the game is about to be played by rules it was not
            # set up under, which is not something to default past
            raise UnreadableGame(
                f"the file for player {number} at "
                f"{self._player_file(number)} carries no point budget")
        return record

    def write_player(self, number, types, budget):
        with self._replace(self._player_file(number)) as file:
            yaml.safe_dump(
                {'number': number, 'budget': budget, 'types': types}, file)

    # --- what a player can see

    def _view_file(self, number):
        return os.path.join(self.player_path, f'{number}_units_seen.yaml')

    def read_view(self, number):
        view = self._read_yaml(self._view_file(number),
                               f'the view for player {number}')
        if view is None:
            return None
        listed = view['units']
        return [] if listed == 'None' or not listed else listed

    def write_view(self, number, document):
        with self._replace(self._view_file(number)) as file:
            file.write(dump_units(document))

    # --- orders, and the commit barrier they signal

    def _orders_file(self, number):
        return os.path.join(self.player_path, f'{number}_units.yaml')

    def has_orders(self, number):
        return os.path.exists(self._orders_file(number))

    def read_orders(self, number):
        return self._read_yaml(self._orders_file(number),
                               f'the orders published by player {number}')

    def write_orders(self, number, document):
        with self._replace(self._orders_file(number)) as file:
            file.write(dump_units(document))

    def clear_orders(self):
        for name in os.listdir(self.player_path):
            if name.endswith('_units.yaml') and not name.endswith('_units_seen.yaml'):
                try:
                    os.remove(os.path.join(self.player_path, name))
                except FileNotFoundError:
                    pass

    def committed_players(self, turn=None):
        """The players whose commit stands for the turn now open.

        Read from the commit markers rather than by listing order files. That
        an order file exists means "committed for this turn" only because the
        server deletes it when it resolves one - the fact was encoded in the
        absence of a deletion, which is not a thing to ask a question of.
        """
        if not os.path.exists(self.player_path):
            return []
        numbers = []
        for name in os.listdir(self.player_path):
            if not name.startswith('commit_'):
                continue
            stem = name[len('commit_'):]
            if not stem.isdigit():
                continue
            if turn is not None and self._committed_turn(int(stem)) != turn:
                continue
            numbers.append(int(stem))
        return sorted(numbers)

    def _commit_marker(self, number):
        return os.path.join(self.player_path, f'commit_{number}')

    def _committed_turn(self, number):
        """The turn this player's commit was for, or None if it does not say.

        A marker written before commits recorded a turn is empty. It still
        means the player has committed at least once, which is all it ever
        meant, so it is read as belonging to no particular turn rather than
        as a game that cannot be opened.
        """
        recorded = self._read_yaml(self._commit_marker(number),
                                   f'the commit by player {number}')
        if not isinstance(recorded, dict):
            return None
        return recorded.get('turn')

    def mark_committed(self, number, turn=None):
        with self._replace(self._commit_marker(number)) as file:
            yaml.safe_dump({'turn': turn}, file)

    def has_committed(self, number):
        return os.path.exists(self._commit_marker(number))

    def clear_commits(self):
        # the marker stays, because it is also the record that this player has
        # committed at some point, which is what ends setup for them. What is
        # spent is the turn it was committed for
        for number in self.committed_players():
            self.mark_committed(number, None)

    # --- work a session has not committed yet

    def _draft_file(self, number):
        return os.path.join(self.player_path, f'{number}_draft.yaml')

    def read_draft(self, number):
        return self._read_yaml(self._draft_file(number),
                               f'the draft held by session {number}')

    def write_draft(self, number, draft):
        with self._replace(self._draft_file(number)) as file:
            yaml.safe_dump(draft, file)

    def clear_draft(self, number):
        # a draft that is not there has already been discarded, which is what
        # was being asked for
        try:
            os.remove(self._draft_file(number))
        except FileNotFoundError:
            pass

    # --- refused orders

    def _rejections_file(self, number):
        return os.path.join(self.player_path, f'{number}_rejected.yaml')

    def read_rejections(self, number):
        rejected = self._read_yaml(self._rejections_file(number),
                                   f'the orders refused for player {number}')
        if rejected is None:
            return []
        return rejected.get('rejected') or []

    def write_rejections(self, number, rejected, turn=None):
        with self._replace(self._rejections_file(number)) as file:
            yaml.safe_dump({'turn': turn, 'rejected': rejected}, file)


def dump_units(document):
    """A units document as the hand-crafted YAML text the files hold.

    The file layout is a `board` mapping, a `turn` and `player` scalar (each
    either a number or `None`), and a `units` sequence of flow mappings. The
    empty case writes `units: None` rather than `units: []`, because that is
    what the files already held and everything that reads them handles that
    string. Byte-identical with what `serialise_units` used to produce.
    """
    board = document.get('board') or {}
    size_x = board.get('size_x')
    size_y = board.get('size_y')
    text = "board: {" + f" size_x: {size_x}, size_y: {size_y}" + "}\n"
    turn = document.get('turn')
    if turn is not None:
        text += f"turn: {turn}\n"
    text += f"player: {document.get('player')}\n"

    units = document.get('units') or []
    if not units:
        text += "units: None\n"
        return text

    text += "units:\n"
    for unit in units:
        text += "  - { " + _unit_line(unit) + " }\n"
    return text


def _unit_line(unit):
    """One unit as the body of a YAML flow mapping, without the braces."""
    # numbers stay as numbers so a player number that went out as text does
    # not come back as text and no longer match the integer the rest of the
    # game knew the player by
    return (
        f"id: {unit.get('id')}, "
        f"player: {unit.get('player')}, "
        f'type: "{unit.get("type")}", '
        f'name: "{unit.get("name")}", '
        f'symbol: "{unit.get("symbol")}", '
        f"attack: {unit.get('attack')}, "
        f"health: {unit.get('health')}, "
        f"energy: {unit.get('energy')}, "
        # the design, so that a type learned by contact is the type as its
        # owner built it and not the state the unit was in when it was met
        f"type_attack: {unit.get('type_attack')}, "
        f"type_health: {unit.get('type_health')}, "
        f"type_energy: {unit.get('type_energy')}, "
        f"x: {unit.get('x')}, y: {unit.get('y')}, "
        f"state: {unit.get('state')}, direction: {unit.get('direction')}, "
        f"destroyed: {unit.get('destroyed')}, on_board: {unit.get('on_board')}"
    )


class _Replacement:
    """A file being written under a temporary name, to be renamed into place.

    Renamed only when the body finishes without raising: a write that fails
    part way leaves the target as it was and the temporary behind, which
    nothing lists and nothing reads.
    """

    def __init__(self, path):
        self.path = path
        # the process number keeps two writers of the same file from sharing a
        # temporary; the suffix after `.yaml` is what makes it invisible to
        # everything that classifies a game's files by name
        self.temporary = f'{path}.writing-{os.getpid()}'
        self.file = None

    def __enter__(self):
        self.file = open(self.temporary, 'w', encoding='utf-8')
        return self.file

    def __exit__(self, kind, value, traceback):
        self.file.close()
        if kind is None:
            os.replace(self.temporary, self.path)
            return False
        try:
            os.remove(self.temporary)
        except OSError:
            pass
        return False
