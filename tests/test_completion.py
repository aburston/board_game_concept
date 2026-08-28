"""What completes where, checked without a terminal.

`candidates` is a function of the text left of the cursor, the role's table and
a source of names, so almost everything about completion can be asserted as a
list of strings. The one thing that cannot is the wiring into `readline`, which
has its own test at the end and needs a pseudo-terminal.
"""

import os
import pty
import shutil
import select
import subprocess
import sys
import time

import pytest

from board_game_concept.cli import roles
from board_game_concept.cli.complete import GameNames, candidates, install
from board_game_concept.cli.help import usages_for
from board_game_concept.service import games
from board_game_concept.service.commands import AddType, AddUnit

from game_harness import GameHarness

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def a_game(tmp_path):
    """Two players, a type each, a unit each, deployed and resolved."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [('tank', 'T', 3, 5, 10), ('scout', 'S', 1, 2, 10)],
                   [('tank', 'alpha', 0, 0), ('scout', 'able', 1, 0)])
    harness.deploy(2, [('raider', 'R', 2, 2, 10)],
                   [('raider', 'alpaca', 3, 3)])
    harness.resolve()
    return harness


def names(tmp_path, player_number=1):
    return GameNames(a_game(tmp_path).session(player_number), player_number)


class TestWordsOfTheLanguage:

    def test_an_empty_line_offers_the_commands_help_lists(self):
        offered = candidates('', roles.CLIENT)

        assert offered == sorted({usage.words[0]
                                  for usage in usages_for(roles.CLIENT)})

    def test_a_prefix_offers_only_the_commands_that_start_with_it(self):
        assert candidates('sh', roles.CLIENT) == ['show']
        assert candidates('c', roles.CLIENT) == ['commit']

    def test_show_offers_its_subjects(self):
        assert candidates('show ', roles.SERVER) == [
            'board', 'designs', 'events', 'flags', 'pending', 'players',
            'types', 'units']

    def test_a_subject_offers_the_json_form(self):
        assert candidates('show units ', roles.CLIENT) == ['json']
        assert candidates('show units j', roles.CLIENT) == ['json']

    def test_a_player_is_offered_the_flag_to_set(self):
        assert candidates('set ', roles.CLIENT) == ['flag']
        assert candidates('set ', roles.SERVER) == ['board']

    def test_set_add_and_load_offer_their_subjects(self):
        assert candidates('set ', roles.SERVER) == ['board']
        assert candidates('add ', roles.SERVER) == ['player']
        assert candidates('add ', roles.CLIENT) == ['type', 'unit']
        assert candidates('load ', roles.SERVER) == ['board', 'player']

    def test_move_offers_the_directions_after_a_unit(self):
        assert candidates('move alpha ', roles.CLIENT) == [
            'east', 'north', 'south', 'west']
        assert candidates('move alpha s', roles.CLIENT) == ['south']

    def test_an_optional_number_offers_nothing(self):
        # `add player <number> [<budget>]`: an optional slot completes the way
        # a required one does, and a number is the person's to choose
        assert candidates('add player ', roles.SERVER) == []
        assert candidates('add player 1 ', roles.SERVER) == []

    def test_a_word_that_is_not_in_the_grammar_offers_nothing(self):
        assert candidates('wibble ', roles.CLIENT) == []
        assert candidates('show wibble ', roles.CLIENT) == []


class TestTheRoleDecides:

    def test_the_observer_is_offered_nothing_that_writes(self):
        offered = candidates('', roles.OBSERVER)

        assert 'move' not in offered
        assert 'add' not in offered
        assert 'commit' not in offered
        assert offered == ['exit', 'help', 'reload', 'show']

    def test_a_show_subject_a_role_does_not_have_is_not_offered(self):
        assert 'events' in candidates('show ', roles.CLIENT)
        assert 'pending' in candidates('show ', roles.OBSERVER)
        # the observer changes nothing, so it is offered nothing that does
        assert candidates('remove ', roles.OBSERVER) == []
        assert candidates('remove ', roles.SERVER) == ['player']

    def test_the_server_is_not_offered_a_player_command(self):
        offered = candidates('', roles.SERVER)

        assert 'move' not in offered
        assert candidates('add ', roles.SERVER) == ['player']


class TestNamesFromTheGame:

    def test_move_offers_the_players_own_units(self, tmp_path):
        assert candidates('move ', roles.CLIENT, names(tmp_path)) == [
            'able', 'alpha']

    def test_add_unit_offers_the_players_own_types(self, tmp_path):
        assert candidates('add unit ', roles.CLIENT, names(tmp_path)) == [
            'scout', 'tank']

    def test_another_players_unit_of_a_similar_name_is_not_offered(self,
                                                                  tmp_path):
        offered = candidates('move alp', roles.CLIENT, names(tmp_path))

        assert offered == ['alpha']

    def test_another_players_type_is_not_offered(self, tmp_path):
        assert 'raider' not in candidates('add unit ', roles.CLIENT,
                                          names(tmp_path))

    def test_a_destroyed_unit_is_not_offered(self, tmp_path):
        session = a_game(tmp_path).session(1)
        session.getBoard().getUnitByName('alpha')[0].setDestroyed(True)

        offered = candidates('move ', roles.CLIENT, GameNames(session, 1))

        assert offered == ['able']

    def test_a_type_defined_this_session_is_offered(self, tmp_path):
        # the source holds the session's own game, so what the session has just
        # done is already in it and nothing is read again to see it
        harness = GameHarness(tmp_path)
        harness.create(4, 4, [1, 2])
        session = harness.session(1)
        source = GameNames(session, 1)
        before = candidates('add unit ', roles.CLIENT, source)
        games.define_type(session, AddType(name='tank', symbol='T', attack=3,
                                           health=5, energy=10))

        assert before == []
        assert candidates('add unit ', roles.CLIENT, source) == ['tank']

    def test_a_unit_deployed_this_session_is_offered(self, tmp_path):
        harness = GameHarness(tmp_path)
        harness.create(4, 4, [1, 2])
        session = harness.session(1)
        source = GameNames(session, 1)
        games.define_type(session, AddType(name='tank', symbol='T', attack=3,
                                           health=5, energy=10))
        before = candidates('move ', roles.CLIENT, source)
        games.deploy_unit(session, AddUnit(type_name='tank', name='bravo',
                                           x=2, y=2))

        assert before == []
        assert candidates('move ', roles.CLIENT, source) == ['bravo']

    def test_nothing_is_offered_when_the_player_has_nothing(self, tmp_path):
        harness = GameHarness(tmp_path)
        harness.create(4, 4, [1, 2])
        source = GameNames(harness.session(1), 1)

        assert candidates('move ', roles.CLIENT, source) == []
        assert candidates('add unit ', roles.CLIENT, source) == []

    def test_a_name_slot_without_a_source_offers_nothing(self):
        assert candidates('move ', roles.CLIENT) == []
        assert candidates('add unit ', roles.CLIENT) == []


class TestPaths:

    def test_a_file_is_offered_where_one_is_expected(self, tmp_path, monkeypatch):
        (tmp_path / 'board.yaml').write_text('size_x: 4\n')
        (tmp_path / 'player_1.yaml').write_text('number: 1\n')
        monkeypatch.chdir(tmp_path)

        assert candidates('load board b', roles.SERVER) == ['board.yaml']
        assert candidates('load player p', roles.SERVER) == ['player_1.yaml']

    def test_a_directory_is_offered_with_a_separator(self, tmp_path,
                                                     monkeypatch):
        (tmp_path / 'games').mkdir()
        monkeypatch.chdir(tmp_path)

        assert candidates('load board g', roles.SERVER) == ['games' + os.sep]

    def test_completing_descends_into_a_directory(self, tmp_path, monkeypatch):
        (tmp_path / 'games').mkdir()
        (tmp_path / 'games' / 'board.yaml').write_text('size_x: 4\n')
        monkeypatch.chdir(tmp_path)

        offered = candidates('load board games' + os.sep, roles.SERVER)

        assert offered == [os.path.join('games', 'board.yaml')]

    def test_a_path_with_a_separator_is_one_word(self, tmp_path, monkeypatch):
        (tmp_path / 'games').mkdir()
        (tmp_path / 'games' / 'board.yaml').write_text('size_x: 4\n')
        monkeypatch.chdir(tmp_path)

        # the whole path is the word being completed, so what comes back is a
        # whole path and not the last segment of one
        assert candidates('load board games' + os.sep + 'bo', roles.SERVER) == [
            os.path.join('games', 'board.yaml')]

    def test_nothing_matching_offers_nothing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        assert candidates('load board wibble', roles.SERVER) == []


class TestNothingToOffer:

    def test_a_coordinate_offers_nothing(self, tmp_path):
        source = names(tmp_path)

        assert candidates('add unit tank alpha ', roles.CLIENT, source) == []
        assert candidates('add unit tank alpha 1 ', roles.CLIENT, source) == []
        assert candidates('set board ', roles.SERVER) == []
        assert candidates('set board 4 ', roles.SERVER) == []

    def test_a_statistic_offers_nothing(self, tmp_path):
        source = names(tmp_path)

        assert candidates('add type tank T ', roles.CLIENT, source) == []
        assert candidates('add type tank T 3 5 ', roles.CLIENT, source) == []

    def test_a_name_being_invented_offers_nothing(self, tmp_path):
        source = names(tmp_path)

        assert candidates('add type ', roles.CLIENT, source) == []
        assert candidates('add unit tank ', roles.CLIENT, source) == []

    def test_a_command_that_takes_no_arguments_offers_nothing(self, tmp_path):
        source = names(tmp_path)

        assert candidates('commit ', roles.CLIENT, source) == []
        assert candidates('help ', roles.CLIENT, source) == []
        assert candidates('exit ', roles.CLIENT, source) == []

    def test_a_finished_command_offers_nothing_more(self, tmp_path):
        source = names(tmp_path)

        assert candidates('show units json ', roles.CLIENT, source) == []
        assert candidates('move alpha north ', roles.CLIENT, source) == []


class TestCompletingChangesNothing:

    def snapshot(self, path):
        """Every file under this directory, with its size and its time."""
        found = {}
        for directory, _, files in os.walk(path):
            for name in files:
                whole = os.path.join(directory, name)
                stat = os.stat(whole)
                found[whole] = (stat.st_size, stat.st_mtime_ns)
        return found

    def test_completing_writes_nothing_to_the_game(self, tmp_path):
        harness = a_game(tmp_path)
        session = harness.session(1)
        source = GameNames(session, 1)
        before = self.snapshot(tmp_path)

        for line in ('', 'move ', 'add unit ', 'show ', 'move alpha '):
            for _ in range(3):
                candidates(line, roles.CLIENT, source)

        assert self.snapshot(tmp_path) == before

    def test_completing_does_not_read_the_game_again(self, tmp_path):
        # a session that had been reloaded would have lost this, because it was
        # never saved
        harness = a_game(tmp_path)
        session = harness.session(1)
        session.getBoard().getUnitByName('alpha')[0].setDestroyed(True)

        candidates('move ', roles.CLIENT, GameNames(session, 1))

        assert session.getBoard().getUnitByName('alpha')[0].destroyed


class TestInstallingIt:

    def test_a_session_without_readline_still_runs(self, monkeypatch, capsys):
        # `readline` is absent on some systems, and a session that cannot
        # complete is still a session
        monkeypatch.setitem(sys.modules, 'readline', None)

        assert install(roles.CLIENT) is False
        assert capsys.readouterr().out == ''
        assert capsys.readouterr().err == ''

    def test_installing_it_leaves_readline_completing_whole_words(self):
        readline = pytest.importorskip('readline')
        before = (readline.get_completer(), readline.get_completer_delims())
        try:
            assert install(roles.CLIENT) is True

            assert readline.get_completer() is not None
            # whitespace only, which is what keeps a path one word
            assert readline.get_completer_delims() == ' \t\n'
        finally:
            readline.set_completer(before[0])
            readline.set_completer_delims(before[1])


@pytest.mark.backend('yaml')
class TestCompletingAtARealPrompt:
    """The wiring into `readline`, which needs a terminal to have any effect."""

    def read_for(self, master, seconds, until=None):
        """Whatever the terminal shows within this long, or sooner if it shows it."""
        deadline = time.monotonic() + seconds
        seen = ''
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    seen += os.read(master, 4096).decode('utf-8', 'replace')
                except OSError:
                    break
            if until is not None and until in seen:
                break
        return seen

    def test_tab_completes_a_command(self, tmp_path):
        pytest.importorskip('readline')
        a_game(tmp_path)
        try:
            master, slave = pty.openpty()
        except OSError:
            pytest.skip('no pseudo-terminal available')

        launcher = shutil.which('bgcclient')
        argv = ([launcher] if launcher else
                [sys.executable,
                 os.path.join(ROOT, 'src', 'board_game_concept', 'cli',
                              'bgcclient.py')])
        process = subprocess.Popen(
            argv + ['harness', '1'], cwd=str(tmp_path),
            stdin=slave, stdout=slave, stderr=slave, close_fds=True,
            env=dict(os.environ, TERM='xterm', PYTHONUNBUFFERED='1',
                     BOARD_GAME_BACKEND='yaml'))
        os.close(slave)
        try:
            self.read_for(master, 10, until='bgcclient> ')
            os.write(master, b'sh\t')
            shown = self.read_for(master, 5, until='show')

            assert 'show' in shown
        finally:
            os.write(master, b'\nexit\n')
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            os.close(master)


@pytest.mark.backend('yaml')
def test_a_piped_session_holds_no_escape_sequence(tmp_path):
    """What a role prints to a pipe is what it always printed.

    The suite drives every role through pipes, so this is the one that would
    notice line editing leaking into a transcript.
    """
    a_game(tmp_path)
    launcher = shutil.which('bgcclient')
    argv = ([launcher] if launcher else
            [sys.executable,
             os.path.join(ROOT, 'src', 'board_game_concept', 'cli',
                          'bgcclient.py')])
    result = subprocess.run(
        argv + ['harness', '1'], cwd=str(tmp_path), input='show units\nexit\n',
        capture_output=True, text=True, timeout=30,
        env=dict(os.environ, PYTHONUNBUFFERED='1',
                 BOARD_GAME_BACKEND='yaml'), check=False)

    assert 'bgcclient> ' in result.stdout
    assert '\x1b' not in result.stdout
    assert '\x1b' not in result.stderr
