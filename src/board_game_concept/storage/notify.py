"""Waking whichever process is on the other side.

The notifier is the rendezvous between server and client. On the YAML backend
that rendezvous is a FIFO; on a backend that carries no bus, it is nothing
and no caller waits. Both are `Notifier`s and callers ask the notifier
rather than the repository.

A waiter blocks on a FIFO until somebody signals it. The signal is only ever a
hint: every caller re-checks the condition it actually cares about before and
after waiting, so a signal that is missed or arrives early costs a little
latency and never correctness. That is also why waiting has a timeout - if a
wake-up is ever lost, the next check finds the state anyway.

FIFOs live under the game's `data` directory rather than beside the player
files, because loading a game opens every file in the players directory and
opening a FIFO would block forever.
"""

import os
import select
import time
from abc import ABC, abstractmethod

# how long a waiter blocks before re-checking on its own. A signal normally
# arrives first; this is the backstop.
SAFETY_TIMEOUT = 5.0

# used instead when the platform has no FIFOs
POLL_INTERVAL = 0.2

HAVE_FIFOS = hasattr(os, 'mkfifo')


def wake_path(data_path, name):
    """Where the FIFO for a given waiter lives."""
    return os.path.join(data_path, f'.wake_{name}')


class Waiter:
    """Blocks until somebody signals, or until the timeout runs out.

    The FIFO is opened read-write so that reads block for data rather than
    returning end-of-file when no writer happens to be attached, and so that a
    signal sent while nobody is inside `wait` is buffered rather than lost.
    """

    def __init__(self, path):
        self.path = path
        self.fd = None
        if not HAVE_FIFOS:
            return
        try:
            if not os.path.exists(path):
                os.mkfifo(path, 0o600)
            self.fd = os.open(path, os.O_RDWR | os.O_NONBLOCK)
        except OSError:
            # an unusable FIFO is not fatal: fall back to waiting on the clock
            self.fd = None

    def wait(self, timeout=SAFETY_TIMEOUT):
        """Wait to be woken. True if a signal arrived, False if it timed out."""
        if self.fd is None:
            time.sleep(min(timeout, POLL_INTERVAL))
            return False
        try:
            ready, _, _ = select.select([self.fd], [], [], timeout)
        except OSError:
            return False
        if not ready:
            return False
        try:
            # drain whatever has accumulated: one wake-up is enough, however
            # many signals produced it
            os.read(self.fd, 4096)
        except OSError:
            pass
        return True

    def close(self):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def signal(path):
    """Wake whoever is waiting on this FIFO. True if anyone was listening.

    Nobody waiting is the ordinary case, not an error: the other side may not
    have reached its wait yet, and will see the state it was waiting for when
    it checks.
    """
    if not HAVE_FIFOS:
        return False
    try:
        fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
    except OSError:
        return False
    try:
        os.write(fd, b'.')
    except OSError:
        return False
    finally:
        os.close(fd)
    return True


class Notifier(ABC):
    """Something that carries a wake between processes, by name.

    Split off the storage port so a backend that does not know how to
    rendezvous - a database, most likely - has no method to leave
    unimplemented. `Game` picks the notifier that fits the repository it
    was handed, or takes one it was passed.
    """

    @abstractmethod
    def wake(self, name):
        """Wake whoever is waiting under this name, if anyone is."""

    @abstractmethod
    def waiter(self, name):
        """Something to block on until `wake` is called with the same name."""


class FifoNotifier(Notifier):
    """The FIFO rendezvous the YAML backend used to expose from the port.

    Takes a `data_path` directly, and knows the FIFO layout the backend
    already used. `Game` builds one of these when the repository is the
    YAML one, so the split is real: the ABC no longer promises the bus,
    the backend still keeps its FIFO helpers around, and this is what
    ties them to a `Notifier` shape.
    """

    def __init__(self, data_path):
        self._data_path = data_path

    def wake(self, name):
        return signal(wake_path(self._data_path, str(name)))

    def waiter(self, name):
        return Waiter(wake_path(self._data_path, str(name)))


class NullNotifier(Notifier):
    """The no-op notifier a backend that carries no bus is fitted with.

    `wake` is a lost signal and `waiter` hands back something that returns
    from `wait` at once. Callers re-check what they were waiting on either
    way, so a game with no notifier polls rather than blocking, which is
    the honest thing to do when no rendezvous exists.
    """

    def wake(self, name):
        return False

    def waiter(self, name):
        return _NullWaiter()


class _NullWaiter:
    # pylint: disable=unused-argument
    def wait(self, timeout=SAFETY_TIMEOUT):
        return False

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
