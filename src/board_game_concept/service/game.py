"""A game, as one session sees it.

Holds what has been read - the board, the players, what this player can see,
what was refused last turn - and knows how to read it. Where any of it is kept
is the repository's business; this asks for units, not for a file.

Everything a session does to a game beyond reading it lives in `turn.py`,
which this delegates to so that callers have one thing to talk to.
"""

from ..domain import Board, Player, UnitType
from . import turn
from .errors import NoSuchGame, NoSuchPlayer


class Game:

    def __init__(self, repository, player_number):
        self.repository = repository
        self.player_number = player_number

        self.players = {}
        self.board = None
        self.seen_board = None
        self.player_obj = None
        self.unprocessed_moves = False
        # orders the server refused when it last resolved a turn
        self.rejected = []
        # the administrator opens an established game; a player only ever
        # joins one that has been set up. XXX needs a better name
        self.new_game = player_number != 0

    # --- what the session can ask about the game

    def getUnprocessedMoves(self):
        return self.unprocessed_moves

    def getRejected(self):
        return self.rejected

    def getPlayerObj(self, player_number):
        if self.player_number == 0:
            return None
        return self.players[player_number]['obj']

    def getPlayers(self):
        return self.players

    def getNewGame(self):
        return self.new_game

    def setNewGame(self, new_game):
        self.new_game = new_game

    def getBoard(self):
        return self.board

    def setBoard(self, board):
        self.board = board

    def getSeenBoard(self):
        return self.seen_board

    def getSizeX(self):
        return self.board.size_x if self.board is not None else 0

    def getSizeY(self):
        return self.board.size_y if self.board is not None else 0

    # --- reading it

    def load(self):
        self.unprocessed_moves = False
        self.repository.ensure()

        size = self.repository.read_board()
        if size is None:
            if self.player_number == 0:
                # nothing has been set up yet, so this session sets it up
                self.new_game = True
            else:
                raise NoSuchGame(
                    f"No game with path: {self.repository.data_path}")
        else:
            self.board = Board(*size)

        self._load_players()
        self.rejected = self.repository.read_rejections(self.player_number)
        self._restore(self.board, self.repository.read_units())

        view = self.repository.read_view(self.player_number)
        if view is not None and self.board is not None:
            self.seen_board = Board(self.board.size_x, self.board.size_y)
            self._restore(self.seen_board, view)

        # the session must belong to a player this game knows about, or to the
        # administrator, who is player 0 and holds no units
        if self.player_number not in self.players and self.player_number != 0:
            raise NoSuchPlayer(f"player {self.player_number} does not exist")

    def _load_players(self):
        for number in self.repository.player_numbers():
            player_data = self.repository.read_player(number)
            if player_data is None:
                # gone since the players were listed
                continue
            self.players[number] = {
                'number': number,
                'obj': Player(number),
                'types': {},
            }
            for type_name in (player_data.get('types') or {}):
                unit_type = player_data['types'][type_name]
                # a player file can be written by hand, so its statistics are
                # converted here, at the edge, and are numbers everywhere below
                unit_type['obj'] = UnitType(
                    unit_type['name'],
                    unit_type['symbol'],
                    int(unit_type['attack']),
                    int(unit_type['health']),
                    int(unit_type['energy']))
                self.players[number]['types'][unit_type['name']] = unit_type

            orders = self.repository.read_orders(number)
            if orders is not None:
                self.players[number]['moves'] = orders
                if number == self.player_number:
                    # this player's own orders are still waiting to be
                    # resolved, so the turn is not over for them
                    self.unprocessed_moves = True

            if self.repository.has_committed(number) and number == self.player_number:
                self.new_game = False

    def _restore(self, board, units):
        """Put saved units back onto a board.

        Restoring is not deploying: whatever was there goes back, including a
        square that ended up shared.
        """
        if board is None or not units:
            return
        for unit in units:
            number = int(unit['player'])
            board.add(
                self.players[number]['obj'],
                unit['x'], unit['y'],
                unit['name'],
                self.players[number]['types'][unit['type']]['obj'],
                unit['health'],
                unit['energy'],
                bool(unit['destroyed']),
                bool(unit['on_board']),
                restoring=True)
        board.commit()

    # --- and doing something to it

    def clientSave(self):
        return turn.publish(self)

    def serverSave(self):
        return turn.resolve(self)

    def waitForPlayerCommit(self):
        return turn.wait_for_all_commits(self)

    def waitForTurn(self):
        return turn.wait_for_turn(self)

    def committedPlayerCount(self):
        return len(self.repository.committed_players())
