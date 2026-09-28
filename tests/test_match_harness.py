"""The match harness under `matches/`, held to the `match-series` capability.

A series of bot-played games is evidence about the rules only if each bot was
handed its own player's view and nothing else, every command went through a
real role's prompt, and the game - not the harness - decided what was
allowed. The games themselves are not tests: they take minutes and their
outcomes are the question. What is tested here is the boundary the harness
keeps and the armies the doctrines state, without playing a game, plus two
slow tests that do play one for a turn or two through the real roles.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from board_game_concept.domain.army import ARRAY, CATALOGUE, FLAG_UNIT
from board_game_concept.domain.unit import UnitType

ROOT = Path(__file__).resolve().parent.parent
MATCHES = ROOT / 'matches'
BOTS = MATCHES / 'bots'

STOCK = ('garrison', 'advance', 'flag_hunt', 'screen')
REBUILT = ('lancers', 'heavies', 'runners', 'bulwark', 'executioner',
           'fugitive')
DOCTRINES = STOCK + REBUILT

BUDGET = 250
SIZE = 8
HALF = 4


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
def common(arena):
    if str(BOTS) not in sys.path:
        sys.path.insert(0, str(BOTS))
    return load('common', BOTS / 'common.py')


def bot(arena, name, player):
    return arena.load_bot(BOTS / f'{name}.py', player)


# ------------------------------------------------------------ canned views

def stock_units(player, north):
    """The stock army as the game deploys it for this seat (R2.13)."""
    designs = {name: (symbol, attack, health, energy)
               for name, symbol, attack, health, energy in CATALOGUE}
    units = []
    for depth, x, type_name, name in ARRAY:
        symbol, attack, health, energy = designs[type_name]
        y = depth if north else SIZE - 1 - depth
        units.append({'player': player, 'name': name, 'type': type_name,
                      'symbol': symbol, 'attack': attack, 'health': health,
                      'energy': energy, 'x': x, 'y': y, 'state': 'holding',
                      'direction': None, 'flag': name == FLAG_UNIT})
    return units


def stock_view(player, turn=1):
    """A seat's own view of the stock army facing the stock army."""
    north = player == 1
    rows = list(range(0, HALF)) if north else list(range(HALF, SIZE))
    mine = stock_units(player, north)
    flags = []
    for who in (1, 2):
        carrier = next(u for u in stock_units(who, who == 1)
                       if u['name'] == FLAG_UNIT)
        flags.append({'player': who, 'x': carrier['x'], 'y': carrier['y'],
                      'standing': True})
    return {
        'turn': turn, 'me': player, 'rejected': [],
        'board': {'size_x': SIZE, 'size_y': SIZE, 'empty': ' ', 'rows': [],
                  'legend': []},
        'units': mine,
        'types': [{'player': player, 'name': name, 'symbol': symbol,
                   'attack': attack, 'health': health, 'energy': energy,
                   'cost': attack + health + energy}
                  for name, symbol, attack, health, energy in CATALOGUE],
        'players': [{'player': 1, 'status': 'active',
                     'budget': BUDGET if player == 1 else None,
                     'spent': 242 if player == 1 else None,
                     'left': 8 if player == 1 else None},
                    {'player': 2, 'status': 'active',
                     'budget': BUDGET if player == 2 else None,
                     'spent': 242 if player == 2 else None,
                     'left': 8 if player == 2 else None}],
        'flags': flags,
        'placement': {'size_x': SIZE, 'size_y': SIZE, 'rows': rows,
                      'neutral_row': None, 'restricted': True},
    }


def transcript(docs):
    """What a client prints for a run of `show ... json` commands."""
    return ''.join(f'bgcclient> {json.dumps(doc, indent=2)}\n' for doc in docs)


# ------------------------------------------------- the view a bot is given

