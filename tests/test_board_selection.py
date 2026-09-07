"""Selecting several units, and ordering them as one.

The interface is served as plain files with no build step, so - exactly as
`test_web_flow.py` does for the contract's words - these read the source the
browser is given and hold it to what the specs say. Where a rule is arithmetic
rather than wiring, it is run instead of read: `directionForGroup` decides
which way a double-click pushes a group, and a test that only grepped for it
would not have noticed it pushing the wrong way.
"""

import os
import re
import shutil
import subprocess

import pytest


STATIC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'src', 'board_game_concept', 'http', 'static')


def _static(name):
    with open(os.path.join(STATIC, name), encoding='utf-8') as file:
        return file.read()


def _function(source, name):
    """One function's source, by matching its braces.

    Enough to lift a pure function out of a module that cannot be imported
    without a browser, so it can be run rather than read.
    """
    start = source.index(f'function {name}(')
    depth = 0
    for index in range(start, len(source)):
        if source[index] == '{':
            depth += 1
        elif source[index] == '}':
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(f'{name} has unbalanced braces')


# --- the selection holds more than one unit

def test_the_selection_is_a_set_of_names():
    """It was one name, and a group cannot be held in one name."""
    assert re.search(r'^\s*selected: \[\],', _static('app.js'), re.M)


def test_the_selection_is_kept_in_name_order():
    """So a group gives its orders in the game's order, not the clicker's."""
    source = _static('play.js')
    body = _function(source, 'selectedUnits')
    assert 'localeCompare' in body, 'the selection should be sorted by name'
    assert 'standing(game)' in body, (
        'a destroyed unit has to fall out of the selection by itself')


def test_the_board_marks_every_selected_unit():
    """A group with one unit outlined disagrees with the order it is given."""
    source = _static('board.js')
    assert 'new Set(settings.selected || [])' in source
    assert 'selected.has(unit.name)' in source


def test_the_orders_tray_marks_every_selected_unit():
    source = _static('play.js')
    assert source.count('state.selected.includes(unit.name)') >= 2, (
        'the row and its aria-pressed both have to read the whole selection')


# --- boxing

def test_the_board_offers_a_box():
    source = _static('board.js')
    assert 'settings.onBox(' in source
    assert "class: 'selection-box'" in source


def test_a_box_takes_more_travel_than_a_drag():
    """A double-click jitters, and a box drawn on that jitter wipes the
    selection the second click was about to order - which is what it did the
    first time this was tried in a browser, with the drag's four units of
    board coordinate standing in for a deliberate movement.
    """
    source = _static('board.js')
    assert 'const BOX_THRESHOLD = SQUARE / 2;' in source
    assert 'const DRAG_THRESHOLD = 4;' in source
    body = _function(source, 'makeBoxable')
    assert 'BOX_THRESHOLD' in body
    assert 'DRAG_THRESHOLD' not in body, (
        'a box and a drag do not travel the same distance')


def test_the_thresholds_are_declared_after_the_square_they_are_measured_in():
    """`BOX_THRESHOLD` is half a square, and a const read before it is
    declared is a dead zone, not a number: the whole board would fail to load.
    """
    source = _static('board.js')
    assert source.index('const SQUARE') < source.index('const BOX_THRESHOLD')


def test_a_box_can_be_anchored_outside_the_board():
    """A group in a corner has no empty square beside it to start from."""
    source = _static('board.js')
    assert 'const grab = settings.onBox ? SQUARE / 2 : 0;' in source
    assert 'viewBox: `${-grab} ${-grab} ' in source, (
        'the margin has to be inside the viewBox to be pressed on')
    assert "class: 'field'" in source, (
        'and something has to be there for the pointer to land on')


def test_the_box_listens_on_the_whole_board():
    """So a press in the margin, or on a flag, begins a box too."""
    body = _function(_static('board.js'), 'makeBoxable')
    assert 'root.addEventListener' in body
    assert 'squares' not in body


