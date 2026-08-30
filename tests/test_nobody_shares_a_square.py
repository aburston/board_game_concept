"""A square holds one unit at the end of a turn, and a blocked column piles up.

A contest nobody won used to leave its survivors standing on top of each
other. The unit that moved in falls back where it came from, and that square
is often gone - the unit behind it stepped into it - so it stayed put, sharing
the square with whoever it had failed to shift.

Found in a played game: a Heavy and a Pawn on one square for four turns, the
Heavy too spent to strike back and too spent to leave; and on another square
two units of the *same* player, both at no energy, unable to fight their way
apart or step apart, though `R4.10` says there is no way to stack with your
own units.

It crashes into whoever took the square instead, and that unit gives ground
and crashes into whoever is behind it, all the way down the column. Everybody
pays for the pile-up, and a unit may take damage from what it moved into and
again from being forced back into its own.
"""

from board_game_concept import Board, Player, UnitType


def a_type(name='T', symbol='T', attack=1, health=4, energy=20):
    return UnitType(name, symbol, attack, health, energy)


def squares(board):
    """What each occupied square holds, as a count."""
    held = {}
    for x in range(board.size_x):
        for y in range(board.size_y):
            square = board.board[x, y]
            if type(square) is list:
                held[(x, y)] = len(square)
            elif type(square) is UnitType:
                held[(x, y)] = 1
    return held


def a_column(depth, board_height=8):
    """A column of `depth` units ordered north into a unit that will not move."""
    board = Board(3, board_height)
    one, two = Player(1), Player(2)
    board.add(two, 1, 0, 'wall', a_type(health=10))
    for index in range(1, depth + 1):
        board.add(one, 1, index, f'a{index}', a_type())
    board.commit()
    for index in range(1, depth + 1):
        board.getUnitByName(f'a{index}', one)[0].move(UnitType.NORTH)
    return board, board.commit()


# --- the invariant


def test_no_square_ends_a_turn_holding_two_units():
    board, _ = a_column(2)
    assert max(squares(board).values()) == 1, squares(board)


def test_your_own_two_units_do_not_end_up_stacked():
    """`R4.10`: there is no way to stack with your own units."""
    board = Board(3, 4)
    one = Player(1)
    board.add(one, 1, 1, 'mine1', a_type())
    board.add(one, 1, 2, 'mine2', a_type())
    board.add(one, 1, 3, 'mine3', a_type())
    board.commit()

    # ordered onto each other, which is what a misclick does
    board.getUnitByName('mine2', one)[0].move(UnitType.NORTH)
    board.getUnitByName('mine3', one)[0].move(UnitType.NORTH)
    board.commit()

    assert max(squares(board).values()) == 1, squares(board)


def test_every_square_holds_one_unit_however_deep_the_column():
    for depth in range(1, 6):
        board, _ = a_column(depth)
        held = squares(board)
        assert max(held.values()) == 1, (depth, held)
        assert len(held) == depth + 1, (depth, held)


# --- what the pile-up costs


def test_a_blocked_column_ends_where_it_started():
    board, _ = a_column(3)

    where = {unit.name: (unit.x, unit.y) for unit in board.units}
    assert where == {'wall': (1, 0), 'a1': (1, 1), 'a2': (1, 2), 'a3': (1, 3)}


def test_the_column_crashes_into_itself_all_the_way_down():
    _board, events = a_column(3)

    crashes = [(e.detail['unit'], e.detail['target'])
               for e in events if e.kind == 'collided']
    assert crashes == [('a1', 'a2'), ('a2', 'a3')]


def test_a_unit_takes_damage_from_what_it_met_and_from_being_forced_back():
    board, _ = a_column(3)

    health = {unit.name: unit.health for unit in board.units}
    assert health['a1'] == 2, 'struck by the wall it met and by a2 behind it'
    assert health['a2'] == 2, 'struck by a1 in front and a3 behind'
    assert health['a3'] == 3, 'struck by a2 only: nothing was behind it'
    assert health['wall'] == 9, 'and it was struck by what walked into it'


def test_a_unit_strikes_each_other_unit_once_a_turn():
    """A turn holds more than one exchange now, but not two on one pair."""
    _board, events = a_column(4)

    blows = [(e.detail['unit'], e.detail['target'])
             for e in events if e.kind == 'attacked']
    assert len(blows) == len(set(blows)), blows


