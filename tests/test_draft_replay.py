"""Putting back what a session had done and not committed.

The step that changes what anyone can observe. A draft is replayed through the
same rules that accepted it in the first place, onto the view its owner was
published - so what comes back is what they built, and nothing of anyone
else's comes back at all.
"""

import pytest
import yaml

from board_game_concept import Game
from board_game_concept.cli import views
from board_game_concept.service import games
from board_game_concept.service.commands import (AddPlayer, AddType, AddUnit,
                                                 Move, SetBoard, SetFlag)
from game_harness import GameHarness

CROSS = ('Cross', 'X', 1, 5, 10)
RING = ('Ring', 'O', 1, 5, 10)


def abandon(session):
    """End a session without committing, as a killed process does."""
    del session


def deployed_without_committing(harness, number, types, units, flag=True):
    """A session that defines types and deploys units, and then dies.

    It designates a carrier too, because a setup that has one is what a
    session interrupted mid-setup would have had - and what it must have to
    be committable when it is reopened.
    """
    session = harness.session(number)
    for name, symbol, attack, health, energy in types:
        games.perform(session, AddType(name=name, symbol=symbol, attack=attack,
                                       health=health, energy=energy))
    for type_name, unit_name, x, y in units:
        games.perform(session, AddUnit(type_name=type_name, name=unit_name,
                                       x=x, y=y))
    if flag and units:
        games.perform(session, SetFlag(unit=units[0][1]))
    abandon(session)


# --- 3.1 what comes back


def test_a_session_that_ended_mid_setup_gets_its_work_back(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])

    deployed_without_committing(harness, 1, [CROSS],
                                [('Cross', 'x1', 0, 0), ('Cross', 'x2', 1, 0)])

    reopened = harness.session(1)
    assert sorted(reopened.getPlayers()[1]['types']) == ['Cross']
    assert {unit.name: (unit.x, unit.y)
            for unit in reopened.getBoard().units} == {'x1': (0, 0),
                                                       'x2': (1, 0)}
    assert reopened.getDropped() == []


def test_replaying_deployments_builds_the_board_typing_them_builds(tmp_path):
    """`deploy_unit` ends each deployment with a turn on the local board.

    Replay must go through the same function rather than putting units back
    some shorter way, or a board built by restoring differs from the one built
    by typing.
    """
    typed = GameHarness(tmp_path / 'typed')
    typed.create(4, 4, [1])
    live = typed.session(1)
    for command in (AddType(name='Cross', symbol='X', attack=1, health=5,
                            energy=10),
                    AddUnit(type_name='Cross', name='x1', x=0, y=0),
                    AddUnit(type_name='Cross', name='x2', x=1, y=1),
                    AddUnit(type_name='Cross', name='x3', x=2, y=2)):
        games.perform(live, command)

    replayed = GameHarness(tmp_path / 'replayed')
    replayed.create(4, 4, [1])
    deployed_without_committing(
        replayed, 1, [CROSS],
        [('Cross', 'x1', 0, 0), ('Cross', 'x2', 1, 1), ('Cross', 'x3', 2, 2)])
    reopened = replayed.session(1)

    def described(session):
        return sorted((unit.name, unit.x, unit.y, unit.health, unit.energy,
                       unit.state, unit.direction, unit.destroyed,
                       unit.on_board)
                      for unit in session.getBoard().units)

    assert described(reopened) == described(live)


