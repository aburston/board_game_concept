"""What a reader can catch a writer doing, and what a crash can leave behind.

A game directory is written by one process and read by others, with nothing
arranging for them to take turns. These are the two ends of that: a write that
cannot be caught half done, and a game that can be held while it is used.
"""

import os
import time

import pytest
import yaml

from board_game_concept import YamlGameRepository

# this file is about the YAML backend's write path - the tempfile-and-rename
# dance and the advisory `flock` lock. The SQLite backend's equivalents live
# in `test_sqlite_safety.py`
pytestmark = pytest.mark.backend('yaml')


def repository(tmp_path, gameno='one'):
    made = YamlGameRepository(gameno, base_path=str(tmp_path))
    made.ensure()
    return made


# --- a write replaces what it replaces


def test_a_write_leaves_no_moment_where_the_file_is_empty(tmp_path):
    """The target is renamed into place, so it is never open for truncation."""
    made = repository(tmp_path)
    made.write_units({'units': None})
    target = os.path.join(made.data_path, 'units.yaml')
    before = open(target, encoding='utf-8').read()

    seen = []
    original = made._replace

    def watched(path):
        # what a reader would find while the new contents are being written
        if path == target:
            seen.append(open(path, encoding='utf-8').read())
        return original(path)

    made._replace = watched
    made.write_units({'units': [{'id': 0}]})

    assert seen == [before], 'the target changed before the write finished'
    assert 'id: 0' in open(target, encoding='utf-8').read()


def test_a_write_that_does_not_finish_leaves_the_previous_contents(tmp_path):
    made = repository(tmp_path)
    made.write_board(4, 4)
    target = os.path.join(made.data_path, 'board.yaml')

    with pytest.raises(RuntimeError):
        with made._replace(target) as file:
            file.write('board: {size_x: 9')
            raise RuntimeError('the process ended here')

    assert made.read_board() == (4, 4)
    assert yaml.safe_load(open(target, encoding='utf-8'))['board']['size_x'] == 4


def test_a_write_that_does_not_finish_leaves_nothing_behind(tmp_path):
    made = repository(tmp_path)
    target = os.path.join(made.data_path, 'board.yaml')

    with pytest.raises(RuntimeError):
        with made._replace(target) as file:
            file.write('half')
            raise RuntimeError('the process ended here')

    assert os.listdir(made.data_path) == []


@pytest.mark.parametrize('written', ['player', 'commit', 'orders'])
def test_what_a_write_leaves_behind_is_not_read_as_a_game_file(tmp_path,
                                                               written):
    """The three places that classify a game's files by name must skip it."""
    made = repository(tmp_path)
    made.write_player(1, {})
    made.mark_committed(1, turn=0)
    made.write_orders(1, {'units': None})

    target = {'player': made._player_file(1),
              'commit': made._commit_marker(1),
              'orders': made._orders_file(1)}[written]
    leftover = f'{target}.writing-99999'
    with open(leftover, 'w', encoding='utf-8') as file:
        file.write('half a file')

    assert made.player_numbers() == [1]
    assert made.committed_players() == [1]
    made.clear_orders()
    assert os.path.exists(leftover), 'the leftover was mistaken for orders'
    assert made.has_orders(1) is False


def test_a_game_written_before_this_change_still_reads(tmp_path):
    """The files are the same files; only the way they are put there changed."""
    made = repository(tmp_path)
    with open(os.path.join(made.data_path, 'board.yaml'), 'w',
              encoding='utf-8') as file:
        yaml.safe_dump({'board': {'size_x': 5, 'size_y': 6}}, file)

    assert made.read_board() == (5, 6)


# --- holding a game


def test_a_game_is_held_and_let_go(tmp_path):
    made = repository(tmp_path)

    with made.held():
        assert made._holding.depth == 1
    assert made._holding.depth == 0
    assert made._holding.fd is None


def test_a_game_is_let_go_even_when_its_caller_fails(tmp_path):
    made = repository(tmp_path)

    with pytest.raises(RuntimeError):
        with made.held():
            raise RuntimeError('the caller failed here')

    assert made._holding.depth == 0
    assert made._holding.fd is None
    # and can be held again
    with made.held():
        pass


def test_holding_a_game_inside_a_hold_of_it_does_not_wait_for_itself(tmp_path):
    """`flock` is per open file description, so this would wait for itself."""
    made = repository(tmp_path)

    with made.held():
        with made.held():
            assert made._holding.depth == 2
        assert made._holding.depth == 1
    assert made._holding.depth == 0


def test_what_holds_a_game_is_not_one_of_its_files(tmp_path):
    made = repository(tmp_path)
    made.write_player(1, {})
    made.mark_committed(1, turn=0)

    with made.held():
        pass

    assert os.path.exists(os.path.join(made.root, '.lock'))
    assert made.player_numbers() == [1]
    assert made.committed_players() == [1]
    assert made.read_board() is None


def test_a_hold_that_cannot_be_had_is_reported_rather_than_waited_on(
        tmp_path, monkeypatch):
    """A wedged holder becomes an error that says what it wanted."""
    from board_game_concept.storage import lock as lock_module

    made = repository(tmp_path)
    other = repository(tmp_path)
    monkeypatch.setattr(lock_module, 'TIMEOUT', 0.05)

    with other.held():
        with pytest.raises(lock_module.GameIsBusy):
            with made.held():
                pass