def test_a_corner_begun_outside_the_grid_is_the_edge_square():
    body = _function(_static('board.js'), 'makeBoxable')
    corner = body[body.index('const corner ='):body.index('root.addEventListener')]
    assert 'Math.min(Math.max(' in corner, 'clamped rather than refused'


def test_a_press_that_never_travelled_is_a_click():
    """The square's own click listener deals with it."""
    body = _function(_static('board.js'), 'makeBoxable')
    assert 'if (!moved) return;' in body


def test_pressing_the_board_does_not_capture_the_pointer():
    """A captured pointer takes the click with it.

    The browser dispatches the click at the element holding the capture, so
    capturing on the way down delivered every click on the board to the <svg>
    itself and the square under the pointer never heard it - which is why no
    double-click on a square ordered anything at all.
    """
    body = _function(_static('board.js'), 'makeBoxable')
    down = body[body.index("addEventListener('pointerdown'"):
                body.index('const opposite')]
    single = down[down.index('gesture = { id: event.pointerId'):]
    assert 'setPointerCapture' not in single, (
        'a press that may yet be a click must not capture the pointer')


def test_the_capture_is_taken_once_it_is_really_a_box():
    """By then there is no click left to lose."""
    body = _function(_static('board.js'), 'makeBoxable')
    move = body[body.index("addEventListener('pointermove'"):]
    assert 'gesture.moved = true;' in move
    after = move[move.index('gesture.moved = true;'):]
    assert 'root.setPointerCapture(event.pointerId);' in after


def test_a_press_on_a_unit_does_not_start_a_box():
    """Picking a unit up is not also drawing a box round it."""
    body = _function(_static('board.js'), 'makeDraggable')
    assert 'event.stopPropagation();' in body


def test_the_box_takes_only_this_seats_standing_units():
    """An enemy is not something this seat can order."""
    body = _function(_static('play.js'), 'renderBoardCard')
    box = body[body.index('onBox:'):body.index('onDrop:')]
    assert 'standing(game).filter' in box, (
        'the box should filter the seat\'s own standing units')
    assert 'game.units' not in box


def test_the_box_replaces_the_selection():
    body = _function(_static('play.js'), 'renderBoardCard')
    box = body[body.index('onBox:'):body.index('onDrop:')]
    assert 'set({ selected: names })' in box, (
        'a box replaces what was selected rather than adding to it')


def test_the_box_is_offered_only_where_ordering_is():
    """Not watching, not committed, not decided - the same guard as a drop."""
    source = _static('play.js')
    assert 'onBox: !ordering ? null' in source
    assert 'onDrop: !ordering' in source
    assert re.search(r'const ordering = !watching && !game\.outcome\s*'
                     r'&& !isOut\(game\)\s*&& !game\.unprocessed_moves;',
                     source), 'the guard should be asked once and shared'


def test_the_stylesheet_draws_the_box():
    source = _static('style.css')
    rule = source[source.index('.board .selection-box'):]
    rule = rule[:rule.index('}')]
    assert 'pointer-events: none' in rule, (
        'the box would otherwise swallow the release that ends the gesture')
    assert 'var(--focus)' in rule, 'it has to read in both colour schemes'


# --- boxing with a finger

def test_one_finger_still_scrolls_the_board():
    """A board fills a phone's screen; a player has to get past it."""
    assert re.search(r'\.board\.boxable \{ touch-action: pan-x pan-y; \}',
                     _static('style.css'))


def test_only_a_board_that_offers_a_box_gives_up_pinch_zoom():
    """The deploy board has no such gesture, and loses nothing for it."""
    source = _static('board.js')
    assert "+ (settings.onBox ? ' boxable' : '')" in source


def test_two_fingers_draw_a_box():
    body = _function(_static('board.js'), 'makeBoxable')
    assert 'second = { id: event.pointerId' in body, (
        'a second pointer should become the far corner of the box')
    assert 'draw(gesture.from, second.at)' in body


