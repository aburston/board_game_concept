from .cell import Empty
from .events import Event
from .player import Player



# Unit
#   name: One or more character
#   symbol: One single character
#   speed: speed 10 is to move once per clock tick and 1 is to move once every 10th tick
#   attack: damage per attack
#   health: total amount of health


class UnitType:

    NONE = 0
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4

    INITIAL = 0
    MOVING = 1
    NOP = 2

    def __init__(self, name, symbol, attack, health, energy):
        self.name = name
        self.type_name = name

        # XXX this is a rather not so nice way of preserving the original type name
        # when this object is copied and turned into a unit
        assert (len(str(name)) >= 1), "name must be one or more character"

        self.symbol = symbol
        assert (len(str(symbol)) == 1), "symbol must be only one character"

        self.attack = attack
        assert isinstance(attack, int), "attack must be an integer value"
        assert ((attack >= 1) and (attack <= 10)
                ), "attack must be a value from 1 to 10"

        self.health = health
        assert isinstance(health, int), "health must be an integer value"
        assert ((health >= 1) and (health <= 10)
                ), "health must be a value from 1 to 10"

        self.energy = energy
        assert isinstance(energy, int), "health must be an integer value"
        assert ((energy >= 1) and (energy <= 100)
                ), "energy must be a value from 1 to 100"

        self.state = UnitType.INITIAL
        self.direction = UnitType.NONE
        self.destroyed = False
        self.on_board = False
        self.seen_by = []
        self.player = None
        # square this unit vacated during the current turn's preCommit phase,
        # so that an undecided contest can send it back where it came from
        self.moved_from = None

    def move(self, direction):
        self.state = UnitType.MOVING
        self.direction = direction

    def setName(self, name):
        self.name = name

    def setBoard(self, board, board_max_x, board_max_y):
        self.board = board
        self.board_max_x = board_max_x
        self.board_max_y = board_max_y
        self.on_board = True

    def setCoords(self, x, y):
        self.x = x
        self.y = y

    def setHealth(self, health):
        self.health = health

    def setEnergy(self, energy):
        self.energy = energy

    def setDestroyed(self, destroyed):
        self.destroyed = destroyed

    def setOnBoard(self, on_board):
        self.on_board = on_board

    def setPlayer(self, player):
        self.player = player
        assert (type(player) is Player), "player object must be provided"

    def incomingAttack(self, attack, events=None):
        self.health = self.health - attack
        if self.health <= 0:
            self.destroyed = True
            if events is not None:
                events.append(Event('destroyed', unit=self.name))

    # calculates attacks and marks units as DESTROYED, creates arrays of units in squares where multiple units are
    # trying to move simultaneously into the same square
    def preCommit(self, events=None):
        if self.state == UnitType.INITIAL:
            # deployment is resolved in commit(). Board.add has already refused
            # any deployment onto an occupied square
            pass
        elif self.state == UnitType.MOVING:
            dest_x = self.x
            dest_y = self.y
            if self.direction == UnitType.NORTH:
                dest_y = self.y - 1
                self.direction = UnitType.NONE
                if dest_y < 0:
                    self.y = 0
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.EAST:
                dest_x = self.x + 1
                self.direction = UnitType.NONE
                if dest_x > self.board_max_x - 1:
                    self.x = self.board_max_x - 1
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.SOUTH:
                dest_y = self.y + 1
                self.direction = UnitType.NONE
                if dest_y > self.board_max_y - 1:
                    self.y = self.board_max_y - 1
                    self.state = UnitType.NOP
                    return
            elif self.direction == UnitType.WEST:
                dest_x = self.x - 1
                self.direction = UnitType.NONE
                if dest_x < 0:
                    self.x = 0
                    self.state = UnitType.NOP
                    return
            else:
                self.state = UnitType.NOP
                return

            if type(self.board[dest_x, dest_y]) is Empty:
                energy = self.energy - (self.energy // 100 + 1)
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    self.vacate()
                    self.moved_from = (self.x, self.y)
                    self.setCoords(dest_x, dest_y)
                    self.board[self.x, self.y] = [self]
                    if events is not None:
                        events.append(Event(
                            'moved', unit=self.name, x=self.x, y=self.y))
            elif type(self.board[dest_x, dest_y]) is list:
                energy = self.energy - (self.energy // 100 + 1)
                # only act if the unit has enough energy
                if energy >= 0:
                    self.energy = energy
                    self.vacate()
                    self.moved_from = (self.x, self.y)
                    self.setCoords(dest_x, dest_y)
                    self.board[dest_x, dest_y].append(self)
                    if events is not None:
                        events.append(Event(
                            'joined', unit=self.name, x=self.x, y=self.y))
            elif type(self.board[dest_x, dest_y]) is UnitType:
                # moving into an occupied square starts a combat exchange
                if self.energy >= self.attack:
                    target = self.board[dest_x, dest_y]
                    self.vacate()
                    self.moved_from = (self.x, self.y)
                    self.setCoords(dest_x, dest_y)
                    self.board[dest_x, dest_y] = [target, self]
                    if events is not None:
                        events.append(Event(
                            'engaged', unit=self.name, target=target.name,
                            x=self.x, y=self.y))
            self.state = UnitType.NOP
            return
        else:
            pass

    # takes this unit out of the square it holds, leaving behind anything else
    # sharing that square
    def vacate(self):
        cell = self.board[self.x, self.y]
        if not (type(cell) is list):
            self.board[self.x, self.y] = Empty()
            return
        remaining = [unit for unit in cell if unit is not self]
        if not remaining:
            self.board[self.x, self.y] = Empty()
        elif len(remaining) == 1:
            self.board[self.x, self.y] = remaining[0]
        else:
            self.board[self.x, self.y] = remaining

    # sends this unit back to the square it left this turn, so that an
    # undecided contest leaves the board as it was. Returns True if the unit
    # retreated.
    def retreat(self, events=None):
        if self.moved_from is None:
            # nothing to go back to: the unit was already holding this square,
            # or was deployed onto it this turn
            return False
        from_x, from_y = self.moved_from
        if not (type(self.board[from_x, from_y]) is Empty):
            # something else took the square during this turn, so there is
            # nowhere to go back to and the unit stays where it is
            return False
        self.setCoords(from_x, from_y)
        self.board[from_x, from_y] = self
        self.moved_from = None
        if events is not None:
            events.append(Event(
                'retreated', unit=self.name, x=from_x, y=from_y))
        return True

    # resolves the contest in the square this unit occupies. Attack rounds repeat
    # until at most one contestant is left standing or a round lands no attacks,
    # which is what stops a contest nobody can win from spinning forever. There
    # is friendly fire: a contestant attacks every other unit in the square,
    # whoever owns it. Running out of energy never destroys a unit, it only
    # makes it inert.
    def resolveContest(self, events=None):
        cell_x = self.x
        cell_y = self.y
        contestants = self.board[cell_x, cell_y]
        if events is not None:
            events.append(Event(
                'contested', x=cell_x, y=cell_y, units=len(contestants)))
        while True:
            # recount the survivors afresh each round, rather than decrementing
            # a running total that counts the same casualty again every round
            standing = [unit for unit in contestants if not unit.destroyed]
            if len(standing) < 2:
                break
            attacked = False
            # attackers and targets are the units standing at the start of the
            # round, so a unit destroyed mid-round still lands its own attack
            for unit in standing:
                for target in standing:
                    if unit is target:
                        continue
                    energy = unit.energy - unit.attack
                    if energy < 0:
                        # too spent to attack: inert, but not destroyed
                        continue
                    unit.energy = energy
                    if events is not None:
                        events.append(Event(
                            'attacked', unit=unit.name, target=target.name,
                            damage=unit.attack))
                    target.incomingAttack(unit.attack, events)
                    # populate seen_by, recording each contestant once however
                    # many rounds of attacks the contest takes: a unit listed
                    # twice is reported twice to the players who saw it
                    if target not in unit.seen_by:
                        unit.seen_by.append(target)
                    if unit not in target.seen_by:
                        target.seen_by.append(unit)
                    attacked = True
            if not attacked:
                # no contestant can pay for an attack, so the contest is over
                break

        for unit in contestants:
            if unit.destroyed:
                unit.on_board = False

        survivors = [unit for unit in contestants if not unit.destroyed]
        if len(survivors) > 1:
            # nobody won the square, so everyone who moved in goes back where
            # it came from and the square is left as it was
            survivors = [unit for unit in survivors
                         if not unit.retreat(events)]

        if not survivors:
            self.board[cell_x, cell_y] = Empty()
            if events is not None:
                events.append(Event('emptied', x=cell_x, y=cell_y))
        elif len(survivors) == 1:
            self.board[cell_x, cell_y] = survivors[0]
            if events is not None:
                events.append(Event(
                    'held', unit=survivors[0].name, x=cell_x, y=cell_y))
        else:
            # no survivor could fall back, so they share the square
            self.board[cell_x, cell_y] = survivors
            if events is not None:
                events.append(Event(
                    'shared', x=cell_x, y=cell_y, units=len(survivors)))

    # processes all arrays created in the precommit phase, by calculating attacks and marking units DESTROYED
    # removes all DESTROYED units from the board
    def commit(self, events=None):
        if self.state == UnitType.INITIAL:
            # add the unit to the board. Board.add refuses to deploy onto an
            # occupied square, so the square is empty unless a saved game is
            # being restored, in which case the units it held are put back as
            # they were
            occupant = self.board[self.x, self.y]
            if type(occupant) is Empty:
                self.board[self.x, self.y] = self
            elif type(occupant) is list:
                occupant.append(self)
            else:
                self.board[self.x, self.y] = [occupant, self]
            self.state = UnitType.NOP
            if events is not None:
                events.append(Event(
                    'deployed', unit=self.name, x=self.x, y=self.y))
        elif self.state == UnitType.MOVING:
            assert not (
                self.state == UnitType.MOVING), "During commit, no unit should be in the MOVING state"
        else:
            if type(self.board[self.x, self.y]) is list:
                self.resolveContest(events)
            else:
                if self.destroyed:
                    self.vacate()
                    self.on_board = False
                    if events is not None:
                        events.append(Event('removed', unit=self.name))

    def __str__(self):
        return (self.symbol)
