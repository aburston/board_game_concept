"""How a `show` result sits on the page.

The layout rules are worth their own tests: they are what the three roles all
now depend on, and a column that stops lining up is the kind of thing that is
easy to break and hard to notice.
"""

from board_game_concept.cli.render import print_board_view, table


def columns(line):
    """Where each run of non-space text starts, so alignment can be compared."""
    starts = []
    for index, character in enumerate(line):
        if character != ' ' and (index == 0 or line[index - 1] == ' '):
            starts.append(index)
    return starts


def test_the_header_names_every_column_in_order():
    drawn = table(('ONE', 'TWO'), [['a', 'b']])

    assert drawn.splitlines()[0].split() == ['ONE', 'TWO']


def test_columns_line_up_down_the_page():
    drawn = table(
        ('NAME', 'TYPE'),
        [['alpha', 'tank'], ['a-much-longer-name', 'scout']])

    lines = drawn.splitlines()
    assert columns(lines[0]) == columns(lines[1]) == columns(lines[2])


def test_numeric_columns_are_right_aligned():
    drawn = table(('N',), [[3], [10], [100]], numeric=('N',))

    assert drawn.splitlines() == ['  N', '  3', ' 10', '100']


def test_text_columns_are_left_aligned():
    drawn = table(('WORD',), [['a'], ['abcd']])

    assert drawn.splitlines() == ['WORD', 'a', 'abcd']


def test_a_missing_value_reads_as_a_dash():
    drawn = table(('X', 'Y'), [[None, 2]], numeric=('X', 'Y'))

    assert drawn.splitlines()[1].split() == ['-', '2']


def test_no_line_carries_trailing_whitespace():
    drawn = table(
        ('NAME', 'NOTE'),
        [['a-long-name', 'x'], ['b', None]])

    for line in drawn.splitlines():
        assert line == line.rstrip()


def test_a_header_is_as_wide_as_its_widest_value():
    drawn = table(('N', 'WORD'), [['x', 'y']])

    # a one-character column is one character wide, header included
    assert drawn.splitlines()[0] == 'N  WORD'


def test_a_table_of_no_rows_is_just_its_header():
    assert table(('ONE', 'TWO'), []) == 'ONE  TWO'


def test_the_board_prints_its_grid_and_a_legend(capsys):
    print_board_view({
        'size_x': 2, 'size_y': 1,
        'rows': [['T', '#']],
        'legend': [{'symbol': 'T', 'player': 1, 'type': 'tank'}]})

    printed = capsys.readouterr().out.splitlines()
    assert printed[:3] == ['+-+-+', '|T|#|', '+-+-+']
    assert printed[3] == ''
    assert printed[4].split() == ['SYMBOL', 'PLAYER', 'TYPE']
    assert printed[5].split() == ['T', '1', 'tank']


def test_a_board_with_nothing_on_it_gets_no_legend(capsys):
    print_board_view({
        'size_x': 2, 'size_y': 1, 'rows': [['#', '#']], 'legend': []})

    assert capsys.readouterr().out.splitlines() == ['+-+-+', '|#|#|', '+-+-+']
