from .square import Empty
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

    # what a turn spent doing nothing gives back. Energy used to be spent and
    # never replenished, which left an exhausted unit a permanent obstacle
    # and every game a race to the bottom of two pockets. A unit that was
    # given no order and landed no attack recovers this much, and never past
    # the energy its type was designed with
    REST_GAIN = 1

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
        assert ((attack >= 0) and (attack <= 10)
                ), "attack must be a value from 0 to 10"

        self.health = health
        assert isinstance(health, int), "health must be an integer value"
        assert ((health >= 1) and (health <= 10)
                ), "health must be a value from 1 to 10"

        self.energy = energy
        assert isinstance(energy, int), "energy must be an integer value"
        assert ((energy >= 0) and (energy <= 100)
                ), "energy must be a value from 0 to 100"

        # a type with no attack is allowed, with or without energy. With none
        # it is a **wall**: health standing on a square, which cannot move,
        # cannot fight and cannot be worn down, and the only way past is
        # through it. With energy it is a **scout**: it goes where it likes
        # and strikes nothing, which is a unit worth paying less for rather
        # than one the rules should refuse.
        #
        # What is still refused is energy 0 with an attack above it: an attack
        # it could never pay for is a wall that was charged for a weapon
        assert (attack == 0 or energy > 0), (
            "a type with no energy can have no attack: an attack it could "
            "never pay for is a wall charged for a weapon")

        # the design this unit was made from, kept alongside the values play
        # wears down. `type_name` was already preserved through the copy for
        # the same reason; a unit's current health is not its type's health,
        # and a destroyed one has none at all.
        #
        # These are set before the energy floor below rather than after every
        # assert, because the floor is stated against `move_cost` and
        # `move_cost` reads `type_health`. Asking the property for the fare is
        # the point: it makes the rule the constructor enforces the same
        # expression movement charges, where a second copy of the arithmetic
        # here could state a different rule from the one a unit is held to in
        # play
        self.type_attack = attack
        self.type_health = health
        self.type_energy = energy

        # a move costs a unit a quarter of its health in energy, so a type
        # designed with less energy than that could never afford a single move
        # at any point in its life. Saying so once, here, beats leaving a
        # player to discover it a turn at a time from refused orders. A wall is
        # exempt and is checked for first: 0 energy against a fare it can never
        # pay is what makes it a wall, and holding it to this rule would
        # abolish it. The exemption is energy rather than attack, so that a
        # scout - no attack, but energy to walk on - is held to it like
        # anything else that means to move
        assert (energy == 0 or energy >= self.move_cost), (
            f"a type that can move must have at least its movement cost in "
            f"energy: health {health} costs {self.move_cost} to move, so it "
            f"needs energy {self.move_cost} or more, not {energy}")

        self.state = UnitType.INITIAL
        self.direction = UnitType.NONE
        self.destroyed = False
        self.on_board = False
        # whether this unit carries its player's flag. Set after construction,
        # the way `state` and `direction` are, because carrying it is
        # something that happens to a unit during setup rather than part of
        # the design it was built from - and because nothing that builds a
        # unit today should have to learn about it.
        #
        # It is a standing and not a statistic: nothing here reads it, so a
        # carrier costs what its type costs, moves for what its type pays, and
        # strikes for what its type strikes
        self.flag = False
        self.seen_by = []
        self.player = None
        # square this unit vacated during the current turn's preCommit phase,
        # so that an undecided contest can send it back where it came from
        self.moved_from = None

    @property
    def cost(self):
        """What deploying one unit of this design spends of a point budget.

        Read from the design this unit was made from rather than from the
        values play wears down, so a unit that has lost health and spent
        energy still costs what it cost when it was deployed - and a destroyed
        one is not free. Computed rather than stored: a second copy of a number
        the type already holds can only ever disagree with it.
        """
        return self.type_attack + self.type_health + self.type_energy

    @property
    def move_cost(self):
        """What one move costs this unit in energy: a quarter of its maximum
        health, rounded up.

        A move used to cost 1 whatever the unit was, so weight was free and
        health bought durability without ever buying a penalty. It costs a
        share of the health the type was designed with instead, so armour is
        paid for in the field. The share was the whole of it to begin with,
        which priced a health-10 unit at ten energy a square against a rest
        rate of one a turn - a unit that crossed the board at a square every
        ten turns and was furniture rather than an army. A quarter keeps
        weight costing mobility and leaves a heavy unit able to campaign.

        Read from the design rather than from the health play has worn down:
        a wounded unit that moved more cheaply would make taking damage a way
        to buy tempo, and would make the fare something a player has to
        recompute after every contest. Computed rather than stored, for the
        reason `cost` above gives.

        Rounded up, and in whole numbers. Up, because rounding down would
        make health 1 to 3 move for nothing, and a unit that moves for
        nothing is outside the energy economy the rest of the game is built
        on - which would be a worse rule than the flat 1 this replaced, and
        would hand it to the cheapest units on the board. In whole numbers,
        because `(h + 3) // 4` on two integers is exact where `h / 4` is a
        float: a float in a rule that decides a turn is the kind of thing the
        determinism invariant exists to keep out.

        Health is 1 to 10, so the fare is 1 for health 1 to 4, 2 for health 5
        to 8, and 3 for health 9 or 10. That is a step, not a slope: two types
        that differ only in health can pay the same fare, which is the price
        of a fare that fits in three values while health fits in ten.
        """
        return (self.type_health + 3) // 4

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
        if self.energy < self.move_cost:
            return None, 'not enough energy to move'
        return (dest_x, dest_y), None

    # takes this unit out of the square it holds, leaving behind anything else
    # sharing that square
    def vacate(self):
        square = self.board[self.x, self.y]
        if not (type(square) is list):
            if square is self:
                self.board[self.x, self.y] = Empty()
            return
        remaining = [unit for unit in square if unit is not self]
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
def _isOut(unit, out):
    """Whether this unit belongs to a player whose flag has already fallen.

    Passed in from the resolution rather than looked up: `unit.board` is the
    grid of squares and knows nothing about players, and a contest has to be
    decided from the position and the orders alone.
    """
    return unit.player is not None and unit.player.number in out


