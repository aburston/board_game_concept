"""A blank square, and every printable character left to the players.

An empty square used to be drawn as `#`, which spent a printable character on
nothing: a type designed with that symbol was invisible among the squares
holding nothing at all. The board draws a blank there now, so `#` is a symbol
like any other - and the one character a symbol may not be is a blank, which
is the rule these hold to from each direction a type can be defined from.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from conftest import make_admin, token_for                   # noqa: E402
from game_harness import DEFAULT_BACKEND, GameHarness        # noqa: E402
from board_game_concept import (Game, UnitType,              # noqa: E402
                                YamlGameRepository)
from board_game_concept.cli import views                     # noqa: E402
from board_game_concept.cli.render import (print_board_view,  # noqa: E402
                                           render_board)
from board_game_concept.cli.parser import ParseError, parse  # noqa: E402
from board_game_concept.http.app import create_app           # noqa: E402
from board_game_concept.service.errors import UnreadableGame  # noqa: E402


def a_board_with(tmp_path, symbol):
    """One player, one type of that symbol, one unit of it at the origin."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    harness.deploy(1, [('marker', symbol, 3, 5, 10)],
                   [('marker', 'alpha', 0, 0)])
    harness.resolve()
    return harness.session(0).getBoard()


# --- a hash is an ordinary symbol


def test_a_type_may_be_designed_with_a_hash():
    designed = UnitType('Hash', '#', 3, 5, 10)
    assert designed.symbol == '#'
    assert str(designed) == '#'


def test_a_hash_unit_is_drawn_as_itself_among_blank_squares(tmp_path):
    drawn = render_board(a_board_with(tmp_path, '#')).splitlines()

    assert drawn[1] == '|#| | | |', 'the unit, and nothing else, is drawn'
    assert drawn[3] == '| | | | |'


def test_a_hash_unit_is_named_in_the_legend_as_its_type(tmp_path, capsys):
    print_board_view(views.board_view(a_board_with(tmp_path, '#')))

    printed = capsys.readouterr().out.splitlines()
    # the legend follows the grid and a blank line, whatever size the grid was
    legend = printed[printed.index('') + 1:]
    assert legend[0].split() == ['SYMBOL', 'PLAYER', 'TYPE']
    assert legend[1].split() == ['#', '1', 'marker']


# --- a blank is not a symbol anybody may have


def test_a_whitespace_symbol_is_refused_at_construction():
    for blank in (' ', '\t', '\n'):
        with pytest.raises(AssertionError) as refused:
            UnitType('Blank', blank, 3, 5, 10)
        assert 'whitespace' in str(refused.value)


def test_a_command_line_cannot_even_express_a_blank_symbol():
    # a line is split on whitespace, so a blank never reaches the symbol slot:
    # the quotes are characters like any other and the arity is what refuses
    with pytest.raises(ParseError):
        parse('add type Blank " " 1 5 10')


def test_a_blank_symbol_is_refused_over_http(tmp_path):
    app = create_app(base_path=str(tmp_path), backend=DEFAULT_BACKEND)
    client = app.test_client()
    headers = {'Authorization': f'Bearer {token_for(app, make_admin(app))}'}
    assert client.post('/games', json={'gameno': 'blank'},
                       headers=headers).status_code == 201
    assert client.post('/games/blank/players/0/commands',
                       json={'kind': 'set_board', 'size_x': 4, 'size_y': 4},
                       headers=headers).status_code == 204

    refused = client.post(
        '/games/blank/players/0/commands',
        json={'kind': 'add_type', 'name': 'Blank', 'symbol': ' ',
              'attack': 1, 'health': 5, 'energy': 10},
        headers=headers)

    assert refused.status_code == 400
    assert 'whitespace' in refused.get_json()['error']


@pytest.mark.backend('yaml')
def test_a_stored_type_with_a_blank_symbol_is_refused(tmp_path):
    # a player file can be written by hand, and a type the rules refuse is a
    # game that cannot be read rather than a unit drawn as an empty square
    repository = YamlGameRepository('one', base_path=str(tmp_path))
    repository.ensure()
    repository.write_board(6, 3)
    repository.write_player(1, {
        'Blank': {'name': 'Blank', 'symbol': ' ',
                  'attack': '3', 'health': '6', 'energy': '10'},
    }, 100)

    with pytest.raises(UnreadableGame) as refused:
        Game(repository, 1).load()
    assert 'Blank' in str(refused.value)
    assert 'whitespace' in str(refused.value)


# --- the blank keeps its column


def test_every_row_of_a_drawn_board_is_the_same_width(tmp_path):
    drawn = [line for line in
             render_board(a_board_with(tmp_path, 'M')).splitlines()
             if line.startswith('|')]

    assert len(drawn) == 4
    assert len({len(row) for row in drawn}) == 1, 'the columns line up'
    assert drawn[0] == '|M| | | |'
    assert all(row == '| | | | |' for row in drawn[1:]), \
        'only the unit reads as anything other than a space'
