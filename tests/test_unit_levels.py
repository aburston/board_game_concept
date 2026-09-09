"""What a unit shows of itself: how much energy and health it has left.

Two things are drawn round a unit, and until this they were both drawn in the
owner's colour with one warning state each. The colour said whose the unit
was - which the ring already said, and which the energy arc was painted over
the top of. They now say how much is left, on one scale, and the ring is left
alone to say whose it is.

Read from the source as the interface's tests are, with the arithmetic run
rather than read: where a boundary falls, and whether one thing drawn round a
unit overlaps the next, are questions a grep cannot answer.
"""

import os
import re
import shutil
import subprocess

import pytest


STATIC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'src', 'board_game_concept', 'http', 'static')

NODE = shutil.which('node')


def _static(name):
    with open(os.path.join(STATIC, name), encoding='utf-8') as file:
        return file.read()


def _run(expression):
    """Evaluate an expression against `board.js`'s own constants."""
    source = _static('board.js').replace('export ', '')
    script = (source + '\n'
              + f'console.log(JSON.stringify({expression}));\n')
    done = subprocess.run([NODE, '--input-type=module', '-e', script],
                          capture_output=True, text=True, check=True)
    return eval(done.stdout.strip()  # noqa: S307
                .replace('null', 'None').replace('true', 'True')
                .replace('false', 'False'))


# --- the bands

@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_three_bands():
    assert _run('[band(1), band(0.9), band(0.5), band(0.1), band(0)]') == \
        ['full', 'full', 'low', 'spent', 'spent']


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_a_boundary_belongs_to_the_worse_band():
    """A player deciding whether to commit a unit should not be told it is
    fine when it is on the line.
    """
    assert _run('[band(2/3), band(2/3 + 0.001)]') == ['low', 'full']
    assert _run('[band(1/3), band(1/3 + 0.001)]') == ['spent', 'low']


def test_one_function_serves_both():
    """Energy and health are read on one scale, not two.

    They each had their own comparison against a quarter, written out twice -
    a pair of boundaries that could have drifted apart with nothing to notice.
    """
    source = _static('board.js')
    assert 'class: `energy ${band(share)}`' in source
    assert 'class: `health-left ${band(share)}`' in source
    assert source.count('function band(') == 1
    assert '0.25' not in source, 'the old thresholds should be gone'


def test_the_boundary_is_written_down_once():
    source = _static('board.js')
    body = source[source.index('function band('):]
    body = body[:body.index('\n}')]
    assert '2 / 3' in body and '1 / 3' in body


# --- where the arc is drawn

@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_arc_is_outside_the_ring():
    """The ring says whose a unit is, and an arc along the same line hid it -
    worst on a unit with most of its energy left, which covered most of its
    own ring.
    """
    # the ring is stroked at 2 and the arc at 3, per the stylesheet
    ring_outer, arc_inner = _run('[RING + 1, (RING + 3) - 1.5]')
    assert arc_inner > ring_outer, 'the arc must not touch the ring'


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_arc_clears_the_health_bar():
    """They are the two things drawn round a unit, and they share a square."""
    # the bar runs from y 3 to y 6, so its lower edge is SQUARE/2 - 6 from
    # the centre
    arc_outer, bar_edge = _run('[(RING + 3) + 1.5, SQUARE / 2 - 6]')
    assert arc_outer <= bar_edge


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_arc_stays_inside_its_square():
    arc_outer, half = _run('[(RING + 3) + 1.5, SQUARE / 2]')
    assert arc_outer < half


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_an_ordered_units_arrow_clears_its_own_energy():
    """Started from the ring as it used to be, the arrow was drawn across the
    arc - the same defect the arc had against the ring, one radius further
    out.
    """
    arc_outer, start = _run('[(RING + 3) + 1.5, ARC + 3]')
    assert start > arc_outer
    assert 'const start = ARC + 3;' in _static('board.js'), (
        'written against the arc, so moving the arc moves this with it')


def test_the_arc_is_stroked_at_three():
    """Which is what the clearances above are computed against."""
    sheet = _static('style.css')
    rule = sheet[sheet.index('.board .unit .energy {'):]
    rule = rule[:rule.index('}')]
    assert 'stroke-width: 3' in rule


# --- what the colours mean

def test_the_level_tokens_are_defined_in_both_schemes():
    sheet = _static('style.css')
    dark = sheet[sheet.index('@media (prefers-color-scheme: dark)'):]
    light = sheet[:sheet.index('@media (prefers-color-scheme: dark)')]
    for token in ('--level-full', '--level-low', '--level-spent'):
        assert token in light, f'{token} missing from the light scheme'
        assert token in dark, f'{token} missing from the dark scheme'


def test_a_level_is_not_an_owner():
    """Reusing the owner's colours would make a healthy enemy's bar the same
    green as one of yours - the confusion this change removes from the ring.
    """
    sheet = _static('style.css')
    for selector in ('.energy', '.health-left'):
        rules = re.findall(rf'^[^\n{{}}]*{re.escape(selector)}[^\n{{}}]*'
                           r'\{[^}}]*\}', sheet, re.M)
        assert rules, selector
        for rule in rules:
            for owner in ('--mine', '--theirs', '--warn', '--focus'):
                assert owner not in rule, f'{selector}: {rule}'


def test_each_band_has_a_colour_for_both_things():
    sheet = _static('style.css')
    for thing, prop in (('.energy', 'stroke'), ('.health-left', 'fill')):
        for level, token in (('full', '--level-full'), ('low', '--level-low'),
                             ('spent', '--level-spent')):
            assert re.search(rf'{re.escape(thing)}\.{level} '
                             rf'\{{ {prop}: var\({token}\); \}}', sheet), \
                f'{thing}.{level}'


def test_the_ring_still_says_whose_the_unit_is():
    """What ownership falls back to, now the arc and the bar have stopped
    saying it - and both are more legible than before, the ring most of all.
    """
    sheet = _static('style.css')
    assert '.board .unit.mine .ring { stroke: var(--mine); }' in sheet
    assert re.search(r'\.board \.unit\.theirs \.ring \{ stroke: '
                     r'var\(--theirs\); stroke-dasharray: [^}]*\}', sheet)
    assert '.board .unit.mine text { fill: var(--mine); }' in sheet
    assert '.board .unit.theirs text { fill: var(--theirs); }' in sheet


def test_an_enemy_is_read_the_same_way():
    """There is no rule that colours a level by whose the unit is, so an
    enemy's energy and health are drawn on the same scale as your own.
    """
    sheet = _static('style.css')
    assert '.unit.theirs .energy' not in sheet
    assert '.unit.theirs .health-left' not in sheet
    assert '.unit.mine .energy' not in sheet
    assert '.unit.mine .health-left' not in sheet


def test_a_watched_board_reads_levels_the_same_way():
    """It colours units by player number, and a level is not a player."""
    sheet = _static('style.css')
    watched = sheet[sheet.index('.board.watching'):]
    assert 'health-left' not in watched, (
        'a watched board should not colour health by player')
    # identity is still carried, by the ring and the glyph
    assert '.board.watching .unit.player-1 .ring' in watched
    assert '.board.watching .unit.player-1 text' in watched


def test_level_is_not_told_by_colour_alone():
    """The length says it too: the arc is a share of a circumference and the
    bar a share of its track.
    """
    source = _static('board.js')
    assert 'stroke-dasharray' in source, 'the arc is a share of its circle'
    assert 'width: Math.max(0, width * share)' in source, (
        'and the bar a share of its track')
