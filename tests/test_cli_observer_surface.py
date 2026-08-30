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
        """An observer on a game with units the server has published.

        `load player` brings units in with the player, and the server publishes
        them as that player's orders for the turn after setup - so the units
        reach `data/units.yaml` on the *second* resolved turn, not the first.
        The server prints "commit complete" once per resolved turn, so waiting
        for the second is waiting for the units to have been published.

        Waiting for only the first was a race the observer usually won by being
        slow to start, and lost on a loaded CI runner.
        """
        self.server = self.start_server()
        self.server.read_until('bgcserver> ')
        self.server.send_line('set board 4 4')
        self.server.read_until_count('bgcserver> ', 2)
        self.server.send_line('load player player_1.yaml')
        self.server.read_until_count('bgcserver> ', 3)
        self.server.send_line('commit')
        self.server.read_until_count('commit complete', 2)
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
        self.assertIn('usage: bgcobserver', observer.errors)

    def test_console_script_entry_point(self):
        # the generated console script calls main() with no arguments at all
        observer = self.start_entry_point('observer')
        self.assertNotEqual(0, observer.wait_for_exit())
        self.assertIn('usage: bgcobserver', observer.errors)
        self.assertNotIn('TypeError', observer.errors)


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
        lines = self.shown_table(observer, OBSERVER_PROMPT, 'types')
        assert lines[0].split() == [
            'PLAYER', 'NAME', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY', 'COST']
        assert lines[1].split() == ['1', 'O', 'O', '1', '1', '10', '12']

    def test_showing_units(self):
        observer = self.watching_a_played_game()
        lines = self.shown_table(observer, OBSERVER_PROMPT, 'units')
        assert lines[0].split()[:4] == ['PLAYER', 'NAME', 'TYPE', 'SYMBOL']
        assert [line.split()[1] for line in lines[1:]] == [
            'o1', 'o2', 'o3', 'o4']

    def test_showing_a_subject_as_json(self):
        observer = self.watching_a_played_game()
        document = self.shown_json(observer, OBSERVER_PROMPT, 'units')
        assert [entry['name'] for entry in document['units']] == [
            'o1', 'o2', 'o3', 'o4']
        assert document['units'][0]['player'] == 1
        assert document['units'][0]['health'] == 1

    def test_a_trailing_word_that_is_not_json(self):
        observer = self.watching()
        assert self.shown(
            observer, OBSERVER_PROMPT,
            'show units wibble') == 'invalid show command'

    def test_showing_the_units_on_the_board(self):
        observer = self.watching_a_played_game()
        observer.send_line('show board')
        observer.read_until('O')

    def test_showing_players(self):
        observer = self.watching()
        lines = self.shown_table(observer, OBSERVER_PROMPT, 'players')
        assert lines[0].split() == [
            'PLAYER', 'STATUS', 'BUDGET', 'SPENT', 'LEFT']
        # the observer reads every record, so every player's points are known
        assert [line.split() for line in lines[1:]] == [
            ['1', 'active', '250', '0', '250'],
            ['2', 'active', '250', '0', '250']]

    def test_showing_pending_orders(self):
        # a player who has committed while the server still waits for the
        # other has orders queued for the next turn
        self.server = self.established_game(players=(1, 2))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.send_line('set flag x1')
        client.read_until_count(CLIENT_PROMPT, 3)
        client.send_line('commit')
        client.read_until('waiting for turn to complete...')

        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)
        lines = self.shown_table(observer, OBSERVER_PROMPT, 'pending')
        assert lines[0].split() == ['PLAYER', 'UNIT', 'ORDER', 'X', 'Y']
        assert lines[1].split() == ['1', 'x1', 'deploy', '0', '0']

    def test_showing_pending_orders_when_none_are_queued(self):
        observer = self.watching()
        assert self.shown(
            observer, OBSERVER_PROMPT, 'show pending') == 'no orders pending'

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
        assert self.shown(
            observer, OBSERVER_PROMPT, 'show units') == 'no units yet'

        # the game gains a unit behind the observer's back: the only player
        # deploys one and commits, which is enough to resolve the turn
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        client.send_line('set flag x1')
        client.read_until_count(CLIENT_PROMPT, 4)
        client.send_line('commit')
        client.read_until_count(CLIENT_PROMPT, 5, timeout=60)

        observer.send_line('reload')
        observer.read_until('reloading')
        observer.read_until_count(OBSERVER_PROMPT, 3)
        lines = self.shown_table(observer, OBSERVER_PROMPT, 'units')
        assert [line.split()[1] for line in lines[1:]] == ['x1']


if __name__ == '__main__':
    unittest.main()