class TestTheViewABotIsGiven:

    def test_six_documents_are_read_back_as_six(self, arena):
        view = stock_view(1)
        docs = [{subject: view[subject]} for subject in arena.SUBJECTS]
        assert len(arena.json_docs(transcript(docs))) == 6

    def test_the_view_holds_every_subject_and_nothing_else(self, arena):
        view = stock_view(2)
        docs = [{subject: view[subject]} for subject in arena.SUBJECTS]
        assembled = arena.assemble_view(3, 2, docs, ['a refusal'])
        assert set(assembled) == set(arena.SUBJECTS) | {'turn', 'me',
                                                        'rejected'}
        assert assembled['turn'] == 3 and assembled['me'] == 2
        assert assembled['rejected'] == ['a refusal']
        assert assembled['flags'] == view['flags']
        assert assembled['placement']['rows'] == [4, 5, 6, 7]

    def test_a_subject_the_client_did_not_answer_is_an_error(self, arena):
        view = stock_view(1)
        docs = [{subject: view[subject]} for subject in arena.SUBJECTS[:-1]]
        with pytest.raises(RuntimeError, match='placement'):
            arena.assemble_view(1, 1, docs, [])

    def test_the_units_table_is_not_a_reply(self, arena):
        said = arena.replies(
            'bgcclient> PLAYER  NAME  TYPE  SYMBOL  ATTACK  HEALTH  ENERGY  '
            'X  Y  STATE  DIRECTION  FLAG\n'
            '     1  pawn1  Pawn  p  1  4  2  0  1  moving  south  -\n'
            'bgcclient> error moving unit Unit nosuch does not exist\n'
            'bgcclient> 1 order(s) rejected last turn:\n'
            '  - pawn1 at (0,1): cannot pay\n'
            'bgcclient> ')
        assert said == ['error moving unit Unit nosuch does not exist',
                        '1 order(s) rejected last turn:',
                        '  - pawn1 at (0,1): cannot pay']


# ------------------------------------------------ the outcome is the game's

class TestTheOutcomeIsReadFromTheGame:

    def test_status_is_read_from_the_players_subject(self, arena):
        doc = {'players': [{'player': 1, 'status': 'active'},
                           {'player': 2, 'status': 'eliminated'}]}
        assert arena.status_from(doc, 1) == 'active'
        assert arena.status_from(doc, 2) == 'eliminated'

    def test_a_change_of_status_is_logged_once(self, arena, tmp_path,
                                               monkeypatch):
        monkeypatch.setattr(arena, 'LOGS', tmp_path)
        bots = {1: bot(arena, 'garrison', 1), 2: bot(arena, 'garrison', 2)}
        match = arena.Match(99999, bots)
        match.turn = 7
        assert match.status_changed(2, 'active') is False
        assert match.status_changed(2, 'eliminated') is True
        assert match.status_changed(2, 'eliminated') is False
        match.log_file.close()
        logged = (tmp_path / 'game_99999.log').read_text()
        assert logged.count('p2 is eliminated from turn 7') == 1

    def test_a_wall_is_not_counted_in_play(self, arena):
        units = stock_units(1, True) + stock_units(2, False)
        units[0] = dict(units[0], x=None, y=None, state='destroyed')
        alive, walls = arena.tally(units)
        assert alive == {1: 13, 2: 14}
        assert walls == {1: 2, 2: 2}


# ---------------------------------------------------------- the helpers