def test_the_last_unit_in_the_column_has_nothing_behind_it():
    board, events = a_column(1)

    crashes = [e for e in events if e.kind == 'collided']
    assert crashes == [], 'the square behind it was free, so nothing crashed'
    where = {unit.name: (unit.x, unit.y) for unit in board.units}
    assert where == {'wall': (1, 0), 'a1': (1, 1)}


# --- and the ordinary cases, undisturbed


def test_a_unit_with_a_free_square_behind_it_simply_falls_back():
    board = Board(3, 4)
    one, two = Player(1), Player(2)
    board.add(one, 1, 2, 'a1', a_type())
    board.add(two, 1, 1, 'b1', a_type())
    board.commit()

    board.getUnitByName('a1', one)[0].move(UnitType.NORTH)
    board.commit()

    where = {unit.name: (unit.x, unit.y) for unit in board.units}
    assert where == {'b1': (1, 1), 'a1': (1, 2)}


def test_a_contest_that_is_won_disturbs_nobody_behind_it():
    board = Board(3, 4)
    one, two = Player(1), Player(2)
    board.add(one, 1, 2, 'a1', a_type(attack=9, health=9))
    board.add(one, 1, 3, 'a2', a_type())
    board.add(two, 1, 1, 'b1', a_type(health=2))
    board.commit()

    board.getUnitByName('a1', one)[0].move(UnitType.NORTH)
    board.getUnitByName('a2', one)[0].move(UnitType.NORTH)
    board.commit()

    where = {unit.name: (unit.x, unit.y)
             for unit in board.units if not unit.destroyed}
    assert where['a1'] == (1, 1), 'it won the square'
    assert where['a2'] == (1, 2), 'and its follower kept the one it took'


def test_a_unit_killed_in_the_pile_up_frees_the_square_for_the_one_behind():
    board = Board(3, 5)
    one, two = Player(1), Player(2)
    board.add(two, 1, 0, 'wall', a_type(health=10))
    board.add(one, 1, 1, 'a1', a_type(attack=5))
    board.add(one, 1, 2, 'a2', a_type(health=2))
    board.commit()

    board.getUnitByName('a1', one)[0].move(UnitType.NORTH)
    board.getUnitByName('a2', one)[0].move(UnitType.NORTH)
    board.commit()

    standing = {unit.name: (unit.x, unit.y)
                for unit in board.units if not unit.destroyed}
    assert 'a2' not in standing, 'a1 crashed into it and it did not survive'
    assert standing['a1'] == (1, 1), 'and a1 took the square it emptied'
    assert max(squares(board).values()) == 1, squares(board)


# --- what being forced back costs, which is nothing


def test_being_forced_back_costs_no_energy():
    """You pay for the move you ordered, and that covers being shoved out.

    The unit behind pays its fare and nothing else: it crashed into nobody by
    choice. Charging for the pile-up made a unit pay twice for one order.
    """
    board = Board(3, 5)
    one, two = Player(1), Player(2)
    board.add(two, 1, 0, 'wall', a_type(health=10))
    board.add(one, 1, 1, 'lead', a_type(attack=5, health=10, energy=15))
    board.add(one, 1, 2, 'back', a_type(attack=5, health=10, energy=15))
    board.commit()

    board.getUnitByName('lead', one)[0].move(UnitType.NORTH)
    board.getUnitByName('back', one)[0].move(UnitType.NORTH)
    board.commit()

    energy = {unit.name: unit.energy for unit in board.units}
    assert energy['lead'] == 15 - 3 - 5, 'its fare, and the strike it ordered'
    assert energy['back'] == 15 - 3, 'its fare, and nothing for the pile-up'


def test_a_free_blow_still_needs_a_unit_that_can_fight():
    """Energy says whether a unit can strike at all, paid for or not."""
    board = Board(3, 5)
    one, two = Player(1), Player(2)
    board.add(two, 1, 0, 'holder', a_type(health=10))
    # enough to pay its fare, strike, and still be able to fight in the pile-up
    board.add(one, 1, 1, 'lead', a_type(attack=5, health=10, energy=15))
    # too spent to strike: 1 energy left after its fare, against attack 5
    board.add(one, 1, 2, 'back', a_type(attack=5, health=4, energy=2))
    board.commit()

    board.getUnitByName('lead', one)[0].move(UnitType.NORTH)
    board.getUnitByName('back', one)[0].move(UnitType.NORTH)
    events = board.commit()

    blows = [(e.detail['unit'], e.detail['target'])
             for e in events if e.kind == 'attacked']
    assert ('lead', 'back') in blows, 'the lead could still afford to fight'
    assert ('back', 'lead') not in blows, 'and the spent one could not'


