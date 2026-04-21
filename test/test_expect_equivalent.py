import os
import sys
import time
import shutil
import signal
import unittest
import threading
from pathlib import Path
from subprocess import Popen, PIPE

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / 'test'
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
        self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self._reader_thread.start()

    def _read_output(self):
        while True:
            char = self.proc.stdout.read(1)
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
                        f"Process exited unexpectedly (exit code {self.proc.returncode}). Output:\n{self.output}"
                    )
            time.sleep(0.01)
        with self._lock:
            raise TimeoutError(
                f"Timed out waiting for '{substring}'. Current output:\n{self.output}"
            )

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


class TestExpectEquivalent(unittest.TestCase):
    def setUp(self):
        remove_games_dir()
        self.processes = []

    def tearDown(self):
        for proc in self.processes:
            proc.terminate()
        remove_games_dir()

    def start_server(self, args):
        proc = InteractiveProcess([str(ROOT / 'server.py')] + args, cwd=TEST_DIR)
        self.processes.append(proc)
        return proc

    def start_client(self, game_number, player_number):
        proc = InteractiveProcess([str(ROOT / 'client.py'), game_number, str(player_number)], cwd=TEST_DIR)
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

        # The server should transition out of wait-for-commit after both players have committed.
        server.read_until('board: {', timeout=30)
        self.assertIn('board:', server.output)

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
