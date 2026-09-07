"""A password is the same password however it was reached.

The point of the change, end to end: a command line with no server running
changes the password, and a browser signs in with the new one - and the other
way round. If these ever disagreed, whose password an account had would depend
on how the person happened to reach the game.
"""

from cli_harness import SERVER_PROMPT, TEST_DIR, CliTestCase
from game_harness import DEFAULT_BACKEND

NEW_PASSWORD = 'a-longer-secret'


def _app():
    """A server over the same directory the roles are run in.

    The store a role signs in against with no server running is the store a
    server serves, because there is one store per deployment and both find it
    the same way.
    """
    from board_game_concept.http.app import create_app

    return create_app(base_path=str(TEST_DIR), backend=DEFAULT_BACKEND)


class EveryAccessMethodAgrees(CliTestCase):

    def _typed(self, role, lines):
        before = role.output.count(SERVER_PROMPT)
        for line in lines:
            role.send_line(line)
        role.read_until_count(SERVER_PROMPT, before + 1)
        return role.output.rsplit(SERVER_PROMPT, 2)[-2]

    def _at_a_prompt(self):
        role = self.start_server('test-01')
        role.read_until(SERVER_PROMPT)
        return role

    def test_a_password_changed_at_a_command_line_holds_over_http(self):
        # no server is running: the role opens the store beside the games
        said = self._typed(self._at_a_prompt(),
                           ['login admin', 'admin',
                            NEW_PASSWORD, NEW_PASSWORD])
        assert 'password changed' in said, said

        client = _app().test_client()

        answered = client.post('/sessions', json={'username': 'admin',
                                                  'password': NEW_PASSWORD})
        assert answered.status_code == 200, answered.get_json()
        assert answered.get_json()['must_change_password'] is False

        refused = client.post('/sessions', json={'username': 'admin',
                                                 'password': 'admin'})
        assert refused.status_code == 401, refused.get_json()

    def test_a_password_changed_in_a_browser_holds_at_a_command_line(self):
        client = _app().test_client()
        signed_in = client.post('/sessions', json={'username': 'admin',
                                                   'password': 'admin'})
        assert signed_in.get_json()['must_change_password'] is True
        changed = client.post(
            '/accounts/current/password',
            json={'current': 'admin', 'new': NEW_PASSWORD},
            headers={'Authorization':
                     f"Bearer {signed_in.get_json()['token']}"})
        assert changed.status_code == 200, changed.get_json()

        said = self._typed(self._at_a_prompt(), ['login admin', NEW_PASSWORD])

        assert 'signed in as admin (admin)' in said, said
        assert 'must change' not in said, said

    def test_the_old_password_authenticates_nowhere(self):
        role = self._at_a_prompt()
        self._typed(role, ['login admin', 'admin',
                           NEW_PASSWORD, NEW_PASSWORD])
        self._typed(role, ['logout'])

        said = self._typed(role, ['login admin', 'admin'])

        assert 'do not match' in said, said

    def test_a_refusal_reads_the_same_either_way(self):
        """The same too-short password, refused in the same words."""
        role = self._at_a_prompt()
        said = self._typed(role, ['login admin', 'admin', 'short', 'short'])

        client = _app().test_client()
        signed_in = client.post('/sessions', json={'username': 'admin',
                                                   'password': 'admin'})
        refused = client.post(
            '/accounts/current/password',
            json={'current': 'admin', 'new': 'short'},
            headers={'Authorization':
                     f"Bearer {signed_in.get_json()['token']}"})

        assert refused.get_json()['error'] in said, said
