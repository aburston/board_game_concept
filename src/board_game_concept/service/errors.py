"""What goes wrong, said in a way a caller can act on.

Loading a game used to report a problem and then call `sys.exit`, which is
fine for a command line session and useless to anything else: one bad request
would take a web worker down with it. These are raised instead, and whoever is
holding the session decides what to do about them.

Each carries the message that used to be printed, so the roles say the same
things they always did.
"""


class GameError(Exception):
    """Something the caller asked for cannot be done."""

    def __init__(self, message, detail=None):
        super().__init__(message)
        self.message = message
        # the underlying error, where there was one worth showing
        self.detail = detail

    def lines(self):
        """What to report, one line at a time."""
        if self.detail is None:
            return [self.message]
        return [self.message, str(self.detail)]


class GameDataError(GameError):
    """The game on disk cannot be read."""


class NoSuchGame(GameDataError):
    """There is no game where one was expected."""


class UnreadableGame(GameDataError):
    """A game file exists but cannot be parsed."""


class NoSuchPlayer(GameDataError):
    """The session is for a player this game does not have."""
