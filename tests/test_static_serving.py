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


def test_the_ordering_controls_are_in_the_board_pane():
    """Choosing a unit, ordering it and seeing the arrow are one action."""
    play = _module('play.js')
    board_card = play[play.index('function renderBoardCard'):
                      play.index('function reachableFrom')]
    assert 'renderDirections(game' in board_card
    assert 'Choose one of your units to order it.' in board_card


def test_a_units_ring_shows_the_energy_it_has_left():
    board, play = _module('board.js'), _module('play.js')
    # drawn as a share of the ring's circumference, from the top
    assert "class: 'energy'" in board or "'energy'" in board
    assert 'stroke-dasharray' in board
    assert 'energyOf' in board and 'energyOf:' in play
    # and an enemy design nobody has met is not drawn as a proportion
    assert 'designOf' in play
    assert '.unit .energy' in _stylesheet()


def test_the_number_fields_refuse_what_the_domain_would():
    """A negative attack was typed, sent, and refused only by the server."""
    app_js, armoury = _module('app.js'), _module('armoury.js')
    assert 'min' in app_js and 'max' in app_js, 'the field carries limits'
    # the ranges the domain enforces: attack 0-10, health 1-10, energy 0-100
    assert re.search(r'\{ min: 0, max: 10 \}', armoury)
    assert re.search(r'\{ min: 1, max: 10 \}', armoury)
    assert re.search(r'\{ min: 0, max: 100 \}', armoury)


def test_an_order_can_be_taken_back_from_the_board():
    """Nothing is final until the turn is committed, the keyboard included."""
    play = _module('play.js')
    assert 'clearOrder' in play
    assert 'api.hold(' in play
    assert "event.key === 'Backspace' || event.key === 'Delete'" in play
    # and the centre of the compass, for a hand on a mouse
    assert "class: 'point hold'" in play.replace("'point hold' +", "'point hold'")


def test_the_five_orders_are_laid_out_as_a_compass():
    """Four headings around a centre that means stay where you are."""
    play, sheet = _module('play.js'), _stylesheet()
    # placed in the shape of what they do, and named for a reader that
    # cannot see an arrow
    assert 'at.north' in play and 'at.south' in play
    assert 'at.west' in play and 'at.east' in play
    assert "'aria-label': `move ${direction.word}`" in play
    assert re.search(r'\.compass\s*\{[^}]*grid-template-columns', sheet)
    assert '.compass .point.hold' in sheet


def test_the_armoury_offers_to_take_a_deployed_unit_back():
    armoury = _module('armoury.js')
    assert 'renderDeployed' in armoury
    assert 'api.removeUnit(' in armoury
    assert 'take back' in armoury


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


# --- what the orders tray withheld
#
# The tray is the table a player reads while deciding what to do, and two of
# the numbers the decision turns on were not in it: what a unit hits for, and
# how much of its energy is left of what it was built with.


def test_the_tray_shows_energy_against_what_the_type_was_built_with():
    """`3/5` rather than `3`, the way health is already shown beside it."""
    play = _module('play.js')
    assert 'function energy(game, unit)' in play
    # read off the design rather than restated, as `health` reads the type
    assert re.search(r'function energy\(game, unit\)\s*\{\s*\n'
                     r'\s*const design = designOf\(game, unit\);', play)
    assert '`${now}/${full}`' in play
    tray = play[play.index('function renderOrders'):
                play.index('function renderBarrier')]
    assert 'energy(game, unit)' in tray, 'the tray goes through the helper'
    assert 'String(unit.energy)' not in tray, 'and not round it'
    assert '.power.spent' in _stylesheet()


def test_the_tray_shows_what_a_unit_hits_for():
    """Half of every decision to order a unit at an enemy."""
    play = _module('play.js')
    tray = play[play.index('function renderOrders'):
                play.index('function renderBarrier')]
    assert "element('th', { class: 'number' }, 'Atk')" in tray
    assert "String(unit.attack)" in tray


# --- committing where the orders were given


def test_the_board_pane_offers_the_commit_too():
    """The last order and the commit that publishes it are one thought."""
    play = _module('play.js')
    board_card = play[play.index('function renderBoardCard'):
                      play.index('function reachableFrom')]
    assert 'renderCommit(game)' in board_card
    # one definition, so the confirmation and the call cannot diverge
    assert play.count('function renderCommit') == 1


def test_the_boards_commit_is_the_one_the_c_key_finds():
    """`c` clicks the first primary button, which is the board's."""
    play = _module('play.js')
    assert play.index('function renderBoardCard') < play.index(
        'function renderOrders'), 'the board pane is built first'
    layout = play[play.index('const layout = element'):
                  play.index('wrap.append(layout)')]
    assert layout.index('renderBoardCard') < layout.index('renderOrders'), (
        'and appended before the tray, so it comes first in the document')
    assert "document.querySelector('button.primary')" in play


