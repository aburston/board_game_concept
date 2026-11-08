#!/usr/bin/env python3
"""Play one two-player game between two doctrines, through the real CLI roles.

Nothing here reaches into the game's storage or its domain objects. A match is
driven exactly as people at terminals would drive it: `bgcserver` registers
the players and commits, one `bgcclient` session per player types that seat's
setup and commits, and the last commit resolves the whole game. A doctrine is
a file: the types it fields, the program each type's units run, where its
units stand and which carries the flag - or only programs, for one that keeps
the stock army and tells it how to think. Once both seats have committed
there is nothing left for anybody to decide, and the harness reads the record
back through an observer session and writes down what it says.

**The rule this harness exists to keep: a doctrine is given its own seat and
nothing else.** Its setup is data written before the game exists, so nothing
about the opposing seat can reach it; the view it is handed to place its
units by is read with `show ... json` at its own client, so the game decides
what is in it. The record is read only once the game is resolved, when
nothing can act on what it shows.

**The harness states nothing the game already decides.** It names no board
size and no budget, so a game plays on what a new two-player game is given:
the 8 x 8 board (R2.1), 320 points a seat (R2.3.1), the halves the game
publishes (R2.6a), and the stock army each seat opens with, flag on `keep1`
(R2.13). Where a doctrine may deploy, what it may afford, whether a program
will run and whether its setup carries a flag are the game's to refuse, and
a refusal is logged as the client printed it. Who is still in the game, and
how it ended, are read from the record rather than counted off the board.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import yaml

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

# what a doctrine is handed to set its seat up by: every subject its own
# client will answer about the seat, and nothing the observer sees. `flags`
# and `placement` are a player's to know (R6.5, R2.6a) and so are read for it
SUBJECTS = ('board', 'units', 'types', 'players', 'flags', 'placement')

# how long the last commit may take to resolve the whole game: hundreds of
# turns on a local SQLite file are a few seconds, and the cap is 500
RESOLUTION_TIMEOUT = 600


def role(name, *args):
    """The argv that launches a CLI role through the running interpreter.

    Not the console script: that is wherever the person installed it, and a
    guess at `venv/bin` is what stopped the old harness running in a fresh
    checkout.
    """
    return [sys.executable, '-u', '-m', f'{PACKAGE}.{name}', *args]


class NotPlayed(Exception):
    """The game could not be played as set up, and that is the result."""


# ------------------------------------------------------------------ doctrines

def depth_row(view, depth):
    """The row at this depth from the seat's own edge, read from where the
    game says the seat may deploy: depth 0 is the edge row."""
    rows = view['placement']['rows']
    if not rows:
        return depth
    return rows[0] + depth if rows[0] == 0 else rows[-1] - depth


def mine(view):
    """The seat's units that stand on the board."""
    return [unit for unit in view['units']
            if unit['player'] == view['me'] and unit.get('x') is not None]


class Doctrine:
    """What a seat fields, as the commands that set it up.

    `data` is the doctrine file's content: `name` and `doctrine` for the
    log; `rebuild` to take the stock army back first; `types`, each a
    mapping of name, symbol, attack, health, energy, compute and an optional
    program file; `units`, each `[type, name, column, depth]` with depth
    counted from the seat's own edge; `flag`, the carrier; and `programs`,
    a mapping of type name to program file for types the seat keeps.
    Program files are named relative to `base`, the doctrine file's
    directory, and are given to the client as absolute paths - it is the
    client that reads them.
    """

    def __init__(self, data, base):
        self.name = data['name']
        self.doctrine = data.get('doctrine', '')
        self.rebuild = bool(data.get('rebuild'))
        self.types = list(data.get('types') or [])
        self.units = [tuple(unit) for unit in data.get('units') or []]
        self.flag = data.get('flag')
        self.programs = dict(data.get('programs') or {})
        self.base = Path(base)

    def program_path(self, name):
        return str((self.base / name).resolve())

    def setup(self, view):
        """The commands that turn the seat as handed into this army."""
        commands = []
        if self.rebuild:
            commands += [f'remove unit {unit["name"]}'
                         for unit in sorted(mine(view),
                                            key=lambda u: u['name'])]
        for design in self.types:
            commands.append(
                f"add type {design['name']} {design['symbol']} "
                f"{design['attack']} {design['health']} {design['energy']} "
                f"{design.get('compute', 0)}")
            if design.get('program'):
                commands.append(f"set program {design['name']} "
                                f"{self.program_path(design['program'])}")
        for type_name, unit_name, x, depth in self.units:
            commands.append(f'add unit {type_name} {unit_name} {x} '
                            f'{depth_row(view, depth)}')
        if self.flag:
            commands.append(f'set flag {self.flag}')
        for type_name, program in sorted(self.programs.items()):
            commands.append(f'set program {type_name} '
                            f'{self.program_path(program)}')
        return commands


