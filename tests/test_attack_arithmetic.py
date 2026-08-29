"""What one exchange of a fight costs and does, checked twice over.

A turn on a running game looked wrong: a unit ordered one square onto a wall
struck it six times in that one turn. That was the old rule - a contest was
fought in rounds until one side died or nobody could pay - and a single order
bought as many strikes as a unit could afford.

The rule now is one strike a turn. A unit standing in a contested square
strikes once, if it can pay, and stops; to press a fight it is ordered back in
next turn. `test_the_turn_a_running_game_reported` is that same turn under the
new rule - one strike, not six.

Two kinds of test here. The first are sums anybody can check by hand: what one
strike costs, what it lands, and when it decides a square. The second is a
differential: `by_the_book` is the single-exchange rule implemented again from
the prose, and every combination of statistics in a modest space is fought
both ways and compared. It is a second opinion, not a second copy - the engine
charges and strikes as it walks the square, this deals the exchange's blows
after they have all been paid for, and if the two ever disagree one is wrong.
"""

import itertools

from board_game_concept import Board, Player, UnitType
from board_game_concept.domain.unit import exchangeAttacks

from game_harness import GameHarness


def unit(name, attack, health, energy):
    """One unit with exactly these statistics, whatever play would allow.

    A type is built with the energy it needs to exist - a wall has none, and
    anything that attacks must be able to afford one move - and is then set to
    the energy the case is about, which is what play leaves behind.
    """
    built = 0 if attack == 0 else max(energy, health, 1)
    made = UnitType(name, name[0].upper(), attack, health, built)
    made.setName(name)
    made.setPlayer(Player(1))
    made.setEnergy(energy)
    made.setHealth(health)
    return made


def by_the_book(stats):
    """The single exchange, read off the page (R5.2-R5.6).

    Everyone standing who can pay their attack value does so, once, and deals
    that value to every other unit standing. The blows land together, so a
    unit destroyed by the exchange has already struck. Then it is over: there
    is no second exchange.
    """
    state = [{'attack': a, 'health': h, 'energy': e} for a, h, e in stats]
    standing = [each for each in state if each['health'] > 0]
    if len(standing) >= 2:
        blows = []
        for each in standing:
            if each['attack'] <= 0 or each['energy'] < each['attack']:
                continue
            each['energy'] -= each['attack']
            for target in standing:
                if target is not each:
                    blows.append((target, each['attack']))
        for target, damage in blows:
            target['health'] -= damage
    return [(each['health'], each['energy']) for each in state]


def fought(stats):
    """The same exchange, through the engine."""
    units = [unit(f'u{index}', *each) for index, each in enumerate(stats)]
    events = []
    exchangeAttacks(units, events)
    return ([(each.health, each.energy) for each in units],
            [event for event in events if event.kind == 'attacked'])


# --- the differential

ATTACKS = (0, 1, 2, 3, 5)
HEALTHS = (1, 2, 3, 4, 7, 10)
ENERGIES = (0, 1, 2, 3, 5, 9, 20)

SPACE = [(attack, health, energy)
         for attack in ATTACKS
         for health in HEALTHS
         for energy in ENERGIES]


def test_every_two_unit_exchange_is_fought_by_the_book():
    disagreed = []
    for pair in itertools.combinations_with_replacement(SPACE, 2):
        want = by_the_book(list(pair))
        got, _ = fought(list(pair))
        if want != got:
            disagreed.append((pair, want, got))
    assert not disagreed, disagreed[:5]


def test_every_three_unit_exchange_is_fought_by_the_book():
    small = [(attack, health, energy)
             for attack in (0, 1, 3)
             for health in (1, 3, 6)
             for energy in (0, 2, 6)]
    disagreed = []
    for trio in itertools.combinations_with_replacement(small, 3):
        want = by_the_book(list(trio))
        got, _ = fought(list(trio))
        if want != got:
            disagreed.append((trio, want, got))
    assert not disagreed, disagreed[:5]


