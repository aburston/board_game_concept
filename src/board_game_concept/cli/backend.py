"""The seam between a role's REPL and the game it drives.

Every role holds a session and talks to it, rather than holding a `Game` and
reaching into it. That is the whole of this seam's job: to be the one thing a
role depends on, so that a later change can put an HTTP client behind the same
interface without the REPLs knowing. The REST API the game is headed for cannot
slot in where a `Game` is soldered into a role; it can slot in here.

`Session` names the surface. `LocalSession` is the one implementation there is
today: the in-process `Game`, `service.games` and turn functions the roles call
now, behind the interface instead of in front of it.

The read methods keep their `Game` names on purpose. `show.py`, `complete.py`
and `cli/session.py` already call `getBoard`, `getPlayers`, `getOutcome` and the
rest, and are held to those names by their own tests, so the session presents
the same surface and those callers do not change. The view-object reads -
`getBoard`, `getPlayers`, `getEliminated` - are the part an HTTP session cannot
answer, because a client holds no board. They are local-only, and turning them
into fetched view data is the work of the change that moves `views.py`
server-side. Until then the seam is drawn for actions, lifecycle and state, and
these three are the coupling still to cut.
"""

from .. import Game
from ..service import games, identity


class Session:
    """What a role's REPL asks of the game it drives.

    Subclasses implement all of it. This class says what the set is and fails
    loudly rather than silently when one is missing, the way `GameRepository`
    does for storage.
    """

    # --- lifecycle and actions, through the seam

    def load(self):
        """Read the game, or re-read it. Raises the game-data errors the
        session loop turns into an exit."""
        raise NotImplementedError

    def perform(self, command):
        """Carry out a command, recording it; raises `GameError` if refused."""
        raise NotImplementedError

    def commit(self):
        """Commit as this role commits: a player publishes, the administrator
        ends setup."""
        raise NotImplementedError

    def resolve_pending(self):
        """Resolve the turn if the barrier is met; the server's unattended
        act. `None` when it is not met, else `resolve`'s own result."""
        raise NotImplementedError

    def waitForTurn(self):
        """Wait until this player's committed orders have been resolved."""
        raise NotImplementedError

    def waitForPlayerCommit(self):
        """Wait until every player still in the game has committed."""
        raise NotImplementedError

    # --- reading the game's state

    def getOutcome(self):
        raise NotImplementedError

    def getTurnNumber(self):
        raise NotImplementedError

    def getNewGame(self):
        raise NotImplementedError

    def setNewGame(self, new_game):
        raise NotImplementedError

    def getUnprocessedMoves(self):
        raise NotImplementedError

    def getRejected(self):
        raise NotImplementedError

    def getDropped(self):
        raise NotImplementedError

    def isEliminated(self, player_number):
        raise NotImplementedError

    # --- view objects the reading half still needs (local-only; see the
    # module docstring). `show.py` and `complete.py` build views from these.

    def getBoard(self):
        raise NotImplementedError

    def getPlayers(self):
        raise NotImplementedError

    def getEliminated(self):
        raise NotImplementedError


class LocalSession(Session):
    """The in-process implementation: a `Game`, driven as the roles drive it."""

    def __init__(self, repository, player_number):
        self.player_number = player_number
        self._game = Game(repository, player_number)

    def load(self):
        return self._game.load()

    def perform(self, command):
        return games.perform(self._game, command)

    def commit(self):
        # a player's commit publishes orders and waits to be woken; the
        # administrator's ends setup. Which one is decided by identity, the
        # same fact `sees_everything` and the barrier are decided by
        if identity.is_player(self.player_number):
            return self._game.clientSave()
        return self._game.serverSave()

    def resolve_pending(self):
        return self._game.resolveWhenReady()

    def waitForTurn(self):
        return self._game.waitForTurn()

    def waitForPlayerCommit(self):
        return self._game.waitForPlayerCommit()

    def getOutcome(self):
        return self._game.getOutcome()

    def getTurnNumber(self):
        return self._game.getTurnNumber()

    def getNewGame(self):
        return self._game.getNewGame()

    def setNewGame(self, new_game):
        return self._game.setNewGame(new_game)

    def getUnprocessedMoves(self):
        return self._game.getUnprocessedMoves()

    def getRejected(self):
        return self._game.getRejected()

    def getDropped(self):
        return self._game.getDropped()

    def isEliminated(self, player_number):
        return self._game.isEliminated(player_number)

    def getBoard(self):
        return self._game.getBoard()

    def getPlayers(self):
        return self._game.getPlayers()

    def getEliminated(self):
        return self._game.getEliminated()
