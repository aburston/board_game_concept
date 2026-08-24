"""Holding a game while it is read or written.

A game directory is written by one process and read by others, and until this
there was nothing arranging for them to take turns. A client loading a game
raced the server deleting orders, and a reader could catch a file part way
through being written.

An advisory lock on a file in the game's directory. Advisory means it binds only
those who ask for it, which is the same contract every process here already runs
under - nothing stops somebody editing a game directory by hand, and nothing
ever did.

Where the platform has no such lock this does nothing and says so, the way
`notify.py` waits on the clock where there are no FIFOs. That is not safe, and
it is not claimed to be: a caller gets exactly the behaviour it had before any
of this existed.

Waiting is bounded rather than indefinite. The process that dies holding a lock
has it released by the operating system, so the bound is for the wedged process
rather than the dead one - and a bound turns a hang, which is the worst thing to
debug, into something that says what it was waiting for.
"""

import errno
import os
import time

from ..service.errors import GameDataError

try:
    import fcntl
except ImportError:  # pragma: no cover - platforms without it
    fcntl = None

HAVE_LOCKS = fcntl is not None

# how long to wait for a game somebody else is holding. The spans that hold one
# are milliseconds, so reaching this means a holder is wedged rather than busy
TIMEOUT = 30.0

# how often to ask again while waiting
RETRY_INTERVAL = 0.005


class GameIsBusy(GameDataError):
    """Somebody has been holding this game for longer than they should."""


class Holding:
    """The lock on one game, and how deep into it this repository is.

    Re-entrant because `flock` is per open file description: a second hold
    inside a first would take a second descriptor and wait for the first to let
    go, which is a process waiting for itself. Nothing nests today, and the
    failure mode if something ever did would be a hang.
    """

    def __init__(self, path):
        self.path = path
        self.depth = 0
        self.fd = None

    def take(self, read=False):
        return _Held(self, read=read)

    # --- what `_Held` does at each end

    def acquire(self, read):
        if self.depth:
            # already held by this repository, and `flock` would wait for us
            self.depth += 1
            return
        if HAVE_LOCKS:
            self.fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
            try:
                self._flock(read)
            except BaseException:
                os.close(self.fd)
                self.fd = None
                raise
        self.depth = 1

    def release(self):
        self.depth -= 1
        if self.depth or self.fd is None:
            return
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)
            self.fd = None

    def _flock(self, read):
        """Wait for the lock, but not for ever."""
        wanted = (fcntl.LOCK_SH if read else fcntl.LOCK_EX) | fcntl.LOCK_NB
        deadline = time.monotonic() + TIMEOUT
        while True:
            try:
                fcntl.flock(self.fd, wanted)
                return
            except OSError as e:
                if e.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    raise GameIsBusy(
                        f"gave up waiting to {'read' if read else 'write'} "
                        f"a game somebody else is holding: {self.path}") from e
                time.sleep(RETRY_INTERVAL)


class _Held:
    """One hold, released when its caller is done with it however that happens."""

    def __init__(self, holding, read):
        self.holding = holding
        self.read = read

    def __enter__(self):
        self.holding.acquire(self.read)
        return self

    def __exit__(self, kind, value, traceback):
        self.holding.release()
        return False
