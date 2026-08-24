"""Which numbers each role may be launched as, and what it may do once it is.

The command line used to keep the observer honest by not offering it a command
that writes. That is enough for a person at a prompt and nothing at all for a
caller that does not go through one, so the refusal is checked here at both
levels.
"""

import pytest

from cli_harness import (CLIENT_PROMPT, OBSERVER_PROMPT, SERVER_PROMPT,
                         CliTestCase)
from board_game_concept.service import identity


class ClientInvocation(CliTestCase):

    def _refused(self, number):
        self.established_game(players=(1,))
        client = self.start_client_with_args(['test-01', str(number)])
        self.assertNotEqual(0, client.wait_for_exit(),
                            f'a client for {number} should not have started')
        return client.errors + client.output

    def test_a_client_may_not_be_the_administrator(self):
        said = self._refused(identity.ADMINISTRATOR)
        self.assertIn('reserved', said)

    def test_a_client_may_not_be_the_observer(self):
        said = self._refused(identity.OBSERVER)
        self.assertIn('reserved', said)

    def test_a_client_may_not_be_a_number_below_the_range(self):
        self.assertIn('999', self._refused(-1))

    def test_a_client_may_not_be_a_number_above_the_range(self):
        self.assertIn('999', self._refused(1000000))

    def test_a_client_may_be_the_first_player_number(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)

    def test_a_client_may_be_the_last_player_number(self):
        self.established_game(players=(999,))
        client = self.start_client('test-01', 999)
        client.read_until(CLIENT_PROMPT)


class ServerRefusals(CliTestCase):

    def _add_player(self, number):
        server = self.start_server('test-01')
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        said = self.shown(server, SERVER_PROMPT, f'add player {number}')
        # the session survives the refusal and still takes commands
        self.at_prompt(server, SERVER_PROMPT)
        return said

    def test_adding_the_administrator_as_a_player_is_refused(self):
        self.assertIn('reserved', self._add_player(0))

    def test_adding_the_observer_as_a_player_is_refused(self):
        self.assertIn('reserved', self._add_player(1000))

    def test_a_negative_player_number_is_refused_rather_than_fatal(self):
        """It used to raise an AssertionError, which killed the server."""
        self.assertIn('999', self._add_player(-1))

    def test_a_player_number_above_the_range_is_refused(self):
        self.assertIn('999', self._add_player(1000000))


class ObserverIdentity(CliTestCase):

    def test_the_observer_is_not_the_administrator(self):
        """Both see the whole game; only one of them may change it."""
        self.established_game(players=(1,))
        observer = self.start_observer('test-01')
        observer.read_until(OBSERVER_PROMPT)

        # the observer's writing commands are not merely absent from its
        # grammar - the service layer refuses them too, checked below
        said = self.shown(observer, OBSERVER_PROMPT, 'add player 2')
        self.assertIn('invalid command', said)


@pytest.mark.parametrize('line', [
    'set board 4 4',
    'add player 2',
    'add type Cross X 1 1 10',
    'add unit Cross x1 0 0',
    'move x1 north',
])
def test_the_observer_is_refused_below_the_command_line(tmp_path, line):
    """No role table is consulted here; the identity alone decides."""
    from board_game_concept import Game, YamlGameRepository
    from board_game_concept.cli.parser import parse
    from board_game_concept.service import games
    from board_game_concept.service.errors import GameError

    repository = YamlGameRepository('watched', str(tmp_path))
    admin = Game(repository, identity.ADMINISTRATOR)
    admin.load()
    games.perform(admin, parse('set board 4 4'))
    games.perform(admin, parse('add player 1'))
    assert admin.serverSave()

    observer = Game(repository, identity.OBSERVER)
    observer.load()

    with pytest.raises(GameError):
        games.perform(observer, parse(line))


def test_the_administrator_and_a_player_are_not_refused(tmp_path):
    """`may_change` excludes the observer, not everyone who is not a player."""
    from board_game_concept.cli.parser import parse
    from board_game_concept.service import games
    from game_harness import GameHarness

    harness = GameHarness(tmp_path)
    admin = harness.session(identity.ADMINISTRATOR)
    games.perform(admin, parse('set board 4 4'))
    games.perform(admin, parse('add player 1'))
    assert admin.serverSave()

    client = harness.session(1)
    games.perform(client, parse('add type Cross X 1 5 10'))
    games.perform(client, parse('add unit Cross x1 0 0'))
