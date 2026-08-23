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
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)
        server.send_line('add player 2')
        server.read_until_count(SERVER_PROMPT, 4)
        server.send_line('commit')
        server.read_until('commit complete')

        # a heavy unit against a light one, one square apart
        for number, type_name, symbol, stats, unit, square in (
                (1, 'Cross', 'X', '10 10 100', 'x1', '0 0'),
                (2, 'Naught', 'O', '1 1 100', 'o1', '1 0')):
            client = self.start_client(game_number, number)
            client.read_until(CLIENT_PROMPT)
            client.send_line(f'add type {type_name} {symbol} {stats}')
            client.read_until_count(CLIENT_PROMPT, 2)
            client.send_line(f'add unit {type_name} {unit} {square}')
            client.read_until_count(CLIENT_PROMPT, 3)
            client.send_line('commit')
            client.read_until('waiting for turn to complete...')

        # the deployment turn resolves
        server.read_until_count('commit complete', 2)

        # and now player 1 walks into player 2's only unit
        for number, order in ((1, 'move x1 east'), (2, None)):
            client = self.start_client(game_number, number)
            client.read_until(CLIENT_PROMPT)
            if order:
                client.send_line(order)
                client.read_until_count(CLIENT_PROMPT, 2)
            client.send_line('commit')
            client.read_until('commit complete')
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
        client.send_line('move x1 east')
        client.read_until('the game is over')
        client.send_line('commit')
        client.read_until('the game is over')
        # and it can still be looked at
        client.send_line('show board')
        client.read_until_count(CLIENT_PROMPT, 4)

    def test_the_observer_reports_the_outcome(self):
        server = self.play_to_a_finish()
        server.wait_for_exit()

        observer = self.start_observer('test-01')
        observer.read_until('game over: player 1 wins')
        observer.read_until(OBSERVER_PROMPT)

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
        assert ['2', 'eliminated'] in [line.split() for line in lines[1:]]


if __name__ == '__main__':
    unittest.main()