def test_an_order_given_before_a_session_ended_comes_back(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    ordered = harness.session(1)
    games.perform(ordered, Move(unit='x1', direction=1))
    abandon(ordered)

    reopened = harness.session(1)
    restored = reopened.getBoard().getUnitByName('x1')[0]
    assert views.order_word(restored.state, restored.direction) == 'move north'


def test_a_game_with_no_draft_loads_as_it_always_did(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    reopened = harness.session(1)

    assert not reopened.getDraft()
    assert not reopened.getDropped()
    assert sorted(unit.name for unit in reopened.getBoard().units) == ['x1']


# --- 3.2 whose draft is whose


def test_nobody_else_sees_a_drafted_deployment(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    drafting = harness.session(1)
    games.perform(drafting, Move(unit='x1', direction=1))
    abandon(drafting)

    for watcher in (0, 2):
        session = harness.session(watcher)
        ordered = [unit for unit in session.getBoard().units
                   if views.order_word(unit.state, unit.direction) == 'move north']
        assert ordered == [], f"session {watcher} was shown a drafted order"
        assert session.getDraft() == []


def test_show_pending_lists_committed_orders_and_not_drafts(tmp_path):
    """Watching an opponent deliberate is information nobody could get before."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    drafting = harness.session(1)
    games.perform(drafting, Move(unit='x1', direction=1))
    abandon(drafting)

    admin = harness.session(0)
    pending = views.pending_view(admin.getPlayers(), admin.getBoard())
    assert pending == []

    # once it is committed it is pending, exactly as before this change
    harness.order(1, [('x1', 1)])
    admin = harness.session(0)
    pending = views.pending_view(admin.getPlayers(), admin.getBoard())
    assert [entry['unit'] for entry in pending] == ['x1']


# --- 3.3 a draft that belongs to another turn


def test_a_draft_left_from_an_earlier_turn_is_discarded(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    # an order drafted for this turn, and then the turn moves on without it
    drafting = harness.session(1)
    games.perform(drafting, Move(unit='x1', direction=1))
    abandon(drafting)
    harness.turn({1: [], 2: []})

    reopened = harness.session(1)
    restored = reopened.getBoard().getUnitByName('x1')[0]
    assert views.order_word(restored.state, restored.direction) == 'hold'
    assert reopened.getDraft() == []


# --- 3.4 a drafted command that can no longer be carried out


def test_a_drafted_command_that_went_stale_is_dropped(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    deployed_without_committing(harness, 1, [CROSS], [('Cross', 'x1', 0, 0)])

    # a deployment onto the square `x1` already holds, followed by one that is
    # still fine. The order matters: the refused one has to come after the
    # deployment that took the square, or it is the earlier one that is refused
    repository = harness.repository()
    draft = repository.read_draft(1)
    draft['commands'].append({'kind': 'add_unit', 'type_name': 'Cross',
                              'name': 'x0', 'x': 0, 'y': 0})
    draft['commands'].append({'kind': 'add_unit', 'type_name': 'Cross',
                              'name': 'x2', 'x': 2, 'y': 2})
    repository.write_draft(1, draft)

    reopened = harness.session(1)

    assert sorted(unit.name for unit in reopened.getBoard().units) == ['x1',
                                                                       'x2']
    dropped = reopened.getDropped()
    assert len(dropped) == 1
    assert dropped[0][0].name == 'x0'


def test_a_dropped_command_is_not_offered_again(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    deployed_without_committing(harness, 1, [CROSS], [('Cross', 'x1', 0, 0)])
    repository = harness.repository()
    draft = repository.read_draft(1)
    draft['commands'].append({'kind': 'add_unit', 'type_name': 'Cross',
                              'name': 'x0', 'x': 0, 'y': 0})
    repository.write_draft(1, draft)

    harness.session(1)

    # the designation is a command like any other, and is drafted like one
    assert [record['kind'] for record in repository.read_draft(1)['commands']] \
        == ['add_type', 'add_unit', 'set_flag']
    assert harness.session(1).getDropped() == []


@pytest.mark.parametrize('commands', [
    'not a list at all',
    [{'kind': 'fly', 'unit': 'x1'}],
    [{'unit': 'x1'}],
    [{'kind': 'move', 'unit': 'x1'}],
])
def test_no_draft_can_stop_a_game_being_opened(tmp_path, commands):
    """A draft is a session's own work; it cannot be a way to lock yourself out."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    repository = harness.repository()
    repository.write_draft(1, {'turn': 0, 'commands': commands})

    reopened = harness.session(1)

    assert reopened.getBoard() is not None
    assert reopened.getDropped() != []


@pytest.mark.backend('yaml')
def test_an_unreadable_draft_costs_the_draft_and_not_the_game(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    path = (tmp_path / 'games' / '_harness' / 'players' / '1_draft.yaml')
    path.write_text('commands: [{kind: move,\n  unreadable')

    reopened = harness.session(1)

    assert reopened.getBoard() is not None
    assert reopened.getDropped() != []
    assert harness.repository().read_draft(1) is None


# --- 3.5 what committing leaves behind


@pytest.mark.backend('yaml')
def test_committing_publishes_the_same_orders_however_the_work_got_there(
        tmp_path):
    """A session that died and one that did not must publish the same turn."""
    straight = GameHarness(tmp_path / 'straight')
    straight.create(4, 4, [1])
    straight.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])

    interrupted = GameHarness(tmp_path / 'interrupted')
    interrupted.create(4, 4, [1])
    deployed_without_committing(interrupted, 1, [CROSS],
                                [('Cross', 'x1', 0, 0)])
    reopened = interrupted.session(1)
    assert reopened.clientSave()

    def published(harness):
        path = (harness.base_path + '/games/_harness/players/1_units.yaml')
        with open(path) as file:
            return yaml.safe_load(file)

    assert published(interrupted) == published(straight)


def test_reopening_after_committing_restores_nothing(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])

    reopened = harness.session(1)

    assert reopened.getDraft() == []
    assert harness.repository().read_draft(1) is None


def test_the_administrator_gets_uncommitted_setup_back(tmp_path):
    harness = GameHarness(tmp_path)

    doomed = Game(harness.repository(), 0)
    doomed.load()
    games.perform(doomed, SetBoard(size_x=5, size_y=6))
    games.perform(doomed, AddPlayer(number=1))
    games.perform(doomed, AddPlayer(number=2))
    abandon(doomed)

    reopened = Game(harness.repository(), 0)
    reopened.load()

    assert (reopened.getSizeX(), reopened.getSizeY()) == (5, 6)
    assert sorted(reopened.getPlayers()) == [1, 2]
    assert reopened.getDropped() == []
    assert reopened.serverSave()
