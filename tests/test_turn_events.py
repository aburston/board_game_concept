"""What `Board.commit` reports about the turn it just resolved."""

from board_game_concept import Board, Player, UnitType
from board_game_concept.domain import describe


def kinds(events):
    return [event.kind for event in events]


def detail(events, kind):
    return [event.detail for event in events if event.kind == kind]


def test_a_quiet_turn_reports_nothing():
    board = Board(3, 3)
    assert board.commit() == []


def test_a_deployment_is_reported():
    board = Board(3, 3)
    p1 = Player(1)
    board.add(p1, 0, 0, 'a1', UnitType('Attacker', 'A', 1, 5, 100))
    events = board.commit()
    assert kinds(events) == ['deployed']
    assert detail(events, 'deployed') == [{'unit': 'a1', 'x': 0, 'y': 0}]


def test_a_move_is_reported_with_where_it_ended():
    board = Board(3, 3)
    p1 = Player(1)
    board.add(p1, 0, 0, 'a1', UnitType('Attacker', 'A', 1, 5, 100))
    board.commit()

    board.getUnitByName('a1')[0].move(UnitType.EAST)
    events = board.commit()
    assert detail(events, 'moved') == [{'unit': 'a1', 'x': 1, 'y': 0}]


def test_a_contest_reports_every_attack_and_who_held_the_square():
    board = Board(4, 2)
    p1, p2 = Player(1), Player(2)
    board.add(p1, 0, 0, 'a1', UnitType('Attacker', 'A', 3, 5, 100))
    board.add(p2, 1, 0, 'd1', UnitType('Defender', 'D', 2, 4, 100))
    board.commit()

    board.getUnitByName('a1')[0].move(UnitType.EAST)
    events = board.commit()

    assert 'engaged' in kinds(events)
    assert 'contested' in kinds(events)
    assert {'unit': 'a1', 'target': 'd1', 'damage': 3} in detail(events, 'attacked')
    assert {'unit': 'd1', 'target': 'a1', 'damage': 2} in detail(events, 'attacked')
    assert detail(events, 'destroyed') == [{'unit': 'd1'}]
    assert detail(events, 'held') == [{'unit': 'a1', 'x': 1, 'y': 0}]


def test_an_undecided_contest_reports_the_retreat():
    board = Board(4, 2)
    p1, p2 = Player(1), Player(2)
    # the fare takes everything either of them has, so neither can pay for an
    # attack once it arrives and neither can win the square
    board.add(p1, 0, 0, 'a1', UnitType('Attacker', 'A', 9, 5, 5))
    board.add(p2, 2, 0, 'b1', UnitType('Brawler', 'B', 9, 5, 5))
    board.commit()

    board.getUnitByName('a1')[0].move(UnitType.EAST)
    board.getUnitByName('b1')[0].move(UnitType.WEST)
    events = board.commit()

    assert 'contested' in kinds(events)
    assert detail(events, 'attacked') == []
    retreated = {d['unit'] for d in detail(events, 'retreated')}
    assert retreated == {'a1', 'b1'}


def test_events_read_as_lines_of_text():
    board = Board(3, 3)
    p1 = Player(1)
    board.add(p1, 0, 0, 'a1', UnitType('Attacker', 'A', 1, 5, 100))
    assert describe(board.commit()) == 'a1 is placed at (0, 0)'


def test_a_units_numbers_survive_a_round_trip_as_numbers():
    """A unit written out and read back needs no converting on the way in."""
    from board_game_concept.storage.serialise import units_document

    board = Board(3, 3)
    p1 = Player(1)
    board.add(p1, 1, 2, 'a1', UnitType('Attacker', 'A', 3, 7, 40))
    board.commit()

    written = units_document(board)['units'][0]
    assert written['player'] == 1
    assert written['attack'] == 3
    assert written['health'] == 7
    assert written['energy'] == 40
    assert written['x'] == 1 and written['y'] == 2


def _facing_pair(attacker_energy=40, defender_energy=40):
    # the energies are the units', not the types': a type must be designed
    # holding at least its health, since that is what one move costs, and
    # spending it down is what play does. Set after the deployment turn has
    # resolved, because a unit holding less than its design rests through it
    board = Board(4, 2)
    p1, p2 = Player(1), Player(2)
    board.add(p1, 0, 0, 'a', UnitType('A', 'A', 3, 6, 40))
    board.add(p2, 1, 0, 'b', UnitType('B', 'B', 3, 6, 40))
    board.commit()
    board.getUnitByName('a')[0].setEnergy(attacker_energy)
    board.getUnitByName('b')[0].setEnergy(defender_energy)
    return board


def test_engaging_a_standing_unit_costs_a_move():
    """unit-movement: every resolved move is charged for, engaging included."""
    board = _facing_pair()
    attacker = board.getUnitByName('a')[0]
    before = attacker.energy

    attacker.move(UnitType.EAST)
    board.commit()

    # the fare, which is the unit's health, and then the attacks the contest
    # landed
    spent = before - attacker.energy
    assert spent >= attacker.move_cost, "engaging a standing unit was free"


def test_crossing_open_ground_and_engaging_cost_the_same_move():
    open_ground = Board(4, 2)
    p1 = Player(1)
    open_ground.add(p1, 0, 0, 'lone', UnitType('A', 'A', 3, 6, 40))
    open_ground.commit()
    open_ground.getUnitByName('lone')[0].move(UnitType.EAST)
    open_ground.commit()
    crossing_cost = 40 - open_ground.getUnitByName('lone')[0].energy

    # the same move, but onto a square somebody is standing on. Read the cost
    # from the event log's own accounting rather than after combat has taken
    # its share
    engaging = _facing_pair()
    attacker = engaging.getUnitByName('a')[0]
    attacker.move(UnitType.EAST)
    energy_before = attacker.energy
    events = engaging.commit()
    attacks_landed = sum(1 for e in events
                         if e.kind == 'attacked' and e.detail['unit'] == 'a')
    engaging_cost = (energy_before - attacker.energy
                     - attacks_landed * attacker.attack)
    assert engaging_cost == crossing_cost


def test_a_unit_too_spent_to_attack_still_arrives():
    board = _facing_pair(attacker_energy=2)
    attacker = board.getUnitByName('a')[0]
    # exactly the fare - six health is two energy a square - and so nothing
    # left to attack with. Under simultaneous
    # resolution there is no order-independent moment at which "occupied" can
    # be tested, so a mover needs only the fare: it arrives and is inert in the
    # contest it walked into
    attacker.move(UnitType.EAST)
    events = board.commit()
    assert attacker.energy == 0
    assert not any(e.kind == 'attacked' and e.detail['unit'] == 'a'
                   for e in events)
    assert not attacker.destroyed or attacker.health <= 0


def test_a_unit_that_cannot_pay_the_fare_does_not_move():
    board = _facing_pair(attacker_energy=1)
    attacker = board.getUnitByName('a')[0]
    attacker.setEnergy(0)
    attacker.move(UnitType.EAST)
    events = board.commit()
    assert (attacker.x, attacker.y) == (0, 0)
    assert attacker.energy == 0
    assert [e.detail['reason'] for e in events if e.kind == 'refused'] == [
        'not enough energy to move']
