"""Characterisation of the neutral observer command surface.

One test per scenario in `openspec/specs/game-observer/spec.md`. See
`test_cli_server_surface.py` for why these exist.
"""

import unittest

from cli_harness import CliTestCase, OBSERVER_PROMPT, CLIENT_PROMPT


class ObserverTestCase(CliTestCase):

    def watching(self, game_number='test-01', players=(1, 2)):
        """An observer on a game that has been set up and committed."""
        self.server = self.established_game(players=players)
        observer = self.start_observer(game_number)
        observer.read_until(OBSERVER_PROMPT)
        return observer

    def watching_a_played_game(self):
        """An observer on a game with units the server has published."""
        self.server = self.start_server()
        self.server.read_until('server.py> ')
        self.server.send_line('set board 4 4')
        self.server.read_until_count('server.py> ', 2)
        self.server.send_line('load player player_1.yaml')
        self.server.read_until_count('server.py> ', 3)
        self.server.send_line('commit')
        self.server.read_until('commit complete')
        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)
        return observer


class ObserverInvocation(CliTestCase):

    def test_starting_the_observer(self):
        self.established_game()
        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)

    def test_wrong_arguments(self):
        observer = self.start_observer_with_args([])
        self.assertNotEqual(0, observer.wait_for_exit())
        self.assertIn('usage, observer.py <gameno>', observer.errors)


class ObserverIsReadOnly(ObserverTestCase):

    def test_no_mutating_commands(self):
        observer = self.watching()
        for command in ('add type Cross X 1 1 10', 'add unit Cross x1 0 0',
                        'move x1 north', 'commit', 'set board 8 8',
                        'load player player_1.yaml'):
            before = observer.output.count('invalid command')
            observer.send_line(command)
            observer.read_until_count('invalid command', before + 1)
        self.assertIsNone(observer.proc.poll())


class ObserverCommandLoop(ObserverTestCase):

    def test_blank_input(self):
        observer = self.watching()
        observer.send_line('')
        observer.read_until_count(OBSERVER_PROMPT, 2)
        self.assertNotIn('invalid', observer.since(OBSERVER_PROMPT))

    def test_unrecognised_command(self):
        observer = self.watching()
        observer.send_line('wibble')
        observer.read_until('invalid command')

    def test_help_lists_commands(self):
        observer = self.watching()
        observer.send_line('help')
        observer.read_until('reload')
        for command in ('show players', 'show types', 'show units',
                        'show pending', 'show board', 'exit'):
            self.assertIn(command, observer.output)

    def test_exit_ends_the_session(self):
        observer = self.watching()
        observer.send_line('exit')
        self.assertEqual(0, observer.wait_for_exit())


class ObserverDisplayCommands(ObserverTestCase):

    def test_showing_the_board(self):
        observer = self.watching()
        observer.send_line('show board')
        observer.read_until('#')

    def test_showing_the_board_before_one_exists(self):
        observer = self.start_observer('no-such-game')
        observer.read_until(OBSERVER_PROMPT)
        observer.send_line('show board')
        observer.read_until('must create board - set size and commit')

    def test_showing_types(self):
        observer = self.watching_a_played_game()
        observer.send_line('show types')
        observer.read_until('name: O')

    def test_showing_units(self):
        observer = self.watching_a_played_game()
        observer.send_line('show units')
        observer.read_until('name: "o1"')

    def test_showing_the_units_on_the_board(self):
        observer = self.watching_a_played_game()
        observer.send_line('show board')
        observer.read_until('O')

    def test_showing_players(self):
        observer = self.watching()
        observer.send_line('show players')
        observer.read_until('number: 1')

    def test_showing_pending_orders(self):
        # a player who has committed while the server still waits for the
        # other has orders queued for the next turn
        self.server = self.established_game(players=(1, 2))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        client.send_line('commit')
        client.read_until('waiting for turn to complete...')

        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)
        observer.send_line('show pending')
        observer.read_until('player: 1, moves:')

    def test_showing_pending_orders_when_none_are_queued(self):
        observer = self.watching()
        observer.send_line('show pending')
        observer.read_until_count(OBSERVER_PROMPT, 2)
        self.assertNotIn('invalid show command', observer.since(OBSERVER_PROMPT))

    def test_incomplete_show_command(self):
        observer = self.watching()
        observer.send_line('show')
        observer.read_until('invalid show command')

    def test_unrecognised_show_subject(self):
        observer = self.watching()
        observer.send_line('show wibble')
        observer.read_until('invalid show command')


class RefreshingTheView(ObserverTestCase):

    def test_reloading(self):
        observer = self.watching()
        observer.send_line('reload')
        observer.read_until('reloading')
        observer.read_until_count(OBSERVER_PROMPT, 2)

    def test_reloading_picks_up_a_resolved_turn(self):
        # one player, so that player's commit is the whole barrier and the
        # turn resolves without a second client
        observer = self.watching(players=(1,))
        observer.send_line('show units')
        observer.read_until('units: None')

        # the game gains a unit behind the observer's back: the only player
        # deploys one and commits, which is enough to resolve the turn
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        client.send_line('commit')
        # see test_cli_client_surface for why this tolerance is wide
        client.read_until_count(CLIENT_PROMPT, 4, timeout=180)

        observer.send_line('reload')
        observer.read_until('reloading')
        observer.read_until_count(OBSERVER_PROMPT, 3)
        observer.send_line('show units')
        observer.read_until('name: "x1"')


if __name__ == '__main__':
    unittest.main()
