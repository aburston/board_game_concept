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
        """An observer on a game the server has played to its end.

        `load player` brings units in with the player, committed as loaded,
        so the administrator's commit is the last setup outstanding and the
        game is resolved from there: units with no controller stand still,
        the state repeats on turn 2, and the server reports the undecided
        stop and exits. The observer opens the resolved game.
        """
        self.server = self.start_server()
        self.server.read_until('bgcserver> ')
        self.server.send_line('set board 4 4')
        self.server.read_until_count('bgcserver> ', 2)
        self.server.send_line('load player player_1.yaml')
        self.server.read_until_count('bgcserver> ', 3)
        self.server.send_line('commit')
        self.server.read_until('game over', timeout=60)
        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)
        return observer

    def program_file(self, text, name='program_under_test.asm'):
        from cli_harness import TEST_DIR
        path = TEST_DIR / name
        path.write_text(text)
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return name


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
                        'set program Cross hunt.asm', 'commit',
                        'set board 8 8', 'load player player_1.yaml'):
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
                        'show pending', 'show board', 'show turn',
                        'show program', 'next', 'prev', 'exit'):
            self.assertIn(command, observer.output)

    def test_exit_ends_the_session(self):
        observer = self.watching()
        observer.send_line('exit')
        self.assertEqual(0, observer.wait_for_exit())


class ObserverDisplayCommands(ObserverTestCase):

    def test_showing_the_board(self):
        observer = self.watching()
        observer.send_line('show board')
        observer.read_until('+-')

    def test_showing_the_board_before_one_exists(self):
        observer = self.start_observer('no-such-game')
        observer.read_until(OBSERVER_PROMPT)
        observer.send_line('show board')
        observer.read_until('must create board - set size and commit')

    def test_showing_types(self):
        observer = self.watching_a_played_game()
        lines = self.shown_table(observer, OBSERVER_PROMPT, 'types')
        assert lines[0].split() == [
            'PLAYER', 'NAME', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY',
            'COMPUTE', 'PROGRAM', 'COST']
        assert lines[1].split() == ['1', 'O', 'O', '1', '1', '10', '0', 'no',
                                    '12']

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
            ['1', 'active', '320', '0', '320'],
            ['2', 'active', '320', '0', '320']]

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
        client.read_until('waiting for player(s) 2 to commit their setup')

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
        # the game has been resolved since the session started, and the
        # observer reports the outcome after reloading
        observer.read_until('game over: undecided on turn 2')
        observer.read_until_count(OBSERVER_PROMPT, 3)
        lines = self.shown_table(observer, OBSERVER_PROMPT, 'units')
        assert [line.split()[1] for line in lines[1:]] == ['x1']


class WatchingTheReplay(ObserverTestCase):
    """The observer sees everything: every turn, every trace, any program."""

    def test_opening_a_game_still_being_set_up(self):
        observer = self.watching()
        assert 'game over' not in observer.output
        self.assertIn('turn: 0', observer.output)
        self.assertIn('the game is being set up; waiting for player(s) 1, 2 '
                      'to commit their setup', observer.output)
        assert self.shown(observer, OBSERVER_PROMPT, 'show turn 1').startswith(
            'the game has not been resolved')

    def test_opening_a_decided_game(self):
        observer = self.watching_a_played_game()
        self.assertIn('game over: undecided on turn 2', observer.output)
        # the final board is shown, and the replay is there to step through
        self.assertIn('turn 2', observer.output)
        self.assertIn('|O| | | |', observer.output)

    def test_reading_a_turn(self):
        observer = self.watching_a_played_game()
        shown = self.shown(observer, OBSERVER_PROMPT, 'show turn 1')
        lines = shown.splitlines()
        assert lines[0] == 'turn 1'
        assert lines.count('|O| | | |') == 4
        # what the turn did: the four deployments
        assert shown.count('is placed at') == 4

    def test_stepping(self):
        observer = self.watching_a_played_game()
        self.shown(observer, OBSERVER_PROMPT, 'show turn 1')
        assert self.shown(observer, OBSERVER_PROMPT,
                          'next').splitlines()[0] == 'turn 2'
        assert self.shown(observer, OBSERVER_PROMPT,
                          'prev').splitlines()[0] == 'turn 1'

    def test_reading_a_program_and_a_trace(self):
        # one player, who gives a type a program and commits; the server
        # resolves the game and the observer reads what the controller did
        self.server = self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Runner r 2 4 10 3')
        client.read_until_count(CLIENT_PROMPT, 2)
        path = self.program_file('SELF\nFLAG enemy\nJIF neg r0, rest\n'
                                 'MOVE south\nHALT\nrest: SLEEP 2\n')
        client.send_line(f'set program Runner {path}')
        client.read_until_count(CLIENT_PROMPT, 3)
        client.send_line('add unit Runner r1 0 0')
        client.read_until_count(CLIENT_PROMPT, 4)
        client.send_line('set flag r1')
        client.read_until_count(CLIENT_PROMPT, 5)
        client.send_line('commit')
        client.read_until('game over', timeout=60)

        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)
        listed = self.shown(observer, OBSERVER_PROMPT,
                            'show program Runner').splitlines()
        assert listed[0] == ('Runner: compute 3, 300 ticks per energy, '
                             'cap 300 ticks a turn')
        assert listed[1].split() == ['LINE', 'TICKS', 'PROGRAM']
        # the controller ran on turn 2: no enemy flag, so it slept
        shown = self.shown(observer, OBSERVER_PROMPT, 'show turn 2')
        trace = [line.split() for line in shown.splitlines()
                 if line.split()[:1] == ['r1']][-1]
        assert trace[:2] == ['r1', '1']
        assert '2' in trace                  # SLEEP 2


if __name__ == '__main__':
    unittest.main()
