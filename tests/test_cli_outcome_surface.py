"""What the three roles say once a game has been decided.

One test per scenario in `openspec/specs/game-outcome/spec.md` that names a
role, driving each as a subprocess the way the other surface suites do.
"""

import unittest

from cli_harness import (CliTestCase, CLIENT_PROMPT, OBSERVER_PROMPT,
                         SERVER_PROMPT)


class DecidedGame(CliTestCase):
    """A two-player game played to a finish: player 1 wipes player 2 out."""

    def play_to_a_finish(self, game_number='test-01'):
        server = self.start_server(game_number)
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        # registered with the top budget, because this fixture's heavy unit
        # costs 120 points and what is under test here is the outcome, not
        # what an army may cost
        server.send_line('add player 1 1000')
        server.read_until_count(SERVER_PROMPT, 3)
        server.send_line('add player 2 1000')
        server.read_until_count(SERVER_PROMPT, 4)
        server.send_line('commit')
        server.read_until('commit complete')

        # a heavy unit against a light one, one square apart. Each deploys in
        # its own half - rows 0 and 1 are player 1's on a four-row board, rows
        # 2 and 3 player 2's - so they face each other down a column. Player
        # 1's type thinks, and its program walks it south into player 2's
        # only unit; player 2's has no controller and stands its ground
        from cli_harness import TEST_DIR
        program = TEST_DIR / 'south.asm'
        program.write_text('MOVE south\n')
        self.addCleanup(lambda: program.unlink(missing_ok=True))
        for number, type_name, symbol, stats, unit, square in (
                (1, 'Cross', 'X', '10 10 100 1', 'x1', '0 1'),
                (2, 'Naught', 'O', '1 1 100', 'o1', '0 2')):
            client = self.start_client(game_number, number)
            client.read_until(CLIENT_PROMPT)
            client.send_line(f'add type {type_name} {symbol} {stats}')
            client.read_until_count(CLIENT_PROMPT, 2)
            if number == 1:
                client.send_line(f'set program {type_name} south.asm')
                client.read_until_count(CLIENT_PROMPT, 3)
            client.send_line(f'add unit {type_name} {unit} {square}')
            client.send_line(f'set flag {unit}')
            client.read_until_count(CLIENT_PROMPT, 5 if number == 1 else 4)
            client.send_line('commit')
            client.read_until('commit complete')
        # the last setup commit plays the game to its end
        client.read_until('game over', timeout=60)
        return server

    def test_the_server_reports_the_winner_and_exits(self):
        server = self.play_to_a_finish()
        self.assertEqual(0, server.wait_for_exit())
        self.assertIn('game over: player 1 wins', server.output)

    def test_the_server_started_against_a_decided_game_reports_and_exits(self):
        server = self.play_to_a_finish()
        server.wait_for_exit()

        again = self.start_server('test-01')
        self.assertEqual(0, again.wait_for_exit())
        self.assertIn('game over: player 1 wins', again.output)

    def test_the_client_reports_the_outcome_and_refuses_orders(self):
        server = self.play_to_a_finish()
        server.wait_for_exit()

        client = self.start_client('test-01', 1)
        client.read_until('game over: player 1 wins')
        client.read_until(CLIENT_PROMPT)
        client.send_line('add unit Cross x2 1 1')
        client.read_until('the game is over')
        client.send_line('commit')
        client.read_until_count('the game is over', 2)
        # and it can still be looked at
        client.send_line('show board')
        client.read_until_count(CLIENT_PROMPT, 4)

    def test_the_observer_reports_the_outcome(self):
        server = self.play_to_a_finish()
        server.wait_for_exit()

        observer = self.start_observer('test-01')
        # one square apart: the cross steps onto the naught on the first
        # turn of play and takes the flag with it
        observer.read_until('game over: player 1 wins on turn 2')
        observer.read_until(OBSERVER_PROMPT)

    def test_the_server_reports_an_undecided_stop(self):
        # two units with no controller never move, so the state repeats
        server = self.start_server('test-02')
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        server.send_line('add player 2')
        server.read_until_count(SERVER_PROMPT, 4)
        server.send_line('commit')
        server.read_until('commit complete')
        for number, square in ((1, '0 0'), (2, '3 3')):
            client = self.start_client('test-02', number)
            client.read_until(CLIENT_PROMPT)
            client.send_line('add type Cross X 1 1 10')
            client.read_until_count(CLIENT_PROMPT, 2)
            client.send_line(f'add unit Cross u{number} {square}')
            client.send_line(f'set flag u{number}')
            client.read_until_count(CLIENT_PROMPT, 4)
            client.send_line('commit')
            client.read_until('commit complete')

        self.assertEqual(0, server.wait_for_exit(timeout=60))
        self.assertIn('game over: undecided on turn 2, its state repeated '
                      '(as it stood after turn 1)', server.output)

    def test_the_observer_reports_the_turn_number_while_playing(self):
        self.established_game(players=(1,))
        observer = self.start_observer('test-01')
        observer.read_until('turn: 0')
        observer.read_until(OBSERVER_PROMPT)

    def test_show_players_marks_an_eliminated_player(self):
        server = self.play_to_a_finish()
        server.wait_for_exit()

        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)
        lines = self.shown_table(observer, OBSERVER_PROMPT, 'players')
        assert ['2', 'eliminated', '1000', '102', '898'] in [
            line.split() for line in lines[1:]]


if __name__ == '__main__':
    unittest.main()