def test_a_pan_the_browser_claims_ends_the_box():
    """Which is what keeps scrolling and boxing from fighting."""
    body = _function(_static('board.js'), 'makeBoxable')
    assert "addEventListener('pointercancel'" in body


# --- one gesture, one outcome

def test_a_single_click_waits_to_see_if_it_is_a_double():
    source = _static('board.js')
    assert 'const CLICK_DELAY = 350;' in source
    body = _function(source, 'makeClickable')
    assert 'setTimeout' in body
    assert 'clearTimeout' in body


def test_the_pair_is_counted_here_rather_than_by_the_browser():
    """The first click redraws the board, so the element the browser would
    fire `dblclick` at is gone before it could.
    """
    source = _static('board.js')
    assert "'dblclick'" not in source, (
        'a redraw between the two clicks loses the browser\'s own event')
    body = _function(source, 'makeClickable')
    assert 'if (timer) {' in body, 'a second click while one is pending'
    assert 'double(event);' in body


def test_a_board_with_no_double_click_does_not_wait():
    """The deploy board places a unit the moment it is asked."""
    body = _function(_static('board.js'), 'makeClickable')
    head = body[:body.index('if (timer)')]
    assert 'if (!double)' in head
    assert 'if (single) single(event);' in head


def test_the_board_hands_the_event_to_the_screen():
    """Whether shift was held is the screen's to interpret, not the board's."""
    source = _static('board.js')
    assert 'settings.onUnit(unit, event)' in source
    assert 'settings.onSquare(x, y, event)' in source
    assert 'shiftKey' not in source, (
        'the board should not know what a selection is')


def test_shift_click_adds_and_takes_out():
    body = _function(_static('play.js'), 'renderBoardCard')
    unit = body[body.index('onUnit:'):body.index('onSquare:')]
    assert 'event.shiftKey' in unit
    assert 'state.selected.includes(unit.name)' in unit
    assert "filter((name) => name !== unit.name)" in unit, 'takes it out'
    assert 'state.selected.concat([unit.name]).sort()' in unit, 'adds it'


def test_a_plain_click_narrows_to_one():
    body = _function(_static('play.js'), 'renderBoardCard')
    unit = body[body.index('onUnit:'):body.index('onSquare:')]
    assert 'set({ selected: [unit.name], cursor })' in unit


def _code(fragment):
    """A handler with its prose stripped, so a comment cannot pass a test."""
    return '\n'.join(line for line in fragment.splitlines()
                     if not line.strip().startswith('//'))


def test_a_single_click_on_a_square_puts_the_selection_down():
    """Clicking away from your own units is how a group is put down.

    It used to be the order itself, and then it was a cursor move that left
    the selection alone. Clearing here is only safe because the single click
    is held to see whether a second is coming.
    """
    body = _function(_static('play.js'), 'renderBoardCard')
    square = body[body.index('onSquare:'):body.index('onSquareDouble:')]
    code = _code(square)
    assert 'set({ selected: [], cursor: { x, y } })' in code
    assert 'order' not in code, 'a single click must not give an order'


def test_a_double_click_is_not_preceded_by_that_clearing():
    """Or every double-click would order a selection its own first click had
    just emptied. The deferral is what makes clicking away safe at all.
    """
    body = _function(_static('board.js'), 'makeClickable')
    code = _code(body)
    # the second click cancels the first before the first has run
    assert code.index('clearTimeout(timer)') < code.index('double(event)')
    assert 'setTimeout' in code


# --- which way a double-click pushes a group

NODE = shutil.which('node')