class TestWhatABotReadsFromItsView:

    def test_size_comes_from_the_board_and_nowhere_else(self, common):
        assert common.size(stock_view(1)) == (8, 8)
        with pytest.raises(KeyError):
            common.size({'units': []})

    def test_the_flags(self, common):
        view = stock_view(1)
        assert common.my_flag(view) == (3, 0)
        assert common.enemy_flags(view) == [(2, 3, 7)]
        view['flags'][1] = {'player': 2, 'x': None, 'y': None,
                            'standing': False}
        assert common.enemy_flags(view) == []
        view['flags'][0]['standing'] = False
        assert common.my_flag(view) is None

    def test_rows_and_depth_from_either_side(self, common):
        north, south = stock_view(1), stock_view(2)
        assert common.rows(north) == [0, 1, 2, 3]
        assert common.rows(south) == [4, 5, 6, 7]
        assert common.north(north) and not common.north(south)
        assert [common.depth_row(north, d) for d in range(4)] == [0, 1, 2, 3]
        assert [common.depth_row(south, d) for d in range(4)] == [7, 6, 5, 4]

    def test_budget_and_what_is_left(self, common):
        view = stock_view(2)
        assert common.budget(view) == 250
        assert common.left(view) == 8

    def test_the_fare_is_a_quarter_of_the_health_rounded_up(self, common):
        assert [common.fare_for(h) for h in range(1, 11)] == \
            [1, 1, 1, 1, 2, 2, 2, 2, 3, 3]
        fares = common.fares(stock_view(1))
        assert fares['heavy1'] == 3 and fares['pawn1'] == 1
        assert fares['line1'] == 2

    def test_lethal_is_the_strikes_of_one_exchange(self, common):
        assert common.lethal([8], 8)
        assert not common.lethal([5], 10)
        assert common.lethal([5, 5], 10)
        assert common.lethal([2, 2, 2], 6)


class TestResolve:

    def contact_view(self, common):
        """Three Runners beside a Line they have all seen."""
        view = stock_view(1)
        runners = [{'player': 1, 'name': f'r{i}', 'type': 'Runner',
                    'symbol': 'r', 'attack': 2, 'health': 4, 'energy': 10,
                    'x': x, 'y': y, 'state': 'holding', 'direction': None,
                    'flag': False}
                   for i, (x, y) in enumerate([(2, 3), (4, 3), (3, 2)])]
        view['units'] = runners
        return view

    def test_several_units_may_be_ordered_at_one_seen_enemy(self, common):
        view = self.contact_view(common)
        target = (3, 3)
        wishes = {u['name']: common.steps_towards(u, target)
                  for u in view['units']}
        orders = common.resolve(view, wishes, together=[target])
        assert sorted(orders) == ['move r0 east', 'move r1 west',
                                  'move r2 south']

    def test_two_units_are_never_ordered_at_one_empty_square(self, common):
        view = self.contact_view(common)
        target = (3, 3)
        wishes = {u['name']: common.steps_towards(u, target)
                  for u in view['units']}
        orders = common.resolve(view, wishes)
        assert len(orders) == 1

    def test_a_unit_that_cannot_pay_is_not_ordered(self, common):
        view = self.contact_view(common)
        for unit in view['units']:
            unit['energy'] = 0
        wishes = {u['name']: [(0, 1)] for u in view['units']}
        assert common.resolve(view, wishes) == []

    def test_a_unit_walking_off_the_board_is_not_ordered(self, common):
        view = self.contact_view(common)
        wishes = {u['name']: [(0, -1)] for u in view['units']}
        orders = common.resolve(view, wishes)
        assert orders == ['move r0 north', 'move r1 north', 'move r2 north']
        view['units'][2]['y'] = 0
        assert 'move r2 north' not in common.resolve(view, wishes)


# ------------------------------------------------------- the doctrines

