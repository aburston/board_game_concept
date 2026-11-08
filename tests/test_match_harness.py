"""The match harness under `matches/`, held to the `match-series` capability.

A series of games between doctrines is evidence about the rules only if each
doctrine was given its own seat and nothing else, every command went through
a real role's prompt, and the game - not the harness - decided what was
allowed and how the game went. The games themselves are not tests: their
outcomes are the question. What is tested here is the boundary the harness
keeps and the armies and programs the doctrines state, without playing a
game through the roles, plus one slow test that does.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from board_game_concept.cli import parser
from board_game_concept.cli.session import read_program_file
from board_game_concept.domain.army import ARRAY, CATALOGUE, FLAG_UNIT
from board_game_concept.domain.player import Player
from board_game_concept.domain.program import Program, cap
from board_game_concept.domain.unit import UnitType
from board_game_concept.service import games
from board_game_concept.service.commands import SetProgram

from game_harness import GameHarness

ROOT = Path(__file__).resolve().parent.parent
MATCHES = ROOT / 'matches'
BOTS = MATCHES / 'bots'

STOCK = ('garrison', 'advance', 'flag_hunt', 'screen')
REBUILT = ('lancers', 'heavies', 'runners', 'bulwark', 'executioner',
           'fugitive')
DOCTRINES = STOCK + REBUILT

BUDGET = Player.DEFAULT_BUDGET
SIZE = 8
HALF = 4
DESIGNS = {name: (symbol, attack, health, energy, compute)
           for name, symbol, attack, health, energy, compute, _program
           in CATALOGUE}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def arena():
    return load('arena', MATCHES / 'arena.py')


@pytest.fixture(scope='module')
def checker():
    return load('check_records', MATCHES / 'check_records.py')


def doctrine(arena, name):
    return arena.load_doctrine(BOTS / f'{name}.yaml')


# ------------------------------------------------------------ canned views

def stock_units(player, north):
    """The stock army as the game deploys it for this seat (R2.13)."""
    units = []
    for depth, x, type_name, name in ARRAY:
        symbol, attack, health, energy, _compute = DESIGNS[type_name]
        y = depth if north else SIZE - 1 - depth
        units.append({'player': player, 'name': name, 'type': type_name,
                      'symbol': symbol, 'attack': attack, 'health': health,
                      'energy': energy, 'x': x, 'y': y, 'state': 'holding',
                      'direction': None, 'flag': name == FLAG_UNIT})
    return units


def stock_view(player, turn=0):
    """A seat's own view of the stock army, as it is handed it."""
    north = player == 1
    rows = list(range(0, HALF)) if north else list(range(HALF, SIZE))
    mine = stock_units(player, north)
    flags = []
    for who in (1, 2):
        carrier = next(u for u in stock_units(who, who == 1)
                       if u['name'] == FLAG_UNIT)
        flags.append({'player': who, 'x': carrier['x'], 'y': carrier['y'],
                      'standing': True})
    spent = sum(sum(DESIGNS[type_name][1:]) for _d, _x, type_name, _n
                in ARRAY)
    return {
        'turn': turn, 'me': player, 'rejected': [],
        'board': {'size_x': SIZE, 'size_y': SIZE, 'empty': ' ', 'rows': [],
                  'legend': []},
        'units': mine,
        'types': [{'player': player, 'name': name, 'symbol': symbol,
                   'attack': attack, 'health': health, 'energy': energy,
                   'compute': compute, 'program': program is not None,
                   'cost': attack + health + energy + compute}
                  for name, symbol, attack, health, energy, compute, program
                  in CATALOGUE],
        'players': [{'player': 1, 'status': 'active',
                     'budget': BUDGET if player == 1 else None,
                     'spent': spent if player == 1 else None,
                     'left': BUDGET - spent if player == 1 else None},
                    {'player': 2, 'status': 'active',
                     'budget': BUDGET if player == 2 else None,
                     'spent': spent if player == 2 else None,
                     'left': BUDGET - spent if player == 2 else None}],
        'flags': flags,
        'placement': {'size_x': SIZE, 'size_y': SIZE, 'rows': rows,
                      'neutral_row': None, 'restricted': True},
    }


