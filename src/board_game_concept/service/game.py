"""A game, as one session sees it.

Holds what has been read - the board, the players, what this player can see,
what was refused last turn - and knows how to read it. Where any of it is kept
is the repository's business; this asks for units, not for a file.

Everything a session does to a game beyond reading it lives in `turn.py`,
which this delegates to so that callers have one thing to talk to.
"""

from ..domain import Board, Player, UnitType
from ..storage.notify import NullNotifier
from ..storage.serialise import restore_draft, serialise_draft, units_document
from . import games, identity, turn
from .errors import (GameDataError, GameError, NoSuchGame, NoSuchPlayer,
                     UnreadableGame)


class Game:

    def __init__(self, repository, player_number, notifier=None):
        self.repository = repository
        self.player_number = player_number
        # the bus is on its own interface: local flows poll through a
        # `NullNotifier`, HTTP flows never reach here (`bgcapiserver` uses
        # long-poll directly). A caller that arranges push semantics
        # itself passes its own `Notifier`
        self.notifier = notifier or NullNotifier()

        self.players = {}
        self.board = None
        self.player_obj = None
        # the administrator and the observer are different identities and
        # both are entitled to the whole game. A player is entitled to their
        # own view of it and nothing else, which is enforced by never reading
        # them more than that rather than by filtering it on the way out
        self.sees_everything = identity.sees_everything(player_number)
        self.unprocessed_moves = False
        # orders the server refused when it last resolved a turn
        self.rejected = []
        # drafted commands that could no longer be carried out when the draft
        # was restored, and so were dropped
        self.dropped = []
        # how far the game has got: the last turn resolved, who is out of it,
        # and how it ended if it has
        self.turn_number = 0
        self.eliminated = []
        self.outcome = None
        # an identity entitled to the whole game opens an established one; a
        # player only ever joins one that has been set up. This gates deploying
        # and ordering, so an observer for which it were true would be a session
        # the rules considered mid-setup. XXX needs a better name
        self.new_game = not self.sees_everything

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
        # an identity that is not a player's owns no units, so there is no
        # player object to hand back
        if not identity.is_player(self.player_number):
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

    def resizeBoard(self, size_x, size_y):
        """A board of this size, with whatever was standing moved across.

        Sizing a board that already existed used to be refused outright, so an
        administrator who typed the wrong number had a game to throw away and
        make again. It is a decision like any other in setup: it stands until
        the setup that holds it is committed, and until then it can be taken
        back.

        Nothing standing is quietly dropped. A unit outside the board being
        asked for is a refusal naming it, because the alternative is somebody
        finding out later that a corner of their army was rubbed out by a
        number typed into a form.
        """
        standing = [] if self.board is None else [
            (unit.name, unit.x, unit.y) for unit in self.board.units
            if unit.on_board and not unit.destroyed]
        # and the armies loaded from files, which are records waiting to be
        # deployed rather than units standing anywhere. They are the ones
        # this is really for: during setup they are all there is
        for player in self.players.values():
            for unit in player.get('units') or []:
                standing.append(
                    (str(unit['name']), int(unit['x']), int(unit['y'])))
        outside = [name for name, x, y in standing
                   if x >= size_x or y >= size_y]
        if outside:
            raise GameError(
                f"a {size_x}x{size_y} board has no square for "
                f"{', '.join(sorted(outside))}: move or remove "
                f"{'it' if len(outside) == 1 else 'them'} first")
        board = Board(size_x, size_y)
        if self.board is not None and self.board.units:
            self._restore(board, units_document(self.board)['units'])
        self.board = board

    def removePlayer(self, number):
        """Take a player out of the game, with anything they had deployed.

        Registering a player is a decision made during setup, and every other
        decision made during setup can be taken back until it is committed.
        This one could not, so a mistyped seat number was a game to start
        again.
        """
        if number not in self.players:
            raise GameError(f"there is no player {number} to remove")
        board = self.board
        if board is not None:
            theirs = [unit for unit in board.units
                      if unit.player.number == number]
            for unit in theirs:
                if unit.on_board and not unit.destroyed:
                    unit.vacate()
                board.units.remove(unit)
        del self.players[number]

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
        self.dropped = []
        self.draft = []
        self.repository.ensure()

        # held for reading while the game's shared state is read, so that
        # nothing here catches a turn part way through being published. Several
        # sessions may read at once; a session resolving a turn excludes them
        # all. The draft is replayed after it is let go - it is this session's
        # own, nobody else reads or writes it, and holding a *read* lock across
        # a write would misdescribe what is happening
        with self.repository.held(read=True):
            self._read()
        self._replay_draft()

    def _read(self):
        """The game's shared state, read while the game is held."""
        size = self.repository.read_board()
        if size is None:
            if self.sees_everything:
                # nothing has been set up yet. The administrator's session is
                # the one that sets it up, and the observer is told there is no
                # board rather than refused the game outright
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

        # a session opened as a player must be one this game knows about. The
        # administrator and the observer hold no units and are registered as
        # nobody, so neither has to be found among the players
        if (identity.is_player(self.player_number)
                and self.player_number not in self.players):
            raise NoSuchPlayer(f"player {self.player_number} does not exist")


    def _replay_draft(self):
        """Put back what this session had done and not committed.

        Only this session's own draft, never another's. The repository will
        hand over any draft it is asked for, because a repository holds no
        rules; not asking for somebody else's is this layer's part of the
        bargain, as it already is for a player's file and a player's view.

        A draft belongs to one turn. One stamped with another is work left
        behind by a session that ended while a turn was being resolved, and is
        discarded rather than replayed into a turn it was never meant for.

        A command that can no longer be carried out is dropped and remembered,
        and the rest of the draft is still restored. Refusing to open a game
        because one drafted order went stale would make a draft a way to lock
        yourself out of your own game.
        """
        try:
            draft = self.repository.read_draft(self.player_number)
        except GameDataError as error:
            # an unreadable draft is this session's own work and nobody
            # else's, so it costs the draft rather than the game
            self.dropped.append((None, error.message))
            self.repository.clear_draft(self.player_number)
            return

        try:
            restored = restore_draft(draft, self.turn_number)
        except GameError as error:
            self.dropped.append((None, error.message))
            self.repository.clear_draft(self.player_number)
            return

        for command in restored:
            try:
                games.carry_out(self, command)
            except GameError as error:
                self.dropped.append((command, error.message))
                continue
            self.draft.append(command)

        if self.dropped:
            # what is written down is what was put back, so the draft does not
            # keep offering a command that cannot be carried out
            self.repository.write_draft(
                self.player_number,
                serialise_draft(self.draft, self.turn_number))

    def getDropped(self):
        """Drafted commands that could not be put back, and why."""
        return self.dropped

    def _load_players(self):
        for number in self.repository.player_numbers():
            # a game is a directory anyone can write into, so a number it holds
            # is checked before it is trusted. This is not a command that can be
            # refused and the session carry on - it is a game that cannot be
            # read, and it ends the session the way an unparseable one does
            if not identity.is_player(number):
                raise UnreadableGame(
                    f"{self.repository.data_path} holds a player that cannot "
                    f"exist: {identity.out_of_range(number)}")
            # which players are registered is not secret; what they have
            # designed and where it is standing are
            mine = self.sees_everything or number == self.player_number
            player_data = self.repository.read_player(number) if mine else None
            if mine and player_data is None:
                # gone since the players were listed
                continue
            # a budget comes from the record, and a record this session is not
            # entitled to read leaves it unknown rather than defaulted: an
            # opponent's budget is not this session's to guess at. The
            # repository refuses a record that carries no budget at all, so a
            # record that was read always has one
            budget = player_data['budget'] if mine else None
            self.players[number] = {
                'number': number,
                'obj': Player(number, budget),
                'types': {},
            }
            if not mine:
                continue
            for type_name in (player_data.get('types') or {}):
                unit_type = player_data['types'][type_name]
                # a player file can be written by hand, so its statistics are
                # converted here, at the edge, and are numbers everywhere below
                # a type the rules refuse is a game that cannot be read, not
                # a command that can be turned down and the session carry on.
                # `define_type` catches the same assertions at the prompt; here
                # they would escape as a bare AssertionError and kill the role
                try:
                    unit_type['obj'] = UnitType(
                        unit_type['name'],
                        unit_type['symbol'],
                        int(unit_type['attack']),
                        int(unit_type['health']),
                        int(unit_type['energy']))
                except (AssertionError, ValueError, TypeError) as e:
                    raise UnreadableGame(
                        f"{self.repository.data_path} holds a type that "
                        f"cannot exist: {type_name}: {e}") from e
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
        design = 'type_health' in unit
        attack = int(unit.get('type_attack', unit['attack']))
        health = int(unit.get('type_health', unit['health']))
        energy = int(unit.get('type_energy', unit['energy']))
        if not design and attack != 0:
            # a record carrying no `type_*` fields has already lost the design
            # and leaves only what play has worn the unit down to. Current
            # energy is routinely below the floor a type is held to - that is
            # what spending looks like - so reconstructing from it would build
            # a type the rules refuse and turn a legitimate sighting into a
            # crash. This reconstruction exists to describe an enemy that was
            # seen, not to price one, so it takes the floor the rule asks for
            # and carries on. A wall is left alone: its 0 energy is not
            # spending, it is what makes it a wall, and floored it would fail
            # the wall rule.
            #
            # The floor is the movement cost and not a point more. What comes
            # out of here is what a player is shown about an enemy, so energy
            # raised further than the rule requires is an overstatement of what
            # that enemy has left - a floor of the health would report a spent
            # unit as a fresh one
            energy = max(energy, (health + 3) // 4)
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
        """Resolve the turn now, asking no barrier.

        What the administrator's `commit` calls to end setup, where nobody has
        committed and nothing is being waited for.
        """
        return turn.resolve(self)

    def resolveWhenReady(self):
        """Resolve the turn if it may be: `None` if the barrier is not met."""
        return turn.resolve_when_ready(self)

    def waitForPlayerCommit(self):
        return turn.wait_for_all_commits(self)

    def waitForTurn(self):
        return turn.wait_for_turn(self)

    def committedPlayerCount(self):
        """How many players have committed for the turn now open."""
        return len(self.repository.committed_players(self.turn_number))
