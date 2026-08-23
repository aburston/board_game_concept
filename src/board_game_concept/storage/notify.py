"""Waking the other side of the file transport.

Players publish orders by writing files and the server publishes results the
same way, so each side has to find out that the other has written something.
Both used to discover it by looking again every few seconds, which cost up to
fifteen seconds of dead time per turn for work that takes milliseconds.

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