def load_doctrine(path):
    """A doctrine from its file."""
    path = Path(path)
    with open(path, encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return Doctrine(data, path.parent)


# ------------------------------------------------------- reading a session

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
# what the client says back after `set program`: the type's tariff, its
# listing and the price of a straight run, which are an answer rather than
# a refusal
LISTING = re.compile(r'^(\S+: compute \d+, \d+ ticks per energy|'
                     r'a straight run costs \d+ ticks)')


def replies(text):
    """What a session said in reply, with the prompts and blank lines gone.

    The client reads a program back after `set program`, as a table; that is
    what was just given, not a reply, and is left out. A refusal is a
    sentence, and a rejection starts with a dash.
    """
    said = []
    for line in PROMPT.sub('', text).splitlines():
        if not line.strip():
            continue
        if TABLE_HEADER.match(line) or TABLE_ROW.match(line):
            continue
        if LISTING.match(line):
            continue
        said.append(line.rstrip())
    return said


def assemble_view(turn, player, docs, notes):
    """The view a doctrine is handed, from the documents its own client
    printed.

    One document per subject in `SUBJECTS`, each holding one key named for
    its subject, and the lines the client printed since the doctrine last
    looked: refusals of its own commands.
    """
    view = {'turn': turn, 'me': player, 'rejected': list(notes)}
    for doc in docs:
        view.update(doc)
    missing = [subject for subject in SUBJECTS if subject not in view]
    if missing:
        raise RuntimeError(f'player {player} was not answered for {missing}')
    return view


def status_of(turn_doc, player):
    """Whether the game still counts this seat in after a turn, from the
    record's own list of the eliminated."""
    return ('eliminated' if player in (turn_doc.get('eliminated') or [])
            else 'active')


def tally(units):
    """How many of each player's units stand on the board, and how many of
    those are walls.

    What keeps a player in the game is holding a unit that could act again
    (R7.1), which is every unit whose type has energy - a wall is the one
    kind that has none (R2.10). A unit merely out of energy counts, because
    resting gives it back. This count is for the reader; who is in the game
    is what `status_of` says.
    """
    alive, walls = {}, {}
    for unit in units:
        if unit.get('x') is None:
            continue
        energy = unit.get('type_energy')
        if energy is None:
            energy = unit['energy']
        wall = unit['attack'] == 0 and energy == 0
        tally_ = walls if wall else alive
        tally_[unit['player']] = tally_.get(unit['player'], 0) + 1
    return alive, walls


def order_text(trace):
    """What a controller decided, in a few words, for the log."""
    if trace.get('slept'):
        return f"{trace['unit']} sleeps"
    order = trace.get('order')
    heading = {1: 'north', 2: 'east', 3: 'south', 4: 'west'}.get(order, order)
    decided = 'holds' if order in (None, 'hold') else f'moves {heading}'
    halted = (f" (halts at line {trace['halted']})"
              if trace.get('halted') is not None else '')
    return f"{trace['unit']} {decided}{halted}"


def draw(board):
    """A turn's board as the grid the roles print, from the record's rows."""
    rule = '+' + '-+' * board['size_x']
    lines = [rule]
    for row in board['rows']:
        lines.append('|' + '|'.join(row) + '|')
        lines.append(rule)
    return '\n'.join(lines)


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

    def ask(self, commands, documents, timeout=120):
        """Type these `show ... json` commands and read the answers back."""
        mark = self.mark()
        for command in commands:
            self.send(command)
        self.wait_for(lambda text: len(json_docs(text[mark:])) >= documents
                      and self.prompts(mark) >= len(commands),
                      timeout=timeout)
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


# -------------------------------------------------------------------- a match

# the turn a game ended on, as the outcome line says it: `player 1 wins on
# turn 75`, `a draw on turn 12`, `undecided on turn 90, its state repeated
# (as it stood after turn 10)` - the first turn named, not the last
OUTCOME = re.compile(r'\bon turn (\d+)')


def final_turn(outcome):
    """The turn the game ended on, from its outcome line, or None."""
    found = OUTCOME.search(outcome or '')
    return int(found.group(1)) if found else None


class Match:
    def __init__(self, gameno, doctrines):
        self.gameno = gameno
        self.doctrines = doctrines            # {player_number: Doctrine}
        self.log_file = open(LOGS / f'game_{gameno}.log', 'w',
                             encoding='utf-8')
        self.server = None
        self.clients = {}
        self.observer = None
        self.outcome = None
        self.turns = 0
        self.history = []
        self.notes = {player: [] for player in doctrines}
        self.status = {player: 'active' for player in doctrines}

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
        for player in sorted(self.doctrines):
            self.server.send(f'add player {player}')
        self.server.send('commit')
        self.server.wait_for(lambda text: 'waiting for player(s)' in text)
        for player in sorted(self.doctrines):
            session = Session(
                role('bgcclient', str(self.gameno), str(player)),
                LOGS / f'game_{self.gameno}_p{player}.txt')
            session.wait_for(lambda text: 'bgcclient> ' in text)
            self.clients[player] = session

    # ------------------------------------------------------------------ views

    def read_view(self, player):
        """What this seat may see of itself, asked for in its own session.

        This is the only thing a doctrine is ever given.
        """
        docs = self.clients[player].ask(
            [f'show {subject} json' for subject in SUBJECTS], len(SUBJECTS))
        view = assemble_view(0, player, docs, self.notes[player])
        self.notes[player] = []
        return view

    def note(self, player, line):
        self.log(f'    p{player}: {line}')
        self.notes[player].append(line)

    # ------------------------------------------------------------------- play

    def give(self, player, commands):
        """Type one seat's setup. Whatever the client says back - a refusal -
        is logged and kept."""
        for line in self.clients[player].tell(commands):
            self.note(player, line)

    def commit(self, player, last):
        """Commit one seat's setup.

        Player 1 commits and waits; player 2's commit is the last, and
        resolves the whole game (R3.1). A commit the client refuses brings
        the prompt back without `commit complete`, and during setup that
        means the game cannot be played as this doctrine set it up.
        """
        session = self.clients[player]
        mark = session.mark()
        session.send('commit')
        session.wait_for(
            lambda text: ('commit complete' in text[mark:]
                          or 'bgcclient> ' in text[mark:]))
        said = session.since(mark)
        if 'commit complete' not in said:
            lines = replies(said)
            for line in lines:
                self.note(player, line)
            raise NotPlayed(f'p{player} {self.doctrines[player].name}: '
                            + (lines[0] if lines else 'commit refused'))
        if last:
            session.wait_for(lambda text: 'game over' in text[mark:],
                             timeout=RESOLUTION_TIMEOUT)
        else:
            session.wait_for(lambda text: 'setup committed' in text[mark:]
                             or 'game over' in text[mark:])
        return mark

    def resolved(self, player, mark):
        """Wait for this seat's session to be shown the outcome."""
        session = self.clients[player]
        session.wait_for(lambda text: 'game over' in text[mark:],
                         timeout=RESOLUTION_TIMEOUT)
        for line in replies(session.since(mark)):
            if line.startswith('game over'):
                self.outcome = line
                return
        raise RuntimeError(f'p{player} was not told the outcome')

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

    def setup(self):
        """Each seat's setup, from what the game handed it, and the commits
        that end setup and resolve the game."""
        views = {player: self.read_view(player) for player in self.doctrines}
        first = views[min(views)]
        board = first['board']
        self.log(f"  board {board['size_x']}x{board['size_y']}, "
                 + ', '.join(f"p{p}: {self.budget(views[p])} points, rows "
                             f"{self.rows(views[p])}" for p in sorted(views)))
        for player, doctrine in self.doctrines.items():
            self.log(f'  p{player} {doctrine.name}: {doctrine.doctrine}')
        for player, doctrine in self.doctrines.items():
            given = sorted(u['name'] for u in mine(views[player]))
            self.log(f'  p{player} is handed {len(given)} units: '
                     f'{", ".join(given)}')
            commands = doctrine.setup(views[player])
            self.log(f'  p{player} setup: '
                     + ('; '.join(_short(c) for c in commands)
                        or 'keeps the army as given, programs and all'))
            self.give(player, commands)
        marks = {}
        players = sorted(self.doctrines)
        for player in players:
            marks[player] = self.commit(player, last=player == players[-1])
        for player in players:
            self.resolved(player, marks[player])

    def play(self):
        self.create()
        self.log(f'=== game {self.gameno}: '
                 f'p1 {self.doctrines[1].name} vs p2 {self.doctrines[2].name}')
        try:
            self.setup()
        except NotPlayed as reason:
            self.outcome = f'not played: {reason}'
            self.log(f'  {self.outcome}')
            self.close()
            return self.outcome
        self.record()
        self.close()
        return self.outcome

    # ----------------------------------------------------------- the record

    def read_turn(self, turn):
        """One turn of the record, read at the observer's prompt once the
        game is over. The observer sees every army's traces and every
        refusal (R6.6), which is what the log is for; nobody who could act
        on it is given any of it."""
        if self.observer is None:
            self.observer = Session(
                role('bgcobserver', str(self.gameno)),
                LOGS / f'game_{self.gameno}_observer.txt')
            self.observer.wait_for(lambda text: 'bgcobserver> ' in text)
        docs = self.observer.ask([f'show turn {turn} json'], 1)
        # printed as `{"turn": {...}}`, the way every subject is
        return docs[-1]['turn']

    def record(self):
        """Write the game down, turn by turn, from the record."""
        self.turns = final_turn(self.outcome)
        if self.turns is None:
            raise RuntimeError(f'no turn in the outcome: {self.outcome!r}')
        for turn in range(1, self.turns + 1):
            doc = self.read_turn(turn)
            self.log(f'  -- turn {turn}')
            orders = {}
            for player in sorted(self.doctrines):
                traces = [t for t in doc.get('traces') or []
                          if t.get('player') == player]
                orders[player] = [order_text(t) for t in traces]
                self.log(f'    p{player}: '
                         + ('; '.join(orders[player])
                            or ('places its army' if turn == 1
                                else 'nothing thinks')))
            for entry in doc.get('events') or []:
                text = entry.get('text') or entry.get('kind')
                self.log(f'      {text}')
            for rejection in doc.get('rejected') or []:
                self.log(f"    p{rejection['player']}: - {rejection['unit']} "
                         f"at ({rejection['x']},{rejection['y']}): "
                         f"{rejection['reason']}")
            board = draw(doc['board'])
            self.log(board)
            units = doc.get('units') or []
            alive, walls = tally(units)
            status = {}
            for player in self.doctrines:
                status[player] = status_of(doc, player)
                if status[player] != self.status[player]:
                    self.log(f'    p{player} is {status[player]} '
                             f'from turn {turn}')
                    self.status[player] = status[player]
            note = ''
            if walls:
                note = f"  (walls: {walls.get(1, 0)} v {walls.get(2, 0)})"
            self.log(f'    after turn {turn}: in play '
                     f'{alive.get(1, 0)} v {alive.get(2, 0)}{note}')
            self.history.append({
                'turn': turn, 'board': board, 'units': units,
                'alive': alive, 'walls': walls, 'status': status,
                'orders': orders,
                'events': [e.get('text') for e in doc.get('events') or []],
                'rejected': doc.get('rejected') or [],
                'traces': doc.get('traces') or [],
            })
        self.log(f'  {self.outcome}')
        self.summarise(self.history[-1]['units'] if self.history else [])

    def summarise(self, units):
        self.log('  final units:')
        for unit in sorted(units, key=lambda u: (u['player'], u['name'])):
            state = ('off the board' if unit.get('x') is None else
                     f"({unit['x']},{unit['y']}) hp {unit['health']} "
                     f"en {unit['energy']}")
            flag = ' flag' if unit.get('flag') else ''
            self.log(f"    p{unit['player']} {unit['name']:<9}"
                     f"{unit['type']:<7} a{unit['attack']} "
                     f"h{unit.get('type_health', unit['health'])} "
                     f"{state}{flag}")
        with open(LOGS / f'game_{self.gameno}_history.json', 'w',
                  encoding='utf-8') as record:
            json.dump({'game': self.gameno,
                       'p1': self.doctrines[1].name,
                       'p2': self.doctrines[2].name,
                       'outcome': self.outcome, 'turns': self.turns,
                       'history': self.history}, record, indent=1)

    def close(self):
        for session in list(self.clients.values()):
            session.close()
        if self.observer:
            self.observer.close()
        if self.server and self.server.proc.poll() is None:
            try:
                self.server.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server.proc.terminate()
        self.log_file.close()


def _short(command):
    """A setup command for the log, with a program's path cut to its name."""
    words = command.split()
    if words[:2] == ['set', 'program']:
        return f'set program {words[2]} {Path(words[3]).name}'
    return command


def main():
    parser = argparse.ArgumentParser(
        description='play one game between two doctrines on the default '
                    'board')
    parser.add_argument('--game', type=int, required=True)
    parser.add_argument('--p1', required=True)
    parser.add_argument('--p2', required=True)
    args = parser.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    doctrines = {1: load_doctrine(args.p1), 2: load_doctrine(args.p2)}
    outcome = Match(args.game, doctrines).play()
    if outcome and outcome.startswith('not played'):
        sys.exit(2)


if __name__ == '__main__':
    main()
