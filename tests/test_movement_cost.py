"""What a move costs: a quarter of the moving unit's maximum health, rounded up.

A move used to cost 1 whatever the unit was, so a 10-health brute crossed the
board on the same fare as a 1-health scout. Then it cost the whole of the
type's health, which priced that brute at ten energy a square against a rest
rate of one a turn — a unit that crossed at a square every ten turns. It costs
a quarter of that health instead, rounded up, so weight still costs mobility
and a heavy unit can still campaign.

The cost is read from the design, not from the health play has worn down: a
wounded unit pays exactly what it paid when it was whole. Rounding is upward,
so nothing moves for nothing.
"""

import pytest

from board_game_concept import Board, Player, UnitType


#: what each permitted health pays for a square
FARES = {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3}

#: what every standing unit gets back at the end of a turn (R3.9), which
#: every energy read after a turn here carries
GAIN = UnitType.REST_GAIN


def board_with(units, size_x=6, size_y=3):
    """`units` are `(player, name, x, y, attack, health, energy)`.

    Each type is designed with `GAIN` more energy than its unit starts the
    turn holding, so that the turn's gain is never hidden by the cap and the
    fare can be read: a unit ends a turn at what it held, less what it paid,
    plus `GAIN`. A hundred is the most a type may hold, so a unit that must
    start below its cap starts at ninety here rather than a hundred.
    """
    board = Board(size_x, size_y)
    players = {}
    for number, name, x, y, attack, health, energy in units:
        player = players.setdefault(number, Player(number))
        board.add(player, x, y, name,
                  UnitType(name, name[0].upper(), attack, health,
                           min(100, energy + GAIN)))
    board.commit()
    for number, name, x, y, attack, health, energy in units:
        board.getUnitByName(name)[0].setEnergy(energy)
    return board


def order(board, *orders):
    for name, direction in orders:
        board.getUnitByName(name)[0].move(direction)
    return board.commit()


def at(board, name):
    unit = board.getUnitByName(name)[0]
    return (unit.x, unit.y)


# --- the fare is a quarter of the maximum health, rounded up


@pytest.mark.parametrize('health,fare', sorted(FARES.items()))
def test_a_move_costs_a_quarter_of_the_units_maximum_health(health, fare):
    board = board_with([(1, 'u', 0, 0, 1, health, 90)])
    order(board, ('u', UnitType.EAST))
    unit = board.getUnitByName('u')[0]
    assert unit.move_cost == fare
    assert unit.energy == 90 - fare + GAIN
    assert at(board, 'u') == (1, 0)


