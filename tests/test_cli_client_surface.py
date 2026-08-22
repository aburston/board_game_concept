"""Characterisation of the player client command surface.

One test per scenario in `openspec/specs/player-client/spec.md`. See
`test_cli_server_surface.py` for why these exist and what `expectedFailure`
means here.
"""

import unittest

from cli_harness import CliTestCase, CLIENT_PROMPT, SERVER_PROMPT


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
        # the sole player's commit satisfies the barrier; the client reloads.
        # The server polls for commits every ten seconds and the client polls
        # for the resolved turn every five, so how long this takes depends on
        # where in those two cycles the commit lands, and on how loaded the
        # machine is. The tolerance is wide because of the polling, not because
        # anything here is slow.
        client.read_until_count(CLIENT_PROMPT, 4, timeout=180)
        return client


class ClientInvocation(CliTestCase):

    def test_starting_a_client(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)

    def test_wrong_arguments(self):
        client = self.start_client_with_args(['test-01'])
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('client.py <gameno> <player_number>', client.errors)

    def test_unknown_game(self):
        client = self.start_client('no-such-game', 1)
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('No game with path', client.errors)

    def test_console_script_entry_point(self):
        # the generated console script calls main() with no arguments at all
        client = self.start_entry_point('client')
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('client.py <gameno> <player_number>', client.errors)
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
        client.send_line('show types')
        client.read_until('name: Cross')

    def test_wrong_argument_count(self):
        client = self.player_client()
        client.send_line('add type')
        client.read_until('must provide 5 args for type')

    def test_invalid_statistics(self):
        client = self.player_client()
        client.send_line('add type Cross X 99 1 10')
        client.read_until('error adding unit type: attack must be a value from 1 to 10')

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


class OrderingMovement(ClientTestCase):

    def test_ordering_a_move(self):
        client = self.in_play()
        client.send_line('move x1 north')
        client.read_until('state: 1')

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
        client.send_line('show types')
        client.read_until('name: Cross')

    def test_showing_units(self):
        client = self.with_a_unit()
        client.send_line('show units')
        client.read_until('name: "x1"')

    def test_showing_players(self):
        client = self.player_client()
        client.send_line('show players')
        client.read_until('number: 1')

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