def transcript(docs):
    """What a client prints for a run of `show ... json` commands."""
    return ''.join(f'bgcclient> {json.dumps(doc, indent=2)}\n' for doc in docs)


def parsed(commands):
    """The setup commands as the words they are: the type, its statistics,
    the units and their squares, the carrier and the programs."""
    types, units, flags, programs = {}, [], [], {}
    for command in commands:
        words = command.split()
        if words[:2] == ['add', 'type']:
            _, _, name, symbol, attack, health, energy, compute = words
            types[name] = (symbol, int(attack), int(health), int(energy),
                           int(compute))
        elif words[:2] == ['add', 'unit']:
            _, _, type_name, name, x, y = words
            units.append((type_name, name, int(x), int(y)))
        elif words[:2] == ['set', 'flag']:
            flags.append(words[2])
        elif words[:2] == ['set', 'program']:
            programs[words[2]] = Path(words[3])
    return types, units, flags, programs


# ------------------------------------------------- the view a doctrine gets

class TestTheViewADoctrineIsGiven:

    def test_six_documents_are_read_back_as_six(self, arena):
        view = stock_view(1)
        docs = [{subject: view[subject]} for subject in arena.SUBJECTS]
        assert len(arena.json_docs(transcript(docs))) == 6

    def test_the_view_holds_every_subject_and_nothing_else(self, arena):
        view = stock_view(2)
        docs = [{subject: view[subject]} for subject in arena.SUBJECTS]
        assembled = arena.assemble_view(0, 2, docs, ['a refusal'])
        assert set(assembled) == set(arena.SUBJECTS) | {'turn', 'me',
                                                        'rejected'}
        assert assembled['me'] == 2
        assert assembled['rejected'] == ['a refusal']
        assert assembled['flags'] == view['flags']
        assert assembled['placement']['rows'] == [4, 5, 6, 7]

    def test_a_subject_the_client_did_not_answer_is_an_error(self, arena):
        view = stock_view(1)
        docs = [{subject: view[subject]} for subject in arena.SUBJECTS[:-1]]
        with pytest.raises(RuntimeError, match='placement'):
            arena.assemble_view(0, 1, docs, [])

    def test_a_program_listing_is_not_a_reply(self, arena):
        said = arena.replies(
            'bgcclient> Lance: compute 3, 30 ticks per energy, cap 30 ticks '
            'a turn\n'
            'LINE  TICKS  PROGRAM\n'
            '   1      1  SELF\n'
            '   2      0  HALT\n'
            'a straight run costs 1 ticks\n'
            'bgcclient> error adding unit: that square is occupied\n'
            'bgcclient> ')
        assert said == ['error adding unit: that square is occupied']

    def test_depth_is_counted_from_the_seats_own_edge(self, arena):
        north, south = stock_view(1), stock_view(2)
        assert [arena.depth_row(north, d) for d in range(4)] == [0, 1, 2, 3]
        assert [arena.depth_row(south, d) for d in range(4)] == [7, 6, 5, 4]


# ------------------------------------------- the outcome is the record's