def test_a_unit_strikes_at_most_once_over_the_whole_space():
    """The heart of the change: one strike a turn, whatever the statistics."""
    for pair in itertools.combinations_with_replacement(SPACE, 2):
        units = [unit(f'u{index}', *each)
                 for index, each in enumerate(pair)]
        before = [each.energy for each in units]
        events = []
        exchangeAttacks(units, events)
        for each, started in zip(units, before):
            struck = [event for event in events
                      if event.kind == 'attacked'
                      and event.detail['unit'] == each.name]
            spent = started - each.energy
            # in a duel a unit strikes its one opponent at most once
            assert len(struck) <= 1, (pair, each.name, len(struck))
            if struck:
                assert spent == each.attack, (pair, each.name, spent)
            else:
                assert spent == 0, (pair, each.name, spent)


# --- the sums, by hand


def test_one_strike_costs_the_attack_value_once():
    a = unit('a', 3, 10, 20)
    b = unit('b', 0, 10, 0)
    events = []
    exchangeAttacks([a, b], events)

    assert a.energy == 20 - 3, 'one strike, one charge'
    assert b.health == 10 - 3
    assert len([e for e in events if e.kind == 'attacked']) == 1


def test_a_strike_hits_every_other_unit_in_the_square_for_one_charge():
    a = unit('a', 2, 10, 2)
    b = unit('b', 1, 10, 0)
    c = unit('c', 1, 10, 0)
    exchangeAttacks([a, b, c])

    assert a.energy == 0, 'paid its attack value once'
    assert (10 - b.health, 10 - c.health) == (2, 2), 'both struck for 2'


def test_a_strike_decides_the_square_only_when_it_is_lethal():
    # attack 4 kills a 4-health defender outright; the survivor takes the one
    # blow the defender lands back
    board = Board(4, 2)
    one, two = Player(1), Player(2)
    board.add(one, 0, 0, 'a1',
              UnitType('Attacker', 'A', 4, 5, 100))
    board.add(two, 1, 0, 'd1',
              UnitType('Defender', 'D', 2, 4, 100))
    board.commit()

    board.getUnitByName('a1')[0].move(UnitType.EAST)
    board.commit()

    a1 = board.getUnitByName('a1')[0]
    d1 = board.getUnitByName('d1')[0]
    assert d1.destroyed is True
    assert board.getUnitByCoords(1, 0) is a1
    assert a1.health == 5 - 2, "it took the defender's one strike"


def test_a_strike_that_is_not_lethal_leaves_the_square_undecided():
    board = Board(4, 2)
    one, two = Player(1), Player(2)
    board.add(one, 0, 0, 'a1',
              UnitType('Attacker', 'A', 3, 5, 100))
    board.add(two, 1, 0, 'd1',
              UnitType('Defender', 'D', 2, 4, 100))
    board.commit()

    board.getUnitByName('a1')[0].move(UnitType.EAST)
    events = board.commit()

    a1 = board.getUnitByName('a1')[0]
    d1 = board.getUnitByName('d1')[0]
    # both take one strike and both live, so the mover is turned back
    assert d1.destroyed is False and a1.destroyed is False
    assert d1.health == 4 - 3 and a1.health == 5 - 2
    assert (a1.x, a1.y) == (0, 0), 'undecided, so it falls back'
    assert board.getUnitByCoords(1, 0) is d1
    assert any(e.kind == 'undecided' for e in events)


def test_striking_three_costs_what_striking_one_costs():
    alone = unit('a', 2, 10, 40)
    exchangeAttacks([alone, unit('x', 0, 10, 0)])
    spent_alone = 40 - alone.energy

    crowded = unit('a', 2, 10, 40)
    exchangeAttacks([crowded] + [unit(f'x{i}', 0, 10, 0) for i in range(3)])
    spent_crowded = 40 - crowded.energy

    assert spent_alone == spent_crowded == 2, 'one attack value, once'


def test_a_unit_that_cannot_pay_strikes_nothing():
    short = unit('a', 3, 10, 2)
    target = unit('b', 0, 10, 0)
    events = []
    exchangeAttacks([short, target])

    assert short.energy == 2, 'it paid for a strike it could not make'
    assert target.health == 10
    assert not [e for e in events if e.kind == 'attacked']


def test_identical_units_both_survive_one_exchange():
    """The old model annihilated equals; one strike each no longer does."""
    for health in (2, 3, 8):
        first = unit('a', 1, health, 50)
        second = unit('b', 1, health, 50)
        exchangeAttacks([first, second])
        assert not first.destroyed and not second.destroyed, health
        assert first.health == second.health == health - 1
        assert first.energy == second.energy == 50 - 1


