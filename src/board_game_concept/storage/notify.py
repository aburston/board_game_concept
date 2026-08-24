"""The `Notifier` interface a `Game` waits through.

The bus lives on its own interface so a repository does not have to
implement it - a caller polls if the environment carries no rendezvous.
`NullNotifier` is what the local flow uses: the outer loops in
`service/turn.py` re-check the condition after every `wait()` return, so
sleeping `POLL_INTERVAL` between checks is what any implementation would
fall back to when it cannot be told.

`FifoNotifier` used to sit here too, wrapping a `mkfifo` rendezvous
between a client and a server that ran on the same host. Long-poll over
HTTP replaced it in step 5, so what stayed after step 6 was a bus with
one implementation for two transports (the FIFO for local, long-poll for
HTTP - and long-poll never went through this interface). Step 7 retires
the FIFO helpers entirely; local waits poll at `POLL_INTERVAL`, which is
what the FIFO waiter's safety timeout was already doing on any platform
without `mkfifo`.
"""

import time
from abc import ABC, abstractmethod


# how long a caller sleeps between re-checks of the condition it is
# actually waiting for. Kept as a constant so a future notifier that does
# have push semantics (SSE, WebSocket, Redis pub/sub) can override the
# waiter without touching the callers
SAFETY_TIMEOUT = 5.0
POLL_INTERVAL = 0.2


class Notifier(ABC):
    """Something that carries a wake between processes, by name.

    Split off the storage port so a backend that does not know how to
    rendezvous has no method to leave unimplemented. `Game` builds a
    `NullNotifier` by default; a caller passing something else opts into
    push semantics they arranged themselves.
    """

    @abstractmethod
    def wake(self, name):
        """Wake whoever is waiting under this name, if anyone is."""

    @abstractmethod
    def waiter(self, name):
        """Something to block on until `wake` is called with the same name."""


class NullNotifier(Notifier):
    """The no-op notifier every `Game` gets by default.

    `wake` is a lost signal and `waiter` hands back something that sleeps
    briefly and returns. Callers re-check what they were waiting on
    either way, so a game polls at `POLL_INTERVAL` rather than blocking -
    the honest thing to do when no rendezvous exists.
    """

    def wake(self, name):
        return False

    def waiter(self, name):
        return _NullWaiter()


class _NullWaiter:
    # pylint: disable=unused-argument
    def wait(self, timeout=SAFETY_TIMEOUT):
        # the outer loop re-checks the condition after this returns; the
        # sleep is what keeps the loop from spinning. `min` with the
        # caller's timeout so a short-timeout caller still gets that
        time.sleep(min(timeout, POLL_INTERVAL))
        return False

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