def test_the_fare_is_the_ceiling_and_never_zero():
    """Rounding down would let health 1 to 3 move for nothing."""
    for health, fare in FARES.items():
        assert fare == -(-health // 4)
        assert fare >= 1


def test_the_lightest_unit_pays_one_and_the_heaviest_three():
    board = board_with([(1, 'scout', 0, 0, 1, 1, 90),
                        (1, 'brute', 0, 2, 1, 10, 90)])
    order(board, ('scout', UnitType.EAST), ('brute', UnitType.EAST))
    assert board.getUnitByName('scout')[0].energy == 89 + GAIN
    assert board.getUnitByName('brute')[0].energy == 87 + GAIN


def test_the_fare_is_a_step_and_health_one_to_four_are_equally_quick():
    """Two types that differ only in health can pay the same to move.

    That was impossible when the fare was the health itself, and it is the
    price of a fare that fits in three values while health fits in ten.
    """
    board = board_with([(1, 'thin', 0, 0, 1, 1, 90),
                        (1, 'stout', 0, 2, 1, 4, 90)])
    order(board, ('thin', UnitType.EAST), ('stout', UnitType.EAST))
    assert board.getUnitByName('thin')[0].energy == 89 + GAIN
    assert board.getUnitByName('stout')[0].energy == 89 + GAIN


def test_the_fare_is_the_same_from_any_starting_energy():
    for energy in (2, 5, 50, 90, 98):
        board = board_with([(1, 'u', 0, 0, 1, 8, energy)])
        order(board, ('u', UnitType.EAST))
        assert board.getUnitByName('u')[0].energy == energy - 2 + GAIN


def test_a_unit_with_exactly_its_fare_moves_and_is_spent():
    board = board_with([(1, 'u', 0, 0, 1, 8, 100)])
    board.getUnitByName('u')[0].setEnergy(2)
    order(board, ('u', UnitType.EAST))
    unit = board.getUnitByName('u')[0]
    assert at(board, 'u') == (1, 0)
    assert unit.energy == 0 + GAIN, 'spent, and then the turn gives back'


def test_a_unit_of_one_health_with_a_single_energy_can_still_move():
    board = board_with([(1, 'u', 0, 0, 1, 1, 100)])
    board.getUnitByName('u')[0].setEnergy(1)
    order(board, ('u', UnitType.EAST))
    unit = board.getUnitByName('u')[0]
    assert at(board, 'u') == (1, 0)
    assert unit.energy == 0 + GAIN


# --- what happens when the fare cannot be paid


def test_a_unit_one_energy_short_of_its_fare_does_not_move():
    board = board_with([(1, 'u', 0, 0, 1, 8, 100)])
    board.getUnitByName('u')[0].setEnergy(1)
    events = order(board, ('u', UnitType.EAST))
    unit = board.getUnitByName('u')[0]
    assert at(board, 'u') == (0, 0)
    assert unit.energy == 1 + GAIN, 'paid nothing, and recovered'
    assert [e.detail['reason'] for e in events if e.kind == 'refused'] == [
        'not enough energy to move']


def test_a_heavy_unit_is_refused_on_energy_a_light_one_could_spend():
    """Two energy carries a health-8 unit and leaves a health-9 one standing."""
    board = board_with([(1, 'light', 0, 0, 1, 8, 100),
                        (1, 'heavy', 0, 2, 1, 9, 100)])
    for name in ('light', 'heavy'):
        board.getUnitByName(name)[0].setEnergy(2)
    events = order(board, ('light', UnitType.EAST), ('heavy', UnitType.EAST))
    assert at(board, 'light') == (1, 0)
    assert board.getUnitByName('light')[0].energy == 0 + GAIN
    assert at(board, 'heavy') == (0, 2)
    assert board.getUnitByName('heavy')[0].energy == 2 + GAIN
    assert [(e.detail['unit'], e.detail['reason'])
            for e in events if e.kind == 'refused'] == [
        ('heavy', 'not enough energy to move')]


# --- damage does not change the fare


def test_a_wounded_unit_pays_what_it_paid_while_whole():
    board = board_with([(1, 'u', 0, 0, 1, 8, 90)])
    order(board, ('u', UnitType.EAST))
    whole = 90 + GAIN - board.getUnitByName('u')[0].energy

    board.getUnitByName('u')[0].setHealth(1)
    before = board.getUnitByName('u')[0].energy
    order(board, ('u', UnitType.EAST))
    wounded = before + GAIN - board.getUnitByName('u')[0].energy

    assert whole == 2
    assert wounded == 2


def test_a_wounded_unit_is_refused_where_a_lighter_type_would_move():
    """Health lost is not weight shed: the fare is the design, not the damage."""
    board = board_with([(1, 'u', 0, 0, 1, 8, 100)])
    unit = board.getUnitByName('u')[0]
    unit.setHealth(1)
    unit.setEnergy(1)
    events = order(board, ('u', UnitType.EAST))
    assert at(board, 'u') == (0, 0)
    assert board.getUnitByName('u')[0].energy == 1 + GAIN
    assert board.getUnitByName('u')[0].move_cost == 2
    assert any(e.kind == 'refused' for e in events)


# --- a head-on collision, where each side pays its own fare


def collide(board):
    return order(board, ('a', UnitType.EAST), ('b', UnitType.WEST))


def fare_paid(board, name, before, events):
    """What the move cost, with the fight's share of the bill taken off
    and the turn's gain put back."""
    unit = board.getUnitByName(name)[0]
    attacks = sum(1 for e in events
                  if e.kind == 'attacked' and e.detail['unit'] == name)
    return before + GAIN - unit.energy - attacks * unit.attack


def test_colliding_units_of_different_weights_pay_differently():
    # the fare is each unit's own quarter-of-health, and there is no reason
    # the two should match. A collision is fought, so the fight's share of the
    # bill is taken off before the fare is read
    board = board_with([(1, 'a', 0, 0, 1, 2, 50),
                        (2, 'b', 1, 0, 1, 9, 50)])
    events = collide(board)
    assert fare_paid(board, 'a', 50, events) == 1
    assert fare_paid(board, 'b', 50, events) == 3


def test_a_collision_only_one_side_can_pay_is_not_a_collision():
    # b cannot afford the square it was ordered into, so there is no head-on
    # to fight: a simply walks into the square b is still standing in
    board = board_with([(1, 'a', 0, 0, 1, 2, 50),
                        (2, 'b', 1, 0, 1, 9, 50)])
    board.getUnitByName('b')[0].setEnergy(2)
    events = collide(board)

    assert at(board, 'b') == (1, 0), 'it could not pay, so it did not move'
    assert fare_paid(board, 'b', 2, events) == 0, 'and it paid no fare'
    assert [(e.detail['unit'], e.detail['reason'])
            for e in events if e.kind == 'refused'] == [
        ('b', 'not enough energy to move')]

    # a walked into the square b was standing in and a contest was fought
    # there - not a head-on collision, which is the thing this is about
    assert fare_paid(board, 'a', 50, events) == 1, 'a paid its own fare'
    assert any(e.kind == 'contested' for e in events)
    assert not any(e.kind == 'collided' for e in events), 'no head-on'
    # neither could finish the other in the one exchange a turn buys, so the
    # square is undecided and a, which moved in, is turned back
    assert at(board, 'a') == (0, 0)
    assert any(e.kind == 'undecided' for e in events)


# --- what health now buys, and costs


def test_health_is_paid_for_twice_over():
    """Once at the till, and again every square the unit walks."""
    light = UnitType('Light', 'L', 1, 2, 50)
    heavy = UnitType('Heavy', 'H', 1, 9, 50)

    assert heavy.cost > light.cost, 'the heavier costs more to deploy'
    assert heavy.move_cost > light.move_cost, 'and more for every square'
    assert 50 // heavy.move_cost < 50 // light.move_cost, \
        'so it has fewer squares in it before it must wait to recover'


def test_the_heavier_never_pays_less_though_it_may_pay_the_same():
    """The fare is a step, so `more health costs more` is `costs no less`."""
    fares = [UnitType('T', 'T', 1, health, 100).move_cost
             for health in range(1, 11)]
    assert fares == sorted(fares), 'never falls as health rises'
    assert len(set(fares)) < len(fares), 'and is flat in places'
