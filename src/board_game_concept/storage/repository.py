"""Where a game's state lives.

A repository reads and writes; it holds no rules. It does not know when a turn
may be resolved, who is allowed to move what, or that an order file appearing
means a player has committed - only how to put a thing somewhere and get it
back.

That line is the point of the interface. Everything above it is written against
these operations rather than against a directory of YAML, so the same game can
be kept somewhere else - a database, most likely - by writing another
implementation and changing nothing else.

The names are deliberately about game concepts rather than files:
`read_units`, not `read_units_yaml`. An implementation that keeps units in a
table should not have to pretend they are a document.
"""


class GameRepository:
    """The operations a game's storage has to offer.

    Subclasses implement all of them. This class exists to say what the set is,
    and to fail loudly rather than silently when one is missing.
    """

    # --- holding a game while it is used

    def held(self, read=False):
        """Hold this game while the caller reads or writes it.

        Used as a context manager. A caller holding a game for writing excludes
        every other holder; callers holding it for reading may hold it
        together. Which is what a turn being resolved needs and what a game
        being read needs, and the difference is the only thing a caller says.

        Holding is the repository's to arrange rather than the caller's, so
        that a repository keeping a game some other way can hold it some other
        way - a database implementing the same two words as a transaction.

        A game is never held across a wait for something a person must do. A
        commit barrier holds a turn open for as long as a player takes to
        decide, and a game held across that would be stopped rather than
        protected.
        """
        raise NotImplementedError

    # --- the game itself

    def ensure(self):
        """Make whatever the game needs to exist, exist."""
        raise NotImplementedError

    def read_board(self):
        """The board's dimensions as (size_x, size_y), or None if unset."""
        raise NotImplementedError

    def write_board(self, size_x, size_y):
        raise NotImplementedError

    def read_progress(self):
        """How far the game has got: the turn number, who is out, how it ended.

        Returns a record or None when no turn has been resolved yet.
        """
        raise NotImplementedError

    def write_progress(self, progress):
        raise NotImplementedError

    def read_units(self):
        """Every unit on the board, as plain records."""
        raise NotImplementedError

    def write_units(self, text):
        raise NotImplementedError

    # --- players

    def player_numbers(self):
        """The players this game holds."""
        raise NotImplementedError

    def read_player(self, number):
        """One player's record, or None if there is no such player."""
        raise NotImplementedError

    def write_player(self, number, types):
        raise NotImplementedError

    # --- what a player can see

    def read_view(self, number):
        """The units last published to this player, as plain records."""
        raise NotImplementedError

    def write_view(self, number, text):
        raise NotImplementedError

    # --- orders, and the commit barrier they signal

    def has_orders(self, number):
        """Whether this player has orders the turn has not yet consumed."""
        raise NotImplementedError

    def read_orders(self, number):
        raise NotImplementedError

    def write_orders(self, number, text):
        raise NotImplementedError

    def clear_orders(self):
        """Discard every player's orders, the turn having consumed them."""
        raise NotImplementedError

    def committed_players(self, turn=None):
        """The players who have committed, for this turn if one is named.

        Naming a turn is the question the commit barrier actually asks. Asking
        without one is asking who has ever committed.
        """
        raise NotImplementedError

    def mark_committed(self, number, turn=None):
        """Record that this player has committed, and for which turn."""
        raise NotImplementedError

    def has_committed(self, number):
        raise NotImplementedError

    def clear_commits(self):
        """Consume every player's commit, the turn having been resolved.

        A commit belongs to the turn it was made for, the way orders do, and
        is spent when that turn is resolved. Having ever committed is a
        different fact and survives this.
        """
        raise NotImplementedError

    # --- work a session has not committed yet

    def read_draft(self, number):
        """This session's uncommitted work, or None if it has none.

        Read only for the session it belongs to. A repository will hand over
        any draft it is asked for, because a repository holds no rules; not
        asking for another player's is the caller's part of the bargain, the
        same way a client reads its own view rather than the whole board.
        """
        raise NotImplementedError

    def write_draft(self, number, draft):
        raise NotImplementedError

    def clear_draft(self, number):
        """Discard this session's draft, committed or abandoned."""
        raise NotImplementedError

    # --- refused orders

    def read_rejections(self, number):
        raise NotImplementedError

    def write_rejections(self, number, rejected, turn=None):
        raise NotImplementedError

    # --- telling the other side something has changed

    def wake(self, name):
        """Wake whoever is waiting under this name, if anyone is."""
        raise NotImplementedError

    def waiter(self, name):
        """Something to block on until `wake` is called with the same name."""
        raise NotImplementedError
