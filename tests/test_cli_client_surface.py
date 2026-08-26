"""Characterisation of the player client command surface.

One test per scenario in `openspec/specs/player-client/spec.md`. See
`test_cli_server_surface.py` for why these exist and what `expectedFailure`
means here.
"""

import unittest

from cli_harness import CliTestCase, CLIENT_PROMPT


class ClientTestCase(CliTestCase):
    """A client attached to a game that is already set up."""

    def player_client(self, players=(1,), player=1):
        self.server = self.established_game(players=players)
        client = self.start_client('test-01', player)
        client.read_until(CLIENT_PROMPT)
        return client

    def with_a_unit(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        return client

    def in_play(self):
        """Past setup: the player has committed and the turn has resolved."""
        client = self.with_a_unit()
        client.send_line('commit')
        client.read_until('commit complete')
        # the sole player's commit satisfies the barrier and the server
        # signals the client, so this returns as soon as the turn is resolved
        client.read_until_count(CLIENT_PROMPT, 4, timeout=60)
        return client


class ClientInvocation(CliTestCase):

    def test_starting_a_client(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)

    def test_wrong_arguments(self):
        client = self.start_client_with_args(['test-01'])
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('bgcclient <gameno> <player_number>', client.errors)

    def test_unknown_game(self):
        client = self.start_client('no-such-game', 1)
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('No game with path', client.errors)

    def test_console_script_entry_point(self):
        # the generated console script calls main() with no arguments at all
        client = self.start_entry_point('client')
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('bgcclient <gameno> <player_number>', client.errors)
        self.assertNotIn('TypeError', client.errors)


class ClientCommandLoop(ClientTestCase):

    def test_blank_input(self):
        client = self.player_client()
        client.send_line('')
        client.read_until_count(CLIENT_PROMPT, 2)
        self.assertNotIn('invalid', client.since(CLIENT_PROMPT))

    def test_unrecognised_command(self):
        client = self.player_client()
        client.send_line('wibble')
        client.read_until('invalid command')

    def test_help_lists_commands(self):
        client = self.player_client()
        client.send_line('help')
        client.read_until('commit')
        for command in ('add type', 'add unit', 'show board', 'show types',
                        'show units', 'move', 'exit'):
            self.assertIn(command, client.output)

    def test_exit_ends_the_session(self):
        client = self.player_client()
        client.send_line('exit')
        self.assertEqual(0, client.wait_for_exit())


class DefiningUnitTypes(ClientTestCase):

    def test_defining_a_type(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        lines = self.shown_table(client, CLIENT_PROMPT, 'types')
        assert lines[1].split() == ['1', 'Cross', 'X', '1', '1', '10', '12']

    def test_wrong_argument_count(self):
        client = self.player_client()
        client.send_line('add type')
        client.read_until('must provide 5 args for type')

    def test_invalid_statistics(self):
        client = self.player_client()
        client.send_line('add type Cross X 99 1 10')
        client.read_until(
            'error adding unit type: attack must be a value from 0 to 10')

    def test_a_wall_needs_both_zeroes(self):
        client = self.player_client()
        client.send_line('add type Half H 0 10 5')
        client.read_until('error adding unit type: a type with no attack must '
                          'have no energy')

    def test_a_type_that_cannot_afford_a_move_is_refused(self):
        client = self.player_client()
        client.send_line('add type Heavy H 3 6 5')
        client.read_until('error adding unit type: a type that can move must '
                          'have at least as much energy as health')

    def test_defining_a_wall(self):
        client = self.player_client()
        client.send_line('add type Wall W 0 10 0')
        client.send_line('show types')
        client.read_until('Wall')

    def test_defining_a_type_after_setup(self):
        client = self.in_play()
        client.send_line('add type Later L 1 1 10')
        client.read_until("can't add types after first turn")


class DeployingUnits(ClientTestCase):

    def test_deploying_a_unit(self):
        client = self.with_a_unit()
        client.send_line('show board')
        client.read_until('X')

    def test_a_deployed_unit_is_drawn(self):
        client = self.with_a_unit()
        client.send_line('show board')
        client.read_until('X')

    def test_wrong_argument_count(self):
        client = self.player_client()
        client.send_line('add unit')
        client.read_until('must provide 4 args for unit')

    def test_unknown_type(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Nope n1 0 0')
        client.read_until('error creating new unit')

    def test_coordinates_outside_the_board(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 9 9')
        client.read_until('are out of bounds for this board')

    def test_deploying_onto_a_cell_the_player_already_holds(self):
        client = self.with_a_unit()
        client.send_line('add unit Cross x2 0 0')
        client.read_until("that square is occupied")
        # the session survives the refusal
        client.send_line('add unit Cross x2 1 1')
        client.read_until_count(CLIENT_PROMPT, 5)

    def test_reusing_a_unit_name(self):
        client = self.with_a_unit()
        client.send_line('add unit Cross x1 2 2')
        client.read_until('error creating new unit')

    def test_deploying_after_setup(self):
        client = self.in_play()
        client.send_line('add unit Cross x9 2 2')
        client.read_until("can't add units after first turn")

    def test_deploying_more_than_the_budget_can_pay_for(self):
        client = self.player_client(players=((1, 30),))
        client.send_line('add type Cross X 1 10 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        # 21 spent of 30, so a second costs more than the 9 that are left
        client.send_line('add unit Cross x2 1 1')
        client.read_until('costs 21 points')
        client.read_until('9 of player 1')
        client.read_until('30-point budget')
        # the session survives the refusal, and the square is still free
        client.send_line('show units')
        client.read_until_count(CLIENT_PROMPT, 5)


class OrderingMovement(ClientTestCase):

    def test_ordering_a_move(self):
        client = self.in_play()
        lines = self.shown(client, CLIENT_PROMPT, 'move x1 north').splitlines()
        # the order is read back as the units table, showing it took
        assert lines[0].split() == [
            'PLAYER', 'NAME', 'TYPE', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY',
            'X', 'Y', 'STATE', 'DIRECTION']
        assert lines[1].split()[-2:] == ['moving', 'north']

    def test_wrong_argument_count(self):
        client = self.player_client()
        client.send_line('move x1')
        client.read_until('must provide 2 args for move')

    def test_moving_before_the_first_turn_resolves(self):
        client = self.player_client()
        client.send_line('move x1 north')
        client.read_until("can't move units until after the first turn is complete")

    def test_moving_a_unit_that_does_not_exist(self):
        client = self.in_play()
        client.send_line('move nosuch north')
        client.read_until('error moving unit')

    def test_invalid_direction(self):
        client = self.in_play()
        client.send_line('move x1 nowhere')
        client.read_until('invalid direction nowhere')


class ClientDisplayCommands(ClientTestCase):

    def test_showing_the_board(self):
        client = self.player_client()
        client.send_line('show board')
        client.read_until('#')

    def test_showing_types(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        lines = self.shown_table(client, CLIENT_PROMPT, 'types')
        assert lines[0].split() == [
            'PLAYER', 'NAME', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY', 'COST']
        assert lines[1].split() == ['1', 'Cross', 'X', '1', '1', '10', '12']

    def test_showing_units(self):
        client = self.with_a_unit()
        lines = self.shown_table(client, CLIENT_PROMPT, 'units')
        assert lines[0].split() == [
            'PLAYER', 'NAME', 'TYPE', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY',
            'X', 'Y', 'STATE', 'DIRECTION']
        assert lines[1].split() == [
            '1', 'x1', 'Cross', 'X', '1', '1', '10', '0', '0', 'holding', '-']

    def test_showing_units_before_any_are_deployed(self):
        client = self.player_client()
        assert self.shown(client, CLIENT_PROMPT, 'show units') == 'no units yet'

    def test_showing_players(self):
        client = self.player_client()
        lines = self.shown_table(client, CLIENT_PROMPT, 'players')
        assert lines[0].split() == [
            'PLAYER', 'STATUS', 'BUDGET', 'SPENT', 'LEFT']
        # a player reads their own points, and a `-` where another player's
        # record was never theirs to read
        assert ['1', 'active', '100', '0', '100'] in [
            line.split() for line in lines[1:]]

    def test_another_players_points_are_not_shown(self):
        client = self.player_client(players=(1, 2), player=1)
        lines = self.shown_table(client, CLIENT_PROMPT, 'players')
        rows = {line.split()[0]: line.split() for line in lines[1:]}
        # player 2's record is not this session's to read, so the three point
        # columns have nothing to put in them
        assert rows['2'][2:] == ['-', '-', '-']

    def test_showing_the_board_with_a_legend(self):
        client = self.with_a_unit()
        lines = self.shown_table(client, CLIENT_PROMPT, 'board')
        assert lines[0].startswith('+-+')
        legend = lines[lines.index('SYMBOL  PLAYER  TYPE'):]
        assert legend[1].split() == ['X', '1', 'Cross']

    def test_showing_a_subject_as_json(self):
        client = self.with_a_unit()
        document = self.shown_json(client, CLIENT_PROMPT, 'units')
        assert document['units'] == [{
            'player': 1, 'name': 'x1', 'type': 'Cross', 'symbol': 'X',
            'attack': 1, 'health': 1, 'energy': 10, 'x': 0, 'y': 0,
            'state': 'holding', 'direction': None}]

    def test_the_json_holds_no_storage_field(self):
        client = self.with_a_unit()
        document = self.shown_json(client, CLIENT_PROMPT, 'units')
        for storage_only in ('type_attack', 'type_health', 'type_energy',
                             'on_board', 'destroyed', 'id'):
            assert storage_only not in document['units'][0]

    def test_the_table_and_the_json_describe_the_same_units(self):
        client = self.with_a_unit()
        rows = self.shown_table(client, CLIENT_PROMPT, 'units')[1:]
        document = self.shown_json(client, CLIENT_PROMPT, 'units')

        assert len(rows) == len(document['units'])
        for row, entry in zip(rows, document['units']):
            cells = row.split()
            assert cells[1] == entry['name']
            assert cells[0] == str(entry['player'])
            assert cells[5] == str(entry['health'])
            assert cells[9] == entry['state']

    def test_the_board_as_json(self):
        client = self.with_a_unit()
        document = self.shown_json(client, CLIENT_PROMPT, 'board')
        board = document['board']
        assert (board['size_x'], board['size_y']) == (4, 4)
        assert board['rows'][0][0] == 'X'
        assert board['legend'] == [
            {'symbol': 'X', 'player': 1, 'type': 'Cross'}]

    def test_a_trailing_word_that_is_not_json(self):
        client = self.player_client()
        assert self.shown(
            client, CLIENT_PROMPT,
            'show units wibble') == 'invalid show command'

    def test_incomplete_show_command(self):
        client = self.player_client()
        client.send_line('show')
        client.read_until('invalid show command')

    def test_unrecognised_show_subject(self):
        client = self.player_client()
        client.send_line('show wibble')
        client.read_until('invalid show command')


class CommittingATurn(ClientTestCase):

    def test_committing(self):
        client = self.with_a_unit()
        client.send_line('commit')
        client.read_until('commit complete')
        client.read_until('waiting for turn to complete...')

    def test_reloading_after_resolution(self):
        client = self.in_play()
        # back at the prompt, taking orders again
        client.send_line('show board')
        client.read_until('X')


class ReportingRejectedOrders(ClientTestCase):

    def test_nothing_was_rejected(self):
        client = self.in_play()
        self.assertNotIn('rejected', client.output)


if __name__ == '__main__':
    unittest.main()
