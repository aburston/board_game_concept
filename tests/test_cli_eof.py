"""What each role does when its input runs out.

`read_command` read a line with `sys.stdin.readline()`, which returns the empty
string at end of input; after stripping, that is indistinguishable from a blank
line, so the role took it as nothing to do and prompted again - forever. It
never showed to a person, who types `exit`; it made the roles unusable from a
script, which is how it was found.
"""

import unittest

from cli_harness import (CliTestCase, CLIENT_PROMPT, OBSERVER_PROMPT,
                         SERVER_PROMPT)


class EndOfInput(CliTestCase):

    def test_the_server_ends_when_its_input_runs_out(self):
        server = self.start_server()
        server.read_until(SERVER_PROMPT)
        server.close_input()
        self.assertEqual(0, server.wait_for_exit())

    def test_the_client_ends_when_its_input_runs_out(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.close_input()
        self.assertEqual(0, client.wait_for_exit())

    def test_the_observer_ends_when_its_input_runs_out(self):
        self.established_game(players=(1,))
        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)
        observer.close_input()
        self.assertEqual(0, observer.wait_for_exit())

    def test_a_role_does_not_spin_after_its_input_runs_out(self):
        # the spin filled the pipe with prompts rather than hanging quietly
        self.established_game(players=(1,))
        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)
        observer.close_input()
        observer.wait_for_exit()
        self.assertLess(observer.output.count(OBSERVER_PROMPT), 5,
                        observer.output[:500])

    def test_a_blank_line_is_still_not_an_ending(self):
        # the two used to be the same string; they must not be again
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('')
        client.read_until_count(CLIENT_PROMPT, 2)
        self.assertIsNone(client.proc.poll())


if __name__ == '__main__':
    unittest.main()
