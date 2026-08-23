"""A game, as one session sees it.

Holds what has been read - the board, the players, what this player can see,
what was refused last turn - and knows how to read it. Where any of it is kept
is the repository's business; this asks for units, not for a file.

Everything a session does to a game beyond reading it lives in `turn.py`,
which this delegates to so that callers have one thing to talk to.
"""

from ..domain import Board, Player, UnitType
from ..storage.serialise import restore_draft, serialise_draft
from . import turn
from .errors import NoSuchGame, NoSuchPlayer


class Game:

    def __init__(self, repository, player_number):
        self.repository = repository
        self.player_number = player_number

        self.players = {}
        self.board = None
        self.player_obj = None
        # the administrator and the observer are both player 0, and both are
        # entitled to the whole game. A player is entitled to their own view of
        # it and nothing else, which is enforced by never reading them more
        # than that rather than by filtering it on the way out
        self.sees_everything = player_number == 0
        self.unprocessed_moves = False
        # orders the server refused when it last resolved a turn
        self.rejected = []
        # how far the game has got: the last turn resolved, who is out of it,
        # and how it ended if it has
        self.turn_number = 0
        self.eliminated = []
        self.outcome = None
        # the administrator opens an established game; a player only ever
        # joins one that has been set up. XXX needs a better name
        self.new_game = player_number != 0

        # what this session has done since it last committed, in the order it
        # did it. Held here as well as on disk so that recording one more is a
        # write rather than a read and a write
        self.draft = []

    # --- what the session can ask about the game

    def getUnprocessedMoves(self):
        return self.unprocessed_moves

    def getRejected(self):
        return self.rejected

    def getTurnNumber(self):
        return self.turn_number

    def getEliminated(self):
        return self.eliminated

    def getOutcome(self):
        """How the game ended, or None while it is still being played."""
        return self.outcome

    def isEliminated(self, player_number):
        return player_number in self.eliminated

    def setProgress(self, progress):
        """Take the turn number, who is out, and the outcome from a record."""
        progress = progress or {}
        self.turn_number = int(progress.get('turn') or 0)
        self.eliminated = list(progress.get('eliminated') or [])
        self.outcome = progress.get('outcome') or None

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

    def seesEverything(self):
        return self.sees_everything

    def getSizeX(self):
        return self.board.size_x if self.board is not None else 0

    def getSizeY(self):
        return self.board.size_y if self.board is not None else 0

    # --- work this session has not committed yet

    def getDraft(self):
        """The commands this session has issued since it last committed."""
        return self.draft

    def recordDraft(self, command):
        """Remember a command, so that ending the session does not lose it.

        Stamped with the turn it was drafted for. A draft belongs to one turn;
        one found under a turn the game has moved past is work left behind by a
        session that ended while a turn was being resolved.
        """
        self.draft.append(command)
        self.repository.write_draft(
            self.player_number, serialise_draft(self.draft, self.turn_number))

    def clearDraft(self):
        """Discard the draft, committed or abandoned."""
        self.draft = []
        self.repository.clear_draft(self.player_number)

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

        self.setProgress(self.repository.read_progress())
        self._load_players()
        self.rejected = self.repository.read_rejections(self.player_number)
        if self.sees_everything:
            self._restore(self.board, self.repository.read_units())
        else:
            # a player's session is built from that player's own published
            # view, and never from the record of every unit on the board. It
            # used to load the whole board and hide the parts the player was
            # not entitled to when it drew them, which left every enemy
            # position in the client's memory and on its disk
            self._restore(self.board, self.repository.read_view(
                self.player_number))

        # the session must belong to a player this game knows about, or to the
        # administrator, who is player 0 and holds no units
        if self.player_number not in self.players and self.player_number != 0:
            raise NoSuchPlayer(f"player {self.player_number} does not exist")

    def _load_players(self):
        for number in self.repository.player_numbers():
            # which players are registered is not secret; what they have
            # designed and where it is standing are
            mine = self.sees_everything or number == self.player_number
            player_data = self.repository.read_player(number) if mine else None
            if mine and player_data is None:
                # gone since the players were listed
                continue
            self.players[number] = {
                'number': number,
                'obj': Player(number),
                'types': {},
            }
            if not mine:
                continue
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
        square that ended up shared. The turn is not resolved here - a saved
        contest that was left undecided must stay undecided, not be fought
        again every time the game is opened.
        """
        if board is None or not units:
            return
        for unit in units:
            number = int(unit['player'])
            board.add(
                self.players[number]['obj'],
                unit['x'], unit['y'],
                unit['name'],
                self._type_for(number, unit),
                unit['health'],
                unit['energy'],
                bool(unit['destroyed']),
                bool(unit['on_board']),
                restoring=True)

    def _type_for(self, number, unit):
        """The type a saved unit was made from.

        A player knows their own types from their own file. An enemy type
        arrives with the unit that carried it into contact, which is the only
        way a player learns of one - so it is taken from the record itself and
        remembered against its owner, for as long as the contact lasts.
        """
        types = self.players[number]['types']
        known = types.get(unit['type'])
        if known is not None and 'obj' in known:
            return known['obj']
        attack = int(unit.get('type_attack', unit['attack']))
        health = int(unit.get('type_health', unit['health']))
        energy = int(unit.get('type_energy', unit['energy']))
        unit_type = UnitType(unit['type'], unit['symbol'], attack, health, energy)
        types[unit['type']] = {
            'name': unit['type'],
            'symbol': unit['symbol'],
            'attack': attack,
            'health': health,
            'energy': energy,
            'obj': unit_type,
        }
        return unit_type

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