def test_a_repository_carries_on_where_the_platform_has_no_lock(
        tmp_path, monkeypatch):
    """As `notify.py` waits on the clock where there are no FIFOs."""
    from board_game_concept.storage import lock as lock_module

    monkeypatch.setattr(lock_module, 'HAVE_LOCKS', False)
    made = repository(tmp_path)

    with made.held():
        # nothing is holding it, and nothing claims otherwise
        assert made._holding.fd is None
    assert made._holding.depth == 0
    # and the game is still usable
    made.write_board(4, 4)
    assert made.read_board() == (4, 4)


# --- the sharing rules, between processes rather than between threads


HOLDER = """
import sys, time
sys.path.insert(0, {src!r})
sys.path.insert(0, {tests!r})
from board_game_concept import YamlGameRepository
made = YamlGameRepository(sys.argv[4], base_path=sys.argv[1])
made.ensure()
read = sys.argv[2] == 'read'
with made.held(read=read):
    print('held', flush=True)
    time.sleep(float(sys.argv[3]))
print('done', flush=True)
"""


def a_holder(tmp_path, how, seconds, gameno='one'):
    """A separate process holding the game, for reading or for writing."""
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    code = HOLDER.format(src=str(root / 'src'), tests=str(root / 'tests'))
    proc = subprocess.Popen(
        [sys.executable, '-c', code, str(tmp_path), how, str(seconds), gameno],
        stdout=subprocess.PIPE, universal_newlines=True)
    assert proc.stdout.readline().strip() == 'held', 'the holder never held it'
    return proc


def how_long(call):
    started = time.monotonic()
    call()
    return time.monotonic() - started


def test_a_writer_waits_for_another_writer(tmp_path):
    made = repository(tmp_path)
    holder = a_holder(tmp_path, 'write', 0.4)
    try:
        def hold():
            with made.held():
                pass

        assert how_long(hold) > 0.2, 'the second writer did not wait'
    finally:
        holder.wait(timeout=10)


def test_a_reader_waits_for_a_writer(tmp_path):
    made = repository(tmp_path)
    holder = a_holder(tmp_path, 'write', 0.4)
    try:
        def hold():
            with made.held(read=True):
                pass

        assert how_long(hold) > 0.2, 'the reader read a game being written'
    finally:
        holder.wait(timeout=10)


def test_readers_do_not_exclude_each_other(tmp_path):
    made = repository(tmp_path)
    holder = a_holder(tmp_path, 'read', 0.4)
    try:
        def hold():
            with made.held(read=True):
                pass

        assert how_long(hold) < 0.2, 'a reader waited for another reader'
    finally:
        holder.wait(timeout=10)


def test_a_writer_waits_for_a_reader(tmp_path):
    made = repository(tmp_path)
    holder = a_holder(tmp_path, 'read', 0.4)
    try:
        def hold():
            with made.held():
                pass

        assert how_long(hold) > 0.2, 'a writer wrote a game being read'
    finally:
        holder.wait(timeout=10)


# --- what is never held


class WatchesHolding:
    """A repository that remembers when it was asked to hold the game."""

    def __init__(self, wrapped):
        self._wrapped = wrapped
        self.holds = 0
        self.watching = False

    def __getattr__(self, name):
        return getattr(self._wrapped, name)

    def held(self, read=False):
        if self.watching:
            self.holds += 1
        return self._wrapped.held(read=read)


def test_waiting_for_players_does_not_hold_the_game(tmp_path):
    """A barrier waits for as long as a player takes to decide.

    Held across that, a game would be stopped rather than protected: the very
    players it is waiting for could not commit, because committing holds it.
    """
    from board_game_concept import Game
    from game_harness import GameHarness

    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    harness.deploy(1, [('Cross', 'X', 1, 5, 10)], [('Cross', 'x1', 0, 0)])

    watched = WatchesHolding(harness.repository())
    server = Game(watched, 0)
    server.load()
    watched.watching = True
    # the sole player has already committed, so the barrier is satisfied and
    # the loop finishes without blocking
    server.waitForPlayerCommit()

    assert watched.holds == 0, 'the game was held while waiting for players'


def test_waiting_for_a_turn_does_not_hold_the_game(tmp_path):
    from board_game_concept import Game
    from game_harness import GameHarness

    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    harness.deploy(1, [('Cross', 'X', 1, 5, 10)], [('Cross', 'x1', 0, 0)])
    harness.resolve()

    watched = WatchesHolding(harness.repository())
    client = Game(watched, 1)
    client.load()
    watched.watching = True
    # the turn has been resolved, so there are no orders left to wait for
    client.waitForTurn()

    assert watched.holds == 0, 'the game was held while waiting for a turn'


def test_a_player_can_commit_while_the_server_waits_for_them(tmp_path):
    """End to end: the thing that would freeze the game if a wait held it."""
    from game_harness import GameHarness

    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [('Cross', 'X', 1, 5, 10)], [('Cross', 'x1', 0, 0)])

    # player 1 has committed and player 2 has not, so the turn is open. Another
    # process holding it for reading, as a watching observer would, must not
    # stop player 2 committing either
    holder = a_holder(tmp_path, 'read', 0.05, gameno='harness')
    try:
        harness.deploy(2, [('Ring', 'O', 1, 5, 10)], [('Ring', 'o1', 3, 3)])
    finally:
        holder.wait(timeout=10)

    assert harness.repository().committed_players(0) == [1, 2]
    assert harness.resolve()