def test_identical_units_annihilate_only_on_a_lethal_strike():
    # attack 2 against health 2 is lethal in one, so equals do destroy each
    # other - but only because the single strike is enough
    first = unit('a', 2, 2, 50)
    second = unit('b', 2, 2, 50)
    exchangeAttacks([first, second])
    assert first.destroyed and second.destroyed


def test_a_destroyed_unit_still_lands_its_own_blow():
    # three into one square: the strong unit kills both others outright, and
    # both land their blow in the same exchange, so it drops by two
    board = Board(3, 3)
    one, two = Player(1), Player(2)
    board.add(one, 1, 0, 's1', UnitType('Strong', 'S', 10, 10, 100))
    board.add(two, 0, 1, 'm1', UnitType('Medium', 'M', 1, 5, 100))
    board.add(two, 2, 1, 'w1', UnitType('Weak', 'W', 1, 5, 100))
    board.commit()

    board.getUnitByName('s1')[0].move(UnitType.SOUTH)
    board.getUnitByName('m1')[0].move(UnitType.EAST)
    board.getUnitByName('w1')[0].move(UnitType.WEST)
    board.commit()

    s1 = board.getUnitByName('s1')[0]
    assert board.getUnitByName('m1')[0].destroyed is True
    assert board.getUnitByName('w1')[0].destroyed is True
    assert s1.health == 8, 'a point from each unit it destroyed'
    assert board.getUnitByCoords(1, 1) is s1


# --- the whole turn, where the move fare and the strike meet


def test_the_turn_a_running_game_reported(tmp_path):
    """The turn that started this, replayed - one strike, not six.

    A unit of attack 1, health 10 and energy 9 is ordered one square east onto
    a wall of health 10. The fare is a quarter of its health rounded up
    (R4.3), so 3, leaving 6. Under the old rule those 6 bought six strikes and
    drained the unit dry; now it strikes once for 1 and keeps the other 5. The
    wall has no attack, so nobody is destroyed, the square is undecided, and
    the mover falls back with energy to spare.
    """
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1], budget=200)
    harness.deploy(1,
                   [('#', '#', 0, 10, 0), ('=', '=', 1, 10, 9),
                    ('@', '@', 1, 8, 2)],
                   [('=', '=-1', 0, 0), ('#', '#-2', 1, 0),
                    ('@', '@-3', 0, 1)],
                   flag='@-3')
    harness.resolve()
    units = harness.units()
    assert (units['=-1'].health, units['=-1'].energy) == (10, 9)
    assert units['=-1'].move_cost == 3

    harness.turn({1: [('=-1', UnitType.EAST)]})

    units = harness.units()
    mover, wall = units['=-1'], units['#-2']
    assert mover.energy == 9 - 3 - 1, 'the fare, and one strike, and no more'
    assert wall.health == 10 - 1, 'struck once, not six times'
    assert not mover.destroyed and not wall.destroyed
    assert (mover.x, mover.y) == (0, 0), 'undecided, so it falls back'

    feed = harness.repository().read_turn_events(2)
    struck = [entry for entry in feed if entry['kind'] == 'attacked']
    assert len(struck) == 1
    assert struck[0]['detail']['damage'] == 1


def test_pressing_a_wall_takes_a_strike_a_turn(tmp_path):
    """What clearing a wall looks like now: one point a turn, ordered each time.

    The wall has 10 health; a strike of 1 takes ten turns of being ordered
    back in, resting the fare back between - which is the point of the change.
    Here, two turns take two points, and the mover is never drained.
    """
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1], budget=200)
    # energy high enough to move in and strike, twice over
    harness.deploy(1,
                   [('#', '#', 0, 10, 0), ('=', '=', 1, 4, 40),
                    ('@', '@', 1, 8, 2)],
                   [('=', '=-1', 0, 0), ('#', '#-2', 1, 0),
                    ('@', '@-3', 0, 1)],
                   flag='@-3')
    harness.resolve()

    struck = 0
    for _ in range(2):
        # the mover was turned back to (0, 0) last turn, so it is ordered east
        # into the wall again
        harness.turn({1: [('=-1', UnitType.EAST)]})
        struck += 1
        assert harness.units()['#-2'].health == 10 - struck
        assert not harness.units()['#-2'].destroyed
