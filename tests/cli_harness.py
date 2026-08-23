"""Driving the three command line roles as subprocesses.

The existing integration test carries its own copy of this machinery. This
module is deliberately a separate one so that
`tests/test_server_client_integration.py` can stay untouched while the package
is split into layers, and remain evidence that nothing observable changed.
"""

import os
import sys
import time
import shutil
import threading
import unittest
from pathlib import Path
from subprocess import Popen, PIPE

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / 'tests'
GAMES_DIR = TEST_DIR / 'games'
PYTHON = sys.executable

# the one place that knows where the role entry points live
CLI_DIR = ROOT / 'src' / 'board_game_concept' / 'cli'


def launcher(command, module):
    """How to start a role: the installed command, or its module file.

    The point of the suite is to drive what a user drives, so an installed
    `bgc<role>` on the path wins. Without one - a fresh clone, nothing
    installed - fall back to running the module file with this interpreter,
    which the role's own `sys.path` bootstrap makes work. Either way the role
    names itself from its `PROGRAM` constant, so both launchers produce the
    same prompts and the same usage, and every test below reads the same.
    """
    installed = shutil.which(command)
    if installed is not None:
        return [installed]
    return [PYTHON, str(CLI_DIR / module)]


SERVER = launcher('bgcserver', 'bgcserver.py')
CLIENT = launcher('bgcclient', 'bgcclient.py')
OBSERVER = launcher('bgcobserver', 'bgcobserver.py')

SERVER_PROMPT = 'bgcserver> '
CLIENT_PROMPT = 'bgcclient> '
OBSERVER_PROMPT = 'bgcobserver> '


class InteractiveProcess:
    def __init__(self, args, cwd):
        # an installed console script cannot be handed `-u`, so ask for
        # unbuffered output the way that works for both launchers
        environment = dict(os.environ, PYTHONUNBUFFERED='1')
        self.proc = Popen(
            [str(a) for a in args],
            cwd=str(cwd),
            env=environment,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            universal_newlines=True,
            bufsize=0,
        )
        self.output = ''
        self.errors = ''
        self._lock = threading.Lock()
        self._readers = [
            threading.Thread(target=self._read, args=(self.proc.stdout, 'output'), daemon=True),
            threading.Thread(target=self._read, args=(self.proc.stderr, 'errors'), daemon=True),
        ]
        for reader in self._readers:
            reader.start()

    def _read(self, stream, attribute):
        while True:
            try:
                char = stream.read(1)
            except (ValueError, KeyboardInterrupt):
                break
            if char == '':
                break
            with self._lock:
                setattr(self, attribute, getattr(self, attribute) + char)

    def send_line(self, line):
        if self.proc.stdin:
            self.proc.stdin.write(line + '\n')
            self.proc.stdin.flush()

    def read_until(self, substring, timeout=15):
        """Wait for substring on stdout. Raises if the process dies first."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if substring in self.output:
                    return self.output
            if self.proc.poll() is not None:
                with self._lock:
                    raise ProcessDied(
                        f"exit code {self.proc.returncode} while waiting for "
                        f"{substring!r}\nstdout:\n{self.output}\nstderr:\n{self.errors}")
            time.sleep(0.01)
        with self._lock:
            raise TimeoutError(
                f"timed out waiting for {substring!r}\nstdout:\n{self.output}\n"
                f"stderr:\n{self.errors}")

    def read_until_count(self, substring, count, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if self.output.count(substring) >= count:
                    return self.output
            if self.proc.poll() is not None:
                with self._lock:
                    raise ProcessDied(
                        f"exit code {self.proc.returncode} while waiting for "
                        f"{count} of {substring!r}\nstdout:\n{self.output}\n"
                        f"stderr:\n{self.errors}")
            time.sleep(0.01)
        with self._lock:
            raise TimeoutError(
                f"timed out waiting for {count} of {substring!r}\n"
                f"stdout:\n{self.output}\nstderr:\n{self.errors}")

    def wait_for_exit(self, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            code = self.proc.poll()
            if code is not None:
                return code
            time.sleep(0.01)
        raise TimeoutError(
            f"process still running\nstdout:\n{self.output}\nstderr:\n{self.errors}")

    def close_input(self):
        """Close this role's input, as a pipe running dry does."""
        self.proc.stdin.close()

    def since(self, marker):
        """Everything printed after the last occurrence of marker."""
        with self._lock:
            return self.output.rsplit(marker, 1)[-1]

    def terminate(self):
        if self.proc.poll() is None:
            for kill in (self.proc.terminate, self.proc.kill):
                try:
                    kill()
                    self.proc.wait(timeout=5)
                    break
                except Exception:
                    continue
        for stream in (self.proc.stdout, self.proc.stderr, self.proc.stdin):
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass


class ProcessDied(RuntimeError):
    """A role exited while the test was waiting for it to prompt again."""


def remove_games_dir():
    shutil.rmtree(GAMES_DIR, ignore_errors=True)


class CliTestCase(unittest.TestCase):
    """Starts and stops roles, and cleans the game directory around each test."""

    def setUp(self):
        remove_games_dir()
        self.processes = []

    def tearDown(self):
        for proc in self.processes:
            proc.terminate()
        remove_games_dir()

    def _start(self, args):
        proc = InteractiveProcess(args, cwd=TEST_DIR)
        self.processes.append(proc)
        return proc

    def start_server(self, game_number='test-01'):
        return self._start(SERVER + ['-g', game_number])

    def start_server_with_args(self, args):
        return self._start(SERVER + list(args))

    def start_client(self, game_number, player_number):
        return self._start(CLIENT + [game_number, str(player_number)])

    def start_client_with_args(self, args):
        return self._start(CLIENT + list(args))

    def start_observer(self, game_number):
        return self._start(OBSERVER + [game_number])

    def start_observer_with_args(self, args):
        return self._start(OBSERVER + list(args))

    def start_entry_point(self, role):
        """Call a role's main() with no arguments, as its console script does.

        `pyproject.toml` declares `bgc<role>` as `...cli.bgc<role>:main`, and
        setuptools generates a wrapper that calls it with nothing at all. Run
        in a subprocess that puts `src` on the path itself, so this holds
        whether or not the package happens to be installed.
        """
        code = (f"import sys; sys.path.insert(0, {str(ROOT / 'src')!r}); "
                f"from board_game_concept.cli.bgc{role} import main; main()")
        return self._start([PYTHON, '-c', code])

    def at_prompt(self, proc, prompt):
        """Send nothing; just confirm the role is still asking for input."""
        before = proc.output.count(prompt)
        proc.send_line('')
        proc.read_until_count(prompt, before + 1)

    def established_game(self, game_number='test-01', players=(1, 2)):
        """A server past setup: board sized, players registered, committed."""
        server = self.start_server(game_number)
        server.read_until(SERVER_PROMPT)
        server.send_line('set board 4 4')
        server.read_until_count(SERVER_PROMPT, 2)
        for number in players:
            before = server.output.count(SERVER_PROMPT)
            server.send_line(f'add player {number}')
            server.read_until_count(SERVER_PROMPT, before + 1)
        server.send_line('commit')
        server.read_until('commit complete')
        return server