def exchangeAttacks(contestants, events=None, out=()):
    """Fight one exchange in a contested square. Returns the survivors.

    Every unit standing gets **one** attack, if it can pay for it, and no
    more. That attack costs its attack value in energy, once, and lands that
    value on every other unit in the square at the same instant - an enemy, a
    friend, whoever is there. Then the exchange is over, whoever is left.

    It used to run in rounds, repeating until one unit was left or nobody
    could pay, so a single order bought as many strikes as a unit could
    afford - which drained a full unit dry in one turn and killed anything it
    outnumbered before the turn was out. One exchange a turn is the rule now:
    to press a fight you have to be ordered back into it, turn after turn.

    All the strikes land together, so a unit destroyed by this exchange has
    already dealt its own. `out` is the players whose flag has fallen; their
    units hold the square and strike nothing - an army without its flag is
    terrain - but are struck and destroyed like anything else.
    """
    standing = [unit for unit in contestants if not unit.destroyed]
    if len(standing) >= 2:
        # who is going to strike, and what it will land, is decided against
        # the square as the exchange begins - so charging one unit cannot
        # spare another, and destroying one cannot stop its own blow. The
        # attacks are gathered before any damage is applied
        blows = []
        for unit in standing:
            if unit.attack <= 0:
                # a wall does not fight: no attack to pay with, none to land
                continue
            if _isOut(unit, out):
                # its player's flag has fallen: it holds its square and
                # strikes nothing, though it is still struck and destroyed
                continue
            if unit.energy < unit.attack:
                # too spent to strike: inert, not destroyed. All or nothing,
                # so there is no half-paid attack to hand out
                continue
            unit.energy = unit.energy - unit.attack
            for target in standing:
                if unit is target:
                    continue
                blows.append((unit, target))
                # each contestant is seen by every other it shared the square
                # with, recorded once: a unit listed twice is a unit reported
                # twice to the players who saw it
                if target not in unit.seen_by:
                    unit.seen_by.append(target)
                if unit not in target.seen_by:
                    target.seen_by.append(unit)
        for unit, target in blows:
            if events is not None:
                events.append(Event(
                    'attacked', unit=unit.name, target=target.name,
                    damage=unit.attack))
            target.incomingAttack(unit.attack, events)

    for unit in contestants:
        if unit.destroyed:
            unit.on_board = False
    return [unit for unit in contestants if not unit.destroyed]


def resolveContest(board, x, y, contestants, free, events=None, out=()):
    """Fight out one square and decide who is left holding it."""
    if events is not None:
        events.append(Event(
            'contested', x=x, y=y, units=len(contestants)))
    survivors = exchangeAttacks(contestants, events, out)

    for unit in contestants:
        if unit.destroyed:
            unit.vacate()

    if len(survivors) > 1:
        # nobody won the square, so everyone who moved in goes back where it
        # came from and the square is left as it was
        if events is not None:
            events.append(Event(
                'undecided', x=x, y=y,
                units=','.join(sorted(unit.name for unit in survivors))))
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


def resolveCollision(first, second, events=None, out=()):
    """Fight out a head-on exchange, in which neither unit moved.

    Two units ordered into each other's squares used to pass straight through
    one another, each arriving where the other started without either noticing.
    They collide instead. There is no square to put them both in that does not
    favour one of them, so they fight where they stand and the survivor - if
    there is one - completes its move.
    """
    if events is not None:
        # named in a settled order: which of the two is "first" is an accident
        # of how the board holds them, and the collision is the same either way
        near, far = sorted((first, second),
                           key=lambda u: (u.player.number, u.name))
        events.append(Event(
            'collided', unit=near.name, target=far.name,
            x=near.x, y=near.y, to_x=far.x, to_y=far.y))
    survivors = exchangeAttacks([first, second], events, out)

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
            units=','.join(sorted(unit.name for unit in survivors))))
