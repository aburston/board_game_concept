"""Waking the other side of the file transport instead of polling for it."""

import os
import time

import pytest

from board_game_concept.storage import notify
from cli_harness import CliTestCase, CLIENT_PROMPT

pytestmark = pytest.mark.skipif(
    not notify.HAVE_FIFOS, reason="this platform has no FIFOs")


def test_signalling_nobody_is_not_an_error(tmp_path):
    # the other side may not have reached its wait yet; it will see the state
    # it was waiting for when it checks
    assert notify.signal(notify.wake_path(str(tmp_path), 'server')) is False


def test_a_waiter_is_woken(tmp_path):
    path = notify.wake_path(str(tmp_path), 'server')
    with notify.Waiter(path) as waiter:
        assert notify.signal(path) is True
        assert waiter.wait(timeout=5) is True


def test_a_signal_sent_before_the_wait_is_not_lost(tmp_path):
    # the FIFO is opened before the condition is checked, so a signal that
    # arrives while nobody is inside wait() is buffered
    path = notify.wake_path(str(tmp_path), 'server')
    with notify.Waiter(path) as waiter:
        notify.signal(path)
        notify.signal(path)
        assert waiter.wait(timeout=5) is True


def test_waiting_gives_up_rather_than_blocking_for_ever(tmp_path):
    path = notify.wake_path(str(tmp_path), '1')
    with notify.Waiter(path) as waiter:
        started = time.monotonic()
        assert waiter.wait(timeout=0.3) is False
        assert time.monotonic() - started < 5


def test_the_fifo_is_kept_out_of_the_players_directory(tmp_path):
    # loading a game opens every file in the players directory, and opening a
    # FIFO would block for ever
    data = tmp_path / 'data'
    data.mkdir()
    with notify.Waiter(notify.wake_path(str(data), 'server')):
        assert os.listdir(str(tmp_path)) == ['data']


def test_the_fifo_notifier_wakes_and_waits(tmp_path):
    """The bus a YAML-backed game uses, exercised through the `Notifier` shape."""
    notifier = notify.FifoNotifier(str(tmp_path))
    with notifier.waiter('server') as waiter:
        assert notifier.wake('server') is True
        assert waiter.wait(timeout=5) is True


def test_the_null_notifier_does_nothing_and_does_not_raise():
    """The notifier a backend that carries no bus is fitted with."""
    notifier = notify.NullNotifier()
    # a signal is a lost signal
    assert notifier.wake('server') is False
    # and a waiter returns from `wait` at once, so callers poll
    with notifier.waiter('server') as waiter:
        started = time.monotonic()
        assert waiter.wait(timeout=0.5) is False
        assert time.monotonic() - started < 0.4


def test_game_wraps_the_yaml_repository_in_a_fifo_notifier(tmp_path):
    """A `Game` built with a YAML backend still rendezvous over FIFOs."""
    from board_game_concept import Game, YamlGameRepository

    game = Game(YamlGameRepository('one', base_path=str(tmp_path)), 0)
    assert isinstance(game.notifier, notify.FifoNotifier)


def test_game_falls_back_to_a_null_notifier_when_the_repository_has_no_bus():
    """A backend that only reads and writes carries no bus, so `Game` polls."""
    from board_game_concept import Game

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
        # resolved turn by looking every five, so this took upwards of fifteen
        # seconds. The threshold is here to catch polling creeping back, not
        # to measure performance
        assert elapsed < 8, f"the turn took {elapsed:.1f}s to come back"
