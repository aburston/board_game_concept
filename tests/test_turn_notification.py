"""What the notifier interface still promises, after the FIFO retirement.

The FIFO transport is gone. `NullNotifier` is the only implementation:
its `waiter` sleeps `POLL_INTERVAL` and returns, and the outer loops in
`service/turn.py` re-check the condition. `TurnsResolveWithoutWaiting`
is the guard against a poll loop creeping back - a committed turn still
comes back within seconds, not minutes.
"""

import time

from board_game_concept.storage import notify
from cli_harness import CliTestCase, CLIENT_PROMPT


def test_the_null_notifier_does_nothing_and_does_not_raise():
    """The notifier every `Game` gets by default."""
    notifier = notify.NullNotifier()
    # a signal is a lost signal
    assert notifier.wake('server') is False
    # and a waiter returns from `wait` after `POLL_INTERVAL`, so the
    # outer loop can re-check the condition it was waiting on. Callers
    # poll rather than block
    with notifier.waiter('server') as waiter:
        started = time.monotonic()
        assert waiter.wait(timeout=1.0) is False
        elapsed = time.monotonic() - started
        # POLL_INTERVAL is 0.2s; a short-timeout caller still gets that
        assert elapsed < 1.0


def test_every_game_gets_a_null_notifier():
    """After step 7, no repository carries a bus - every `Game` polls."""
    from board_game_concept import Game
    from board_game_concept.storage.sqlite_repository import (
        SqliteGameRepository)
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        game = Game(SqliteGameRepository('one', base_path=tmp), 0)
        assert isinstance(game.notifier, notify.NullNotifier)

    class QuietRepository:
        pass

    game = Game(QuietRepository(), 0)
    assert isinstance(game.notifier, notify.NullNotifier)


class TurnsResolveWithoutWaiting(CliTestCase):

    def test_a_committed_turn_comes_back_promptly(self):
        self.server = self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)

        started = time.monotonic()
        client.send_line('commit')
        client.read_until('commit complete')
        client.read_until_count(CLIENT_PROMPT, 4, timeout=60)
        elapsed = time.monotonic() - started

        # the barrier used to be found by looking every ten seconds and the
        # resolved turn by looking every five, so this took upwards of
        # fifteen seconds. Under `NullNotifier` a `POLL_INTERVAL` of 0.2s
        # keeps it well under the threshold; the assertion catches a poll
        # loop creeping back
        assert elapsed < 8, f"the turn took {elapsed:.1f}s to come back"
