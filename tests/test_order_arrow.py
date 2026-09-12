"""The arrow drawn for a unit under orders: a hollow outline, and not far.

As `test_board_selection.py` does, these read the source the browser is given
and hold it to the spec. The geometry is run rather than read: `orderArrow` is
lifted out of `board.js` and drawn against a stub `svg`, so the test can say
where the arrow's tip lands and where it starts, for every heading, without
naming the constants that put it there.
"""

import json
import os
import re
import shutil
import subprocess

import pytest


STATIC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'src', 'board_game_concept', 'http', 'static')

NODE = shutil.which('node')

# the square's own units: `SQUARE` is 44, so its centre is 22 from its edge
# and a quarter of the next square is 11 past that edge
HALF = 22
QUARTER = 11


def _static(name):
    with open(os.path.join(STATIC, name), encoding='utf-8') as file:
        return file.read()


def _function(source, name):
    """One function's source, by matching its braces.

    The count starts at the body, past the parameter list: `orderArrow`
    destructures its argument, and a count that began at the first brace
    would end at the first one to close it, before the body opened.
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


def _constant(source, name):
    """The line that defines a top-level constant, as shipped."""
    match = re.search(rf'^const {name} = .*?;$', source, re.M)
    assert match, f'{name} should be a constant of board.js'
    return match.group(0)


def _draw_arrows():
    """Run the shipped `orderArrow` for each heading.

    Returns, per heading, the list of elements it drew, each as its tag and
    attributes, with the polygon's points parsed to numbers.
    """
    source = _static('board.js')
    script = (
        '\n'.join(_constant(source, name)
                  for name in ('SQUARE', 'RING', 'ARC', 'REACH')) + '\n'
        + 'function svg(tag, attributes) {\n'
        + '  const node = { tag, attributes: attributes || {}, children: [],\n'
        + '                 append(child) { this.children.push(child); } };\n'
        + '  return node;\n'
        + '}\n'
        + _function(source, 'orderArrow') + '\n'
        + 'const headings = { north: { dx: 0, dy: -1 }, east: { dx: 1, dy: 0 },\n'
        + '  south: { dx: 0, dy: 1 }, west: { dx: -1, dy: 0 } };\n'
        + 'const out = {};\n'
        + 'for (const [word, heading] of Object.entries(headings)) {\n'
        + '  const group = orderArrow(heading);\n'
        + '  out[word] = { group: group.attributes, children: group.children\n'
        + '    .map((c) => ({ tag: c.tag, attributes: c.attributes })) };\n'
        + '}\n'
        + 'console.log(JSON.stringify({ ARC, out }));\n')
    done = subprocess.run([NODE, '-e', script], capture_output=True,
                          text=True, check=True)
    return json.loads(done.stdout)


def _points(polygon):
    return [tuple(float(n) for n in pair.split(','))
            for pair in polygon['attributes']['points'].split()]


HEADINGS = {
    'north': (0, -1), 'east': (1, 0), 'south': (0, 1), 'west': (-1, 0),
}


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_arrow_is_one_outlined_shape():
    """Shaft and head together, so there is nothing to fill."""
    drawn = _draw_arrows()
    for word in HEADINGS:
        children = drawn['out'][word]['children']
        assert drawn['out'][word]['group'] == {'class': 'order'}
        assert [c['tag'] for c in children] == ['polygon'], (
            f'{word}: the arrow should be a single polygon, not {children}')
        assert children[0]['attributes']['class'] == 'outline'


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_tip_is_in_the_next_square_but_only_just():
    """Past the edge, so the square it names is unambiguous; within a
    quarter of the next square, so a unit standing there is not drawn over.
    """
    drawn = _draw_arrows()
    for word, (dx, dy) in HEADINGS.items():
        polygon = drawn['out'][word]['children'][0]
        along = [(x - HALF) * dx + (y - HALF) * dy for x, y in _points(polygon)]
        tip = max(along)
        assert tip > HALF, f'{word}: the tip should cross the edge ({tip})'
        assert tip <= HALF + QUARTER, (
            f'{word}: the tip reaches too far into the next square ({tip})')


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_arrow_starts_outside_the_energy_arc():
    """The arc is stroked at 3 around `ARC`, so its outer edge is 1.5 beyond."""
    drawn = _draw_arrows()
    for word, (dx, dy) in HEADINGS.items():
        polygon = drawn['out'][word]['children'][0]
        along = [(x - HALF) * dx + (y - HALF) * dy for x, y in _points(polygon)]
        assert min(along) >= drawn['ARC'] + 1.5, (
            f'{word}: the arrow starts across the energy arc ({min(along)})')


@pytest.mark.skipif(NODE is None, reason='node is not installed')
def test_the_arrow_is_the_same_shape_whichever_way_it_points():
    """Every heading is east turned about the square's centre."""
    drawn = _draw_arrows()
    east = _points(drawn['out']['east']['children'][0])
    turns = {
        'south': lambda x, y: (2 * HALF - y, x),
        'west': lambda x, y: (2 * HALF - x, 2 * HALF - y),
        'north': lambda x, y: (y, 2 * HALF - x),
    }
    def settled(points):
        return [(round(x, 6), round(y, 6)) for x, y in points]

    for word, turn in turns.items():
        drawn_points = _points(drawn['out'][word]['children'][0])
        expected = [turn(x, y) for x, y in east]
        assert settled(drawn_points) == settled(expected), word


def test_the_stylesheet_strokes_the_arrow_and_fills_nothing():
    source = _static('style.css')
    rule = source[source.index('.board .order .outline'):]
    rule = rule[:rule.index('}')]
    assert 'fill: none' in rule, 'the arrow is an outline, not a solid'
    assert 'var(--order)' in rule, 'it has to read in both colour schemes'
    assert 'stroke-linejoin: round' in rule, (
        'the tip is acute and a mitre would spike past it')


def test_the_stylesheet_has_no_solid_arrow_left():
    source = _static('style.css')
    assert not re.search(r'\.board \.order \.(shaft|head)\b', source), (
        'the solid shaft and filled head are gone')