def _run_direction(cases):
    """Run the shipped `directionForGroup` over a list of cases."""
    source = _function(_static('play.js'), 'directionForGroup')
    script = (
        'const api = { directionByWord: (word) => ({ word }) };\n'
        + source + '\n'
        + 'const out = ' + cases + '.map(([units, x, y]) => {\n'
        + '  const answer = directionForGroup('
        + '    units.map(([ux, uy]) => ({ x: ux, y: uy })), x, y);\n'
        + '  return answer ? answer.word : null;\n'
        + '});\n'
        + 'console.log(JSON.stringify(out));\n')
    done = subprocess.run([NODE, '-e', script], capture_output=True,
                          text=True, check=True)
    return eval(done.stdout.strip().replace('null', 'None'))  # noqa: S307


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_direction_comes_from_the_centre_of_the_group():
    group = '[[0, 4], [2, 4]]'          # centre (1, 4)
    answers = _run_direction(
        f'[[{group}, 7, 4], [{group}, 1, 0], '
        f'[{group}, 1, 9], [{group}, 0, 4]]')
    assert answers == ['east', 'north', 'south', 'west']


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_a_unit_north_of_the_click_is_still_ordered_north():
    """The direction is the group's, not each unit's."""
    # units at y 0 and y 4, centre y 2; a click at y 1 is north of the centre
    answers = _run_direction('[[[[3, 0], [3, 4]], 3, 1]]')
    assert answers == ['north']


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_diagonal_goes_east_or_west_and_always_the_same_way():
    # centre (2, 2); (4, 4) is as far across as it is down, and (0, 0) as far
    # across as it is up
    answers = _run_direction('[[[[2, 2]], 4, 4], [[[2, 2]], 0, 0]]')
    assert answers == ['east', 'west']


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_centre_itself_is_no_direction_at_all():
    answers = _run_direction('[[[[2, 2]], 2, 2], [[[1, 1], [3, 1]], 2, 1]]')
    assert answers == [None, None]


def test_the_middle_of_a_group_is_said_rather_than_ignored():
    body = _function(_static('play.js'), 'renderBoardCard')
    assert 'That is the middle of the group' in body


def test_a_double_click_names_a_direction_not_a_destination():
    """One unit is the case where the group has one member.

    The squares beside a unit are the ones most likely to have something
    standing on them, and moving onto an enemy is how a player attacks - so
    an order that could only name a neighbouring square could not be given
    where it was most wanted.
    """
    body = _function(_static('play.js'), 'renderBoardCard')
    double = body[body.index('onSquareDouble:'):body.index('onUnitDouble:')]
    assert 'directionForGroup(selected, x, y)' in double
    assert 'selected.length === 1' not in double, (
        'one unit and a group take the same path')
    assert 'moves one square at a time' not in double, (
        'the adjacency refusal is gone')


def test_a_unit_that_is_not_yours_is_a_square_like_any_other():
    """Otherwise an enemy swallows every click that lands on it."""
    source = _static('board.js')
    assert 'settings.onSquare(unit.x, unit.y, event)' in source
    assert 'settings.onSquareDouble(unit.x, unit.y, event)' in source


def test_your_own_unit_still_means_itself():
    """A double-click on one of yours takes its orders back."""
    source = _static('board.js')
    assert 'settings.onUnitDouble(unit, event)' in source
    assert re.search(r'if \(\(settings\.onUnit \|\| settings\.onUnitDouble\)'
                     r' && own\) \{', source)


# --- a group order is N ordinary orders

def test_a_group_order_is_one_command_per_unit():
    body = _function(_static('play.js'), 'orderGroup')
    assert 'for (const unit of units)' in body
    assert 'api.move(unit.name, direction.value)' in body


def test_a_group_order_re_reads_the_seat_once():
    """N reloads would redraw the board N times."""
    body = _function(_static('play.js'), 'orderGroup')
    assert body.count('loadSeat(') == 1
    assert body.index('loadSeat(') > body.index('for (const unit of units)'), (
        'the re-read belongs after the loop, not inside it')


def test_a_refused_unit_is_named_and_the_rest_still_stand():
    body = _function(_static('play.js'), 'orderGroup')
    assert 'refused.push(`${unit.name} (${error.message})`)' in body
    assert 'Not ordered:' in body
    assert 'continue' not in body.split('catch')[1].split('}')[0], (
        'a refusal must not abandon the units after it')


def test_ordering_clears_the_selection():
    """Or every arrow key after it would order the same units again."""
    body = _function(_static('play.js'), 'orderGroup')
    assert 'set({ selected: [] })' in body


