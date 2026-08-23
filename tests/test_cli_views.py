"""What a `show` command has to say, checked without printing any of it.

The views are the one place the table and the JSON both read from, so what is
asserted here is asserted about both formats at once.
"""

from board_game_concept import Board, Player, UnitType
from board_game_concept.cli import views
from board_game_concept.service import games
from board_game_concept.service.commands import Move

from game_harness import GameHarness


def a_game(tmp_path):
    """Two players, a type each, a unit each, deployed and resolved."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [('tank', 'T', 3, 5, 10)], [('tank', 'alpha', 0, 0)])
    harness.deploy(2, [('scout', 'S', 1, 2, 10)], [('scout', 'recon', 3, 3)])
    harness.resolve()
    return harness


def test_types_view_lists_every_type_with_its_statistics(tmp_path):
    session = a_game(tmp_path).session(0)

    entries = views.types_view(session.getPlayers())

    by_name = {entry['name']: entry for entry in entries}
    assert by_name['tank'] == {
        'player': 1, 'name': 'tank', 'symbol': 'T',
        'attack': 3, 'health': 5, 'energy': 10}
    assert by_name['scout']['player'] == 2


def test_units_view_carries_the_units_own_statistics(tmp_path):
    session = a_game(tmp_path).session(0)

    entries = views.units_view(session.getBoard())

    alpha = [entry for entry in entries if entry['name'] == 'alpha'][0]
    assert alpha['player'] == 1
    assert alpha['type'] == 'tank'
    assert alpha['symbol'] == 'T'
    assert (alpha['x'], alpha['y']) == (0, 0)
    assert alpha['state'] == 'holding'
    assert alpha['direction'] is None
    assert alpha['health'] == 5


def test_units_view_says_a_unit_is_moving_and_where(tmp_path):
    # an order is held by the session that gave it until the turn resolves,
    # so the view is taken there rather than from a reloaded game
    client = a_game(tmp_path).session(1)
    games.order_move(client, Move(unit='alpha', direction=UnitType.EAST))

    entries = views.units_view(client.getBoard())

    alpha = [entry for entry in entries if entry['name'] == 'alpha'][0]
    assert alpha['state'] == 'moving'
    assert alpha['direction'] == 'east'


def test_units_view_gives_a_destroyed_unit_no_position(tmp_path):
    harness = a_game(tmp_path)
    board = harness.session(0).getBoard()
    board.getUnitByName('alpha')[0].setDestroyed(True)

    entries = views.units_view(board)

    alpha = [entry for entry in entries if entry['name'] == 'alpha'][0]
    assert alpha['state'] == 'destroyed'
    assert alpha['x'] is None and alpha['y'] is None
    assert alpha['direction'] is None


def test_units_view_gives_an_undeployed_unit_no_position():
    # a unit waiting to be deployed holds the square it asked for and is not
    # standing on it yet, which is the board's own state rather than one a
    # session keeps for long: `deploy unit` resolves it at once
    board = Board(4, 4)
    board.add(Player(1), 1, 1, 'alpha', UnitType('tank', 'T', 3, 5, 10))

    entries = views.units_view(board)

    assert entries[0]['state'] == 'waiting'
    assert entries[0]['x'] is None and entries[0]['y'] is None


def test_players_view_marks_the_eliminated(tmp_path):
    session = a_game(tmp_path).session(0)

    entries = views.players_view(session.getPlayers(), eliminated=(2,))

    assert entries == [{'player': 1, 'status': 'active'},
                       {'player': 2, 'status': 'eliminated'}]


def test_pending_view_names_the_order_each_unit_holds(tmp_path):
    harness = a_game(tmp_path)
    harness.order(1, [('alpha', UnitType.NORTH)])

    entries = views.pending_view(harness.session(0).getPlayers())

    ordered = [entry for entry in entries if entry['unit'] == 'alpha'][0]
    assert ordered['player'] == 1
    assert ordered['order'] == 'move north'


def test_pending_view_is_empty_before_anyone_orders(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])

    assert views.pending_view(harness.session(0).getPlayers()) == []


def test_board_view_holds_the_squares_and_a_legend(tmp_path):
    session = a_game(tmp_path).session(0)

    view = views.board_view(session.getBoard())

    assert (view['size_x'], view['size_y']) == (4, 4)
    assert len(view['rows']) == 4 and len(view['rows'][0]) == 4
    assert view['rows'][0][0] == 'T'
    assert view['rows'][3][3] == 'S'
    assert view['rows'][0][1] == '#'
    assert view['legend'] == [
        {'symbol': 'S', 'player': 2, 'type': 'scout'},
        {'symbol': 'T', 'player': 1, 'type': 'tank'}]


def test_board_view_of_an_empty_board_has_no_legend(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(3, 3, [1])

    view = views.board_view(harness.session(0).getBoard())

    assert view['legend'] == []
    assert view['rows'] == [['#'] * 3] * 3


def test_types_view_is_empty_before_a_type_is_defined(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(3, 3, [1])
    session = harness.session(0)

    assert views.types_view(session.getPlayers()) == []
    assert views.units_view(session.getBoard()) == []