class TestSetup:

    @pytest.mark.parametrize('name', STOCK)
    def test_a_stock_doctrine_changes_nothing(self, arena, name):
        for player in (1, 2):
            assert bot(arena, name, player).setup(stock_view(player)) == []

    @pytest.mark.parametrize('name', REBUILT)
    def test_a_rebuilt_doctrine_takes_everything_back_first(self, arena,
                                                            name):
        commands = bot(arena, name, 1).setup(stock_view(1))
        removed = [c for c in commands if c.startswith('remove unit ')]
        assert len(removed) == 16
        assert commands[:16] == removed
        assert all(not c.startswith('remove') for c in commands[16:])

    @pytest.mark.parametrize('name', REBUILT)
    def test_the_army_is_one_the_game_accepts(self, arena, name):
        """Every type through the game's own constructor, the cost against
        the budget, every square inside the seat's half, no square twice,
        and exactly one carrier among the units deployed."""
        for player in (1, 2):
            view = stock_view(player)
            commands = bot(arena, name, player).setup(view)
            designs, units, flags, squares, cost = {}, [], [], set(), 0
            for command in commands:
                parts = command.split()
                if parts[:2] == ['add', 'type']:
                    _, _, tname, symbol, attack, health, energy = parts
                    kind = UnitType(tname, symbol, int(attack), int(health),
                                    int(energy))
                    designs[tname] = kind
                elif parts[:2] == ['add', 'unit']:
                    _, _, tname, uname, x, y = parts
                    x, y = int(x), int(y)
                    assert tname in designs, f'{uname} of an undefined type'
                    assert 0 <= x < SIZE
                    assert y in view['placement']['rows'], \
                        f'{uname} at ({x},{y}) is outside rows ' \
                        f'{view["placement"]["rows"]}'
                    assert (x, y) not in squares, f'({x},{y}) taken twice'
                    squares.add((x, y))
                    kind = designs[tname]
                    cost += kind.attack + kind.health + kind.energy
                    units.append(uname)
                elif parts[:2] == ['set', 'flag']:
                    flags.append(parts[2])
            assert len(set(units)) == len(units)
            assert cost <= BUDGET, f'{name} costs {cost}'
            assert len(flags) == 1 and flags[0] in units

    def test_deploy_puts_depth_zero_at_the_seat_edge(self, arena):
        south = bot(arena, 'lancers', 2).setup(stock_view(2))
        assert 'add unit Keep keep1 3 7' in south
        assert 'add unit Lance lance1 0 4' in south
        assert south[-1] == 'set flag keep1'
        north = bot(arena, 'lancers', 1).setup(stock_view(1))
        assert 'add unit Keep keep1 3 0' in north
        assert 'add unit Lance lance1 0 3' in north


class TestTheStockDoctrinesOnTurnOne:

    def ordered(self, arena, name, player=1):
        view = stock_view(player, turn=2)
        by_name = {u['name']: u for u in view['units']}
        orders = bot(arena, name, player).orders(view)
        parsed = []
        for order in orders:
            _, unit, direction = order.split()
            parsed.append((by_name[unit], direction))
        return parsed

    def test_garrison_orders_nothing(self, arena):
        assert self.ordered(arena, 'garrison') == []
        assert self.ordered(arena, 'garrison', 2) == []

    def test_advance_orders_only_the_front_rank_forward(self, arena):
        ordered = self.ordered(arena, 'advance')
        assert ordered
        assert {u['type'] for u, _ in ordered} <= {'Pawn', 'Heavy'}
        assert {d for _, d in ordered} == {'south'}
        assert {d for _, d in self.ordered(arena, 'advance', 2)} == {'north'}

    def test_flag_hunt_sends_everything_but_keeps_and_walls(self, arena):
        for player, away in ((1, 'north'), (2, 'south')):
            ordered = self.ordered(arena, 'flag_hunt', player)
            names = sorted(u['name'] for u, _ in ordered)
            # on turn one the front rank steps out, and the Runners and
            # Scouts behind the Pawns follow them out of their squares
            # (R4.8); the Lines behind the Walls and the Keeps stay
            assert names == ['heavy1', 'heavy2', 'pawn1', 'pawn2', 'pawn3',
                             'pawn4', 'runner1', 'runner2', 'scout1',
                             'scout2']
            assert {u['type'] for u, _ in ordered} <= set(
                bot(arena, 'flag_hunt', player).hunters)
            assert away not in {d for _, d in ordered}

    def test_a_hunter_walks_round_its_own_units(self, arena, common):
        """A Runner in the corner with the rank in front gone: the way to
        the flag is round the Scout beside it, not through it."""
        view = stock_view(1)
        view['units'] = [u for u in view['units']
                         if u['name'] in ('runner1', 'scout1', 'keep1')]
        runner = next(u for u in view['units'] if u['name'] == 'runner1')
        assert common.path_step(view, runner, (3, 7)) == (0, 1)
        view['units'].append(dict(runner, name='blocker', x=0, y=1))
        assert common.path_step(view, runner, (3, 7)) is None
        view['units'][-1]['y'] = 2
        assert common.path_step(view, runner, (3, 7)) == (0, 1)
        orders = bot(arena, 'flag_hunt', 1).orders(view)
        assert 'move runner1 south' in orders

    def test_screen_moves_the_scouts(self, arena):
        ordered = self.ordered(arena, 'screen')
        scouts = [u['name'] for u, _ in ordered if u['type'] == 'Scout']
        assert sorted(scouts) == ['scout1', 'scout2']


