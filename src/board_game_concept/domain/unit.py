from .cell import Empty
from .events import Event
from .player import Player


# Unit
#   name: One or more character
#   symbol: One single character
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

    # what one move costs. This was `energy // 100 + 1`, which under the
    # 1 to 100 energy cap only ever yielded 1 - except from exactly 100,
    # where it yielded 2 - so it read as though it scaled and never did
    MOVE_COST = 1

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

        # the design this unit was made from, kept alongside the values play
        # wears down. `type_name` was already preserved through the copy for
        # the same reason; a unit's current health is not its type's health,
        # and a destroyed one has none at all
        self.type_attack = attack
        self.type_health = health
        self.type_energy = energy

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

    # where this unit would like to go, decided against the board as the turn
    # began. Nothing is written: the board plans every move before it applies
    # any, so that what a unit finds at its destination cannot depend on
    # whether the unit standing there has been resolved yet
    def planMove(self):
        """`(destination, refusal)` for this unit's order this turn.

        `destination` is None when the unit is not moving or cannot; `refusal`
        names the reason when an order was given and will not be carried out.
        """
        if self.state != UnitType.MOVING:
            return None, None

        dest_x, dest_y = self.x, self.y
        if self.direction == UnitType.NORTH:
            dest_y = self.y - 1
        elif self.direction == UnitType.EAST:
            dest_x = self.x + 1
        elif self.direction == UnitType.SOUTH:
            dest_y = self.y + 1
        elif self.direction == UnitType.WEST:
            dest_x = self.x - 1
        else:
            return None, None

        if not (0 <= dest_x < self.board_max_x and 0 <= dest_y < self.board_max_y):
            return None, 'the move would leave the board'
        if self.energy < UnitType.MOVE_COST:
            return None, 'not enough energy to move'
        return (dest_x, dest_y), None

    # takes this unit out of the square it holds, leaving behind anything else
    # sharing that square
    def vacate(self):
        cell = self.board[self.x, self.y]
        if not (type(cell) is list):
            if cell is self:
                self.board[self.x, self.y] = Empty()
            return
        remaining = [unit for unit in cell if unit is not self]
        if not remaining:
            self.board[self.x, self.y] = Empty()
        elif len(remaining) == 1:
            self.board[self.x, self.y] = remaining[0]
        else:
            self.board[self.x, self.y] = remaining

    # puts this unit into the square it is standing on, joining whatever is
    # already there rather than displacing it
    def occupy(self, x, y):
        self.setCoords(x, y)
        occupant = self.board[x, y]
        if type(occupant) is Empty:
            self.board[x, y] = self
        elif type(occupant) is list:
            if self not in occupant:
                occupant.append(self)
        elif occupant is not self:
            self.board[x, y] = [occupant, self]

    # sends this unit back to the square it left this turn, so that an
    # undecided contest leaves the board as it was. `free` is the set of
    # squares movement left empty, judged once for the whole turn so that one
    # contest resolving cannot change the answer for another. Returns True if
    # the unit retreated.
    def retreat(self, free, events=None):
        if self.moved_from is None:
            # nothing to go back to: the unit was already holding this square,
            # or was deployed onto it this turn
            return False
        if self.moved_from not in free:
            # something else took the square during this turn, so there is
            # nowhere to go back to and the unit stays where it is
            return False
        from_x, from_y = self.moved_from
        free.discard(self.moved_from)
        self.vacate()
        self.setCoords(from_x, from_y)
        self.board[from_x, from_y] = self
        self.moved_from = None
        if events is not None:
            events.append(Event(
                'retreated', unit=self.name, x=from_x, y=from_y))
        return True

    def __str__(self):
        return (self.symbol)


# Attack rounds repeat until at most one contestant is left standing or a round
# lands no attacks, which is what stops a contest nobody can win from spinning
# forever. There is friendly fire: a contestant attacks every other unit in the
# contest, whoever owns it. Running out of energy never destroys a unit, it only
# makes it inert.
def exchangeAttacks(contestants, events=None):
    """Fight until the contest is decided or nobody can pay. Returns survivors."""
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
    return [unit for unit in contestants if not unit.destroyed]


def resolveContest(board, x, y, contestants, free, events=None):
    """Fight out one square and decide who is left holding it."""
    if events is not None:
        events.append(Event(
            'contested', x=x, y=y, units=len(contestants)))
    survivors = exchangeAttacks(contestants, events)

    for unit in contestants:
        if unit.destroyed:
            unit.vacate()

    if len(survivors) > 1:
        # nobody won the square, so everyone who moved in goes back where it
        # came from and the square is left as it was
        if events is not None:
            events.append(Event(
                'undecided', x=x, y=y,
                units=','.join(unit.name for unit in survivors)))
        survivors = [unit for unit in survivors
                     if not unit.retreat(free, events)]

    if not survivors:
        board[x, y] = Empty()
        if events is not None:
            events.append(Event('emptied', x=x, y=y))
    elif len(survivors) == 1:
        board[x, y] = survivors[0]
        if events is not None:
            events.append(Event(
                'held', unit=survivors[0].name, x=x, y=y))
    else:
        # no survivor could fall back, so they share the square
        board[x, y] = survivors
        if events is not None:
            events.append(Event(
                'shared', x=x, y=y, units=len(survivors)))


def resolveCollision(first, second, events=None):
    """Fight out a head-on exchange, in which neither unit moved.

    Two units ordered into each other's squares used to pass straight through
    one another, each arriving where the other started without either noticing.
    They collide instead. There is no square to put them both in that does not
    favour one of them, so they fight where they stand and the survivor - if
    there is one - completes its move.
    """
    if events is not None:
        events.append(Event(
            'collided', unit=first.name, target=second.name,
            x=first.x, y=first.y))
    survivors = exchangeAttacks([first, second], events)

    for unit in (first, second):
        if unit.destroyed:
            unit.vacate()

    if len(survivors) == 1:
        survivor = survivors[0]
        loser = second if survivor is first else first
        target_x, target_y = loser.x, loser.y
        survivor.vacate()
        survivor.occupy(target_x, target_y)
        if events is not None:
            events.append(Event(
                'held', unit=survivor.name, x=target_x, y=target_y))
    elif len(survivors) == 2 and events is not None:
        # neither could decide it, so both stay where the turn found them
        events.append(Event(
            'undecided', x=first.x, y=first.y,
            units=','.join(unit.name for unit in survivors)))
