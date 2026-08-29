"""What a round of a contest costs the units fighting it.

A unit used to be charged its attack value once per opponent, so a crowd drained
it at a rate decided by how many happened to be standing there. Worse, a unit
that could afford some but not all of its attacks struck whichever opponents came
first in the square's list — a rule decided by list position, which is exactly the
unpredictability this game does not have.
"""

import itertools

from board_game_concept import Player, UnitType
from board_game_concept.domain.unit import exchangeAttacks


def unit(name, attack, health, energy):
    # a type must be built holding at least its health in energy, because that
    # is what one move costs; play is what runs it down, so a unit that has
    # spent everything is made whole and then set
    made = UnitType(name, name[0].upper(), attack, health, max(energy, health))
    made.setName(name)
    made.setPlayer(Player(1))
    made.setEnergy(energy)
    return made


def test_a_round_is_charged_once_however_many_opponents():
    for opponents in (1, 2, 3):
        units = [unit(f'u{i}', 2, 10, 100) for i in range(opponents + 1)]
        attacker = units[0]
        before = attacker.energy
        events = []
        exchangeAttacks(units, events)
        rounds = max(
            1, len([e for e in events if e.kind == 'attacked'
                    and e.detail['unit'] == 'u0']) // opponents)
        assert before - attacker.energy == rounds * attacker.attack, opponents


def test_a_round_strikes_every_opponent_for_one_charge():
    units = [unit('a', 2, 10, 2), unit('b', 1, 10, 0), unit('c', 1, 10, 0)]
    a, b, c = units
    exchangeAttacks(units)
    # a paid once and hit both; b and c had no energy to answer with
    assert a.energy == 0
    assert (10 - b.health, 10 - c.health) == (2, 2)


def test_a_crowd_costs_one_strike_however_many_it_faces():
    # one exchange a turn: a strikes each opponent once and pays its attack
    # value exactly once, whether it faces one opponent or three
    for opponents in (1, 2, 3):
        a = unit('a', 2, 10, 6)
        units = [a] + [unit(f'o{i}', 1, 10, 0) for i in range(opponents)]
        events = []
        exchangeAttacks(units, events)
        struck = [e for e in events if e.kind == 'attacked'
                  and e.detail['unit'] == 'a']
        assert len(struck) == opponents, (opponents, len(struck))
        assert a.energy == 6 - a.attack, opponents


def test_a_round_is_all_or_nothing_whatever_order_the_cell_holds():
    # attack 2 on energy 2: one round's worth each
    outcomes = set()
    for order in itertools.permutations('abc'):
        units = {name: unit(name, 2, 10, 2) for name in 'abc'}
        exchangeAttacks([units[name] for name in order])
        outcomes.add(tuple(sorted(
            (name, 10 - made.health, made.energy)
            for name, made in units.items())))
    assert len(outcomes) == 1, outcomes


def test_a_unit_that_cannot_pay_strikes_nobody():
    units = [unit('a', 5, 10, 4), unit('b', 1, 10, 0), unit('c', 1, 10, 0)]
    a, b, c = units
    exchangeAttacks(units)
    assert a.energy == 4
    assert (b.health, c.health) == (10, 10)
