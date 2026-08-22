import os
import sys
import time
import shutil
import signal
import unittest
import threading
import yaml
from pathlib import Path
from subprocess import Popen, PIPE

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
        self.proc = Popen(
            [PYTHON, '-u'] + args,
            cwd=str(cwd),
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
            [str(ROOT / 'src' / 'board_game_concept' / 'server.py')] + args,
            cwd=TEST_DIR)
        self.processes.append(proc)
        return proc

    def start_client(self, game_number, player_number):
        proc = InteractiveProcess(
            [str(ROOT / 'src' / 'board_game_concept' / 'client.py'), game_number, str(player_number)],
            cwd=TEST_DIR)
        self.processes.append(proc)
        return proc

    def test_server_interactive_start(self):
        server = self.start_server(['-g', 'test-01'])
        server.read_until('server.py> ')

        server.send_line('set board 4 4')
        server.read_until('server.py> ')

        server.send_line('add player 1')
        server.read_until('server.py> ')

        server.send_line('add player 2')
        server.read_until('server.py> ')

        server.send_line('commit')
        server.read_until('wait for player commit')

        self.assertIn('wait for player commit', server.output)

    def test_server_interactive_load(self):
        server = self.start_server(['-g', 'test-02'])
        server.read_until('server.py> ')

        server.send_line('load board board.yaml')
        server.read_until('server.py> ')

        server.send_line('load player player_1.yaml')
        server.read_until('server.py> ')

        server.send_line('load player player_2.yaml')
        server.read_until('server.py> ')

        server.send_line('commit')
        server.read_until('wait for player commit')

        self.assertIn('wait for player commit', server.output)

    def test_player_interactive_setup(self):
        server = self.start_server(['-g', 'test-01'])
        server.read_until('server.py> ')

        server.send_line('set board 4 4')
        server.read_until('server.py> ')
        server.send_line('add player 1')
        server.read_until('server.py> ')
        server.send_line('add player 2')
        server.read_until('server.py> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        client1 = self.start_client('test-01', 1)
        client1.read_until('client.py> ')

        client1.send_line('add type Cross X 1 1 10')
        client1.read_until('client.py> ')
        client1.send_line('add unit Cross x1 0 0')
        client1.send_line('add unit Cross x2 0 1')
        client1.send_line('add unit Cross x3 0 2')
        client1.send_line('add unit Cross x4 0 3')
        client1.read_until('client.py> ')

        client1.send_line('commit')
        client1.read_until('waiting for turn to complete...')

        client2 = self.start_client('test-01', 2)
        client2.read_until('client.py> ')

        client2.send_line('add type Naught O 1 1 10')
        client2.read_until('client.py> ')
        client2.send_line('add unit Naught o1 3 0')
        client2.send_line('add unit Naught o2 3 1')
        client2.send_line('add unit Naught o3 3 2')
        client2.send_line('add unit Naught o4 3 3')
        client2.read_until('client.py> ')

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
        server.read_until('server.py> ')

        server.send_line('set board 3 3')
        server.read_until('server.py> ')
        server.send_line('add player 1')
        server.read_until('server.py> ')
        server.send_line('add player 2')
        server.read_until('server.py> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        # attack 5 with energy 1: enough energy to move once, never enough to
        # attack, so neither unit can win the square
        client1 = self.start_client('test-01', 1)
        client1.read_until('client.py> ')
        client1.send_line('add type Spent S 5 1 1')
        client1.read_until('client.py> ')
        client1.send_line('add unit Spent s1 0 1')
        client1.read_until('client.py> ')
        client1.send_line('commit')
        client1.read_until('waiting for turn to complete...')

        client2 = self.start_client('test-01', 2)
        client2.read_until('client.py> ')
        client2.send_line('add type Spent T 5 1 1')
        client2.read_until('client.py> ')
        client2.send_line('add unit Spent t1 2 1')
        client2.read_until('client.py> ')
        client2.send_line('commit')
        client2.read_until('waiting for turn to complete...')

        # the deployment turn resolves
        self.read_until_count(server, 'commit complete', 2)

        # now order both units onto the middle square
        client1b = self.start_client('test-01', 1)
        client1b.read_until('client.py> ')
        client1b.send_line('move s1 east')
        client1b.read_until('client.py> ')
        client1b.send_line('commit')
        client1b.read_until('waiting for turn to complete...')

        client2b = self.start_client('test-01', 2)
        client2b.read_until('client.py> ')
        client2b.send_line('move t1 west')
        client2b.read_until('client.py> ')
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
        server.read_until('server.py> ')

        server.send_line('set board 3 3')
        server.read_until('server.py> ')
        server.send_line('add player 1')
        server.read_until('server.py> ')
        server.send_line('add player 2')
        server.read_until('server.py> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        client1 = self.start_client('test-01', 1)
        client1.read_until('client.py> ')
        client1.send_line('add type Cross X 1 1 10')
        client1.read_until('client.py> ')
        client1.send_line('add unit Cross x1 1 1')
        client1.read_until('client.py> ')
        client1.send_line('commit')
        client1.read_until('waiting for turn to complete...')

        client2 = self.start_client('test-01', 2)
        client2.read_until('client.py> ')
        client2.send_line('add type Naught O 1 1 10')
        client2.read_until('client.py> ')
        client2.send_line('add unit Naught o1 1 1')
        client2.read_until('client.py> ')
        client2.send_line('commit')
        client2.read_until('waiting for turn to complete...')

        # the turn resolves rather than taking the server down
        self.read_until_count(server, 'commit complete', 2)

        units_file = GAMES_DIR / '_test-01' / 'data' / 'units.yaml'
        units = yaml.safe_load(units_file.read_text())['units']

        # exactly one of the two deployments was accepted
        self.assertEqual(len(units), 1)
        self.assertEqual((units[0]['x'], units[0]['y']), (1, 1))
        self.assertIn(units[0]['name'], ('x1', 'o1'))

    def test_a_client_refuses_to_deploy_onto_a_square_it_already_holds(self):
        # the same rule, caught at the client before anything is sent
        server = self.start_server(['-g', 'test-01'])
        server.read_until('server.py> ')

        server.send_line('set board 3 3')
        server.read_until('server.py> ')
        server.send_line('add player 1')
        server.read_until('server.py> ')
        server.send_line('add player 2')
        server.read_until('server.py> ')
        server.send_line('commit')
        server.read_until('wait for player commit')

        client1 = self.start_client('test-01', 1)
        client1.read_until('client.py> ')
        client1.send_line('add type Cross X 1 1 10')
        client1.read_until('client.py> ')
        client1.send_line('add unit Cross x1 0 0')
        client1.read_until('client.py> ')
        client1.send_line('add unit Cross x2 0 0')
        client1.read_until('error creating new unit')

        self.assertIn('occupied', client1.output)
        # the client is still usable afterwards
        client1.send_line('add unit Cross x3 1 0')
        client1.read_until('client.py> ')
        client1.send_line('commit')
        client1.read_until('commit complete')

    def test_server_auto_load_equivalent(self):
        server = self.start_server(['-g', 'test-04'])
        server.read_until('server.py> ')

        server.send_line('load board board.yaml')
        server.read_until('server.py> ')

        server.send_line('load player player_1.yaml')
        server.read_until('server.py> ')

        server.send_line('load player player_2.yaml')
        server.read_until('server.py> ')

        server.send_line('commit')
        server.read_until('wait for player commit')
        self.assertIn('wait for player commit', server.output)


if __name__ == '__main__':
    unittest.main()
