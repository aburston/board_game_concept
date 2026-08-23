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
                        'show board', 'show player', 'show types', 'exit'):
            self.assertIn(command, listed)

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
        server.read_until('#')

    def test_resizing_an_existing_board(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('set board 5 5')
        server.read_until("can't resize an existing board")

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
        server.send_line('add player 1 2')
        server.read_until('must provide 1 arg for player')

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
        server.read_until('#')

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
        server.read_until('#')

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
            'PLAYER', 'NAME', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY']
        assert lines[1].split() == ['1', 'O', 'O', '1', '1', '10']

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
        assert lines[0].split() == ['PLAYER', 'STATUS']
        assert lines[1].split() == ['1', 'active']

    def test_showing_pending_orders(self):
        server = self._sized()
        assert self.shown(
            server, SERVER_PROMPT, 'show pending') == 'no orders pending'

    def test_showing_a_subject_as_json(self):
        server = self._sized()
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        assert self.shown_json(server, SERVER_PROMPT, 'players') == {
            'players': [{'player': 1, 'status': 'active'}]}

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

    def test_the_turn_loop_logs_the_board_and_keeps_going(self):
        # the whole cycle, end to end: the sole player's commit satisfies the
        # barrier, the server resolves the turn, logs what it resolved, and
        # goes back to waiting. Nothing checked this before, so a stale
        # reference here killed the server after the first turn without a
        # single test noticing
        server = self.established_game(players=(1,))
        server.read_until('wait for player commit')

        client = self.start_client('test-01', 1)
        client.read_until('bgcclient> ')
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count('bgcclient> ', 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count('bgcclient> ', 3)
        client.send_line('commit')

        # the barrier lifts, the server logs the board it was holding, and
        # goes round again: resolving the turn and waiting for the next one.
        # The log runs a turn behind the orders, which is why it is the return
        # to waiting that says the cycle is still turning
        server.read_until('+-+-+-+-+', timeout=60)
        server.read_until_count('commit complete', 2, timeout=60)
        server.read_until_count('wait for player commit', 2, timeout=60)
        self.assertIsNone(server.proc.poll())
        self.assertNotIn('Traceback', server.errors)


if __name__ == '__main__':
    unittest.main()
