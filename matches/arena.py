#!/usr/bin/env python3
"""Play one two-player game between two bots, through the real CLI roles.

Nothing here reaches into the game's storage or its domain objects. A match is
driven exactly as three people at three terminals would drive it: `bgcserver`
sets the board and registers the players and then resolves each turn, and one
`bgcclient` session per player stays open for the whole game, typing that
player's orders and committing. Sessions are long-lived and take their turns in
the order the integration tests use - player 1 commits and blocks, then player
2 commits and the turn resolves - because a local game directory is held by one
process at a time.

**The rule this harness exists to keep: a bot is handed its own player view and
nothing else.** `read_view` types `show ... json` into that player's own
session, so the visibility rules (R6) decide what comes back - an enemy unit is
in it only if it was fought last turn. The two views are never mixed. The
observer, which sees everything (R6.5), is read only to write the match log,
after both players have already given their orders for that turn.
"""

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / 'venv' / 'bin'
LOGS = ROOT / 'matches' / 'logs'

ENV = dict(os.environ)
ENV.update({
    'BOARD_GAME_BACKEND': 'sqlite',
    # this harness runs the game out of a local directory; without this the
    # roles probe 127.0.0.1:8080 for an API server first
    'BOARD_GAME_NO_REDIRECT': '1',
    'PYTHONUNBUFFERED': '1',
})

PROMPT = re.compile(r'bgc(client|server|observer)> ')


def load_bot(path, player):
    """Import a bot module and build its Bot for this player number."""
    path = Path(path)
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f'bot_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.Bot(player)


def json_docs(text):
    """Every JSON document in a session transcript, in the order printed.

    Only a brace in the first column starts one. A `show units json` document
    is printed indented, so its unit objects are complete JSON too, and
    counting those as documents is how a half-printed answer came to look
    like a whole one.
    """
    text = PROMPT.sub('', text)
    decoder = json.JSONDecoder()
    docs = []
    at = 0
    while True:
        at = text.find('{', at)
        if at < 0:
            return docs
        if at and text[at - 1] != '\n':
            at += 1
            continue
        try:
            doc, end = decoder.raw_decode(text, at)
        except ValueError:
            at += 1
            continue
        docs.append(doc)
        at = end