class TestADoctrineIsAFunctionOfItsView:

    @pytest.mark.parametrize('name', DOCTRINES)
    def test_the_same_view_twice_gives_the_same_orders(self, arena, name):
        for player in (1, 2):
            view = stock_view(player, turn=2)
            first = bot(arena, name, player).orders(view)
            second = bot(arena, name, player).orders(view)
            assert first == second

    def test_nothing_under_bots_consults_chance_or_the_clock(self):
        forbidden = re.compile(r'\b(random|time|id|hash)\s*[.(]')
        for path in BOTS.glob('*.py'):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                code = line.split('#')[0]
                assert not forbidden.search(code), f'{path.name}:{number}'


# ------------------------------------------------ through the real roles

@pytest.mark.slow
class TestThroughTheRealRoles:

    def play(self, arena, tmp_path, monkeypatch, p1, p2, turns):
        monkeypatch.setattr(arena, 'LOGS', tmp_path)
        bots = {1: bot(arena, p1, 1), 2: bot(arena, p2, 2)}
        match = arena.Match(99998, bots, max_turns=turns)
        outcome = match.play()
        return outcome, (tmp_path / 'game_99998.log').read_text(), match

    def test_garrison_against_garrison_for_two_turns(self, arena, tmp_path,
                                                     monkeypatch):
        outcome, log, match = self.play(arena, tmp_path, monkeypatch,
                                        'garrison', 'garrison', 2)
        assert outcome is None
        assert 'board 8x8, p1: 250 points, rows 0-3, p2: 250 points, ' \
               'rows 4-7' in log
        assert log.count('is handed 16 units') == 2
        assert log.count('keeps the army as given') == 2
        assert 'after turn 2: in play 14 v 14  (walls: 2 v 2)' in log
        assert match.status == {1: 'active', 2: 'active'}
        final = match.history[-1]['units']
        carriers = sorted((u['player'], u['name']) for u in final
                          if u.get('flag'))
        assert carriers == [(1, 'keep1'), (2, 'keep1')]

    def test_a_setup_without_a_flag_is_not_played(self, arena, tmp_path,
                                                  monkeypatch):
        class Flagless:
            name = 'Flagless'
            doctrine = 'takes the carrier back and names no other'

            def __init__(self, player):
                pass

            def setup(self, view):
                return ['remove unit keep1']

            def orders(self, view):
                return []

        monkeypatch.setattr(arena, 'LOGS', tmp_path)
        bots = {1: Flagless(1), 2: bot(arena, 'garrison', 2)}
        outcome = arena.Match(99997, bots, max_turns=2).play()
        assert outcome.startswith('not played: p1 Flagless: ')
        assert 'flag' in outcome
        log = (tmp_path / 'game_99997.log').read_text()
        assert '-- turn 2' not in log
