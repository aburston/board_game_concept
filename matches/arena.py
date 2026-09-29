#!/usr/bin/env python3
"""Play one two-player game between two bots, through the real CLI roles.

Nothing here reaches into the game's storage or its domain objects. A match is
driven exactly as three people at three terminals would drive it: `bgcserver`
registers the players and then resolves each turn, and one `bgcclient` session
per player stays open for the whole game, typing that player's commands and
committing. Sessions are long-lived and take their turns in the order the
integration tests use - player 1 commits and blocks, then player 2 commits and
the turn resolves - because a local game directory is held by one process at
a time.

**The rule this harness exists to keep: a bot is handed its own player view and
nothing else.** `read_view` types `show ... json` into that player's own
session, so the visibility rules (R6) decide what comes back - an enemy unit is
in it only if it was fought last turn, and the squares of the flags are in it
because R6.5 shows them to everybody. The two views are never mixed. The
observer, which sees everything (R6.6), is read only to write the match log,
after both players have already given their orders for that turn.

**The harness states nothing the game already decides.** It names no board
size and no budget, so a game plays on what a new two-player game is given:
the 8 x 8 board (R2.1), 250 points a seat (R2.3.1), the halves the game
publishes (R2.6a), and the stock army each seat opens with, flag on `keep1`
(R2.13). Where a bot may deploy, what it may afford, and whether its setup
carries a flag are the game's to refuse, and a refusal is logged as the client
printed it. Who is still in the game is read from the players subject rather
than counted off the board.
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
sys.path.insert(0, str(ROOT / 'src'))
from board_game_concept.service import registry  # noqa: E402
LOGS = ROOT / 'matches' / 'logs'
PACKAGE = 'board_game_concept.cli'

ENV = dict(os.environ)
ENV.update({
    'BOARD_GAME_BACKEND': 'sqlite',
    # this harness runs the game out of a local directory; without this the
    # roles probe 127.0.0.1:45678 for an API server first
    'BOARD_GAME_NO_REDIRECT': '1',
    'PYTHONUNBUFFERED': '1',
    # the roles are launched as modules of the package, which is importable
    # from `src/` whether or not it has been installed
    'PYTHONPATH': os.pathsep.join(
        p for p in (str(ROOT / 'src'), os.environ.get('PYTHONPATH')) if p),
})

PROMPT = re.compile(r'bgc(client|server|observer)> ')

# what a bot is handed: every subject its own client will answer, and nothing
# the observer sees. `flags` and `placement` are a player's to know (R6.5,
# R2.6a) and so are read for it
SUBJECTS = ('board', 'units', 'types', 'players', 'flags', 'placement')


def role(name, *args):
    """The argv that launches a CLI role through the running interpreter.

    Not the console script: that is wherever the person installed it, and a
    guess at `venv/bin` is what stopped the old harness running in a fresh
    checkout.
    """
    return [sys.executable, '-u', '-m', f'{PACKAGE}.{name}', *args]


class NotPlayed(Exception):
    """The game could not be played as set up, and that is the result."""


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


TABLE_HEADER = re.compile(r'^[A-Z]+(\s{2,}[A-Z]+)+\s*$')
TABLE_ROW = re.compile(r'^\s+\d+\s+\S')


def replies(text):
    """What a session said in reply, with the prompts and blank lines gone.

    The client reads a player's units back to them after an order, as a
    table; that is the units they already have, not a reply, and is left out.
    A refusal is a sentence, and a rejection starts with a dash.
    """
    said = []
    for line in PROMPT.sub('', text).splitlines():
        if not line.strip():
            continue
        if TABLE_HEADER.match(line) or TABLE_ROW.match(line):
            continue
        said.append(line.rstrip())
    return said


def assemble_view(turn, player, docs, notes):
    """The view a bot is handed, from the documents its own client printed.

    One document per subject in `SUBJECTS`, each holding one key named for
    its subject, and the lines the client printed since the bot last looked:
    refusals of its own commands and orders the turn rejected.
    """
    view = {'turn': turn, 'me': player, 'rejected': list(notes)}
    for doc in docs:
        view.update(doc)
    missing = [subject for subject in SUBJECTS if subject not in view]
    if missing:
        raise RuntimeError(f'player {player} was not answered for {missing}')
    return view


def status_from(players_doc, player):
    """Whether the game still counts this seat in, from the players subject."""
    for entry in players_doc.get('players', []):
        if entry.get('player') == player:
            return entry.get('status', 'active')
    return 'active'


def tally(units):
    """How many of each player's units stand on the board, and how many of
    those are walls.

    A unit off the board has no square; `state` says why. What keeps a player
    in the game is holding a unit that could act again (R7.1), which is every
    unit whose type has energy - a wall is the one kind that has none (R2.10).
    A unit merely out of energy counts, because resting gives it back. This
    count is for the reader; who is in the game is what `status_from` says.
    """
    alive, walls = {}, {}
    for unit in units:
        if unit.get('x') is None:
            continue
        wall = unit['attack'] == 0 and unit['energy'] == 0
        tally_ = walls if wall else alive
        tally_[unit['player']] = tally_.get(unit['player'], 0) + 1
    return alive, walls


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
                raise RuntimeError(f'{self.argv[-1]} exited: {text[-800:]}')
            time.sleep(poll)
        raise TimeoutError(f'{self.argv[-1]} timed out: {self.output[-800:]}')

    def prompts(self, mark):
        """How many prompts the session has printed since this mark."""
        return len(PROMPT.findall(self.since(mark)))

    def ask(self, commands, documents):
        """Type these `show ... json` commands and read the answers back."""
        mark = self.mark()
        for command in commands:
            self.send(command)
        self.wait_for(lambda text: len(json_docs(text[mark:])) >= documents
                      and self.prompts(mark) >= len(commands))
        return json_docs(self.since(mark))

    def tell(self, commands):
        """Type these commands and read back whatever was said in reply."""
        mark = self.mark()
        for command in commands:
            self.send(command)
        if commands:
            self.wait_for(lambda text: self.prompts(mark) >= len(commands))
        return replies(self.since(mark))

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send('exit')
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
        self.transcript.close()


class Match:
    def __init__(self, gameno, bots, max_turns=60):
        self.gameno = gameno
        self.bots = bots                      # {player_number: Bot}
        self.max_turns = max_turns
        self.log_file = open(LOGS / f'game_{gameno}.log', 'w',
                             encoding='utf-8')
        self.server = None
        self.clients = {}
        self.observer = None
        self.outcome = None
        self.turn = 0
        self.history = []
        self.notes = {player: [] for player in bots}   # what a client said
        self.status = {player: 'active' for player in bots}

    def log(self, *parts):
        line = ' '.join(str(part) for part in parts)
        print(line, flush=True)
        self.log_file.write(line + '\n')
        self.log_file.flush()

    # ----------------------------------------------------------------- set up

    def create(self):
        """Register the seats and open a client at each.

        No board size and no budget: the game is played on what a new
        two-player game is given.
        """
        directory = ROOT / 'games' / f'_{self.gameno}'
        if directory.exists():
            shutil.rmtree(directory)
        # the game is created the way the lobby creates one, which is what
        # gives it the default board (R2.1). `bgcserver -g` opening a number
        # nobody has created yet opens an unsized game instead, and the only
        # other way to a board would be to type `set board 8 8` - restating
        # the default this harness exists not to restate
        registry.create(self.gameno, backend=ENV['BOARD_GAME_BACKEND'],
                        base_path=str(ROOT))
        self.server = Session(role('bgcserver', '-g', str(self.gameno)),
                              LOGS / f'game_{self.gameno}_server.txt')
        self.server.wait_for(lambda text: 'bgcserver> ' in text)
        for player in sorted(self.bots):
            self.server.send(f'add player {player}')
        self.server.send('commit')
        self.server.wait_for(lambda text: 'wait for player commit' in text)
        for player in sorted(self.bots):
            session = Session(
                role('bgcclient', str(self.gameno), str(player)),
                LOGS / f'game_{self.gameno}_p{player}.txt')
            session.wait_for(lambda text: 'bgcclient> ' in text)
            self.clients[player] = session

    # ------------------------------------------------------------------ views

    def read_view(self, player):
        """What this player may see, asked for in their own session.

        This is the only thing a bot is ever given.
        """
        docs = self.clients[player].ask(
            [f'show {subject} json' for subject in SUBJECTS], len(SUBJECTS))
        view = assemble_view(self.turn, player, docs, self.notes[player])
        self.notes[player] = []
        return view

    def read_status(self, player):
        """Whether the game still counts this seat in, as it tells the seat."""
        docs = self.clients[player].ask(['show players json'], 1)
        return status_from(docs[-1], player)

    def status_changed(self, player, status):
        """Log a seat's status the turn it changes, and say whether it did."""
        if status == self.status[player]:
            return False
        self.log(f'    p{player} is {status} from turn {self.turn}')
        self.status[player] = status
        return True

    def observe(self):
        """The whole board, for the match log. Never given to a bot."""
        if self.observer is None or self.observer.proc.poll() is not None:
            self.observer = Session(
                role('bgcobserver', str(self.gameno)),
                LOGS / f'game_{self.gameno}_observer.txt')
            self.observer.wait_for(lambda text: 'bgcobserver> ' in text)
        self.observer.tell(['reload'])
        docs = self.observer.ask(['show units json'], 1)
        mark = self.observer.mark()
        self.observer.send('show board')
        self.observer.wait_for(
            lambda text: self.observer.prompts(mark) >= 1
            and '+-+' in text[mark:])
        board = '\n'.join(
            line for line in PROMPT.sub('', self.observer.since(mark))
            .splitlines() if line.strip())
        return board, (docs[-1]['units'] if docs else [])

    # ------------------------------------------------------------------- play

    def give(self, player, commands):
        """Type one player's commands and commit them.

        Player 1 commits and blocks at the barrier; player 2's commit is what
        lets the server resolve the turn (R3.1). Whatever the client says
        back - a refusal, a rejection - is logged and kept for the bot.
        """
        session = self.clients[player]
        for line in session.tell(commands):
            self.note(player, line)
        mark = session.mark()
        session.send('commit')
        session.wait_for(
            lambda text: ('waiting for turn to complete' in text[mark:]
                          or 'the game is over' in text[mark:]
                          or 'out of the game' in text[mark:]
                          or 'bgcclient> ' in text[mark:]))
        said = session.since(mark)
        if ('bgcclient> ' in said and 'waiting for turn to complete' not in said
                and 'commit complete' not in said):
            # the prompt came back without the barrier: the commit itself was
            # refused, which during setup means the game cannot be played as
            # this doctrine set it up
            lines = replies(said)
            for line in lines:
                self.note(player, line)
            if self.turn <= 1:
                raise NotPlayed(f'p{player} {self.bots[player].name}: '
                                + (lines[0] if lines else 'commit refused'))
        return mark

    def note(self, player, line):
        self.log(f'    p{player}: {line}')
        self.notes[player].append(line)

    def resolved(self, player, mark):
        """Wait for this player's session to come back from the barrier."""
        session = self.clients[player]
        try:
            session.wait_for(
                lambda text: 'bgcclient> ' in text[mark:].split(
                    'waiting for turn to complete...')[-1], timeout=180)
        except (TimeoutError, RuntimeError) as error:
            self.log(f'    p{player}: {error}')
        for line in replies(session.since(mark)):
            if line in ('commit complete', 'waiting for turn to complete...'):
                continue
            if line.startswith('game over'):
                self.outcome = line
            self.note(player, line)

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
        try:
            self.setup()
        except NotPlayed as reason:
            self.outcome = f'not played: {reason}'
            self.log(f'  {self.outcome}')
            self.close()
            return self.outcome

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
            self.phase(orders)
            self.record()

        board, units = self.observe()
        self.log(board)
        self.log(f'  {self.outcome}' if self.outcome
                 else f'  undecided after {self.turn} turns')
        self.summarise(units)
        self.close()
        return self.outcome

    def setup(self):
        """Each seat's setup, from what the game handed it, and the commit
        that ends setup. The turn this resolves as is the game's turn 1."""
        views = {player: self.read_view(player) for player in self.bots}
        first = views[min(views)]
        board = first['board']
        self.log(f"  board {board['size_x']}x{board['size_y']}, "
                 + ', '.join(f"p{p}: {self.budget(views[p])} points, rows "
                             f"{self.rows(views[p])}" for p in sorted(views)))
        for player, bot in self.bots.items():
            self.log(f'  p{player} {bot.name}: {bot.doctrine}')
        orders = {}
        for player, bot in self.bots.items():
            given = sorted(u['name'] for u in views[player]['units'])
            self.log(f'  p{player} is handed {len(given)} units: '
                     f'{", ".join(given)}')
            orders[player] = bot.setup(views[player])
            self.log(f'  p{player} setup: '
                     f'{"; ".join(orders[player]) or "keeps the army as given"}')
        self.turn = 1
        self.phase(orders)
        self.record()

    @staticmethod
    def budget(view):
        for entry in view.get('players', []):
            if entry.get('player') == view['me']:
                return entry.get('budget')
        return None

    @staticmethod
    def rows(view):
        rows = view.get('placement', {}).get('rows') or []
        return f'{rows[0]}-{rows[-1]}' if rows else 'anywhere'

    def record(self):
        board, units = self.observe()
        alive, walls = tally(units)
        status = {}
        for player in self.bots:
            status[player] = self.read_status(player)
            self.status_changed(player, status[player])
        self.history.append({'turn': self.turn, 'board': board,
                             'units': units, 'alive': alive, 'walls': walls,
                             'status': status})
        note = ''
        if walls:
            note = f"  (walls: {walls.get(1, 0)} v {walls.get(2, 0)})"
        self.log(f'    after turn {self.turn}: in play '
                 f'{alive.get(1, 0)} v {alive.get(2, 0)}{note}')

    def summarise(self, units):
        self.log('  final units:')
        for unit in sorted(units, key=lambda u: (u['player'], u['name'])):
            state = unit['state'] if unit.get('x') is None else (
                f"({unit['x']},{unit['y']}) hp {unit['health']} "
                f"en {unit['energy']}")
            flag = ' flag' if unit.get('flag') else ''
            self.log(f"    p{unit['player']} {unit['name']:<8}"
                     f"{unit['type']:<7} a{unit['attack']} h{unit['health']} "
                     f"{state}{flag}")
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
    parser = argparse.ArgumentParser(
        description='play one game between two bots on the default board')
    parser.add_argument('--game', type=int, required=True)
    parser.add_argument('--p1', required=True)
    parser.add_argument('--p2', required=True)
    parser.add_argument('--max-turns', type=int, default=60)
    args = parser.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    bots = {1: load_bot(args.p1, 1), 2: load_bot(args.p2, 2)}
    outcome = Match(args.game, bots, max_turns=args.max_turns).play()
    if outcome and outcome.startswith('not played'):
        sys.exit(2)


if __name__ == '__main__':
    main()