class Session:
    """One CLI role, left running, typed at and read from like a terminal."""

    def __init__(self, argv, transcript):
        self.argv = argv
        self.transcript = open(transcript, 'w', encoding='utf-8')
        self.output = ''
        self.lock = threading.Lock()
        self.proc = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, env=ENV, cwd=ROOT, bufsize=1)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        while True:
            chunk = self.proc.stdout.read(1)
            if not chunk:
                return
            with self.lock:
                self.output += chunk
                self.transcript.write(chunk)
                self.transcript.flush()

    def mark(self):
        with self.lock:
            return len(self.output)

    def since(self, mark):
        with self.lock:
            return self.output[mark:]

    def send(self, line):
        self.proc.stdin.write(line + '\n')
        self.proc.stdin.flush()

    def wait_for(self, predicate, timeout=120, poll=0.05):
        """Wait until the session has said something that satisfies this."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.lock:
                text = self.output
            if predicate(text):
                return text
            if self.proc.poll() is not None:
                # one last look: the process may have said it and then exited
                with self.lock:
                    text = self.output
                if predicate(text):
                    return text
                raise RuntimeError(f'{self.argv[0]} exited: {text[-800:]}')
            time.sleep(poll)
        raise TimeoutError(f'{self.argv[0]} timed out: {self.output[-800:]}')

    def ask(self, mark, commands, documents):
        """Type these `show ... json` commands and read the answers back."""
        for command in commands:
            self.send(command)
        self.wait_for(lambda text: len(json_docs(text[mark:])) >= documents)
        return json_docs(self.since(mark))

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send('exit')
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
        self.transcript.close()


class Match:
    #: consecutive orderless turns after which a bot is called out in the log
    STALLED = 30

    def __init__(self, gameno, bots, max_turns=100, budgets=None, split=True):
        self.gameno = gameno
        self.bots = bots                      # {player_number: Bot}
        self.max_turns = max_turns
        self.budgets = budgets or {}          # {player_number: points}
        self.split = split                    # deploy in your own half only
        self.log_file = open(LOGS / f'game_{gameno}.log', 'w',
                             encoding='utf-8')
        self.server = None
        self.clients = {}
        self.observer = None
        self.outcome = None
        self.turn = 0
        self.history = []

    def log(self, *parts):
        line = ' '.join(str(part) for part in parts)
        print(line, flush=True)
        self.log_file.write(line + '\n')
        self.log_file.flush()

    # ----------------------------------------------------------------- set up

    def create(self):
        directory = ROOT / 'games' / f'_{self.gameno}'
        if directory.exists():
            shutil.rmtree(directory)
        self.server = Session(
            [str(BIN / 'bgcserver'), '-g', str(self.gameno),
             '--backend', 'sqlite'], LOGS / f'game_{self.gameno}_server.txt')
        self.server.wait_for(lambda text: 'bgcserver> ' in text)
        setup = ['set board 10 10']
        for player in sorted(self.bots):
            points = self.budgets.get(player)
            setup.append(f'add player {player}'
                         + (f' {points}' if points else ''))
        setup.append('commit')
        for line in setup:
            self.server.send(line)
        self.server.wait_for(lambda text: 'wait for player commit' in text)
        for player in sorted(self.bots):
            session = Session(
                [str(BIN / 'bgcclient'), str(self.gameno), str(player)],
                LOGS / f'game_{self.gameno}_p{player}.txt')
            session.wait_for(lambda text: 'bgcclient> ' in text)
            self.clients[player] = session

    # -------------------------------------------------------------- the referee

    def half(self, player, size_y=10):
        """The rows this player may deploy in, under the split-board rule.

        The game itself lets a player deploy anywhere on the board (R2.6), so
        halving it is a house rule, and a house rule needs a referee. Player 1
        holds the north half, player 2 the south; the frontier runs between
        them and nothing stops a unit crossing it once play has started.
        """
        if not self.split:
            return range(size_y)
        if player == 1:
            return range(0, size_y // 2)
        return range(size_y - size_y // 2, size_y)

    def vet(self, player, commands):
        """Drop any deployment outside this player's half, and say so."""
        allowed = self.half(player)
        kept = []
        for command in commands:
            parts = command.split()
            if parts[:1] == ['add'] and parts[1:2] == ['unit']:
                y = int(parts[5])
                if y not in allowed:
                    self.log(f'    p{player}: REFEREE refused "{command}" - '
                             f'y={y} is outside rows '
                             f'{allowed.start}-{allowed.stop - 1}')
                    continue
            kept.append(command)
        return kept

    # ------------------------------------------------------------------ views

    def read_view(self, player):
        """What this player may see, asked for in their own session.

        This is the only thing a bot is ever given.
        """
        session = self.clients[player]
        mark = session.mark()
        docs = session.ask(mark, ['show board json', 'show units json',
                                  'show players json', 'show types json'], 4)
        view = {'turn': self.turn, 'me': player, 'rejected': []}
        for doc in docs:
            view.update(doc)
        for line in PROMPT.sub('', session.since(mark)).splitlines():
            if line.strip().startswith('- '):
                view['rejected'].append(line.strip())
        return view

    def observe(self):
        """The whole board, for the match log. Never given to a bot."""
        if self.observer is None or self.observer.proc.poll() is not None:
            self.observer = Session(
                [str(BIN / 'bgcobserver'), str(self.gameno)],
                LOGS / f'game_{self.gameno}_observer.txt')
            self.observer.wait_for(lambda text: 'bgcobserver> ' in text)
        mark = self.observer.mark()
        self.observer.send('reload')
        docs = self.observer.ask(mark, ['show units json'], 1)
        mark2 = self.observer.mark()
        self.observer.send('show board')
        self.observer.wait_for(
            lambda text: text[mark2:].count('bgcobserver> ') >= 1
            and '+-+' in text[mark2:])
        time.sleep(0.3)
        board = '\n'.join(
            line for line in PROMPT.sub('', self.observer.since(mark2))
            .splitlines() if line.strip())
        return board, (docs[0]['units'] if docs else [])

    # ------------------------------------------------------------------- play

    def give(self, player, commands):
        """Type one player's orders and commit them.

        Player 1 commits and blocks at the barrier; player 2's commit is what
        lets the server resolve the turn (R3.1).
        """
        session = self.clients[player]
        mark = session.mark()
        for command in commands:
            session.send(command)
        if commands:
            session.wait_for(
                lambda text: text[mark:].count('bgcclient> ') >= len(commands))
        mark = session.mark()
        session.send('commit')
        session.wait_for(
            lambda text: ('waiting for turn to complete' in text[mark:]
                          or 'the game is over' in text[mark:]
                          or 'out of the game' in text[mark:]
                          or 'bgcclient> ' in text[mark:]))
        return mark

    def resolved(self, player, mark):
        """Wait for this player's session to come back from the barrier."""
        session = self.clients[player]
        try:
            session.wait_for(
                lambda text: 'bgcclient> ' in text[mark:].split(
                    'waiting for turn to complete...')[-1], timeout=180)
        except (TimeoutError, RuntimeError) as error:
            self.log(f'    p{player}: {error}')
        text = session.since(mark)
        for line in PROMPT.sub('', text).splitlines():
            line = line.strip()
            if line.startswith('game over'):
                self.outcome = line
            if (line.endswith('rejected last turn:') or line.startswith('- ')
                    or 'out of the game' in line):
                self.log(f'    p{player}: {line}')

    def phase(self, orders):
        marks = {}
        for player in sorted(orders):
            marks[player] = self.give(player, orders[player])
        for player in sorted(orders):
            self.resolved(player, marks[player])

    def play(self):
        self.create()
        self.log(f'=== game {self.gameno}: '
                 f'p1 {self.bots[1].name} vs p2 {self.bots[2].name}')
        points = ' / '.join(f'p{p}: {self.budgets.get(p, 100)}'
                            for p in sorted(self.bots))
        self.log(f'  board 10x10, budget {points}, deployment '
                 + ('split: p1 in rows 0-4, p2 in rows 5-9'
                    if self.split else 'anywhere'))
        for player, bot in self.bots.items():
            self.log(f'  p{player} {bot.name}: {bot.doctrine}')

        orders = {}
        for player, bot in self.bots.items():
            commands = self.vet(player, bot.setup(self.read_view(player)))
            orders[player] = commands
            self.log(f'  p{player} deploys: {"; ".join(commands)}')
        self.turn = 1
        self.phase(orders)
        self.record()

        # consecutive turns each player has given no order at all. A doctrine
        # is entitled to wait - resting is a move (R3.9), and a defender that
        # holds is playing - but a doctrine that has not given an order in
        # thirty turns has usually stopped playing rather than chosen to wait,
        # and the last time that happened it was a bot keying off a type name
        # its army no longer used. Silent is the wrong thing for that to be
        idle = {player: 0 for player in self.bots}
        while self.outcome is None and self.turn < self.max_turns:
            self.turn += 1
            orders = {}
            for player, bot in self.bots.items():
                view = self.read_view(player)
                orders[player] = bot.orders(view)
            self.log(f'  -- turn {self.turn}')
            for player in sorted(orders):
                self.log(f'    p{player}: '
                         f'{"; ".join(orders[player]) or "holds"}')
                idle[player] = 0 if orders[player] else idle[player] + 1
                if idle[player] == self.STALLED:
                    self.log(f'    ** p{player} has given no order in '
                             f'{self.STALLED} turns')
            self.phase(orders)
            self.record()

        for player, count in sorted(idle.items()):
            if count >= self.STALLED:
                self.log(f'  ** p{player} finished the game having given no '
                         f'order for {count} turns')

        board, units = self.observe()
        self.log(board)
        self.log(f'  {self.outcome}' if self.outcome
                 else f'  undecided after {self.turn} turns')
        self.summarise(units)
        self.close()
        return self.outcome

    def record(self):
        board, units = self.observe()
        alive, spent = {}, {}
        for unit in units:
            # a unit off the board has no square; `state` says why. What keeps
            # a player in the game is holding a unit that could act again
            # (R7.1), which is every unit except a wall - and a wall is the
            # only thing with no attack (R2.10). A unit merely out of energy
            # counts, because resting gives it back
            if unit.get('x') is None:
                continue
            tally = alive if unit['attack'] > 0 else spent
            tally[unit['player']] = tally.get(unit['player'], 0) + 1
        self.history.append({'turn': self.turn, 'board': board,
                             'units': units, 'alive': alive, 'spent': spent})
        note = ''
        if spent:
            note = f"  (walls: {spent.get(1, 0)} v {spent.get(2, 0)})"
        self.log(f'    after turn {self.turn}: in play '
                 f'{alive.get(1, 0)} v {alive.get(2, 0)}{note}')

    def summarise(self, units):
        self.log('  final units:')
        for unit in sorted(units, key=lambda u: (u['player'], u['name'])):
            state = unit['state'] if unit.get('x') is None else (
                f"({unit['x']},{unit['y']}) hp {unit['health']} "
                f"en {unit['energy']}")
            self.log(f"    p{unit['player']} {unit['name']:<5}"
                     f"{unit['type']:<3} a{unit['attack']} h{unit['health']} "
                     f"{state}")
        with open(LOGS / f'game_{self.gameno}_history.json', 'w',
                  encoding='utf-8') as record:
            json.dump({'game': self.gameno,
                       'p1': self.bots[1].name, 'p2': self.bots[2].name,
                       'outcome': self.outcome, 'turns': self.turn,
                       'history': self.history}, record, indent=1)

    def close(self):
        for session in list(self.clients.values()):
            session.close()
        if self.observer:
            self.observer.close()
        if self.server and self.server.proc.poll() is None:
            self.server.proc.terminate()
        self.log_file.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=int, required=True)
    parser.add_argument('--p1', required=True)
    parser.add_argument('--p2', required=True)
    parser.add_argument("--max-turns", type=int, default=100)
    parser.add_argument('--budget1', type=int)
    parser.add_argument('--budget2', type=int)
    parser.add_argument('--budget', type=int,
                        help='the same budget for both players')
    parser.add_argument('--no-split', action='store_true',
                        help='let either player deploy anywhere on the board')
    args = parser.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    bots = {1: load_bot(args.p1, 1), 2: load_bot(args.p2, 2)}
    budgets = {1: args.budget1 or args.budget, 2: args.budget2 or args.budget}
    Match(args.game, bots, max_turns=args.max_turns,
          budgets={k: v for k, v in budgets.items() if v},
          split=not args.no_split).play()


if __name__ == '__main__':
    main()
