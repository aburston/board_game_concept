"""The flag, in the engine: who carries it, what it costs, and what it costs
to lose it.

A game ended when one player was the last with a unit standing, which on a
board where an enemy is hidden until contact meant hunting an army down square
by square. One unit of each army carries a flag everybody can see, and losing
it puts its owner out - so there is somewhere to go from the first turn.

These are the rules as the board resolves them. What each player is told about
a flag is `visibility`'s, and how a player designates one is the service
layer's; neither is here.
"""

import pytest

from board_game_concept import Board, Player, UnitType
from board_game_concept.domain import describe


def kinds(events):
    return [event.kind for event in events]


def a_board(size=(4, 3)):
    return Board(*size)


def deploy(board, player, name, square, stats=(2, 4, 8)):
    attack, health, energy = stats
    board.add(player, square[0], square[1], name,
              UnitType(name[0], name[0], attack, health, energy))
    return board.getUnitByName(name)[0]


# --- carrying it costs nothing


def test_carrying_the_flag_changes_no_statistic():
    """It is a standing, not a statistic."""
    board = a_board()
    one = Player(1)
    plain = deploy(board, one, 'plain', (0, 0))
    carrier = deploy(board, one, 'carrier', (1, 0))
    carrier.flag = True

    assert carrier.cost == plain.cost
    assert carrier.move_cost == plain.move_cost
    assert (carrier.attack, carrier.health, carrier.energy) \
        == (plain.attack, plain.health, plain.energy)


def test_a_unit_carries_nothing_until_it_is_designated():
    board = a_board()
    unit = deploy(board, Player(1), 'a1', (0, 0))
    assert unit.flag is False


# --- what the board can answer about it


def test_the_board_names_the_carrier():
    board = a_board()
    one = Player(1)
    deploy(board, one, 'a1', (0, 0))
    carrier = deploy(board, one, 'a2', (1, 0))
    carrier.flag = True

    assert board.flagOf(1) is carrier
    assert board.flagOf(2) is None


def test_a_flag_is_fallen_only_once_its_carrier_is_destroyed():
    board = a_board()
    carrier = deploy(board, Player(1), 'a1', (0, 0))
    carrier.flag = True
    assert board.flagFallen(1) is False

    carrier.destroyed = True

    assert board.flagFallen(1) is True


def test_a_player_who_designated_nobody_has_no_flag_to_lose():
    """Which is what keeps a game set up before flags playing as it was."""
    board = a_board()
    unit = deploy(board, Player(1), 'a1', (0, 0))
    unit.destroyed = True

    assert board.flagOf(1) is None
    assert board.flagFallen(1) is False


def test_the_bearers_are_answered_in_a_settled_order():
    """Nothing published from the board may depend on list position."""
    board = a_board()
    third = deploy(board, Player(3), 'c1', (0, 0))
    first = deploy(board, Player(1), 'a1', (1, 0))
    second = deploy(board, Player(2), 'b1', (2, 0))
    for unit in (third, first, second):
        unit.flag = True

    assert list(board.flagBearers()) == [1, 2, 3]


# --- what happens when one falls


def a_flag_about_to_fall():
    """A carrier one blow from death, and the unit that will deal it."""
    board = a_board()
    one, two = Player(1), Player(2)
    carrier = deploy(board, one, 'carrier', (0, 0), stats=(1, 1, 4))
    survivor = deploy(board, one, 'survivor', (2, 0), stats=(4, 4, 8))
    # energy enough to cross the board and still pay for its attacks: a
    # killer that runs out of energy proves nothing about flags
    killer = deploy(board, two, 'killer', (1, 0), stats=(4, 4, 40))
    board.commit()
    carrier.flag = True
    return board, carrier, survivor, killer


def test_a_flag_falling_is_reported():
    board, _, _, killer = a_flag_about_to_fall()
    killer.move(UnitType.WEST)

    events = board.commit()

    assert 'flag_fallen' in kinds(events)
    fallen = [event for event in events if event.kind == 'flag_fallen'][0]
    assert fallen.detail == {'unit': 'carrier', 'player': 1}
    assert 'flag' in describe(events)


def test_a_death_that_is_not_a_carrier_reports_no_flag():
    board, _, survivor, killer = a_flag_about_to_fall()
    survivor.flag = False
    killer.move(UnitType.WEST)
    board.commit()                      # the carrier falls here

    events = board.commit()

    assert 'flag_fallen' not in kinds(events)


def test_a_flag_is_reported_fallen_once_and_not_every_turn_after():
    board, _, _, killer = a_flag_about_to_fall()
    killer.move(UnitType.WEST)
    board.commit()

    again = board.commit()

    assert 'flag_fallen' not in kinds(again)


# --- and what the army does afterwards


def test_an_army_without_its_flag_takes_no_orders():
    board, _, survivor, killer = a_flag_about_to_fall()
    killer.move(UnitType.WEST)
    board.commit()
    where = (survivor.x, survivor.y)

    survivor.move(UnitType.WEST)
    board.commit()

    assert (survivor.x, survivor.y) == where


def test_an_army_without_its_flag_lands_no_attack():
    board, _, survivor, killer = a_flag_about_to_fall()
    killer.move(UnitType.WEST)
    board.commit()
    health_before = killer.health

    # the killer walks into the survivor, which is now terrain
    killer.move(UnitType.EAST)
    board.commit()
    killer.move(UnitType.EAST)
    events = board.commit()

    struck = [event.detail['unit'] for event in events
              if event.kind == 'attacked']
    assert 'survivor' not in struck, 'an eliminated army struck back'
    assert killer.health == health_before


def test_an_army_without_its_flag_can_still_be_destroyed():
    board, _, survivor, killer = a_flag_about_to_fall()
    killer.move(UnitType.WEST)
    board.commit()

    for _ in range(6):
        if survivor.destroyed:
            break
        killer.move(UnitType.EAST)
        board.commit()

    assert survivor.destroyed, 'terrain could not be cleared'


def test_a_flag_falling_does_not_silence_the_turn_it_falls_in():
    """The carrier strikes in the round that kills it, as any unit does."""
    board, carrier, _, killer = a_flag_about_to_fall()
    killer.move(UnitType.WEST)

    events = board.commit()

    struck = [event.detail['unit'] for event in events
              if event.kind == 'attacked']
    assert 'carrier' in struck
    assert carrier.destroyed


def test_a_wall_may_carry_the_flag():
    """A stationary flag is a target that never moves, which is a choice."""
    board = a_board()
    one = Player(1)
    board.add(one, 0, 0, 'wall', UnitType('w', 'w', 0, 10, 0))
    wall = board.getUnitByName('wall')[0]
    wall.flag = True
    board.commit()

    assert board.flagOf(1) is wall
    assert board.flagFallen(1) is False


@pytest.mark.parametrize('order', [(1, 2), (2, 1)])
def test_two_flags_falling_together_are_both_reported(order):
    """And which was noticed first decides nothing."""
    board = a_board()
    players = {1: Player(1), 2: Player(2)}
    first = deploy(board, players[order[0]], 'first', (0, 0), stats=(4, 1, 8))
    second = deploy(board, players[order[1]], 'second', (1, 0),
                    stats=(4, 1, 8))
    board.commit()
    first.flag = True
    second.flag = True

    first.move(UnitType.EAST)
    events = board.commit()

    fallen = {event.detail['player'] for event in events
              if event.kind == 'flag_fallen'}
    assert fallen == {1, 2}
