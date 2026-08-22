"""Reading a line as a command.

The parser answers questions about shape - how many arguments, which are
numbers, which words are directions - and nothing about the game, so none of
these tests needs a board, a player or a file.
"""

import pytest

from board_game_concept.cli.parser import ParseError, parse
from board_game_concept.cli import roles
from board_game_concept.service import commands
from board_game_concept.domain import UnitType


def refused(line):
    with pytest.raises(ParseError) as raised:
        parse(line)
    return raised.value.message


class TestBlankAndUnknown:

    def test_a_blank_line_is_no_command(self):
        assert parse('') is None
        assert parse('   ') is None

    def test_an_unknown_verb_is_refused(self):
        assert refused('wibble') == 'invalid command'
        assert refused('wibble with arguments') == 'invalid command'

    @pytest.mark.parametrize('line', [
        'add_player 1', 'add_unit Cross x1 0 0', 'set_board 4 4',
        'add_type Cross X 1 1 10', 'integer 1', 'subject show'])
    def test_the_parser_own_methods_are_not_verbs(self, line):
        # the verb used to be turned into a method name and looked up, so
        # every helper was reachable as a command the grammar does not contain
        assert refused(line) == 'invalid command'


class TestBareCommands:

    @pytest.mark.parametrize('line,expected', [
        ('help', commands.Help()),
        ('exit', commands.Exit()),
        ('reload', commands.Reload()),
        ('commit', commands.Commit()),
    ])
    def test_bare_commands(self, line, expected):
        assert parse(line) == expected


class TestShow:

    @pytest.mark.parametrize('subject', ['board', 'types', 'units', 'players', 'pending'])
    def test_every_subject(self, subject):
        assert parse(f'show {subject}') == commands.Show(subject=subject)

    def test_without_a_subject(self):
        assert refused('show') == 'invalid show command'

    def test_with_an_unknown_subject(self):
        assert refused('show wibble') == 'invalid show command'


class TestSetBoard:

    def test_two_dimensions(self):
        assert parse('set board 4 5') == commands.SetBoard(size_x=4, size_y=5)

    def test_without_a_subject(self):
        assert refused('set') == 'invalid set command'

    def test_with_an_unknown_subject(self):
        assert refused('set wibble 1 2') == 'invalid set command'

    @pytest.mark.parametrize('line', ['set board', 'set board 4', 'set board 4 5 6'])
    def test_wrong_number_of_dimensions(self, line):
        assert refused(line) == 'must provide x and y for size'

    @pytest.mark.parametrize('line', ['set board a b', 'set board 4 b'])
    def test_dimensions_that_are_not_numbers(self, line):
        assert refused(line) == 'x and y must be a numbers'


class TestAdd:

    def test_without_a_subject(self):
        assert refused('add') == 'invalid add command'

    def test_with_an_unknown_subject(self):
        assert refused('add wibble 1') == 'invalid add command'

    def test_a_player(self):
        assert parse('add player 2') == commands.AddPlayer(number=2)

    @pytest.mark.parametrize('line', ['add player', 'add player 1 2'])
    def test_a_player_with_the_wrong_arguments(self, line):
        assert refused(line) == 'must provide 1 arg for player'

    def test_a_player_that_is_not_a_number(self):
        assert refused('add player two') == 'player number must be a number'

    def test_a_type(self):
        assert parse('add type Cross X 1 2 10') == commands.AddType(
            name='Cross', symbol='X', attack=1, health=2, energy=10)

    @pytest.mark.parametrize('line', ['add type', 'add type Cross X 1 2',
                                      'add type Cross X 1 2 10 11'])
    def test_a_type_with_the_wrong_arguments(self, line):
        assert refused(line) == 'must provide 5 args for type'

    def test_a_type_whose_statistics_are_not_numbers(self):
        assert refused('add type Cross X a 2 10') == (
            'attack, health and energy must be numbers')

    def test_a_unit(self):
        assert parse('add unit Cross x1 0 3') == commands.AddUnit(
            type_name='Cross', name='x1', x=0, y=3)

    @pytest.mark.parametrize('line', ['add unit', 'add unit Cross x1 0',
                                      'add unit Cross x1 0 3 4'])
    def test_a_unit_with_the_wrong_arguments(self, line):
        assert refused(line) == 'must provide 4 args for unit'

    def test_a_unit_whose_coordinates_are_not_numbers(self):
        assert refused('add unit Cross x1 a 3') == 'x and y must be numbers'


class TestLoad:

    def test_without_a_subject(self):
        assert refused('load') == 'invalid load command'

    def test_with_an_unknown_subject(self):
        assert refused('load wibble file.yaml') == 'invalid load command'

    def test_a_board(self):
        assert parse('load board board.yaml') == commands.LoadBoard(
            path='board.yaml')

    def test_a_player(self):
        assert parse('load player player_1.yaml') == commands.LoadPlayer(
            path='player_1.yaml')

    @pytest.mark.parametrize('line,subject', [
        ('load board', 'board'), ('load player', 'player'),
        ('load board a b', 'board')])
    def test_with_the_wrong_arguments(self, line, subject):
        assert refused(line) == f'must provide 1 args for load {subject}'


class TestMove:

    @pytest.mark.parametrize('word,direction', [
        ('north', UnitType.NORTH), ('east', UnitType.EAST),
        ('south', UnitType.SOUTH), ('west', UnitType.WEST)])
    def test_every_direction(self, word, direction):
        assert parse(f'move x1 {word}') == commands.Move(
            unit='x1', direction=direction)

    @pytest.mark.parametrize('line', ['move', 'move x1', 'move x1 north east'])
    def test_with_the_wrong_arguments(self, line):
        assert refused(line) == 'must provide 2 args for move'

    def test_an_unknown_direction(self):
        assert refused('move x1 nowhere') == 'invalid direction nowhere'


class TestRoles:

    def test_the_server_may_size_the_board_and_the_others_may_not(self):
        command = parse('set board 4 4')
        assert roles.SERVER.allows(command)
        assert not roles.CLIENT.allows(command)
        assert not roles.OBSERVER.allows(command)

    @pytest.mark.parametrize('line', [
        'add type Cross X 1 1 10', 'add unit Cross x1 0 0',
        'move x1 north', 'commit', 'set board 4 4', 'load player p.yaml'])
    def test_the_observer_holds_nothing_that_writes(self, line):
        command = parse(line)
        assert not roles.OBSERVER.allows(command)
        assert roles.OBSERVER.refusal(command) == 'invalid command'

    def test_the_client_has_no_pending_orders_to_show(self):
        command = parse('show pending')
        assert not roles.CLIENT.allows(command)
        assert roles.CLIENT.refusal(command) == 'invalid show command'
        assert roles.SERVER.allows(command)
        assert roles.OBSERVER.allows(command)

    def test_only_the_observer_reloads(self):
        command = parse('reload')
        assert roles.OBSERVER.allows(command)
        assert not roles.SERVER.allows(command)
        assert not roles.CLIENT.allows(command)


class TestTheTreeIsWalkable:

    def test_a_command_is_visited_by_its_kind(self):
        seen = []

        class Recorder(commands.Visitor):
            def visit_add_unit(self, node):
                seen.append((node.type_name, node.x, node.y))

            def generic_visit(self, node):
                seen.append(node.kind)

        Recorder().visit(parse('add unit Cross x1 1 2'))
        Recorder().visit(parse('commit'))
        assert seen == [('Cross', 1, 2), 'commit']

    def test_a_command_names_what_it_is_missing(self):
        with pytest.raises(TypeError, match='size_y'):
            commands.SetBoard(size_x=4)
