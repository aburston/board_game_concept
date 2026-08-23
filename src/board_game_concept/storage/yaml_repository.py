"""Keeping a game as YAML files under a directory.

The layout `game-persistence` describes: shared game data under `data`,
per-player files under `players`, one directory per game number. This is the
only module that knows any of those names.
"""

import os

import yaml

from ..service.errors import UnreadableGame
from . import notify
from .repository import GameRepository


class YamlGameRepository(GameRepository):

    def __init__(self, gameno, base_path=None):
        # where games live is given, not discovered: reading it from the
        # process working directory made the caller's current directory part
        # of the storage contract
        if base_path is None:
            base_path = os.getcwd()
        self.gameno = gameno
        self.root = os.path.join(base_path, 'games', f'_{gameno}')
        self.data_path = os.path.join(self.root, 'data')
        self.player_path = os.path.join(self.root, 'players')

    # --- the game itself

    def ensure(self):
        for path in (self.data_path, self.player_path):
            if not os.path.exists(path):
                os.makedirs(path)

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
        with open(os.path.join(self.data_path, 'board.yaml'), 'w') as file:
            yaml.safe_dump({'board': {'size_x': size_x, 'size_y': size_y}}, file)

    def read_progress(self):
        return self._read_yaml(
            os.path.join(self.data_path, 'progress.yaml'), 'the game progress')

    def write_progress(self, progress):
        self.ensure()
        with open(os.path.join(self.data_path, 'progress.yaml'), 'w') as file:
            yaml.safe_dump(progress, file)

    def read_units(self):
        units = self._read_yaml(
            os.path.join(self.data_path, 'units.yaml'), 'the units')
        if units is None:
            return []
        # a board holding no units is written as the string, not as null
        listed = units['units']
        return [] if listed == 'None' or not listed else listed

    def write_units(self, text):
        with open(os.path.join(self.data_path, 'units.yaml'), 'w') as file:
            file.write(text)

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
        return self._read_yaml(self._player_file(number),
                               f'the file for player {number}')

    def write_player(self, number, types):
        with open(self._player_file(number), 'w') as file:
            yaml.safe_dump({'number': number, 'types': types}, file)

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

    def write_view(self, number, text):
        with open(self._view_file(number), 'w') as file:
            file.write(text)

    # --- orders, and the commit barrier they signal

    def _orders_file(self, number):
        return os.path.join(self.player_path, f'{number}_units.yaml')

    def has_orders(self, number):
        return os.path.exists(self._orders_file(number))

    def read_orders(self, number):
        return self._read_yaml(self._orders_file(number),
                               f'the orders published by player {number}')

    def write_orders(self, number, text):
        with open(self._orders_file(number), 'w') as file:
            file.write(text)

    def clear_orders(self):
        for name in os.listdir(self.player_path):
            if name.endswith('_units.yaml') and not name.endswith('_units_seen.yaml'):
                try:
                    os.remove(os.path.join(self.player_path, name))
                except FileNotFoundError:
                    pass

    def committed_players(self):
        if not os.path.exists(self.player_path):
            return []
        numbers = []
        for name in os.listdir(self.player_path):
            if name.endswith('_units.yaml') and not name.endswith('_units_seen.yaml'):
                stem = name[:-len('_units.yaml')]
                if stem.isdigit():
                    numbers.append(int(stem))
        return sorted(numbers)

    def _commit_marker(self, number):
        return os.path.join(self.player_path, f'commit_{number}')

    def mark_committed(self, number):
        with open(self._commit_marker(number), 'w') as file:
            file.write("")

    def has_committed(self, number):
        return os.path.exists(self._commit_marker(number))

    # --- work a session has not committed yet

    def _draft_file(self, number):
        return os.path.join(self.player_path, f'{number}_draft.yaml')

    def read_draft(self, number):
        return self._read_yaml(self._draft_file(number),
                               f'the draft held by session {number}')

    def write_draft(self, number, draft):
        with open(self._draft_file(number), 'w') as file:
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
        with open(self._rejections_file(number), 'w') as file:
            yaml.safe_dump({'turn': turn, 'rejected': rejected}, file)

    # --- telling the other side something has changed

    def wake(self, name):
        return notify.signal(notify.wake_path(self.data_path, str(name)))

    def waiter(self, name):
        return notify.Waiter(notify.wake_path(self.data_path, str(name)))