class TestTheOutcomeIsReadFromTheRecord:

    def test_status_is_read_from_the_turns_eliminated(self, arena):
        doc = {'eliminated': [2]}
        assert arena.status_of(doc, 1) == 'active'
        assert arena.status_of(doc, 2) == 'eliminated'
        assert arena.status_of({}, 2) == 'active'

    def test_a_wall_is_not_counted_in_play(self, arena):
        units = stock_units(1, True) + stock_units(2, False)
        for unit in units:
            unit['type_energy'] = unit['energy']
        units[0] = dict(units[0], x=None, y=None)
        alive, walls = arena.tally(units)
        assert alive == {1: 13, 2: 14}
        assert walls == {1: 2, 2: 2}

    def test_what_a_controller_decided_reads_as_a_few_words(self, arena):
        assert arena.order_text({'unit': 'runner1', 'order': 3}) == \
            'runner1 moves south'
        assert arena.order_text({'unit': 'keep1', 'slept': True}) == \
            'keep1 sleeps'
        assert arena.order_text({'unit': 'pawn1', 'order': None,
                                 'halted': 7}) == \
            'pawn1 holds (halts at line 7)'

    def test_the_final_turn_is_the_one_the_game_ended_on(self, arena):
        assert arena.final_turn('game over: player 1 wins on turn 75') == 75
        assert arena.final_turn('game over: a draw on turn 12') == 12
        assert arena.final_turn(
            'game over: undecided on turn 90, its state repeated (as it '
            'stood after turn 10)') == 90
        assert arena.final_turn('not played: p1 Flagless: no flag') is None

    def test_the_board_is_drawn_as_the_roles_draw_it(self, arena):
        board = {'size_x': 2, 'size_y': 1, 'rows': [['K', ' ']]}
        assert arena.draw(board) == '+-+-+\n|K| |\n+-+-+'


# ------------------------------------------------------- the doctrines

class TestSetup:

    @pytest.mark.parametrize('name', STOCK)
    def test_a_stock_doctrine_keeps_the_army(self, arena, name):
        for player in (1, 2):
            commands = doctrine(arena, name).setup(stock_view(player))
            assert not [c for c in commands if c.startswith('remove ')]
            assert not [c for c in commands if c.startswith('add ')]

    @pytest.mark.parametrize('name', REBUILT)
    def test_a_rebuilt_doctrine_takes_everything_back_first(self, arena,
                                                            name):
        commands = doctrine(arena, name).setup(stock_view(1))
        removed = [c for c in commands if c.startswith('remove unit ')]
        assert len(removed) == 16
        assert commands[:16] == removed
        assert all(not c.startswith('remove') for c in commands[16:])

    @pytest.mark.parametrize('name', DOCTRINES)
    def test_the_army_is_one_the_game_accepts(self, arena, name):
        """Every type through the game's own constructor with its program,
        the cost against the budget, every square inside the seat's half,
        no square twice, exactly one carrier among the units deployed, and
        a program only on a type that has the compute to run it."""
        for player in (1, 2):
            view = stock_view(player)
            commands = doctrine(arena, name).setup(view)
            types, units, flags, programs = parsed(commands)
            designs = dict(DESIGNS)
            designs.update(types)
            for type_name, path in programs.items():
                assert path.is_file(), f'{name}: {path} is not a file'
                assert type_name in designs, f'{name}: {type_name} unknown'
                assert designs[type_name][4] > 0, \
                    f'{name}: {type_name} has no compute for a program'
            for type_name, (symbol, attack, health, energy, compute) in \
                    types.items():
                program = programs.get(type_name)
                UnitType(type_name, symbol, attack, health, energy, compute,
                         read_program_file(program) if program else None)
            if not units:
                continue
            squares, cost, named = set(), 0, []
            for type_name, unit_name, x, y in units:
                assert type_name in designs, f'{unit_name} of an undefined type'
                assert 0 <= x < SIZE
                assert y in view['placement']['rows'], \
                    f'{unit_name} at ({x},{y}) is outside rows ' \
                    f'{view["placement"]["rows"]}'
                assert (x, y) not in squares, f'({x},{y}) taken twice'
                squares.add((x, y))
                cost += sum(designs[type_name][1:])
                named.append(unit_name)
            assert len(set(named)) == len(named)
            assert cost <= BUDGET, f'{name} costs {cost}'
            assert len(flags) == 1 and flags[0] in named

    @pytest.mark.parametrize('name', DOCTRINES)
    def test_every_program_parses(self, arena, name):
        commands = doctrine(arena, name).setup(stock_view(1))
        _types, _units, _flags, programs = parsed(commands)
        for path in programs.values():
            Program(read_program_file(path))

    def test_deploy_puts_depth_zero_at_the_seat_edge(self, arena):
        south = doctrine(arena, 'lancers').setup(stock_view(2))
        assert 'add unit Keep keep1 3 7' in south
        assert 'add unit Lance lance1 0 4' in south
        assert 'set flag keep1' in south
        north = doctrine(arena, 'lancers').setup(stock_view(1))
        assert 'add unit Keep keep1 3 0' in north
        assert 'add unit Lance lance1 0 3' in north

    def test_a_programs_path_is_the_clients_to_read(self, arena):
        """The client reads the file, so it is named absolutely - a session
        talking to a server never names a path the server owns."""
        commands = doctrine(arena, 'garrison').setup(stock_view(1))
        _t, _u, _f, programs = parsed(commands)
        assert programs
        assert all(path.is_absolute() for path in programs.values())


