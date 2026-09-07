"""The four account commands, at each of the three roles' prompts.

Driven as a person drives them: the role is started, `login` is typed at its
prompt, and the password is typed at the prompt that asks for it. Every role
answers the same, because who you are is not a thing one role may ask and
another may not - and none of this needs a server, because the store these
sign in against is the one beside the games.
"""

from pathlib import Path

from cli_harness import (CLIENT_PROMPT, OBSERVER_PROMPT, SERVER_PROMPT,
                         TEST_DIR, CliTestCase)


class AccountCommandsAtEveryPrompt(CliTestCase):
    """One set of assertions, run at each role's prompt."""

    def _typed(self, role, prompt, lines):
        """Type these lines, and hand back everything the role printed."""
        before = role.output.count(prompt)
        for line in lines:
            role.send_line(line)
        role.read_until_count(prompt, before + 1)
        return role.output.rsplit(prompt, 2)[-2]

    def _walk_the_four_commands(self, role, prompt):
        role.read_until(prompt)

        # nobody is signed in until somebody signs in
        assert 'not signed in' in self.shown(role, prompt, 'whoami')

        # `admin` is created with a password everybody knows, and may do
        # nothing else until it is changed - so signing in captures the change
        said = self._typed(role, prompt,
                           ['login admin', 'admin',
                            'a-longer-secret', 'a-longer-secret'])
        assert 'signed in as admin (admin)' in said, said
        assert 'must change its password' in said, said
        assert 'password changed' in said, said

        said = self.shown(role, prompt, 'whoami')
        assert 'signed in as admin (admin)' in said, said
        assert 'must change' not in said, said

        # the changed password is the one that authenticates, and the old one
        # is nobody's
        assert 'signed out' in self.shown(role, prompt, 'logout')
        assert 'not signed in' in self.shown(role, prompt, 'whoami')

        said = self._typed(role, prompt, ['login admin', 'admin'])
        assert 'do not match' in said, said

        said = self._typed(role, prompt, ['login admin', 'a-longer-secret'])
        assert 'signed in as admin (admin)' in said, said
        assert 'must change' not in said, said

        # and it can be changed again, by an account that need not
        said = self._typed(role, prompt,
                           ['passwd', 'a-longer-secret',
                            'a-third-secret', 'a-third-secret'])
        assert 'password changed' in said, said

        # the session survives all of it and is still taking commands
        self.at_prompt(role, prompt)

    def test_the_server_signs_in_at_its_prompt(self):
        self._walk_the_four_commands(self.start_server('test-01'),
                                     SERVER_PROMPT)

    def test_the_client_signs_in_at_its_prompt(self):
        self.established_game(players=(1,))
        self._walk_the_four_commands(self.start_client('test-01', 1),
                                     CLIENT_PROMPT)

    def test_the_observer_signs_in_at_its_prompt(self):
        self.established_game(players=(1,))
        self._walk_the_four_commands(self.start_observer('test-01'),
                                     OBSERVER_PROMPT)


class ATokenLivesInTheProcessAndNowhereElse(CliTestCase):
    """A role keeps no credential of its own: no token file, no password."""

    def _files_under(self, directory):
        return {path for path in directory.rglob('*') if path.is_file()}

    def test_a_later_run_is_signed_in_as_nobody(self):
        role = self.start_server('test-01')
        role.read_until(SERVER_PROMPT)
        before = self._files_under(Path(TEST_DIR))
        said = self._typed(role, ['login admin', 'admin',
                                  'a-longer-secret', 'a-longer-secret'])
        assert 'password changed' in said, said
        role.send_line('exit')
        role.wait_for_exit()

        # everything the sign-in wrote is the account store, which is where a
        # token has always lived - and is not a credential the role kept
        written = self._files_under(Path(TEST_DIR)) - before
        assert written, 'the sign-in wrote nothing at all'
        for path in written:
            assert _is_the_account_store(path), f'{path} is not the store'

        again = self.start_server('test-01')
        again.read_until(SERVER_PROMPT)

        assert 'not signed in' in self.shown(again, SERVER_PROMPT, 'whoami')

    def _typed(self, role, lines):
        before = role.output.count(SERVER_PROMPT)
        for line in lines:
            role.send_line(line)
        role.read_until_count(SERVER_PROMPT, before + 1)
        return role.output.rsplit(SERVER_PROMPT, 2)[-2]


def _is_the_account_store(path):
    """Whether this file is part of the account store, whichever backend."""
    from board_game_concept.storage.sqlite_account_store import STORE_FILENAME
    from board_game_concept.storage.yaml_account_store import STORE_DIRNAME

    return (path.name.startswith(STORE_FILENAME)
            or STORE_DIRNAME in path.parts)


class SigningInLocallyIsNotNeededToPlay(CliTestCase):

    def test_a_local_session_says_what_signing_in_is_for(self):
        role = self.start_server('test-01')
        role.read_until(SERVER_PROMPT)

        said = self._typed_lines(role, ['login observer', 'observer',
                                        'a-longer-secret',
                                        'a-longer-secret'])

        assert 'needs no account' in said, said

    def test_a_password_is_never_shown_back(self):
        role = self.start_server('test-01')
        role.read_until(SERVER_PROMPT)

        said = self._typed_lines(role, ['login admin', 'admin',
                                        'a-longer-secret',
                                        'a-longer-secret'])

        assert 'a-longer-secret' not in said, said

    def _typed_lines(self, role, lines):
        before = role.output.count(SERVER_PROMPT)
        for line in lines:
            role.send_line(line)
        role.read_until_count(SERVER_PROMPT, before + 1)
        return role.output.rsplit(SERVER_PROMPT, 2)[-2]
