"""The page and its modules, served as plain files.

No build step and no package manager: everything under `http/static/` is a
file that is served as it was written.
"""

import os
import re

import pytest

from board_game_concept.http.app import create_app


STATIC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'src', 'board_game_concept', 'http', 'static')

MODULES = ['app.js', 'api.js', 'board.js', 'lobby.js', 'armoury.js', 'play.js']


@pytest.fixture(name='client')
def _client(tmp_path):
    return create_app(base_path=str(tmp_path), backend='sqlite').test_client()


def test_the_page_is_served_without_a_credential(client):
    """It is what a person signs in through, so it cannot need one."""
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers['Content-Type']
    assert b'<title>Board Game Concept</title>' in response.data


def test_the_page_holds_no_game_state(client):
    """Everything it draws it fetches through the guarded contract."""
    body = client.get('/').data.decode()
    for leaked in ('units', 'password_hash', 'seats', 'board.rows'):
        assert leaked not in body


@pytest.mark.parametrize('name', MODULES)
def test_each_module_is_served_as_javascript(client, name):
    response = client.get(f'/static/{name}')
    assert response.status_code == 200
    assert 'javascript' in response.headers['Content-Type']


def test_the_stylesheet_is_served(client):
    response = client.get('/static/style.css')
    assert response.status_code == 200
    assert 'text/css' in response.headers['Content-Type']


@pytest.mark.parametrize('path', [
    '/static/../app.py',
    '/static/%2e%2e/app.py',
    '/static/../../../etc/passwd',
    '/static/nothing-here.js',
])
def test_a_path_outside_the_static_directory_is_refused(client, path):
    assert client.get(path).status_code == 404


def test_there_is_no_build_step(client):
    """Nothing under `static/` is generated, and nothing needs installing."""
    names = set(os.listdir(STATIC))
    for artefact in ('node_modules', 'package.json', 'package-lock.json',
                     'dist', 'build', '.cache'):
        assert artefact not in names
    assert names == set(MODULES) | {'index.html', 'style.css'}


def test_every_module_the_page_imports_exists(client):
    """A missing sibling is a blank page, and nothing else would catch it."""
    for name in MODULES + ['index.html']:
        with open(os.path.join(STATIC, name), encoding='utf-8') as file:
            source = file.read()
        for imported in re.findall(r"""from\s+'\./([\w.]+)'""", source):
            assert client.get(f'/static/{imported}').status_code == 200, (
                f'{name} imports {imported}')
        for src in re.findall(r'src="(/static/[\w./]+)"', source):
            assert client.get(src).status_code == 200, f'{name} loads {src}'


def test_the_page_loads_its_entry_module(client):
    body = client.get('/').data.decode()
    assert 'type="module"' in body
    assert '/static/app.js' in body


# --- an address that matches no route

PAGE_PATHS = ['/login', '/play/1/2', '/setup/1/0', '/lobby', '/anything']

API_404_PATHS = ['/accounts/nobody', '/_/nothing', '/games']


@pytest.mark.parametrize('path', PAGE_PATHS)
def test_an_unmatched_address_serves_the_page(client, path):
    """A bare 404 makes a working server look broken.

    Somebody types the host and port, follows a link to a game, or reloads on
    a screen. All of that should land in the application, which then asks them
    to sign in - so it is answered with the page rather than with nothing.
    """
    response = client.get(path)
    assert response.status_code == 200
    assert b'<title>Board Game Concept</title>' in response.data


@pytest.mark.parametrize('path', API_404_PATHS)
def test_an_unmatched_endpoint_is_still_refused_as_json(client, path):
    """A client asking for an endpoint that is not there wants to be told.

    Handing it the page would give it HTML it cannot parse and a 200 it
    should not believe.
    """
    response = client.get(path)
    assert response.status_code in (401, 404)
    assert 'json' in response.headers['Content-Type']


def test_a_caller_that_asked_for_json_gets_json(client):
    response = client.get('/login', headers={'Accept': 'application/json'})
    assert response.status_code == 404
    assert 'json' in response.headers['Content-Type']


def test_a_post_to_nowhere_is_not_answered_with_the_page(client):
    response = client.post('/not-a-route')
    assert response.status_code == 404
    assert b'<title>' not in response.data


def test_the_page_carries_its_own_icon(client):
    """Inline, so a browser asking for one does not miss on every page."""
    body = client.get('/').data.decode()
    assert 'rel="icon"' in body
    assert 'data:image/svg+xml' in body