class TestADoctrineIsAFunctionOfItsFile:

    @pytest.mark.parametrize('name', DOCTRINES)
    def test_the_same_seat_twice_gives_the_same_commands(self, arena, name):
        for player in (1, 2):
            view = stock_view(player)
            first = doctrine(arena, name).setup(view)
            second = doctrine(arena, name).setup(view)
            assert first == second

    def test_nothing_under_bots_is_code(self):
        """A doctrine is data: a file of types, squares and programs, and
        the programs run on the game's own machine. Nothing under `bots/`
        can consult chance, the clock or the other seat."""
        for path in BOTS.rglob('*'):
            if path.is_file():
                assert path.suffix in ('.yaml', '.asm'), path


# --------------------------------------------- the programs run in the game

def apply(session, commands):
    """Type a doctrine's setup at an in-process session, as the client does:
    each line parsed by the grammar, a program file read on this side."""
    for line in commands:
        command = parser.parse(line)
        if command.kind == 'set_program_file':
            command = SetProgram(type_name=command.type_name,
                                 program=read_program_file(command.path))
        games.perform(session, command)


class TestTheProgramsRunWithinTheirCaps:
    """Every doctrine's setup is accepted by the game, and no controller it
    fields is stopped at its cap on any turn of a game against the
    Garrison - a program that fits its type is the one thing a listing
    cannot prove, because the longest path is not the straight run."""

    def play(self, tmp_path, arena, name, against='garrison', turns=12):
        harness = GameHarness(tmp_path)
        harness.create(SIZE, SIZE, [1, 2])
        for player, who in ((1, name), (2, against)):
            session = harness.session(player)
            rows = games_rows(session, player)
            view = {'me': player, 'placement': {'rows': rows},
                    'units': [{'player': player, 'name': u.name, 'x': u.x}
                              for u in session.getBoard().units
                              if u.player is not None
                              and u.player.number == player]}
            apply(session, doctrine(arena, who).setup(view))
            assert session.clientSave()
        server = harness.play()
        outcome = server.getOutcome()
        assert outcome is not None
        records = [harness.turn_record(t)
                   for t in range(1, min(outcome['turn'], turns) + 1)]
        return outcome, records

    @pytest.mark.parametrize('name', DOCTRINES)
    def test_no_controller_is_stopped_at_its_cap(self, tmp_path, arena,
                                                 name):
        """A controller is stopped for one of two reasons: it reached the
        cap its compute buys it, which is the program's fault, or it had no
        energy left to buy another tick with, which is the fight's (R10.5).
        The second is read off the unit's energy as the turn began."""
        _outcome, records = self.play(tmp_path, arena, name)
        before = {}
        halted = []
        for record in records:
            for trace in record.get('traces') or []:
                if trace.get('halted') is None or trace['player'] != 1:
                    continue
                if before.get(trace['unit'], 1) > 0:
                    halted.append((record['turn'], trace['unit'],
                                   trace['halted'], trace['ticks']))
            before = {u['name']: u['energy'] for u in record['units']
                      if u['player'] == 1}
        assert not halted, halted

    @pytest.mark.parametrize('name', DOCTRINES)
    def test_the_setup_is_the_one_the_doctrine_states(self, tmp_path, arena,
                                                      name):
        _outcome, records = self.play(tmp_path, arena, name, turns=1)
        commands = doctrine(arena, name).setup(stock_view(1))
        _types, units, flags, _programs = parsed(commands)
        placed = {u['name'] for u in records[0]['units']
                  if u['player'] == 1 and not u.get('destroyed')}
        wanted = ({u[1] for u in units} if units
                  else {name for _d, _x, _t, name in ARRAY})
        assert placed == wanted
        carrier = [u['name'] for u in records[0]['units']
                   if u['player'] == 1 and u.get('flag')]
        assert carrier == (flags or [FLAG_UNIT])

    def test_garrison_against_garrison_repeats_at_once(self, tmp_path,
                                                       arena):
        outcome, _records = self.play(tmp_path, arena, 'garrison')
        assert outcome['decided'] is False
        assert outcome['reason'] == 'repeated'
        assert outcome['turn'] <= 3


