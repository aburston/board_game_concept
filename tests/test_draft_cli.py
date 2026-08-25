"""What a real session writes down as it is typed into.

`test_draft_recording.py` holds the service layer to recording. This holds the
roles to going through it, by driving the commands a person types and reading
the draft off disk afterwards.
"""

import pytest
import yaml

from board_game_concept.domain import Player
from cli_harness import (CLIENT_PROMPT, GAMES_DIR, SERVER_PROMPT, CliTestCase)

# these tests read the YAML draft file off disk to check what a session
# wrote. The SQLite backend keeps drafts as rows; a JSON snapshot of the
# same thing is a different assertion this file does not need to make
pytestmark = pytest.mark.backend('yaml')


def draft_of(game_number, number):
    """The draft a session left behind, as it was written."""
    path = GAMES_DIR / f'_{game_number}' / 'players' / f'{number}_draft.yaml'
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as file:
        return yaml.safe_load(file)


class ClientDrafts(CliTestCase):

    def test_setup_is_written_down_as_it_is_typed(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)

        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)

        draft = draft_of('test-01', 1)
        self.assertEqual([record['kind'] for record in draft['commands']],
                         ['add_type', 'add_unit'])
        self.assertEqual(draft['commands'][1],
                         {'kind': 'add_unit', 'type_name': 'Cross',
                          'name': 'x1', 'x': 0, 'y': 0})

    def test_an_order_is_written_down_as_it_is_given(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        client.send_line('commit')
        client.read_until('commit complete')
        client.read_until_count(CLIENT_PROMPT, 4, timeout=60)

        client.send_line('move x1 north')
        client.read_until_count(CLIENT_PROMPT, 5)

        draft = draft_of('test-01', 1)
        self.assertEqual(draft['commands'],
                         [{'kind': 'move', 'unit': 'x1', 'direction': 1}])

    def test_committing_leaves_no_draft_behind(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)

        client.send_line('commit')
        client.read_until('commit complete')
        client.read_until_count(CLIENT_PROMPT, 4, timeout=60)

        self.assertIsNone(draft_of('test-01', 1))

    def test_a_refused_command_is_not_written_down(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)

        client.send_line('add unit Nothing x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)

        draft = draft_of('test-01', 1)
        self.assertEqual([record['kind'] for record in draft['commands']],
                         ['add_type'])


class ServerDrafts(CliTestCase):

    def test_setup_is_written_down_before_it_is_committed(self):
        server = self.start_server('test-01')
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        server.send_line('add player 1')
        server.read_until_count(SERVER_PROMPT, 3)

        draft = draft_of('test-01', 0)
        self.assertEqual(draft['commands'],
                         [{'kind': 'set_board', 'size_x': 4, 'size_y': 4},
                          {'kind': 'add_player', 'number': 1,
                           'budget': Player.DEFAULT_BUDGET}])

    def test_committing_setup_leaves_no_draft_behind(self):
        server = self.established_game(players=(1,))
        server.read_until('commit complete')

        self.assertIsNone(draft_of('test-01', 0))


class DroppedCommands(CliTestCase):

    def test_a_command_that_cannot_be_put_back_is_reported(self):
        """Told to the player before they are asked for anything else."""
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        client.terminate()

        # a second deployment onto the square `x1` already holds, added to the
        # draft behind the client's back the way a game that moved on would
        path = GAMES_DIR / '_test-01' / 'players' / '1_draft.yaml'
        draft = yaml.safe_load(path.read_text())
        draft['commands'].append({'kind': 'add_unit', 'type_name': 'Cross',
                                  'name': 'x0', 'x': 0, 'y': 0})
        path.write_text(yaml.safe_dump(draft))

        reopened = self.start_client('test-01', 1)
        reopened.read_until(CLIENT_PROMPT)

        self.assertIn('could not be restored', reopened.output)
        # reported as the line it was typed as, so it can be typed again
        self.assertIn('add unit Cross x0 0 0', reopened.output)
        # and the work that could be put back was
        units = self.shown_json(reopened, CLIENT_PROMPT, 'units')['units']
        self.assertEqual([unit['name'] for unit in units], ['x1'])