# --- the phone
#
# The layout itself is not testable here; what is, is that the rules a phone
# depends on are still in the stylesheet. Each of these was added against a
# measurement on a real emulated device, and losing one silently would put a
# 10x10 board back to 29px squares or push the page sideways.

def _stylesheet():
    with open(os.path.join(STATIC, 'style.css'), encoding='utf-8') as file:
        return file.read()


def test_wide_content_scrolls_inside_its_card():
    """The orders table is five columns and does not fit a narrow phone."""
    assert re.search(r'\.card\s*\{[^}]*overflow-x:\s*auto', _stylesheet())


def test_a_narrow_screen_gives_the_board_its_width():
    assert '@media (max-width: 30rem)' in _stylesheet()


def test_touch_gets_targets_a_finger_can_hit():
    sheet = _stylesheet()
    assert '@media (pointer: coarse)' in sheet
    assert re.search(r'min-height:\s*44px', sheet)


def test_the_keyboard_help_is_hidden_where_there_is_no_keyboard():
    """And on `pointer: coarse` alone - the pair with `hover: none` did not
    match under test and left the card on screen."""
    sheet = _stylesheet()
    hidden = re.search(
        r'@media \(pointer: coarse\)\s*\{\s*\.keys\s*\{\s*display:\s*none',
        sheet)
    assert hidden, 'the keyboard help must be hidden on a touch screen'


def test_a_unit_carries_a_tap_target_the_size_of_its_square():
    """The ring is 23px across on a phone; a finger is about 44."""
    with open(os.path.join(STATIC, 'board.js'), encoding='utf-8') as file:
        source = file.read()
    assert re.search(r"class:\s*'hit'", source)
    assert re.search(r"width:\s*SQUARE,\s*height:\s*SQUARE", source)


def test_an_orders_row_chooses_its_unit():
    """The reliable target on a phone, and where somebody is already reading."""
    with open(os.path.join(STATIC, 'play.js'), encoding='utf-8') as file:
        source = file.read()
    assert "role: 'button'" in source
    assert "row.addEventListener('click', choose)" in source


# --- what a redraw must not throw away
#
# The interface replaces the whole screen from one state object whenever
# anything changes, so a choice held only in the page is lost to the next
# thing the person does. Each of these was found by using the armoury, and
# each is a value that has to live in `state` for the redraw to find it.


def _module(name):
    with open(os.path.join(STATIC, name), encoding='utf-8') as file:
        return file.read()


def test_the_state_holds_what_the_armoury_is_half_way_through():
    state = _module('app.js')
    assert 'deployType' in state, 'the type being deployed'
    assert 'boardSize' in state, 'a board size typed and not yet sent'


def test_the_deploy_chooser_is_read_and_written_through_the_state():
    """It went back to the first type after every placement."""
    armoury = _module('armoury.js')
    assert 'chooser.value = state.deployType' in armoury
    assert re.search(r"chooser\.addEventListener\('change'", armoury)


def test_the_board_size_fields_are_read_and_written_through_the_state():
    """Registering a seat emptied a size somebody was still typing."""
    armoury = _module('armoury.js')
    assert 'state.boardSize[key]' in armoury
    assert "made.input.addEventListener('input'" in armoury


def test_the_deploy_board_greys_where_a_seat_may_not_place():
    """The limit is drawn from the contract, not worked out in the browser."""
    app_js, armoury, board = (_module('app.js'), _module('armoury.js'),
                              _module('board.js'))
    # fetched per seat, held in state, and handed to the board as rows
    assert "'placement'" in app_js
    assert 'placement' in armoury and 'placeable' in armoury
    # the squares outside those rows are greyed and take no click
    assert 'out-of-play' in board
    assert re.search(r'settings\.onSquare && !isOutOfPlay', board)
    assert '.square.out-of-play' in _stylesheet()


def test_the_play_screen_keeps_committed_orders_drawn():
    """The board reset to before the orders on commit; it overlays them now."""
    play = _module('play.js')
    assert 'committedHeadings' in play
    # the committed headings are read from the pending view and laid over the
    # units the board draws, so board.js draws the arrows again
    assert 'game.pending' in play
    assert re.search(r"direction:\s*headings\[unit\.name\]", play)


def test_the_armoury_offers_nothing_to_a_seat_whose_setup_is_over():
    """`unprocessed_moves` stops being true the moment the turn resolves."""
    armoury = _module('armoury.js')
    assert 'game.new_game === false || game.unprocessed_moves' in armoury
