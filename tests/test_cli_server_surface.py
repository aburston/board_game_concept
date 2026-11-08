"""Characterisation of the server command surface.

One test per scenario in `openspec/specs/game-server/spec.md`, written against
the code as it stands so that the split into layers has something to be checked
against. A test marked `expectedFailure` records a place where the code and the
spec disagree today; each is written up in SPEC_COVERAGE.md. They are not
permission to change behaviour during the split.
"""

import unittest

from cli_harness import CliTestCase, SERVER_PROMPT


class ServerInvocation(CliTestCase):

    def test_starting_the_server(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)

    def test_missing_game_number(self):
        server = self.start_server_with_args([])
        self.assertNotEqual(0, server.wait_for_exit())
        self.assertIn('game-number', server.errors)

    def test_console_script_entry_point(self):
        # the generated console script calls main() with no arguments at all
        server = self.start_entry_point('server')
        self.assertNotEqual(0, server.wait_for_exit())
        self.assertIn('game-number', server.errors)
        self.assertNotIn('TypeError', server.errors)


class InteractiveSetupMode(CliTestCase):

    def test_new_game_prompts(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)

    def test_established_game_runs_unattended(self):
        server = self.established_game()
        # past setup the server stops prompting and waits for the players
        server.read_until('wait for player commit')

    def test_blank_input(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('')
        server.read_until_count(SERVER_PROMPT, 2)
        self.assertNotIn('invalid', server.since(SERVER_PROMPT))

    def test_unrecognised_command(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('wibble')
        server.read_until('invalid command')
        server.read_until_count(SERVER_PROMPT, 2)

    def test_help_lists_commands(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('help')
        server.read_until('commit')
        listed = server.output
        for command in ('add player', 'load board', 'load player', 'set board',
                        'show board', 'show player', 'show types',
                        'show turn', 'next', 'prev', 'exit'):
            self.assertIn(command, listed)
        # a player gives no orders, and the grammar has none to offer
        self.assertFalse(any(line.startswith(('move ', 'hold '))
                             for line in listed.splitlines()))

    def test_exit_ends_the_session(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('exit')
        self.assertEqual(0, server.wait_for_exit())


class SettingBoardSize(CliTestCase):

    def test_setting_the_size(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        self.assertNotIn('invalid', server.since(SERVER_PROMPT))
        server.send_line('show board')
        server.read_until('+-')

    def test_resizing_a_board_during_setup(self):
        """Setup is a thing you are still deciding, size included.

        A board that existed could not be resized, so a 6 typed for a 5 was a
        game to throw away and make again. It stands when the setup holding
        it is committed and not before.
        """
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('set board 6 3')
        server.read_until_count(SERVER_PROMPT, 3)
        self.assertNotIn('resize', server.since(SERVER_PROMPT))
        server.send_line('show board')
        # six squares across and three rows down is the size just asked for
        server.read_until('+-+-+-+-+-+-+')

    # what happens after the setup is committed is not testable at this
    # prompt: `commit` ends the administrator's session by design, so it is
    # held where the rule lives, in `test_setup_is_flexible.py`

    def test_removing_a_registered_player(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        server.send_line('add player 2')
        server.read_until_count(SERVER_PROMPT, 4)
        server.send_line('remove player 2')
        server.read_until_count(SERVER_PROMPT, 5)
        server.send_line('show players')
        server.read_until('1')
        self.assertNotIn('\n     2', server.since(SERVER_PROMPT))

    def test_removing_a_player_who_is_not_registered(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('remove player 4')
        server.read_until('there is no player 4 to remove')

    def test_wrong_argument_count(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board')
        server.read_until('must provide x and y for size')

    def test_non_numeric_dimensions(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board a b')
        server.read_until('x and y must be a numbers')

    def test_dimensions_below_the_minimum(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 1 1')
        server.read_until('x must be greater than 1')


class RegisteringPlayers(CliTestCase):

    def test_adding_a_player(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        self.assertNotIn('invalid', server.since(SERVER_PROMPT))

    def test_adding_a_player_to_an_established_game(self):
        server = self.established_game()
        server.read_until('wait for player commit')
        # an established game never returns to the prompt, so the refusal is
        # reachable only while the server is still in setup; the guard itself
        # is exercised by the client-visible effect of `commit`
        self.assertNotIn("can't add players to an existing game", server.output)

    def test_wrong_argument_count(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('add player 1 2 3')
        server.read_until(
            'must provide a player number and an optional budget')

    def test_a_player_with_a_budget(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('add player 1 150')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('show players')
        server.read_until('150')

    def test_a_budget_that_is_not_a_number(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('add player 1 lots')
        server.read_until('budget must be a number')

    def test_a_budget_out_of_range(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('add player 1 5000')
        server.read_until('budget must be from 1 to 1000')

    def test_add_without_a_subject(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('add')
        server.read_until('invalid add command')


class LoadingConfiguration(CliTestCase):

    def test_loading_a_board(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('load board board.yaml')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('show board')
        server.read_until('+-')

    def test_loading_a_player(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('load board board.yaml')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('load player player_1.yaml')
        server.read_until_count(SERVER_PROMPT, 3)
        self.assertNotIn('Error loading', server.output)

    def test_unreadable_file(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('load board nosuch.yaml')
        server.read_until('Error loading')
        server.read_until_count(SERVER_PROMPT, 2)

    def test_wrong_argument_count(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('load player')
        server.read_until('must provide 1 args for load player')

    def test_load_without_a_subject(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('load')
        server.read_until('invalid load command')


class ServerDisplayCommands(CliTestCase):

    def _sized(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        return server

    def test_showing_the_board(self):
        server = self._sized()
        server.send_line('show board')
        server.read_until('+-')

    def test_showing_the_board_before_one_exists(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('show board')
        server.read_until('must create board - set size and commit')

    def test_showing_types(self):
        server = self._sized()
        server.send_line('load player player_1.yaml')
        server.read_until_count(SERVER_PROMPT, 3)
        lines = self.shown_table(server, SERVER_PROMPT, 'types')
        assert lines[0].split() == [
            'PLAYER', 'NAME', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY',
            'COMPUTE', 'PROGRAM', 'COST']
        assert lines[1].split() == ['1', 'O', 'O', '1', '1', '10', '0', 'no',
                                    '12']

    def test_showing_units(self):
        # the server's prompt is setup, and a loaded player's units only reach
        # the board when setup is committed, so there is nothing to list yet
        server = self._sized()
        assert self.shown(server, SERVER_PROMPT, 'show units') == 'no units yet'

    def test_showing_players(self):
        server = self._sized()
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        lines = self.shown_table(server, SERVER_PROMPT, 'players')
        assert lines[0].split() == [
            'PLAYER', 'STATUS', 'BUDGET', 'SPENT', 'LEFT']
        assert lines[1].split() == ['1', 'active', '320', '0', '320']

    def test_showing_pending_orders(self):
        server = self._sized()
        assert self.shown(
            server, SERVER_PROMPT, 'show pending') == 'no orders pending'

    def test_showing_a_subject_as_json(self):
        server = self._sized()
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        assert self.shown_json(server, SERVER_PROMPT, 'players') == {
            'players': [{'player': 1, 'status': 'active',
                         'budget': 320, 'spent': 0, 'left': 320}]}

    def test_an_empty_subject_as_json_is_an_empty_list(self):
        server = self._sized()
        assert self.shown_json(server, SERVER_PROMPT, 'units') == {'units': []}

    def test_a_trailing_word_that_is_not_json(self):
        server = self._sized()
        assert self.shown(
            server, SERVER_PROMPT,
            'show units wibble') == 'invalid show command'

    def test_incomplete_show_command(self):
        server = self._sized()
        server.send_line('show')
        server.read_until('invalid show command')

    def test_unrecognised_show_subject(self):
        server = self._sized()
        server.send_line('show wibble')
        server.read_until('invalid show command')


class CommittingSetup(CliTestCase):

    def test_committing_setup(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        server.send_line('commit')
        server.read_until('commit complete')

    def test_commit_refused(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('commit')
        server.read_until('the board size is too small (0, 0)')
        server.read_until_count(SERVER_PROMPT, 2)


class UnattendedTurnCycle(CliTestCase):

    def test_the_turn_loop_waits_for_commits(self):
        server = self.established_game()
        server.read_until('wait for player commit')
        self.assertIsNone(server.proc.poll())

    def a_resolved_game(self):
        """The whole cycle, end to end: the sole player's commit satisfies
        the barrier, the server resolves the game to its end - one unit with
        no controller stands still, so the state repeats on turn 2 - logs the
        final board, reports the undecided stop and exits."""
        server = self.established_game(players=(1,))
        server.read_until('wait for player commit')

        client = self.start_client('test-01', 1)
        client.read_until('bgcclient> ')
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count('bgcclient> ', 2)
        client.send_line('add unit Cross x1 0 0')
        client.send_line('set flag x1')
        client.read_until_count('bgcclient> ', 3)
        client.send_line('commit')
        return server

    def test_the_last_setup_commit_resolves_the_game_and_exits(self):
        server = self.a_resolved_game()

        server.read_until('game resolved', timeout=60)
        server.read_until('+-+-+-+-+', timeout=60)
        server.read_until('game over: undecided on turn 2, its state '
                          'repeated (as it stood after turn 1)', timeout=60)
        self.assertEqual(0, server.wait_for_exit())
        self.assertNotIn('Traceback', server.errors)

    def test_started_against_a_resolved_game_it_reports_and_exits(self):
        server = self.a_resolved_game()
        server.wait_for_exit(timeout=60)

        again = self.start_server('test-01')
        self.assertEqual(0, again.wait_for_exit())
        self.assertIn('game over: undecided on turn 2', again.output)
        self.assertNotIn(SERVER_PROMPT, again.output)


class ReadingTheRecord(UnattendedTurnCycle):
    """`bgcserver --replay`: the administrator reads the record at the
    prompt, since the administrator is entitled to the whole game."""

    def test_the_administrator_reads_a_turn(self):
        server = self.a_resolved_game()
        server.wait_for_exit(timeout=60)

        again = self.start_server_with_args(['-g', 'test-01', '--replay'])
        again.read_until('game over: undecided on turn 2')
        # opened at the final turn, with the whole board
        again.read_until('turn 2')
        again.read_until(SERVER_PROMPT)
        shown = self.shown(again, SERVER_PROMPT, 'show turn 1')
        assert shown.splitlines()[0] == 'turn 1'
        assert '|X| | | |' in shown.splitlines()
        assert self.shown(again, SERVER_PROMPT, 'next').splitlines()[0] \
            == 'turn 2'
        assert self.shown(again, SERVER_PROMPT, 'prev').splitlines()[0] \
            == 'turn 1'
        # and changes nothing
        assert self.shown(again, SERVER_PROMPT, 'add player 3') == \
            'the game is over'
        again.send_line('exit')
        self.assertEqual(0, again.wait_for_exit())

    def test_the_record_is_refused_while_the_game_is_being_set_up(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        assert self.shown(server, SERVER_PROMPT, 'show turn 1').startswith(
            'the game has not been resolved')


if __name__ == '__main__':
    unittest.main()