def test_neither_pane_offers_to_commit_a_turn_already_committed():
    play = _module('play.js')
    commit = play[play.index('function renderCommit'):
                  play.index('// --- waiting for the others')]
    assert 'if (game.unprocessed_moves)' in commit
    assert 'Committed. Waiting for the turn to resolve.' in commit


# --- clearing a setup in one action


def test_the_armoury_clears_a_whole_deployment():
    """One control, one confirmation, and the `remove_unit` it already sends."""
    armoury = _module('armoury.js')
    assert 'function clearBoard' in armoury
    assert 'Clear board' in armoury
    clear = armoury[armoury.index('async function clearBoard'):
                    armoury.index('function renderFlag')]
    # it undoes more than a click usually does, so it asks first
    assert 'window.confirm' in clear
    # built from the command the list already sends, not a new one
    assert 'api.removeUnit(unit.name)' in clear
    # and redrawn once at the end rather than per unit
    assert clear.count('await loadSeat(') == 1


def test_the_clear_is_offered_only_where_there_is_something_to_clear():
    """And never once the setup is committed, where it would be refused."""
    armoury = _module('armoury.js')
    deployed = armoury[armoury.index('function renderDeployed'):
                       armoury.index('async function clearBoard')]
    # the card returns before the control where nothing is deployed
    assert deployed.index('Nothing deployed yet.') < deployed.index(
        'Clear board')
    # and the whole screen is withheld from a committed seat
    assert 'game.new_game === false || game.unprocessed_moves' in armoury


def test_clearing_stops_at_a_refusal_and_says_so():
    armoury = _module('armoury.js')
    clear = armoury[armoury.index('async function clearBoard'):
                    armoury.index('function renderFlag')]
    assert 'refusal =' in clear and 'break;' in clear
    assert 'say(refusal' in clear


# --- picking a unit up
#
# The gesture cannot be performed here - there is no browser in this suite -
# so what is held is that the mechanics a touchscreen depends on are in the
# file: pointer events rather than HTML5 drag-and-drop, a capture, a threshold
# and the geometry that turns a drop into a square.


def test_a_unit_is_dragged_with_pointer_events():
    """`dragstart` does not fire for touch, which is the device this is for."""
    board = _module('board.js')
    assert 'function makeDraggable' in board
    for handler in ('pointerdown', 'pointermove', 'pointerup', 'pointercancel'):
        assert f"addEventListener('{handler}'" in board, handler
    assert 'setPointerCapture' in board
    assert 'dragstart' not in board, 'HTML5 drag-and-drop has no touch'
    # the drop square is mapped through the SVG's own matrix, not by
    # dividing a bounding rectangle by the square size
    assert 'getScreenCTM' in board and 'matrixTransform' in board
    assert re.search(r'Math\.floor\(\(here\.x - PAD\) / SQUARE\)', board)


def test_the_board_decides_nothing_about_where_a_unit_lands():
    """It reports the drop; the screen it is drawn for decides what it means."""
    board = _module('board.js')
    assert 'settings.onDrop(unit, x, y)' in board
    assert 'onDrop' in _module('play.js') and 'onDrop' in _module('armoury.js')


def test_a_short_movement_is_still_a_click():
    """Without a threshold every tap becomes a one-pixel drag."""
    board = _module('board.js')
    assert 'const DRAG_THRESHOLD' in board
    assert re.search(r'Math\.hypot\(dx, dy\) < DRAG_THRESHOLD', board)
    # and the click the browser fires after a real drag is swallowed once,
    # so a dropped unit is not also selected or ordered by it
    assert re.search(r"addEventListener\('click',[\s\S]*?"
                     r"\{ capture: true, once: true \}", board)


def test_a_finger_dragging_a_unit_does_not_scroll_the_page():
    sheet = _stylesheet()
    assert re.search(r'\.board \.unit\.draggable\s*\{[^}]*touch-action:\s*none',
                     sheet)
    assert re.search(r'\.board \.unit\.draggable\s*\{[^}]*user-select:\s*none',
                     sheet)
    # and the transition that animates a turn's moves is off while a hand is
    # holding the unit, or the piece lags the finger by a third of a second
    assert re.search(r'\.board \.unit\.dragging\s*\{[^}]*transition:\s*none',
                     sheet)


def test_dragging_is_offered_only_where_the_action_behind_it_is():
    """The same conditions that withhold the click withhold the drag."""
    play = _module('play.js')
    board_card = play[play.index('function renderBoardCard'):
                      play.index('function reachableFrom')]
    assert re.search(r'onDrop: watching \|\| game\.outcome', board_card)
    assert 'game.unprocessed_moves' in board_card
    # and board.js draws the handles on this seat's own units only
    assert 'settings.onDrop && own' in _module('board.js')


# --- where a dropped unit lands


