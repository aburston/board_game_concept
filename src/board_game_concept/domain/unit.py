from .square import Empty
from .events import Event, owners
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

    def hold(self):
        """Take back the order this unit was given, leaving it with none.

        Holding is the absence of an order rather than an order of its own,
        which is why this puts the unit back to `NOP` and no direction rather
        than recording a hold: a unit that was never ordered and one whose
        order was taken back are the same unit, and both rest.
        """
        self.state = UnitType.NOP
        self.direction = UnitType.NONE

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
                events.append(Event('destroyed', unit=self.name,
                                    players=owners(self)))

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
                'retreated', unit=self.name, x=from_x, y=from_y,
                players=owners(self)))
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


def _mark(unit):
    """How a unit is named in the record of who has struck whom this turn.

    By player and name rather than by the object, because nothing in the
    resolution of the rules may turn on an object's identity.
    """
    return (unit.player.number if unit.player is not None else None, unit.name)


def exchangeAttacks(contestants, events=None, out=(), struck=None):
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

    `struck` is what has already been landed this turn, as pairs. A unit may
    strike each other unit **once a turn**, and a turn now holds more than one
    exchange: a contest nobody won sends its movers back into whoever took the
    square behind them, and that is a second fight. Without this a unit that
    met the same opponent twice - in the contest and then in the pile-up
    behind it - would strike it twice, which is the repeat this rule exists to
    forbid.
    """
    struck = struck if struck is not None else set()
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
            landing = [target for target in standing
                       if target is not unit
                       and (_mark(unit), _mark(target)) not in struck]
            if not landing:
                # it has already met every one of them this turn, so there is
                # nothing here for it to strike and nothing to pay for
                continue
            unit.energy = unit.energy - unit.attack
            for target in standing:
                if unit is target:
                    continue
                if (_mark(unit), _mark(target)) in struck:
                    continue
                struck.add((_mark(unit), _mark(target)))
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
                    damage=unit.attack, players=owners(unit, target)))
            target.incomingAttack(unit.attack, events)

    for unit in contestants:
        if unit.destroyed:
            unit.on_board = False
    return [unit for unit in contestants if not unit.destroyed]


def _fall_back(unit, board, free, events, out=(), struck=None,
               crashing=frozenset()):
    """Put a unit back where it came from, fighting for it if it has to.

    A unit that moved into a contest nobody won goes back where it came from.
    Its old square is sometimes gone - another unit moved into it during the
    same turn, usually one of its own following it forward - and the unit used
    to stay where it stood, which is how two units came to share one square,
    and how a player's own two units came to stand on top of each other with
    no way to separate.

    It crashes into whoever took the square instead. That is a fight on the
    ordinary terms (`R5.2`): one exchange, simultaneous, everybody in it
    striking everybody else, so a unit that is hit hits back even when the
    blow it takes destroys it. Friendly fire is total (`R5.7`), and a column
    that walks into a wall it cannot shift piles into itself.

    What follows the crash:

      - the falling unit died - it holds nothing, and the square it was
        fighting over is one unit emptier;
      - the unit in the way died - the square is free and the falling unit
        takes it;
      - both stood - the one in the way gives ground and goes back where *it*
        came from, crashing into whoever is behind it in its turn, so the
        whole column pays for the pile-up and everybody ends where they
        started, the worse for it.

    Answers whether the unit is no longer standing on the square it fell back
    from - because it got home, or because it did not survive the attempt.
    """
    if unit.moved_from is None:
        # it was already standing here, or was deployed onto this square this
        # turn: there is nowhere it came from
        return False
    target = unit.moved_from
    if target in free:
        return unit.retreat(free, events)
    occupant = board[target]
    if type(occupant) is list:
        # a contest of its own, still being fought: not one unit to crash into
        return False
    if type(occupant) is not UnitType:
        # empty, but emptied after the free squares were judged - by a contest
        # that killed everyone in it, or by a crash like this one
        free.add(target)
        return unit.retreat(free, events)
    if id(unit) in crashing:
        return False                       # already fighting its way home
    if events is not None:
        events.append(Event(
            'collided', unit=unit.name, target=occupant.name,
            x=unit.x, y=unit.y, to_x=target[0], to_y=target[1],
            players=owners(unit, occupant)))
    exchangeAttacks([unit, occupant], events, out, struck)
    if unit.destroyed:
        unit.vacate()
        return True
    if occupant.destroyed:
        occupant.vacate()
        free.add(target)
        return unit.retreat(free, events)
    # both stood. The one in the way gives ground - it is going back where it
    # came from too, crashing into whoever is behind it in its turn, so a
    # column that walks into something it cannot shift piles into itself and
    # every unit in it pays for the pile-up
    if not _fall_back(occupant, board, free, events, out, struck,
                      crashing | {id(unit)}):
        return False
    free.add(target)
    return unit.retreat(free, events)


def resolveContest(board, x, y, contestants, free, events=None, out=(),
                   struck=None):
    """Fight out one square and decide who is left holding it."""
    if events is not None:
        events.append(Event(
            'contested', x=x, y=y, units=len(contestants)))
    survivors = exchangeAttacks(contestants, events, out, struck)

    for unit in contestants:
        if unit.destroyed:
            unit.vacate()

    if len(survivors) > 1:
        # nobody won the square, so everyone who moved in goes back where it
        # came from and the square is left as it was
        if events is not None:
            events.append(Event(
                'undecided', x=x, y=y,
                units=','.join(sorted(unit.name for unit in survivors)),
                players=owners(*survivors)))
        # in a settled order, because pushing one survivor back can free the
        # square another was going to fall back to: which of them is put back
        # first is the rules' to say rather than the order a list holds them
        survivors = [unit for unit in
                     sorted(survivors, key=lambda u: (u.player.number, u.name))
                     if not _fall_back(unit, board, free, events, out,
                                       struck)]

    if len(survivors) > 1:
        # a ring: every one of them moved in, and every square any of them
        # could go back to is held by another of them, round to the square
        # being fought over. There is no arrangement of them that this pass
        # can find, and a square holds one unit - so the one with the best
        # claim keeps it and the rest are lost with it.
        #
        # The best claim is standing there already; a unit that moved in has
        # none. Which of two movers keeps it is settled by number and name,
        # as everything else here is, rather than by the order a list holds
        # them in
        keeping = next((unit for unit in survivors
                        if unit.moved_from is None), survivors[0])
        for unit in survivors:
            if unit is keeping:
                continue
            unit.destroyed = True
            if events is not None:
                events.append(Event('destroyed', unit=unit.name,
                                    players=owners(unit)))
        survivors = [keeping]

    if not survivors:
        board[x, y] = Empty()
        if events is not None:
            events.append(Event('emptied', x=x, y=y))
    elif len(survivors) == 1:
        board[x, y] = survivors[0]
        if events is not None:
            events.append(Event(
                'held', unit=survivors[0].name, x=x, y=y,
                players=owners(survivors[0])))


def resolveCollision(first, second, events=None, out=(), struck=None):
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
            x=near.x, y=near.y, to_x=far.x, to_y=far.y,
            players=owners(near, far)))
    survivors = exchangeAttacks([first, second], events, out, struck)

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
                'held', unit=survivor.name, x=target_x, y=target_y,
                players=owners(survivor)))
    elif len(survivors) == 2 and events is not None:
        # neither could decide it, so both stay where the turn found them
        events.append(Event(
            'undecided', x=first.x, y=first.y,
            units=','.join(sorted(unit.name for unit in survivors)),
            players=owners(*survivors)))
