"""The page and its modules, served as plain files.

No build step and no package manager: everything under `http/static/` is a
file that is served as it was written. The modules cannot be imported without
a browser, so what is held here is read from their source - and, where a rule
is arithmetic rather than wiring, the function is lifted out and run under
`node`, as the program listing is run against the server's own tariff.
"""

import json
import os
import re
import shutil
import subprocess

import pytest

from board_game_concept.http.app import create_app


STATIC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'src', 'board_game_concept', 'http', 'static')

MODULES = ['app.js', 'api.js', 'board.js', 'lobby.js', 'armoury.js',
           'play.js', 'program.js']

NODE = shutil.which('node')


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


@pytest.mark.skipif(NODE is None, reason='node is not installed')
@pytest.mark.parametrize('name', MODULES)
def test_every_module_parses_as_a_module(name, tmp_path):
    """A syntax error in one module is a blank page, and nothing else here
    would say which."""
    copied = tmp_path / name.replace('.js', '.mjs')
    with open(os.path.join(STATIC, name), encoding='utf-8') as file:
        copied.write_text(file.read())
    done = subprocess.run([NODE, '--check', str(copied)],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


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


def _module(name):
    with open(os.path.join(STATIC, name), encoding='utf-8') as file:
        return file.read()


def _function(source, name):
    """One function's source, by matching its braces.

    The count starts at the body, past the parameter list, so a function
    that destructures its argument is lifted whole.
    """
    start = source.index(f'function {name}(')
    parens = 0
    for body in range(start, len(source)):
        if source[body] == '(':
            parens += 1
        elif source[body] == ')':
            parens -= 1
            if parens == 0:
                break
    depth = 0
    for index in range(body, len(source)):
        if source[index] == '{':
            depth += 1
        elif source[index] == '}':
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(f'{name} has unbalanced braces')


def test_wide_content_scrolls_inside_its_card():
    """The trace table is eight columns and does not fit a narrow phone."""
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
    board = _module('board.js')
    assert re.search(r"class:\s*'hit'", board)
    assert re.search(r"width:\s*SQUARE,\s*height:\s*SQUARE", board)


def test_a_trace_row_chooses_its_unit():
    """The reliable target on a phone, and where somebody is already reading."""
    play = _module('play.js')
    assert "role: 'button'" in play
    assert "row.addEventListener('click', choose)" in play


# --- what a redraw must not throw away
#
# The interface replaces the whole screen from one state object whenever
# anything changes, so a choice held only in the page is lost to the next
# thing the person does. Each of these is a value that has to live in `state`
# for the redraw to find it.


def test_the_state_holds_what_the_armoury_is_half_way_through():
    state = _module('app.js')
    assert 'deployType' in state, 'the type being deployed'
    assert 'boardSize' in state, 'a board size typed and not yet sent'
    assert 'program: null' in state, 'the program being written'
    assert "compute: '0'" in state, 'the fourth statistic of a design'


def test_the_state_holds_where_the_replay_is():
    state = _module('app.js')
    assert re.search(r'replay: \{ turn: null, playing: false, speed: 1, '
                     r'known: false, seat: null,', state)


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


def test_a_units_ring_shows_the_energy_it_has_left():
    board, play = _module('board.js'), _module('play.js')
    # drawn as a share of a circle's circumference, from the top - outside
    # the ring rather than along it, so the ring it is drawn beside is left
    # whole and goes on saying whose the unit is
    assert 'class: `energy ${band(share)}`' in board
    assert 'r: ARC,' in board and 'const ARC = RING + 3;' in board
    assert 'stroke-dasharray' in board
    assert 'energyOf' in board and 'energyOf:' in play
    assert '.unit .energy' in _stylesheet()


def test_the_number_fields_refuse_what_the_domain_would():
    """A negative attack was typed, sent, and refused only by the server."""
    app_js, armoury = _module('app.js'), _module('armoury.js')
    assert 'min' in app_js and 'max' in app_js, 'the field carries limits'
    # the ranges the domain enforces: attack 0-10, health 1-10, energy
    # 0-100, compute 0-10
    assert re.search(r"'attack',\s*\{ min: 0, max: 10 \}", armoury)
    assert re.search(r'\{ min: 1, max: 10 \}', armoury)
    assert re.search(r'\{ min: 0, max: 100 \}', armoury)
    assert re.search(r"'compute',\s*\{ min: 0, max: 10 \}", armoury)


# --- compute, and what a design costs
#
# The cost of a type is the sum of its four statistics, and it is shown as
# they are chosen rather than when the type is defined.


def test_compute_is_chosen_beside_the_other_three_statistics():
    armoury = _module('armoury.js')
    designer = _function(armoury, 'renderDesigner')
    assert "bind('Compute (0–10)', 'number', 'compute'" in designer
    # the cost moves with all four
    assert "Number(compute.input.value || 0)" in designer
    assert 'attack + health + energy + compute' in designer
    # and the four are sent
    assert re.search(r'api\.addType\(\s*name\.input\.value\.trim\(\),'
                     r'[\s\S]*?Number\(compute\.input\.value \|\| 0\)\)',
                     designer)
    assert re.search(r'function costOf\(type\) \{\s*\n\s*return '
                     r'Number\(type\.attack\) \+ Number\(type\.health\) '
                     r'\+ Number\(type\.energy\)\s*\n\s*\+ '
                     r'Number\(type\.compute \|\| 0\);', armoury)


def test_the_types_table_shows_compute_and_whether_there_is_a_program():
    armoury = _module('armoury.js')
    types = _function(armoury, 'renderTypes')
    assert "'Compute'" in types and "'Program'" in types
    # a type with no compute is said to have no controller, rather than
    # shown as a type that forgot its program
    assert "'no controller'" in types


def test_the_designer_says_what_compute_buys():
    armoury = _module('armoury.js')
    designer = _function(armoury, 'renderDesigner')
    assert 'ticks a turn' in designer
    assert 'cost it' in designer and 'one energy' in designer
    assert 'has no controller' in designer


# --- the program editor
#
# A program is written or pasted in the armoury, listed line by line with
# the ticks each line costs, and sent only once every line is accepted.


def test_the_armoury_offers_a_program_editor():
    armoury = _module('armoury.js')
    assert 'function renderProgramEditor' in armoury
    assert 'renderProgramEditor(game)' in _function(armoury, 'renderArmoury')
    editor = _function(armoury, 'renderProgramEditor')
    assert "element('textarea'" in editor
    # read from the server once per type chosen, sent through the command
    # every client sends
    assert 'api.readProgram(' in editor
    assert 'api.setProgram(chosen.name, state.program.text)' in editor


def test_the_editor_lists_each_line_with_its_ticks_as_it_is_typed():
    armoury = _module('armoury.js')
    editor = _function(armoury, 'renderProgramEditor')
    assert 'listing(text, tariff)' in editor
    assert "addEventListener('input'" in editor
    assert "class: 'listing'" in editor
    # the total of a straight run, the ticks an energy buys and the cap
    assert '${total} ticks' in editor
    assert 'is the most a turn may think' in editor
    assert 'cost one energy' in editor
    # a line the set refuses is marked where it stands
    assert "class: wrong ? 'bad' : ''" in editor


def test_a_program_is_not_sent_until_every_line_is_accepted():
    armoury = _module('armoury.js')
    editor = _function(armoury, 'renderProgramEditor')
    assert 'const accepted = bad.size === 0' in editor
    assert "{ class: 'primary', disabled: !accepted }" in editor
    assert 'Fix the marked lines first' in editor
    # the one parser there is has the last word: the text is checked
    # against it, and a line it refuses is marked with its reason
    assert 'api.checkProgram(typed, compute)' in editor
    assert 'programCheck' in editor


def test_a_type_with_no_compute_is_offered_no_program():
    armoury = _module('armoury.js')
    editor = _function(armoury, 'renderProgramEditor')
    assert 'Number(type.compute || 0) > 0' in editor
    assert 'none has a controller to program' in editor


def test_the_tariff_is_the_servers(client):
    """The editor prices a line by the table the server prices it by."""
    from board_game_concept.domain.program import TICKS, TICKS_PER_COMPUTE

    answer = client.get('/_/program').get_json()
    assert answer['ticks'] == TICKS
    assert answer['ticks_per_compute'] == TICKS_PER_COMPUTE
    app_js, api_js = _module('app.js'), _module('api.js')
    assert "get('/_/program')" in api_js
    assert 'state.tariff = await api.programTariff()' in app_js


def _run_listing(text, tariff):
    """Run the shipped `listing` over a program, against a tariff."""
    source = _module('program.js').replace('export function', 'function')
    script = (source + '\n'
              + f'const tariff = {json.dumps(tariff)};\n'
              + f'console.log(JSON.stringify(listing({json.dumps(text)}, '
              + 'tariff)));\n')
    done = subprocess.run([NODE, '-e', script], capture_output=True,
                          text=True, check=True)
    return json.loads(done.stdout)


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_listing_agrees_with_the_server_line_for_line(client):
    """The page's listing and the server's say the same ticks for the same
    program, from the tariff the server exports."""
    from board_game_concept.domain import army

    tariff = client.get('/_/program').get_json()
    for name, record in army.types().items():
        if not record['program']:
            continue
        theirs = client.post('/_/program/check', json={
            'program': record['program'],
            'compute': record['compute']}).get_json()
        assert theirs['ok'] is True, name
        ours = _run_listing(record['program'], tariff)
        assert [(line['line'], line['ticks']) for line in ours] == [
            (line['line'], line['ticks']) for line in theirs['lines']], name
        assert all(line['error'] is None for line in ours), name
    # and a subroutine, priced at a tick each end
    text = 'CALL step\nHALT\nstep: SELF\nRET\n'
    theirs = client.post('/_/program/check', json={
        'program': text, 'compute': 1}).get_json()
    assert theirs['ok'] is True
    ours = _run_listing(text, tariff)
    assert [(line['line'], line['ticks']) for line in ours] == [
        (1, 1), (2, 0), (3, 1), (4, 1)]
    assert [(line['line'], line['ticks']) for line in theirs['lines']] == [
        (1, 1), (2, 0), (3, 1), (4, 1)]


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_listing_marks_a_line_that_is_not_an_instruction(client):
    tariff = client.get('/_/program').get_json()
    listed = _run_listing('SELF\n; a comment\nFLY away\nloop: MOVE north\n',
                          tariff)
    assert [line['ticks'] for line in listed] == [1, None, None, 1]
    assert listed[2]['error'] == 'FLY is not an instruction'
    assert [line['error'] for line in listed if line['line'] != 3] == [
        None, None, None]


# --- the replay
#
# The game is watched as a replay: a scrubber over every turn, play, pause,
# step and speed, the board at each turn drawn from the record.


def test_the_play_screen_is_a_replay():
    play = _module('play.js')
    for control in ('function renderControls', 'async function showTurn',
                    'function stepTurn', 'function play(', 'function pause'):
        assert control in play, control
    controls = _function(play, 'renderControls')
    assert "type: 'range'" in controls, 'the scrubber'
    assert "class: 'speed'" in controls, 'the speed'
    assert "'aria-label': 'play'" in controls
    assert "'aria-label': 'pause'" in controls
    assert "'aria-label': 'previous turn'" in controls
    assert "'aria-label': 'next turn'" in controls


def test_the_board_is_drawn_from_the_record():
    play = _module('play.js')
    assert 'api.readTurn(game.gameno, game.number, wanted,' in play
    board_card = _function(play, 'renderReplayBoard')
    assert 'renderBoard(record.board, units' in board_card
    # and every unit on it: the record shows every seat the whole board
    assert 'unitsOf(record)' in board_card


def test_a_unit_keeps_its_element_so_a_turn_is_seen_as_movement():
    """A change of transform is the animation; the key is what lets the
    browser know which unit moved where."""
    board, sheet = _module('board.js'), _stylesheet()
    assert 'group.dataset.key = `${unit.player}/${unit.name}`' in board
    assert re.search(r'\.board \.unit \{ transition: transform', sheet)
    assert 'prefers-reduced-motion' in sheet


def test_the_replay_opens_at_the_final_turn_with_the_result():
    play = _module('play.js')
    screen = _function(play, 'renderPlay')
    assert 'const wanted = replay.turn === null ? last : replay.turn;' in screen
    assert 'renderOutcome(game, record)' in screen
    outcome = _function(play, 'outcomeText')
    assert 'stopped undecided' in outcome
    assert 'its state repeated' in outcome
    assert 'the turn cap was reached' in outcome
    assert 'nothing happened for fifty turns' in outcome


def test_the_army_knew_toggle_and_whose():
    play = _module('play.js')
    controls = _function(play, 'renderControls')
    assert "id: 'known-toggle'" in controls
    assert 'show what my army knew' in controls
    # the observer and the administrator choose whose knowledge
    assert "'aria-label': 'whose knowledge'" in controls
    assert 'replay.known, seat)' in _function(play, 'showTurn')
    board = _module('board.js')
    assert 'export function knownAt' in board
    assert "class: 'remembered-enemy'" in board, (
        'a remembered enemy is drawn with the turn it was met')
    assert '`t${turn}`' in board
    sheet = _stylesheet()
    assert '.board.known .square.unknown' in sheet


def test_the_trace_panel_shows_what_each_controller_did():
    play = _module('play.js')
    traces = _function(play, 'renderTraces')
    for column in ("'Ticks'", "'Energy'", "'Order'", "'Said'", "'Sleep'",
                   "'Halted'"):
        assert column in traces, column
    assert 'at line ${trace.halted}' in traces
    assert "'woken'" in traces
    # nothing of another seat's thinking
    assert 'Nothing of another seat' in traces
    detail = _function(play, 'renderTraceDetail')
    assert 'halted at line' in detail
    assert 'gave no order' in detail


def test_the_turn_report_is_that_turns_alone():
    play = _module('play.js')
    report = _function(play, 'renderTurnReport')
    assert 'record.rejected' in report
    assert 'record.events' in report
    assert 'Orders the turn would not carry out' in report
    # nothing of an earlier turn is shown with it
    assert 'state.events' not in report
    assert 'showHistory' not in play


def test_waiting_says_whose_setups_are_to_come_and_moves_on_by_itself():
    play = _module('play.js')
    waiting = _function(play, 'renderWaiting')
    assert 'to commit a setup' in waiting
    assert 'Your setup is committed' in waiting
    assert 'replay opens here of its own accord' in waiting
    watch = _function(play, 'watch')
    assert 'api.waitForTurn(' in watch
    assert 'state.game.outcome' in watch, 'read until the outcome is there'
    assert 'api.waitForCommit(' in watch


def test_the_eliminated_player_is_told_when_the_replay_reaches_that_turn():
    play = _module('play.js')
    assert 'isOutAt(record, game.number)' in _function(play, 'renderPlay')
    out = _function(play, 'renderOut')
    assert 'Your flag has fallen by this turn' in out
    assert 'still yours to watch' in out


# --- nothing is ordered
#
# A player gives no orders; their units' controllers do. The box, the
# double-click, the compass, the order arrows and the ordering keyboard went
# with the orders, and nothing in the page builds a move.


def test_nothing_in_the_page_orders_a_unit():
    api_js, play, board = _module('api.js'), _module('play.js'), _module('board.js')
    for gone in ("kind: 'move'", "kind: 'hold'", 'api.move(', 'api.hold('):
        assert gone not in api_js + play + board, gone
    for gone in ('orderGroup', 'holdGroup', 'directionForGroup',
                 'renderDirections', 'renderOrders', 'committedHeadings'):
        assert gone not in play, gone
    for gone in ('makeBoxable', 'onBox', 'orderArrow', 'onSquareDouble',
                 'onUnitDouble', 'makeClickable', 'CLICK_DELAY',
                 'selection-box', "'dblclick'"):
        assert gone not in board, gone
    sheet = _stylesheet()
    for gone in ('.compass', '.selection-box', '.order .outline', '--order',
                 '.boxable'):
        assert gone not in sheet, gone


def test_a_click_on_a_unit_in_the_replay_shows_its_trace():
    play = _module('play.js')
    board_card = _function(play, 'renderReplayBoard')
    assert 'anyUnit: true' in board_card
    assert re.search(r"onUnit: \(unit\) => \{[\s\S]*?set\(\{ selected:",
                     board_card)
    hint = _function(_module('board.js'), 'describeUnit')
    assert 'to read what its' in hint and 'controller did this turn' in hint


# --- dragging, kept for deploying and nowhere else


def test_a_unit_is_dragged_with_pointer_events():
    """`dragstart` does not fire for touch, which is the device this is for."""
    board = _module('board.js')
    assert 'function makeDraggable' in board
    for handler in ('pointerdown', 'pointermove', 'pointerup', 'pointercancel'):
        assert f"addEventListener('{handler}'" in board, handler
    assert 'setPointerCapture' in board
    assert 'dragstart' not in board, 'HTML5 drag-and-drop has no touch'
    assert 'getScreenCTM' in board and 'matrixTransform' in board
    assert re.search(r'Math\.floor\(\(here\.x - PAD\) / SQUARE\)', board)


def test_a_short_movement_is_still_a_click():
    board = _module('board.js')
    assert 'const DRAG_THRESHOLD' in board
    assert re.search(r'Math\.hypot\(dx, dy\) < DRAG_THRESHOLD', board)
    assert re.search(r"addEventListener\('click',[\s\S]*?"
                     r"\{ capture: true, once: true \}", board)


def test_a_finger_dragging_a_unit_does_not_scroll_the_page():
    sheet = _stylesheet()
    assert re.search(r'\.board \.unit\.draggable\s*\{[^}]*touch-action:\s*none',
                     sheet)
    assert re.search(r'\.board \.unit\.draggable\s*\{[^}]*user-select:\s*none',
                     sheet)
    assert re.search(r'\.board \.unit\.dragging\s*\{[^}]*transition:\s*none',
                     sheet)


def test_dragging_is_offered_only_where_deploying_is():
    """The replay board hands the drop to nobody."""
    armoury, play, board = (_module('armoury.js'), _module('play.js'),
                            _module('board.js'))
    assert 'onDrop: replace' in armoury
    assert 'onDrop' not in play
    assert 'settings.onDrop && own' in board


def test_dragging_a_deployed_unit_re_places_it():
    armoury = _module('armoury.js')
    replace = armoury[armoury.index('const replace = async'):
                      armoury.index('card.append(renderBoard(')]
    assert 'placeable && !placeable.includes(y)' in replace
    assert 'is already on' in replace
    assert replace.index('api.removeUnit(unit.name)') < replace.index(
        'api.addUnit(unit.type, unit.name, x, y)')
    assert 'api.addUnit(unit.type, unit.name, unit.x, unit.y)' in replace
    assert 'is no longer deployed' in replace
    assert replace.count('api.setFlag(unit.name)') == 2


def test_the_deploy_board_greys_where_a_seat_may_not_place():
    app_js, armoury, board = (_module('app.js'), _module('armoury.js'),
                              _module('board.js'))
    assert "'placement'" in app_js
    assert 'placement' in armoury and 'placeable' in armoury
    assert 'out-of-play' in board
    assert re.search(r'settings\.onSquare && !isOutOfPlay', board)
    assert '.square.out-of-play' in _stylesheet()


def test_the_armoury_offers_to_take_a_deployed_unit_back():
    armoury = _module('armoury.js')
    assert 'renderDeployed' in armoury
    assert 'api.removeUnit(' in armoury
    assert 'take back' in armoury
    assert 'onSquare: async (x, y)' in armoury, 'click to place'
    assert 'onUnit: takeBack' in armoury, 'click to take back'


def test_the_armoury_clears_a_whole_deployment():
    armoury = _module('armoury.js')
    assert 'function clearBoard' in armoury
    clear = armoury[armoury.index('async function clearBoard'):
                    armoury.index('function renderFlag')]
    assert 'window.confirm' in clear
    assert 'api.removeUnit(unit.name)' in clear
    assert clear.count('await loadSeat(') == 1
    assert 'refusal =' in clear and 'break;' in clear


def test_the_armoury_offers_nothing_to_a_seat_whose_setup_is_over():
    armoury = _module('armoury.js')
    assert 'game.new_game === false || game.unprocessed_moves' in armoury


# --- committing is final, and is said to be


def test_a_commit_is_confirmed_and_says_the_game_plays_out_from_it():
    armoury = _module('armoury.js')
    commit = _function(armoury, 'renderCommit')
    assert 'window.confirm' in commit
    assert 'cannot be withdrawn or amended' in commit
    assert 'plays out' in commit or 'played out' in commit


# --- the board and the trays take turns


def test_which_pane_is_shown_is_held_in_the_state():
    app_js, play = _module('app.js'), _module('play.js')
    assert "pane: 'board'" in app_js
    switch = _function(play, 'renderPaneSwitch')
    assert "set({ pane })" in switch
    assert 'Board shown' in switch and 'Traces and forces shown' in switch
    assert "'aria-pressed'" in switch
    assert 'say(' in switch


def test_the_panes_take_turns_only_where_they_do_not_fit():
    sheet = _stylesheet()
    assert '@media (max-width: 44rem)' in sheet
    narrow = sheet[sheet.index('@media (max-width: 44rem)'):
                   sheet.index('@media (max-width: 30rem)')]
    assert '.panes.pane-board > .tray-pane { display: none; }' in narrow
    assert '.panes.pane-trays > .board-pane { display: none; }' in narrow
    assert re.search(r'\.pane-switch-wrap\s*\{\s*display:\s*none;\s*\}', sheet)
    assert '.pane-switch-wrap { display: block' in narrow


# --- the seat number the administrator is offered


def test_a_new_seat_is_offered_the_next_free_number():
    armoury = _module('armoury.js')
    assert 'function nextSeat(registered)' in armoury
    assert re.search(r'let number = 1;\s*\n\s*while \(taken\.has\(number\)',
                     armoury)
    admin = armoury[armoury.index('function renderAdminSetup'):
                    armoury.index('function nextSeat')]
    assert 'String(nextSeat(registered))' in admin
    assert "seatNumber: ''" in _module('app.js')
    assert 'state.seatNumber = number.input.value' in admin


def test_a_new_game_is_offered_the_next_free_number():
    lobby = _module('lobby.js')
    assert 'function nextGameno(games)' in lobby
    create = lobby[lobby.index('function renderCreate'):
                   lobby.index('function mySeats')]
    assert 'String(nextGameno(state.games))' in create
    assert "newGameno: ''" in _module('app.js')


# --- the board's pane holds the board


def test_the_board_is_drawn_at_the_size_of_its_pane():
    sheet = _stylesheet()
    board = re.search(r'\.board \{[^}]*\}', sheet).group(0)
    assert 'width: 100%' in board
    assert 'height: auto' in board
    assert re.search(r'max-height:\s*calc\(100vh', board)
    board_js = _module('board.js')
    assert 'viewBox: `0 0 ${width} ${height}`' in board_js


# --- the keyboard
#
# Every action the interface offers by pointing is reachable without
# pointing: the setup and the replay both.


def test_every_replay_control_has_a_key():
    play = _module('play.js')
    keys = _function(play, 'handleKey')
    for key in ("'ArrowLeft'", "'ArrowRight'", "' '", "'+'", "'-'", "'Home'",
                "'End'", "'k'", "'Enter'", "'Escape'"):
        assert key in keys, key
    # the controls say which key does what, for a hand that is on a mouse
    controls = _function(play, 'renderControls')
    for said in ('(←)', '(→)', '(space)', '(Home)', '(End)', '(+ and -)',
                 '(K)'):
        assert said in controls, said
    help_card = _function(play, 'renderKeys')
    assert 'play and pause' in help_card and 'faster and slower' in help_card


def test_the_editor_and_the_setup_are_reachable_by_keyboard():
    """A textarea, a select and buttons are focusable as they stand; what
    has to hold is that nothing here is reachable by pointing alone."""
    armoury = _module('armoury.js')
    editor = _function(armoury, 'renderProgramEditor')
    assert "element('textarea'" in editor
    assert "id: 'program-text'" in editor
    assert "element('label', { for: 'program-type' }" in editor
    # the deploy board is still placed from the keyboard: choosing a square
    assert 'onSquare: async (x, y)' in armoury
    deploy = _function(armoury, 'renderDeploy')
    assert "element('select'" in deploy


def test_an_arrow_key_on_the_replay_board_orders_nothing():
    """The arrows step through the record; the cursor moves on WASD."""
    play = _module('play.js')
    keys = _function(play, 'handleKey')
    assert 'stepTurn(game, -1)' in keys and 'stepTurn(game, 1)' in keys
    assert "{ w: [0, -1], a: [-1, 0], s: [0, 1], d: [1, 0] }" in keys
    assert 'order' not in keys.replace('orders nothing', '').replace(
        'no\n  // orders', '').replace('orders', '')


def test_the_selection_is_visible_by_more_than_colour():
    board, sheet = _module('board.js'), _stylesheet()
    assert "class: 'selected'" in board
    assert re.search(r'\.board \.selected \{[^}]*stroke-dasharray', sheet)
    assert re.search(r'\.board \.cursor \{[^}]*stroke-width: 3', sheet)
    assert '.traces tbody tr.chosen td:first-child { box-shadow' in sheet
