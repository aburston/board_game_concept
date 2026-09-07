"""How a credential is read, and where it must never end up.

A password typed at a prompt is the one thing in this system that must not be
written down anywhere: not echoed, not in a history file, not in a process's
arguments. These hold the reading to that.
"""

import getpass
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from board_game_concept.cli import accounts                # noqa: E402
from board_game_concept.cli.accounts import Accounts, SignedIn  # noqa: E402
from cli_harness import CLIENT, OBSERVER, SERVER, TEST_DIR      # noqa: E402


class _Recording(Accounts):
    """An `Accounts` that records what it was given, and refuses nothing."""

    def __init__(self, must_change=False):
        super().__init__()
        self.given = []
        self.changed = []
        self._must_change = must_change

    def sign_in(self, username, password):
        self.given.append((username, password))
        return self._hold(SignedIn(username, 'player', 'a-token',
                                   self._must_change))

    def change_password(self, current, new):
        self.changed.append((current, new))
        self.signed_in.must_change = False

    def whoami(self):
        return self.signed_in

    def sign_out(self):
        self._hold(None)


@pytest.fixture(name='at_a_terminal', autouse=True)
def _at_a_terminal(monkeypatch):
    """Every test below is about a person typing, unless it says otherwise.

    Under pytest neither stream is a terminal, and the reader has a second
    path for that - exercised on its own further down.
    """
    monkeypatch.setattr(accounts, 'at_a_terminal', lambda: True)


@pytest.fixture(name='no_input')
def _no_input(monkeypatch):
    """`input()` set to fail, so anything that reaches it is caught."""
    def refuse(prompt=''):
        raise AssertionError(f'a prompt reached input(): {prompt!r}')
    monkeypatch.setattr('builtins.input', refuse)


# --- 2.1 what reads what


def test_a_password_is_read_with_getpass_and_never_with_input(monkeypatch,
                                                              no_input):
    asked = []
    monkeypatch.setattr(getpass, 'getpass',
                        lambda prompt='': asked.append(prompt) or 'secret')

    assert accounts.ask_password() == 'secret'
    assert asked == ['password: ']


