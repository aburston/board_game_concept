"""The SQLite backend's `held()` as a transaction.

`test_storage_safety.py` is about the YAML backend's tempfile-and-rename and
its advisory `flock`. This is the SQLite equivalent: `held()` is a
transaction, and the same word does what the file lock did.
"""

import pytest

from board_game_concept.storage.lock import GameIsBusy
from board_game_concept.storage.sqlite_repository import SqliteGameRepository

pytestmark = pytest.mark.backend('sqlite')


def _repository(tmp_path, gameno='one'):
    made = SqliteGameRepository(gameno, base_path=str(tmp_path))
    made.ensure()
    return made


def test_a_write_is_atomic(tmp_path):
    """A committed transaction is what the read sees, and only that."""
    made = _repository(tmp_path)
    made.write_board(4, 4)
    assert made.read_board() == (4, 4)

    try:
        with made.held():
            made.write_board(5, 5)
            raise RuntimeError('the process ended here')
    except RuntimeError:
        pass

    # rolled back rather than committed: the board is still what it was
    reader = SqliteGameRepository('one', base_path=str(tmp_path))
    assert reader.read_board() == (4, 4)


def test_a_second_writer_gets_gameisbusy(tmp_path):
    """`BEGIN IMMEDIATE` is what makes two writers serial."""
    first = _repository(tmp_path)
    with first.held():
        second = SqliteGameRepository('one', base_path=str(tmp_path))
        with pytest.raises(GameIsBusy):
            with second.held():
                pass


def test_a_reader_does_not_block_a_writer(tmp_path):
    """WAL lets a reader through while a writer holds the write lock."""
    writer = _repository(tmp_path)
    writer.write_board(4, 4)
    with writer.held():
        writer.write_board(5, 5)  # inside the transaction

        # a separate connection reads through the WAL snapshot: the write in
        # flight is not visible, but the connection is not blocked
        reader = SqliteGameRepository('one', base_path=str(tmp_path))
        with reader.held(read=True):
            assert reader.read_board() == (4, 4)


def test_nested_held_is_one_transaction(tmp_path):
    """A caller inside a `held()` that calls it again does not open a
    second transaction; the outer one covers both."""
    made = _repository(tmp_path)
    made.write_board(3, 3)

    try:
        with made.held():
            made.write_board(4, 4)
            with made.held():
                made.write_board(5, 5)
            raise RuntimeError('the process ended here')
    except RuntimeError:
        pass

    # the outer transaction rolled back, so the inner writes are gone too
    reader = SqliteGameRepository('one', base_path=str(tmp_path))
    assert reader.read_board() == (3, 3)