def test_taking_back_is_the_same_shape():
    body = _function(_static('play.js'), 'holdGroup')
    assert 'api.hold(unit.name)' in body
    assert body.count('loadSeat(') == 1
    assert 'Not taken back:' in body


def test_holding_is_still_a_choice():
    """The centre means "stay where you are" as much as "take that back"."""
    body = _function(_static('play.js'), 'holdGroup')
    assert 'const ordered = units;' in body, (
        'a unit with no order is still allowed to be told to hold')


def test_a_double_click_on_a_unit_acts_on_the_selection():
    """Not on the unit under the pointer.

    A player ordering a move onto another unit is pointing at that unit, so a
    gesture that acted on what lies under it could not give the most ordinary
    order on the board.
    """
    body = _function(_static('play.js'), 'renderBoardCard')
    double = body[body.index('onUnitDouble:'):body.index('onDrop:')]
    assert 'directionForGroup(selected, unit.x, unit.y)' in double
    assert 'orderGroup(game, selected, direction)' in double


def test_no_direction_from_a_double_click_is_a_take_back():
    """The centre of the selection - which, for one unit, is that unit."""
    body = _function(_static('play.js'), 'renderBoardCard')
    double = body[body.index('onUnitDouble:'):body.index('onDrop:')]
    assert 'if (!direction) return holdGroup(game, selected);' in double


def test_with_nothing_selected_a_double_click_takes_that_unit_back():
    """There is no direction to name, so it is all the gesture can mean."""
    body = _function(_static('play.js'), 'renderBoardCard')
    double = body[body.index('onUnitDouble:'):body.index('onDrop:')]
    assert 'if (!selected.length) return holdGroup(game, [unit]);' in double


# --- the compass

def test_the_compass_says_how_many_it_will_order():
    body = _function(_static('play.js'), 'renderDirections')
    assert '${units.length} units selected' in body
    assert 'move all ${units.length} ${direction.word}' in body


def test_the_compass_orders_the_whole_group():
    body = _function(_static('play.js'), 'renderDirections')
    assert 'orderGroup(game, units, direction)' in body
    assert 'holdGroup(game, units)' in body


def test_the_compass_is_shown_for_any_selection():
    body = _function(_static('play.js'), 'renderBoardCard')
    assert 'if (selected.length) card.append(renderDirections(game, selected))' \
        in body


# --- the keyboard

def test_an_arrow_key_orders_the_whole_selection():
    body = _function(_static('play.js'), 'handleKey')
    assert 'orderGroup(game, chosen, direction)' in body


def test_the_take_back_key_takes_the_whole_selection_back():
    body = _function(_static('play.js'), 'handleKey')
    assert 'holdGroup(game, chosen)' in body


def test_no_key_builds_a_group():
    """A selection is built with the pointer only."""
    body = _function(_static('play.js'), 'handleKey')
    assert 'shiftKey' not in body


def test_enter_still_takes_the_unit_under_the_cursor_alone():
    body = _function(_static('play.js'), 'handleKey')
    assert 'set({ selected: here ? [here.name] : [] })' in body


def test_escape_still_clears():
    assert "if (event.key === 'Escape') return set({ selected: [] });" \
        in _static('play.js')


# --- what the player is told

def test_the_help_says_a_move_takes_a_double_click():
    body = _function(_static('play.js'), 'renderKeys')
    assert 'box a group' in body
    assert 'shift-click' in body
    assert 'two fingers draw the ' in body and 'box and one still' in body
    assert 'always acts on the selection, never on whatever is ' in body
    assert 'to move onto it' in body
    assert 'starting outside it ' in body


def test_a_unit_says_how_it_is_grouped():
    body = _function(_static('board.js'), 'describeUnit')
    assert 'Shift-click adds it to a group' in body
    assert 'a direction, not a square' in body
    assert 'it acts on the selection whatever is standing there' in body
    assert 'the selection itself to take its orders back' in body
