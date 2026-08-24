import os
import sys
import time
import shutil
import signal
import unittest
import threading
import pytest
import yaml
from pathlib import Path
from subprocess import Popen, PIPE

# many of these tests reach directly for the YAML files - the units file, the
# rejected file, the seen file - to check what the server wrote. The SQLite
# backend does not put anything at those paths, so the whole module is pinned
# to YAML; the SQLite equivalents would be a whole separate suite of reads
# against the schema, and are not this change's scope
pytestmark = pytest.mark.backend('yaml')


ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / 'tests'
GAMES_DIR = TEST_DIR / 'games'
PYTHON = sys.executable


def remove_games_dir():
    shutil.rmtree(GAMES_DIR, ignore_errors=True)


class InteractiveProcess:
    def __init__(self, args, cwd):
        self.args = args
        self.cwd = cwd
        # the subprocess uses whatever backend the pytest run is using, so a
        # subprocess role and the harness sitting beside it agree on where
        # the game lives
        from game_harness import DEFAULT_BACKEND, BACKEND_ENV
        environment = dict(os.environ)
        environment.setdefault(BACKEND_ENV, DEFAULT_BACKEND)
        self.proc = Popen(
            [PYTHON, '-u'] + args,
            cwd=str(cwd),
            env=environment,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            universal_newlines=True,
            bufsize=0,
        )
        self.output = ''
        self._lock = threading.Lock()
        self._reader_thread = threading.Thread(
            target=self._read_output, daemon=True)
        self._reader_thread.start()

    def _read_output(self):
        while True:
            try:
                char = self.proc.stdout.read(1)
            except KeyboardInterrupt:
                break
            if char == '':
                break
            with self._lock:
                self.output += char

    def send_line(self, line):
        if self.proc.stdin:
            self.proc.stdin.write(line + '\n')
            self.proc.stdin.flush()

    def read_until(self, substring, timeout=10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if substring in self.output:
                    return self.output
            if self.proc.poll() is not None:
                with self._lock:
                    raise RuntimeError(
                        f"Process exited unexpectedly (exit code {self.proc.returncode}). Output:\n{self.output}")
            time.sleep(0.01)
        with self._lock:
            raise TimeoutError(
                f"Timed out waiting for '{substring}'. Current output:\n{self.output}")

    def terminate(self):
        if self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        self.proc.stdout.close()
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stderr:
            self.proc.stderr.close()

    def assert_output_contains(self, substring):
        with self._lock:
            return substring in self.output


class TestServerClientIntegration(unittest.TestCase):
    def setUp(self):
        remove_games_dir()
        self.processes = []

    def tearDown(self):
        for proc in self.processes:
            proc.terminate()
        remove_games_dir()

    def start_server(self, args):
        proc = InteractiveProcess(
            [str(ROOT / 'src' / 'board_game_concept' / 'cli' / 'bgcserver.py')] + args,
            cwd=TEST_DIR)
        self.processes.append(proc)
        return proc

    def start_client(self, game_number, player_number):
        proc = InteractiveProcess(
            [str(ROOT / 'src' / 'board_game_concept' / 'cli' / 'bgcclient.py'), game_number, str(player_number)],
            cwd=TEST_DIR)
        self.processes.append(proc)
        return proc

    def test_server_interactive_start(self):
        server = self.start_server(['-g', 'test-01'])
        server.read_until('bgcserver> ')

        server.send_line('set board 4 4')
        server.read_until('bgcserver> ')

        server.send_line('add player 1')
        server.read_until('bgcserver> ')

        server.send_line('add player 2')
        server.read_until('bgcserver> ')

        server.send_line('commit')
        server.read_until('wait for player commit')

        self.assertIn('wait for player commit', server.output)

    def test_server_interactive_load(self):
        server = self.start_server(['-g', 'test-02'])
        server.read_until('bgcserver> ')

        server.send_line('load board board.yaml')
        server.read_until('bgcserver> ')

        server.send_line('load player player_1.yaml')
        server.read_until('bgcserver> ')

        server.send_line('load player player_2.yaml')
        server.read_until('bgcserver> ')

        server.send_line('commit')
        server.read_until('wait for player commit')

        self.assertIn('wait for player commit', server.output)

    def test_player_interactive_setup(self):
        server = self.start_server(['-g', 'test-01'])
        server.read_until('bgcserver> ')

        server.send_line('set board 4 4')
        server.read_until('bgcserver> ')
        server.send_line('add player 1')
        server.read_until('bgcserver> ')
        server.send_line('add player 2')
        server.read_until('bgcserver> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        client1 = self.start_client('test-01', 1)
        client1.read_until('bgcclient> ')

        client1.send_line('add type Cross X 1 1 10')
        client1.read_until('bgcclient> ')
        client1.send_line('add unit Cross x1 0 0')
        client1.send_line('add unit Cross x2 0 1')
        client1.send_line('add unit Cross x3 0 2')
        client1.send_line('add unit Cross x4 0 3')
        client1.read_until('bgcclient> ')

        client1.send_line('commit')
        client1.read_until('waiting for turn to complete...')

        client2 = self.start_client('test-01', 2)
        client2.read_until('bgcclient> ')

        client2.send_line('add type Naught O 1 1 10')
        client2.read_until('bgcclient> ')
        client2.send_line('add unit Naught o1 3 0')
        client2.send_line('add unit Naught o2 3 1')
        client2.send_line('add unit Naught o3 3 2')
        client2.send_line('add unit Naught o4 3 3')
        client2.read_until('bgcclient> ')

        client2.send_line('commit')
        client2.read_until('waiting for turn to complete...')

        # The server should transition out of wait-for-commit after both
        # players have committed.
        server.read_until('board: {', timeout=30)
        self.assertIn('board:', server.output)

    def read_until_count(self, proc, substring, count, timeout=90):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with proc._lock:
                if proc.output.count(substring) >= count:
                    return proc.output
            if proc.proc.poll() is not None:
                with proc._lock:
                    raise RuntimeError(
                        f"Server exited unexpectedly (exit code {proc.proc.returncode}). "
                        f"Output:\n{proc.output}")
            time.sleep(0.05)
        with proc._lock:
            raise TimeoutError(
                f"Timed out waiting for {count} occurrences of '{substring}'. "
                f"Current output:\n{proc.output}")

    def test_two_units_moving_onto_the_same_square_resolve_the_turn(self):
        # issue #2: two units too spent to attack, ordered onto the same square,
        # used to spin forever in the server's commit and block every player.
        # The server prints "commit complete" once per resolved turn: the
        # interactive setup, then the deployment, then the contested move.
        server = self.start_server(['-g', 'test-01'])
        server.read_until('bgcserver> ')

        server.send_line('set board 3 3')
        server.read_until('bgcserver> ')
        server.send_line('add player 1')
        server.read_until('bgcserver> ')
        server.send_line('add player 2')
        server.read_until('bgcserver> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        # attack 5 with energy 1: enough energy to move once, never enough to
        # attack, so neither unit can win the square
        client1 = self.start_client('test-01', 1)
        client1.read_until('bgcclient> ')
        client1.send_line('add type Spent S 5 1 1')
        client1.read_until('bgcclient> ')
        client1.send_line('add unit Spent s1 0 1')
        client1.read_until('bgcclient> ')
        client1.send_line('commit')
        client1.read_until('waiting for turn to complete...')

        client2 = self.start_client('test-01', 2)
        client2.read_until('bgcclient> ')
        client2.send_line('add type Spent T 5 1 1')
        client2.read_until('bgcclient> ')
        client2.send_line('add unit Spent t1 2 1')
        client2.read_until('bgcclient> ')
        client2.send_line('commit')
        client2.read_until('waiting for turn to complete...')

        # the deployment turn resolves
        self.read_until_count(server, 'commit complete', 2)

        # now order both units onto the middle square
        client1b = self.start_client('test-01', 1)
        client1b.read_until('bgcclient> ')
        client1b.send_line('move s1 east')
        client1b.read_until('bgcclient> ')
        client1b.send_line('commit')
        client1b.read_until('waiting for turn to complete...')

        client2b = self.start_client('test-01', 2)
        client2b.read_until('bgcclient> ')
        client2b.send_line('move t1 west')
        client2b.read_until('bgcclient> ')
        client2b.send_line('commit')
        client2b.read_until('waiting for turn to complete...')

        # the contested turn resolves rather than spinning
        self.read_until_count(server, 'commit complete', 3)

        # nobody won the contested square: both units fell back to where they
        # started, and neither was destroyed
        units_file = GAMES_DIR / '_test-01' / 'data' / 'units.yaml'
        units = yaml.safe_load(units_file.read_text())['units']
        by_name = {unit['name']: unit for unit in units}

        self.assertEqual((by_name['s1']['x'], by_name['s1']['y']), (0, 1))
        self.assertEqual((by_name['t1']['x'], by_name['t1']['y']), (2, 1))
        self.assertFalse(by_name['s1']['destroyed'])
        self.assertFalse(by_name['t1']['destroyed'])

    def test_two_players_deploying_onto_the_same_square(self):
        # issue #1: on the first turn neither player can see the other's units,
        # so both may claim the same square. The server used to die on an
        # assertion; it now refuses the second deployment and resolves the turn
        server = self.start_server(['-g', 'test-01'])
        server.read_until('bgcserver> ')

        server.send_line('set board 3 3')
        server.read_until('bgcserver> ')
        server.send_line('add player 1')
        server.read_until('bgcserver> ')
        server.send_line('add player 2')
        server.read_until('bgcserver> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        client1 = self.start_client('test-01', 1)
        client1.read_until('bgcclient> ')
        client1.send_line('add type Cross X 1 1 10')
        client1.read_until('bgcclient> ')
        client1.send_line('add unit Cross x1 1 1')
        client1.read_until('bgcclient> ')
        client1.send_line('commit')
        client1.read_until('waiting for turn to complete...')

        client2 = self.start_client('test-01', 2)
        client2.read_until('bgcclient> ')
        client2.send_line('add type Naught O 1 1 10')
        client2.read_until('bgcclient> ')
        client2.send_line('add unit Naught o1 1 1')
        client2.read_until('bgcclient> ')
        client2.send_line('commit')
        client2.read_until('waiting for turn to complete...')

        # the turn resolves rather than taking the server down
        self.read_until_count(server, 'commit complete', 2)

        units_file = GAMES_DIR / '_test-01' / 'data' / 'units.yaml'
        units = yaml.safe_load(units_file.read_text())['units']

        # neither deployment was accepted. Letting the first through made
        # the winner whichever player the server read first, which is player
        # number order, in a race neither of them could see they were in
        self.assertEqual(units, 'None')

        # and both players are told, by name and square
        players_dir = GAMES_DIR / '_test-01' / 'players'
        for number, unit_name in ((1, 'x1'), (2, 'o1')):
            refused = yaml.safe_load(
                (players_dir / f'{number}_rejected.yaml').read_text())['rejected']
            self.assertEqual(len(refused), 1)
            self.assertEqual(refused[0]['unit'], unit_name)
            self.assertEqual((refused[0]['x'], refused[0]['y']), (1, 1))
            self.assertIn('both were refused', refused[0]['reason'])

        # and each sees it when they next log in
        for number, unit_name in ((1, 'x1'), (2, 'o1')):
            client = self.start_client('test-01', number)
            client.read_until('bgcclient> ')
            self.assertIn('rejected last turn', client.output)
            self.assertIn(unit_name, client.output)
            client.send_line('commit')
            client.read_until('commit complete')

        # a later turn in which nothing is refused clears the report, so
        # rejections describe the last turn rather than accumulating
        self.read_until_count(server, 'commit complete', 3)
        for number in (1, 2):
            self.assertEqual(yaml.safe_load(
                (players_dir / f'{number}_rejected.yaml').read_text())['rejected'],
                [])

    def test_an_order_with_an_invalid_state_is_rejected_not_fatal(self):
        # game-persistence requires the server to reject an order whose state
        # is not INITIAL, MOVING or NOP. It used to assert and take the server
        # down with it
        server = self.start_server(['-g', 'test-01'])
        server.read_until('bgcserver> ')

        server.send_line('set board 3 3')
        server.read_until('bgcserver> ')
        server.send_line('add player 1')
        server.read_until('bgcserver> ')
        server.send_line('add player 2')
        server.read_until('bgcserver> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        client1 = self.start_client('test-01', 1)
        client1.read_until('bgcclient> ')
        client1.send_line('add type Cross X 1 1 10')
        client1.read_until('bgcclient> ')
        client1.send_line('add unit Cross x1 0 0')
        client1.read_until('bgcclient> ')
        client1.send_line('commit')
        client1.read_until('waiting for turn to complete...')

        # corrupt player 1's published order while the server is still waiting
        # on player 2, so it is read exactly once, as published
        orders_file = GAMES_DIR / '_test-01' / 'players' / '1_units.yaml'
        orders = yaml.safe_load(orders_file.read_text())
        orders['units'][0]['state'] = 99
        orders_file.write_text(yaml.safe_dump(orders))

        client2 = self.start_client('test-01', 2)
        client2.read_until('bgcclient> ')
        client2.send_line('add type Naught O 1 1 10')
        client2.read_until('bgcclient> ')
        client2.send_line('add unit Naught o1 2 2')
        client2.read_until('bgcclient> ')
        client2.send_line('commit')
        client2.read_until('waiting for turn to complete...')

        # the turn still resolves, without the invalid order
        self.read_until_count(server, 'commit complete', 2)

        units_file = GAMES_DIR / '_test-01' / 'data' / 'units.yaml'
        units = yaml.safe_load(units_file.read_text())['units']
        self.assertEqual([unit['name'] for unit in units], ['o1'])

        players_dir = GAMES_DIR / '_test-01' / 'players'
        refused = yaml.safe_load(
            (players_dir / '1_rejected.yaml').read_text())['rejected']
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0]['unit'], 'x1')
        self.assertIn('invalid unit state', refused[0]['reason'])

    def test_a_client_refuses_to_deploy_onto_a_square_it_already_holds(self):
        # the same rule, caught at the client before anything is sent
        server = self.start_server(['-g', 'test-01'])
        server.read_until('bgcserver> ')

        server.send_line('set board 3 3')
        server.read_until('bgcserver> ')
        server.send_line('add player 1')
        server.read_until('bgcserver> ')
        server.send_line('add player 2')
        server.read_until('bgcserver> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        client1 = self.start_client('test-01', 1)
        client1.read_until('bgcclient> ')
        client1.send_line('add type Cross X 1 1 10')
        client1.read_until('bgcclient> ')
        client1.send_line('add unit Cross x1 0 0')
        client1.read_until('bgcclient> ')
        client1.send_line('add unit Cross x2 0 0')
        client1.read_until('error creating new unit')

        self.assertIn('occupied', client1.output)
        # the client is still usable afterwards
        client1.send_line('add unit Cross x3 1 0')
        client1.read_until('bgcclient> ')
        client1.send_line('commit')
        client1.read_until('commit complete')

    def test_client_reads_a_view_of_a_unit_it_fought_for_several_rounds(self):
        # issue #3: a fight lasting several rounds recorded the same contact
        # once per attack, so the view written for each player named the enemy
        # unit once per attack and the client died restoring it a second time
        server = self.start_server(['-g', 'test-01'])
        server.read_until('bgcserver> ')

        server.send_line('set board 3 3')
        server.read_until('bgcserver> ')
        server.send_line('add player 1')
        server.read_until('bgcserver> ')
        server.send_line('add player 2')
        server.read_until('bgcserver> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        # attack 1 against health 3 and 10: several rounds of attrition before
        # the cross wins the square
        client1 = self.start_client('test-01', 1)
        client1.read_until('bgcclient> ')
        client1.send_line('add type Cross X 1 10 100')
        client1.read_until('bgcclient> ')
        client1.send_line('add unit Cross x1 0 1')
        client1.read_until('bgcclient> ')
        client1.send_line('commit')
        client1.read_until('waiting for turn to complete...')

        client2 = self.start_client('test-01', 2)
        client2.read_until('bgcclient> ')
        client2.send_line('add type Naught O 1 3 100')
        client2.read_until('bgcclient> ')
        client2.send_line('add unit Naught o1 2 1')
        client2.read_until('bgcclient> ')
        client2.send_line('commit')
        client2.read_until('waiting for turn to complete...')

        # the deployment turn resolves
        self.read_until_count(server, 'commit complete', 2)

        # order the units into the same square, so that they fight
        client1b = self.start_client('test-01', 1)
        client1b.read_until('bgcclient> ')
        client1b.send_line('move x1 east')
        client1b.read_until('bgcclient> ')
        client1b.send_line('commit')
        client1b.read_until('waiting for turn to complete...')

        client2b = self.start_client('test-01', 2)
        client2b.read_until('bgcclient> ')
        client2b.send_line('move o1 west')
        client2b.read_until('bgcclient> ')
        client2b.send_line('commit')
        client2b.read_until('waiting for turn to complete...')

        # the fight resolves
        self.read_until_count(server, 'commit complete', 3)

        # the view written for the winner names the enemy it fought once
        players_dir = GAMES_DIR / '_test-01' / 'players'
        seen = yaml.safe_load(
            (players_dir / '1_units_seen.yaml').read_text())['units']
        self.assertEqual(
            sorted(unit['name'] for unit in seen), ['o1', 'x1'])

        # and a client reading that view starts and lists the enemy once,
        # rather than dying on the second copy of it
        client1c = self.start_client('test-01', 1)
        client1c.read_until('bgcclient> ')
        client1c.send_line('show units')
        # wait for the prompt that follows the listing, not the one before it
        self.read_until_count(client1c, 'bgcclient> ', 2, timeout=15)
        self.assertNotIn('already exists', client1c.output)
        # one row of the units table names it, not two
        listed = [line.split() for line in client1c.output.splitlines()]
        named = [cells for cells in listed
                 if len(cells) > 1 and cells[1] == 'o1']
        self.assertEqual(len(named), 1)

    def test_server_auto_load_equivalent(self):
        server = self.start_server(['-g', 'test-04'])
        server.read_until('bgcserver> ')

        server.send_line('load board board.yaml')
        server.read_until('bgcserver> ')

        server.send_line('load player player_1.yaml')
        server.read_until('bgcserver> ')

        server.send_line('load player player_2.yaml')
        server.read_until('bgcserver> ')

        server.send_line('commit')
        server.read_until('wait for player commit')
        self.assertIn('wait for player commit', server.output)


if __name__ == '__main__':
    unittest.main()


class TestWorkSurvivesASession(unittest.TestCase):
    """A session that ends before it commits does not cost its owner the work.

    This is the behaviour the drafting change exists for, so it is driven the
    way a person would hit it: kill the process, start it again for the same
    game, and see what is there.
    """

    def setUp(self):
        remove_games_dir()
        self.processes = []

    def tearDown(self):
        for proc in self.processes:
            proc.terminate()
        remove_games_dir()

    # --- driving a role

    def _start(self, args):
        proc = InteractiveProcess(args, cwd=TEST_DIR)
        self.processes.append(proc)
        return proc

    def start_server(self, game_number='test-01'):
        return self._start(
            [str(ROOT / 'src' / 'board_game_concept' / 'cli' / 'bgcserver.py'),
             '-g', game_number])

    def start_client(self, game_number, player_number):
        return self._start(
            [str(ROOT / 'src' / 'board_game_concept' / 'cli' / 'bgcclient.py'),
             game_number, str(player_number)])

    def wait_for(self, proc, substring, count, timeout=60):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if proc.output.count(substring) >= count:
                return
            time.sleep(0.01)
        raise AssertionError(f"timed out waiting for {count} of {substring!r}"
                             f"\n{proc.output}")

    def shown(self, proc, prompt, command):
        """Everything a role printed for one command, between two prompts."""
        before = proc.output.count(prompt)
        proc.send_line(command)
        self.wait_for(proc, prompt, before + 1)
        return proc.output.rsplit(prompt, 2)[-2].strip()

    def typed(self, proc, prompt, command):
        """Send a command and wait for the role to ask for another."""
        self.shown(proc, prompt, command)

    def established_game(self, game_number='test-01', players=(1,)):
        server = self.start_server(game_number)
        self.wait_for(server, 'bgcserver> ', 1)
        self.typed(server, 'bgcserver> ', 'set board 4 4')
        for number in players:
            self.typed(server, 'bgcserver> ', f'add player {number}')
        server.send_line('commit')
        server.read_until('commit complete')
        return server

    def with_an_army(self, game_number='test-01', player=1):
        """A client past setup, holding a unit the server has published."""
        self.established_game(game_number, players=(player,))
        client = self.start_client(game_number, player)
        self.wait_for(client, 'bgcclient> ', 1)
        self.typed(client, 'bgcclient> ', 'add type Cross X 1 5 10')
        self.typed(client, 'bgcclient> ', 'add unit Cross x1 1 1')
        before = client.output.count('bgcclient> ')
        client.send_line('commit')
        client.read_until('commit complete')
        # the sole player's commit satisfies the barrier, so the turn resolves
        self.wait_for(client, 'bgcclient> ', before + 1)
        return client

    def _repository(self, game_number='test-01'):
        from board_game_concept import YamlGameRepository
        return YamlGameRepository(game_number, base_path=str(TEST_DIR))

    def published_turn(self, game_number='test-01'):
        """The last turn the server has published, or 0 before any."""
        repository = self._repository(game_number)
        with repository.held(read=True):
            progress = repository.read_progress() or {}
        return int(progress.get('turn') or 0)

    def published_square(self, name, after, game_number='test-01',
                         timeout=60):
        """Where the named unit is, once a turn later than `after` is published.

        Both reads happen inside one hold of the game. Read separately and
        unheld, they can straddle a resolution: the turn number is written
        early in publishing a turn and the units late, so an unheld reader can
        see the new turn beside the old board and believe both.

        Waited for on the turn number rather than on the unit's state, because
        a unit that is not `MOVING` only means some turn has been through it -
        and the turn that deployed it satisfies that too.
        """
        repository = self._repository(game_number)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with repository.held(read=True):
                progress = repository.read_progress() or {}
                if int(progress.get('turn') or 0) > after:
                    for unit in repository.read_units():
                        if unit['name'] == name:
                            return (unit['x'], unit['y'])
            time.sleep(0.02)
        raise AssertionError(
            f"the server published no turn after {after} holding {name}")

    def unit_names(self, proc):
        """The unit names a client lists, read off its `show units` table."""
        listed = self.shown(proc, 'bgcclient> ', 'show units').splitlines()
        return [line.split()[1] for line in listed[1:]]

    # --- what survives

    def test_a_client_killed_mid_setup_gets_its_army_back(self):
        self.established_game(players=(1,))

        doomed = self.start_client('test-01', 1)
        self.wait_for(doomed, 'bgcclient> ', 1)
        self.typed(doomed, 'bgcclient> ', 'add type Cross X 1 5 10')
        self.typed(doomed, 'bgcclient> ', 'add unit Cross x1 0 0')
        self.typed(doomed, 'bgcclient> ', 'add unit Cross x2 1 0')
        doomed.terminate()

        revived = self.start_client('test-01', 1)
        self.wait_for(revived, 'bgcclient> ', 1)

        self.assertEqual(self.unit_names(revived), ['x1', 'x2'])
        # the type is back too, or the units could not have been
        self.assertIn('Cross', self.shown(revived, 'bgcclient> ', 'show types'))

        # and the work that was restored commits
        revived.send_line('commit')
        revived.read_until('commit complete')

    def test_a_client_killed_mid_turn_gets_its_order_back(self):
        client = self.with_an_army()
        self.typed(client, 'bgcclient> ', 'move x1 north')
        client.terminate()

        revived = self.start_client('test-01', 1)
        self.wait_for(revived, 'bgcclient> ', 1)

        listed = self.shown(revived, 'bgcclient> ', 'show units')
        self.assertIn('moving', listed)
        self.assertIn('north', listed)

    def test_a_restored_order_can_be_changed_before_committing(self):
        client = self.with_an_army()
        self.typed(client, 'bgcclient> ', 'move x1 north')
        client.terminate()

        revived = self.start_client('test-01', 1)
        self.wait_for(revived, 'bgcclient> ', 1)
        # the turn the deployment resolved into, so that what is waited for
        # below is the turn the *move* resolves into and not that one
        deployed_on = self.published_turn()
        self.typed(revived, 'bgcclient> ', 'move x1 south')
        revived.send_line('commit')
        revived.read_until('commit complete')

        # only the later order was taken: the unit moved south from (1, 1)
        self.assertEqual(self.published_square('x1', after=deployed_on), (1, 2))

    def test_a_server_killed_during_setup_gets_its_setup_back(self):
        doomed = self.start_server('test-01')
        self.wait_for(doomed, 'bgcserver> ', 1)
        self.typed(doomed, 'bgcserver> ', 'set board 5 6')
        self.typed(doomed, 'bgcserver> ', 'add player 1')
        self.typed(doomed, 'bgcserver> ', 'add player 2')
        doomed.terminate()

        revived = self.start_server('test-01')
        self.wait_for(revived, 'bgcserver> ', 1)

        listed = self.shown(revived, 'bgcserver> ', 'show players')
        self.assertIn('1', listed)
        self.assertIn('2', listed)

        revived.send_line('commit')
        revived.read_until('commit complete')
        board = yaml.safe_load(
            (GAMES_DIR / '_test-01' / 'data' / 'board.yaml').read_text())
        self.assertEqual(board['board'], {'size_x': 5, 'size_y': 6})

    def test_a_draft_does_not_hold_the_turn_open(self):
        """Drafting is not committing, and the barrier counts commits."""
        server = self.established_game(players=(1, 2))
        server.read_until('wait for player commit')

        drafting = self.start_client('test-01', 1)
        self.wait_for(drafting, 'bgcclient> ', 1)
        self.typed(drafting, 'bgcclient> ', 'add type Cross X 1 5 10')
        self.typed(drafting, 'bgcclient> ', 'add unit Cross x1 0 0')

        other = self.start_client('test-01', 2)
        self.wait_for(other, 'bgcclient> ', 1)
        self.typed(other, 'bgcclient> ', 'add type Ring O 1 5 10')
        self.typed(other, 'bgcclient> ', 'add unit Ring o1 3 3')
        other.send_line('commit')
        other.read_until('commit complete')

        # player 1 has drafted and not committed, so the turn stays open
        time.sleep(1)
        self.assertEqual(server.output.count('commit complete'), 1)

        drafting.send_line('commit')
        drafting.read_until('commit complete')
        self.wait_for(server, 'commit complete', 2)
