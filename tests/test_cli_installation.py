"""That installing the package really does put the roles on the path.

Every one of the console scripts was dead once - each raised `TypeError` and
stopped, because nothing ever ran them and only the module files were tested
(`SPEC_COVERAGE.md` - 9). This is the file that would have caught it: it starts
each role by name alone, the way a user does, with no interpreter and no file
path in the command.

It is the one module in the suite that skips rather than falling back. The rest
of the CLI tests run the module files when nothing is installed, so they pass on
a fresh clone; this one has nothing to say without an install, and says so.
"""

import shutil
import unittest

from cli_harness import (CliTestCase, CLIENT_PROMPT, OBSERVER_PROMPT,
                         SERVER_PROMPT)

COMMANDS = ('bgcserver', 'bgcclient', 'bgcobserver')

# the names these replaced. Nothing should answer to them: not a stale script
# left in a venv by an earlier install, and not a rename that stopped half way
RETIRED = ('board-game-server', 'board-game-client', 'board-game-observer',
           'board-game-test-suite')

INSTALLED = all(shutil.which(command) is not None for command in COMMANDS)

REASON = ("the commands are not on the path - install the package with "
          "`pip install -e '.[dev]'` to run these")


@unittest.skipUnless(INSTALLED, REASON)
class InstalledCommands(CliTestCase):
    """Each role starts from its own name, with nothing else on the line."""

    def start_by_name(self, command, args):
        self.assertIsNotNone(shutil.which(command))
        return self._start([command] + list(args))

    def test_the_server_starts_by_name(self):
        server = self.start_by_name('bgcserver', ['-g', 'test-01'])
        server.read_until(SERVER_PROMPT)

    def test_the_client_starts_by_name(self):
        self.established_game(players=(1,))
        client = self.start_by_name('bgcclient', ['test-01', '1'])
        client.read_until(CLIENT_PROMPT)

    def test_the_observer_starts_by_name(self):
        self.established_game()
        observer = self.start_by_name('bgcobserver', ['test-01'])
        observer.read_until(OBSERVER_PROMPT)

    def test_the_server_reports_its_own_name_in_its_usage(self):
        server = self.start_by_name('bgcserver', [])
        self.assertNotEqual(0, server.wait_for_exit())
        self.assertIn('usage: bgcserver', server.errors)

    def test_the_client_reports_its_own_name_in_its_usage(self):
        client = self.start_by_name('bgcclient', ['test-01'])
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('bgcclient <gameno> <player_number>', client.errors)

    def test_the_observer_reports_its_own_name_in_its_usage(self):
        observer = self.start_by_name('bgcobserver', [])
        self.assertNotEqual(0, observer.wait_for_exit())
        self.assertIn('usage, bgcobserver <gameno>', observer.errors)


@unittest.skipUnless(INSTALLED, REASON)
class OnlyTheRolesAreInstalled(unittest.TestCase):
    """A command for each role, and a command for nothing else."""

    def test_no_old_name_answers(self):
        for command in RETIRED:
            with self.subTest(command=command):
                self.assertIsNone(shutil.which(command))

    def test_the_test_harness_has_no_command(self):
        # it is developer tooling, run as `python -m
        # board_game_concept.test_suite`; an installed game has no use for it
        for command in ('bgctestsuite', 'board-game-test-suite'):
            with self.subTest(command=command):
                self.assertIsNone(shutil.which(command))


if __name__ == '__main__':
    unittest.main()
