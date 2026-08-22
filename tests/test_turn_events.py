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
    # neither can pay for an attack, so neither can win the square
    board.add(p1, 0, 0, 'a1', UnitType('Attacker', 'A', 9, 5, 1))
    board.add(p2, 2, 0, 'b1', UnitType('Brawler', 'B', 9, 5, 1))
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
    import yaml

    from board_game_concept.storage.serialise import serialise_units

    board = Board(3, 3)
    p1 = Player(1)
    board.add(p1, 1, 2, 'a1', UnitType('Attacker', 'A', 3, 7, 40))
    board.commit()

    written = yaml.safe_load(serialise_units(board))['units'][0]
    assert written['player'] == 1
    assert written['attack'] == 3
    assert written['health'] == 7
    assert written['energy'] == 40
    assert written['x'] == 1 and written['y'] == 2