def test_two_attackers_together_break_what_one_never_could():
    """A wall is not indestructible: it takes concentration, and that costs.

    One unit can never finish a ten-health defender - it pays its fare again
    every turn to walk back in, and regains a point a turn only when given no
    order. Two in the same turn land two blows at once, and pay for it by
    striking each other: friendly fire is total.
    """
    from board_game_concept.domain import army
    catalogue = army.types()

    board = Board(3, 3)
    one, two = Player(1), Player(2)
    board.add(two, 1, 1, 'w', catalogue['Wall']['obj'])
    board.add(one, 0, 1, 'h1', catalogue['Heavy']['obj'])
    board.add(one, 2, 1, 'h2', catalogue['Heavy']['obj'])
    board.commit()

    board.getUnitByName('h1', one)[0].move(UnitType.EAST)
    board.getUnitByName('h2', one)[0].move(UnitType.WEST)
    board.commit()

    wall = board.getUnitByName('w', two)[0]
    assert wall.destroyed is True, 'two Heavies deal 10 to a 10-health wall'
    for name in ('h1', 'h2'):
        heavy = board.getUnitByName(name, one)[0]
        assert heavy.destroyed is False
        assert heavy.health == 5, 'and each took the other blow doing it'


def test_a_wall_never_strikes_back():
    """Attack 0 is the whole of what makes it a wall."""
    from board_game_concept.domain import army
    catalogue = army.types()

    board = Board(3, 3)
    one, two = Player(1), Player(2)
    board.add(two, 1, 0, 'w', catalogue['Wall']['obj'])
    board.add(one, 1, 1, 'h', catalogue['Heavy']['obj'])
    board.commit()

    board.getUnitByName('h', one)[0].move(UnitType.NORTH)
    events = board.commit()

    blows = [(e.detail['unit'], e.detail['target'])
             for e in events if e.kind == 'attacked']
    assert blows == [('h', 'w')], 'struck, and nothing came back'
    assert board.getUnitByName('w', two)[0].health == 5, 'and it took damage'


def test_one_unit_destroys_a_wall_over_time_if_it_has_the_energy():
    """One attack a turn, for as long as it can pay for one.

    A unit ordered in every turn cannot: it is forced back out, walks in again
    at the ordinary fare, and a unit given an order does not rest (`R3.9`), so
    it grinds down to nothing having landed one blow. Left alone between
    attacks it recovers, and a wall comes down.
    """
    from board_game_concept.domain import army
    catalogue = army.types()

    board = Board(3, 3)
    one, two = Player(1), Player(2)
    board.add(two, 1, 0, 'w', catalogue['Wall']['obj'])
    board.add(one, 1, 1, 'h', catalogue['Heavy']['obj'])
    board.commit()
    heavy = board.getUnitByName('h', one)[0]
    wall = board.getUnitByName('w', two)[0]
    afford = heavy.move_cost + heavy.attack

    turns = 0
    while not wall.destroyed and turns < 30:
        if heavy.energy >= afford:
            heavy.move(UnitType.NORTH)
        board.commit()
        turns += 1

    assert wall.destroyed is True
    assert turns == 3, 'strike, rest, strike'


def test_a_unit_ordered_in_every_turn_cannot_keep_it_up():
    """Which is why the walls in a played game were untouched at full health.

    Ordering it in again the moment it is forced back spends the fare and
    stops it resting, so it never affords a second blow.
    """
    from board_game_concept.domain import army
    catalogue = army.types()

    board = Board(3, 3)
    one, two = Player(1), Player(2)
    board.add(two, 1, 0, 'w', catalogue['Wall']['obj'])
    board.add(one, 1, 1, 'h', catalogue['Heavy']['obj'])
    board.commit()
    heavy = board.getUnitByName('h', one)[0]
    wall = board.getUnitByName('w', two)[0]

    for _turn in range(8):
        heavy.move(UnitType.NORTH)
        board.commit()

    assert wall.destroyed is False
    assert wall.health == 5, 'one blow landed, and never a second'
    assert heavy.energy < heavy.attack, 'it spent itself walking back in'