def games_rows(session, player):
    """Where this seat may deploy, as the placement view says."""
    from board_game_concept.http import views
    return views.placement_view(player, session.getPlayers(),
                                session.getBoard())['rows']


# ------------------------------------------------ through the real roles

@pytest.mark.slow
class TestThroughTheRealRoles:

    def play(self, arena, tmp_path, monkeypatch, p1, p2, gameno=99998):
        monkeypatch.setattr(arena, 'LOGS', tmp_path)
        doctrines = {1: doctrine(arena, p1), 2: doctrine(arena, p2)}
        match = arena.Match(gameno, doctrines)
        outcome = match.play()
        return outcome, (tmp_path / f'game_{gameno}.log').read_text(), match

    def test_garrison_against_garrison_stops_on_its_first_repeated_state(
            self, arena, checker, tmp_path, monkeypatch):
        outcome, log, match = self.play(arena, tmp_path, monkeypatch,
                                        'garrison', 'garrison')
        assert outcome.startswith('game over: undecided on turn')
        assert 'its state repeated' in outcome
        assert match.turns == 2
        assert log.count('  -- turn ') == 2
        assert 'board 8x8, p1: 320 points, rows 0-3, p2: 320 points, ' \
               'rows 4-7' in log
        assert log.count('is handed 16 units') == 2
        assert log.count('set program Keep hold.asm') == 2
        assert re.search(r'^  -- turn 1\n    p1: places its army', log, re.M)
        assert 'in play 14 v 14  (walls: 2 v 2)' in log
        assert match.status == {1: 'active', 2: 'active'}
        final = match.history[-1]['units']
        carriers = sorted((u['player'], u['name']) for u in final
                          if u.get('flag'))
        assert carriers == [(1, 'keep1'), (2, 'keep1')]
        monkeypatch.setattr(checker, 'LOGS', tmp_path)
        assert checker.check(99998) == []

    def test_a_setup_without_a_flag_is_not_played(self, arena, tmp_path,
                                                  monkeypatch):
        flagless = arena.Doctrine(
            {'name': 'Flagless',
             'doctrine': 'takes the carrier back and names no other',
             'rebuild': False}, BOTS)
        flagless.setup = lambda view: ['remove unit keep1']
        monkeypatch.setattr(arena, 'LOGS', tmp_path)
        doctrines = {1: flagless, 2: doctrine(arena, 'garrison')}
        outcome = arena.Match(99997, doctrines).play()
        assert outcome.startswith('not played: p1 Flagless: ')
        assert 'flag' in outcome
        log = (tmp_path / 'game_99997.log').read_text()
        assert '-- turn 1' not in log