def test_a_username_is_read_the_ordinary_way(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': '  Ada  ')

    assert accounts.ask_username() == 'Ada'


def test_a_new_password_is_typed_twice(monkeypatch, no_input):
    typed = iter(['a-longer-secret', 'a-longer-secret'])
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': next(typed))

    assert accounts.ask_new_password() == 'a-longer-secret'


def test_a_new_password_that_was_mistyped_is_refused(monkeypatch, capsys,
                                                     no_input):
    typed = iter(['a-longer-secret', 'a-longer-secrat'])
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': next(typed))

    assert accounts.ask_new_password() is None
    assert accounts.MISMATCH_MESSAGE in capsys.readouterr().out


def test_signing_in_at_a_prompt_reads_the_password_with_getpass(monkeypatch):
    """The whole flow: one `input()` for the name, `getpass` for the rest."""
    prompted = []
    monkeypatch.setattr('builtins.input',
                        lambda prompt='': prompted.append(prompt) or 'ada')
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': 'a-secret-one')
    accounts_seam = _Recording()

    accounts.sign_in_at_prompt(accounts_seam)

    assert accounts_seam.given == [('ada', 'a-secret-one')]
    assert prompted == ['username: '], 'a password went through input()'


def test_a_forced_change_uses_the_password_just_typed(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': 'admin')
    typed = iter(['admin', 'a-longer-secret', 'a-longer-secret'])
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': next(typed))
    accounts_seam = _Recording(must_change=True)

    accounts.sign_in_at_prompt(accounts_seam)

    assert accounts_seam.changed == [('admin', 'a-longer-secret')]


# --- 2.2 where a password may not end up


def test_a_password_prompt_leaves_the_command_history_alone(monkeypatch):
    """`getpass` does not go through `readline`, which is why it is used.

    The stdlib's no-terminal reader is the one exercised: reaching for
    `/dev/tty` in a test would block on whatever terminal ran it.
    """
    readline = pytest.importorskip('readline')
    monkeypatch.setattr(getpass, 'getpass', getpass.fallback_getpass)
    monkeypatch.setattr(sys, 'stdin', io.StringIO('a-typed-secret\n'))
    readline.add_history('show units')
    before = readline.get_current_history_length()

    assert accounts.ask_password() == 'a-typed-secret'

    assert readline.get_current_history_length() == before
    assert 'a-typed-secret' not in [
        readline.get_history_item(index)
        for index in range(1, before + 1)]


@pytest.mark.parametrize('launcher, arguments', [
    (SERVER, ['-g', 'test-01']),
    (CLIENT, ['test-01', '1']),
    (OBSERVER, ['test-01']),
], ids=['bgcserver', 'bgcclient', 'bgcobserver'])
def test_no_role_takes_a_password_as_an_argument(launcher, arguments):
    """A command line is a public thing: a history file, a process listing."""
    from subprocess import PIPE, Popen

    process = Popen(
        [str(word) for word in launcher] + arguments
        + ['--password', 'a-secret-one'],
        cwd=str(TEST_DIR), stdin=PIPE, stdout=PIPE, stderr=PIPE,
        universal_newlines=True)
    output, errors = process.communicate('exit\n', timeout=30)

    assert process.returncode != 0, 'a password was accepted as an argument'
    assert 'password' not in output.lower().replace('--password', '')


# --- 4.1 and 4.2 the handler the three roles share


def _handled(line, accounts_seam):
    from board_game_concept.cli.parser import parse

    return accounts.handle_account_command(parse(line), accounts_seam)


def test_a_command_that_is_not_an_account_command_is_left_alone():
    from board_game_concept.cli.parser import parse

    assert accounts.handle_account_command(parse('show units'),
                                           _Recording()) is False
    assert accounts.handle_account_command(parse('commit'),
                                           _Recording()) is False


def test_the_handler_signs_in(monkeypatch, capsys):
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': 'a-secret-one')
    seam = _Recording()

    assert _handled('login ada', seam) is True

    assert seam.given == [('ada', 'a-secret-one')]
    assert 'signed in as ada (player)' in capsys.readouterr().out


def test_the_handler_says_who_is_signed_in(monkeypatch, capsys):
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': 'a-secret-one')
    seam = _Recording()
    _handled('login ada', seam)
    capsys.readouterr()

    _handled('whoami', seam)

    assert 'signed in as ada (player)' in capsys.readouterr().out


def test_the_handler_says_when_nobody_is_signed_in(capsys):
    _handled('whoami', _Recording())

    assert 'not signed in' in capsys.readouterr().out


def test_the_handler_signs_out(monkeypatch, capsys):
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': 'a-secret-one')
    seam = _Recording()
    _handled('login ada', seam)

    _handled('logout', seam)

    assert seam.signed_in is None
    assert 'signed out of ada' in capsys.readouterr().out


def test_a_refusal_is_reported_and_the_prompt_comes_back(monkeypatch, capsys):
    """Being told the wrong password does not end somebody's session."""
    from board_game_concept.service.errors import NotAuthenticated

    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': 'wrong-one')

    class _Refusing(_Recording):
        def sign_in(self, username, password):
            raise NotAuthenticated('that username and password do not match')

    assert _handled('login ada', _Refusing()) is True

    assert 'do not match' in capsys.readouterr().out


def test_changing_a_password_at_the_prompt(monkeypatch, capsys):
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': 'a-secret-one')
    seam = _Recording()
    _handled('login ada', seam)
    typed = iter(['a-secret-one', 'a-longer-secret', 'a-longer-secret'])
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': next(typed))

    _handled('passwd', seam)

    assert seam.changed == [('a-secret-one', 'a-longer-secret')]
    assert 'password changed' in capsys.readouterr().out


def test_changing_a_password_while_signed_in_as_nobody(capsys):
    _handled('passwd', _Recording())

    assert 'not signed in' in capsys.readouterr().out


def test_a_forced_change_is_captured_at_the_prompt(monkeypatch, capsys):
    typed = iter(['admin', 'a-longer-secret', 'a-longer-secret'])
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': next(typed))
    seam = _Recording(must_change=True)

    _handled('login admin', seam)

    said = capsys.readouterr().out
    assert 'must change its password' in said
    assert 'password changed' in said
    assert seam.changed == [('admin', 'a-longer-secret')]
    assert seam.signed_in.must_change is False


def test_declining_a_forced_change_leaves_the_session_gated(monkeypatch,
                                                            capsys):
    def refuse(prompt=''):
        if prompt.startswith('new password'):
            raise EOFError
        return 'admin'
    monkeypatch.setattr(getpass, 'getpass', refuse)
    seam = _Recording(must_change=True)

    _handled('login admin', seam)

    said = capsys.readouterr().out
    assert 'must change its password' in said
    assert 'password unchanged' in said
    # signed in as that account, and refused by everything else until it is
    assert seam.signed_in.username == 'admin'
    assert seam.signed_in.must_change is True
    assert seam.changed == []


def test_a_new_password_that_is_too_short_is_refused(monkeypatch, capsys):
    from board_game_concept.service.errors import AccountError

    typed = iter(['admin', 'short', 'short'])
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': next(typed))

    class _Strict(_Recording):
        def change_password(self, current, new):
            raise AccountError('a password must be at least 8 characters')

    seam = _Strict(must_change=True)
    _handled('login admin', seam)

    said = capsys.readouterr().out
    assert '8 characters' in said
    assert seam.signed_in.must_change is True


# --- the other kind of caller: a pipe, with no terminal to type at


def test_a_password_is_read_from_the_input_when_there_is_no_terminal(
        monkeypatch, capsys):
    """A role driven by a pipe reads its line; there is no echo to turn off.

    `getpass` would reach for `/dev/tty` here and read from a terminal the
    caller is not typing at, which is a session that hangs.
    """
    monkeypatch.setattr(accounts, 'at_a_terminal', lambda: False)
    monkeypatch.setattr(getpass, 'getpass', lambda prompt='': pytest.fail(
        'getpass was used where there is no terminal'))
    monkeypatch.setattr(sys, 'stdin', io.StringIO('a-piped-secret\n'))

    assert accounts.ask_password() == 'a-piped-secret'
    assert capsys.readouterr().out == 'password: '


def test_input_that_has_run_dry_is_declining_rather_than_dying(monkeypatch,
                                                               capsys):
    monkeypatch.setattr(accounts, 'at_a_terminal', lambda: False)
    monkeypatch.setattr(sys, 'stdin', io.StringIO(''))
    seam = _Recording(must_change=True)
    seam.sign_in('admin', 'admin')

    assert accounts.capture_password_change(seam, seam.signed_in,
                                            'admin') is False
    assert 'password unchanged' in capsys.readouterr().out