def test_dropping_a_unit_beside_itself_orders_that_move():
    """A move is one square, so the drop rule is the rule rather than a
    softer version of it."""
    play = _module('play.js')
    board_card = play[play.index('function renderBoardCard'):
                      play.index('function reachableFrom')]
    drop = board_card[board_card.index('onDrop:'):]
    assert 'api.DIRECTIONS.find(' in drop
    assert 'unit.x + option.dx === x && unit.y + option.dy === y' in drop
    assert 'order(game, unit, direction)' in drop
    # and a drop that is not next to the unit changes nothing and says so
    assert 'if (!direction)' in drop
    assert 'moves one square at a time' in drop


def test_dragging_a_deployed_unit_re_places_it():
    armoury = _module('armoury.js')
    replace = armoury[armoury.index('const replace = async'):
                      armoury.index('card.append(renderBoard(')]
    # the square is judged before anything is sent: the seat's own rows, and
    # what is already standing there
    assert 'placeable && !placeable.includes(y)' in replace
    assert 'is already on' in replace
    # then the two decisions it is made of, in that order
    assert replace.index('api.removeUnit(unit.name)') < replace.index(
        'api.addUnit(unit.type, unit.name, x, y)')
    assert 'onDrop: replace' in armoury


def test_a_refused_placement_puts_the_unit_back():
    armoury = _module('armoury.js')
    replace = armoury[armoury.index('const replace = async'):
                      armoury.index('card.append(renderBoard(')]
    assert 'api.addUnit(unit.type, unit.name, unit.x, unit.y)' in replace
    assert 'is no longer deployed' in replace, 'and says so if that fails too'
    # the flag goes with the unit that is taken back, so it is designated again
    assert replace.count('api.setFlag(unit.name)') == 2


def test_every_other_way_of_placing_and_ordering_still_works():
    """The drag is an alternative, not a replacement."""
    armoury, play = _module('armoury.js'), _module('play.js')
    assert 'onSquare: async (x, y)' in armoury, 'click to place'
    assert 'onUnit: takeBack' in armoury, 'click to take back'
    assert 'renderDirections(game' in play, 'the compass'
    assert "row.addEventListener('click', choose)" in play, 'the orders rows'
    assert 'export function handleKey' in play, 'the keyboard'


# --- the board and the trays take turns


def test_which_pane_is_shown_is_held_in_the_state():
    """Read back out of the DOM it would not survive the next redraw."""
    app_js, play = _module('app.js'), _module('play.js')
    assert "pane: 'board'" in app_js
    assert 'function renderPaneSwitch' in play
    switch = play[play.index('function renderPaneSwitch'):
                  play.index('function committedArmy')]
    assert "set({ pane })" in switch
    # it says which pane is being shown, not only what pressing it would do
    assert 'Board shown' in switch and 'Orders and forces shown' in switch
    assert "'aria-pressed'" in switch
    # and says again, out loud, what it switched to
    assert 'say(' in switch


def test_the_panes_take_turns_only_where_they_do_not_fit():
    sheet = _stylesheet()
    assert '@media (max-width: 44rem)' in sheet
    narrow = sheet[sheet.index('@media (max-width: 44rem)'):
                   sheet.index('@media (max-width: 30rem)')]
    assert '.panes.pane-board > .tray-pane { display: none; }' in narrow
    assert '.panes.pane-trays > .board-pane { display: none; }' in narrow
    # above that width the switch is not offered and neither pane is hidden
    assert re.search(r'\.pane-switch-wrap\s*\{\s*display:\s*none;\s*\}', sheet)
    assert '.pane-switch-wrap { display: block' in narrow


def test_giving_an_order_does_not_switch_the_view_back():
    """The choice survives the redraw that every action ends with."""
    play = _module('play.js')
    order = play[play.index('async function order(game, unit, direction)'):
                 play.index('async function clearOrder')]
    assert 'pane' not in order
    # and nothing else in the screen resets it either
    assert play.count('set({ pane })') == 1, 'only the switch sets it'
    assert not re.search(r'state\.pane\s*=[^=]', play), (
        'and nothing writes round `set`')


# --- the seat number the administrator is offered


def test_a_new_seat_is_offered_the_next_free_number():
    """Registering four seats meant typing four numbers the screen knew."""
    armoury = _module('armoury.js')
    assert 'function nextSeat(registered)' in armoury
    # the lowest free number rather than one past the highest, so a seat
    # that was removed leaves no hole in the numbering
    assert re.search(r'let number = 1;\s*\n\s*while \(taken\.has\(number\)',
                     armoury)
    admin = armoury[armoury.index('function renderAdminSetup'):
                    armoury.index('function nextSeat')]
    assert 'String(nextSeat(registered))' in admin
    # and the administrator's own number survives the redraw, as the board
    # size beside it does
    assert "seatNumber: ''" in _module('app.js')
    assert 'state.seatNumber = number.input.value' in admin
    assert re.search(r'\(\) => \{ state\.seatNumber = \'\'; \}', admin), (
        'and the field returns to the next free number once one is taken')
