"""When a turn's result becomes readable, relative to when a player is released.

A client waits by testing whether its order file is still there, so deleting
that file is the moment a waiting player is let go. Everything the turn produced
has to be written before that, or a released player reads the previous turn's
board - which is what happened, twice in twenty-six suite runs, as an empty
board drawn straight after `commit complete`.

The order is asserted here rather than raced. A timing test for this would be no
better than the defect.
"""

import pytest

from board_game_concept.service import games
from board_game_concept.service.commands import AddPlayer, SetBoard
from game_harness import GameHarness

CROSS = ('Cross', 'X', 1, 5, 10)
RING = ('Ring', 'O', 1, 5, 10)

# what the turn published, and so what has to be written before a player is let
# go. `write_player` and `write_rejections` are in the same half and are listed
# because a released client reads both
PUBLISHED = ('write_progress', 'write_player', 'write_rejections',
             'write_units', 'write_view')


class Recorder:
    """A repository that remembers the order it was asked to do things in."""

    def __init__(self, repository):
        self._repository = repository
        self.calls = []

    def __getattr__(self, name):
        attribute = getattr(self._repository, name)
        if not callable(attribute):
            return attribute

        def recorded(*args, **kwargs):
            self.calls.append(name)
            return attribute(*args, **kwargs)

        return recorded

    def first(self, name):
        return self.calls.index(name) if name in self.calls else None

    def last(self, name):
        for at in range(len(self.calls) - 1, -1, -1):
            if self.calls[at] == name:
                return at
        return None


def resolved_with_a_recorder(harness, player_number=0):
    """One resolution, with every repository call it made written down."""
    from board_game_concept import Game

    recorder = Recorder(harness.repository())
    server = Game(recorder, player_number)
    server.load()
    recorder.calls.clear()
    assert server.serverSave()
    return recorder


@pytest.fixture(name='resolution')
def _resolution(tmp_path):
    """A game with two players who have both committed, resolved once."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    return resolved_with_a_recorder(harness)


@pytest.mark.parametrize('operation', PUBLISHED)
def test_the_turn_is_published_before_a_player_is_released(resolution,
                                                           operation):
    """Deleting the order files is what lets a waiting player go."""
    released = resolution.first('clear_orders')
    assert released is not None, 'the turn released nobody'
    written = resolution.last(operation)
    assert written is not None, f'the turn never called {operation}'
    assert written < released, (
        f'{operation} happened after clear_orders, so a released player could '
        f'read a turn that had not finished being written:\n'
        f'  {resolution.calls}')


def test_every_view_is_written_before_a_player_is_released(resolution):
    """Not just the last one: each player reads their own."""
    views = [at for at, name in enumerate(resolution.calls)
             if name == 'write_view']
    assert len(views) == 2, 'both players should have been published a view'
    assert max(views) < resolution.first('clear_orders')


def test_the_next_turn_is_seeded_after_the_orders_are_cleared(tmp_path):
    """The trap: a `clear_orders` placed after this erases what it wrote.

    A `load player` file brings units in, and they are published as that
    player's orders for the turn about to be resolved. They are the next turn's
    input, not this turn's leftovers.
    """
    from board_game_concept import Game

    harness = GameHarness(tmp_path)
    recorder = Recorder(harness.repository())
    server = Game(recorder, 0)
    server.load()
    games.perform(server, SetBoard(size_x=4, size_y=4))
    games.perform(server, AddPlayer(number=1))
    server.getPlayers()[1]['units'] = [{
        'player': 1, 'type': 'Cross', 'name': 'x1', 'symbol': 'X',
        'attack': 1, 'health': 5, 'energy': 10, 'x': 0, 'y': 0,
        'state': 0, 'direction': 0, 'destroyed': False, 'on_board': False,
    }]
    server.getPlayers()[1]['types']['Cross'] = {
        'name': 'Cross', 'symbol': 'X', 'attack': 1, 'health': 5, 'energy': 10}
    recorder.calls.clear()
    assert server.serverSave()

    seeded = recorder.last('write_orders')
    assert seeded is not None, 'the loaded player was never given orders'
    assert seeded > recorder.first('clear_orders'), (
        f'the orders seeded for the next turn were written before the turn '
        f'cleared its own, so clearing erased them:\n  {recorder.calls}')


def test_a_commit_is_spent_before_one_is_recorded_on_a_players_behalf(
        tmp_path):
    """Backwards, this hangs the barrier on a player nobody can commit for."""
    from board_game_concept import Game

    harness = GameHarness(tmp_path)
    recorder = Recorder(harness.repository())
    server = Game(recorder, 0)
    server.load()
    games.perform(server, SetBoard(size_x=4, size_y=4))
    games.perform(server, AddPlayer(number=1))
    server.getPlayers()[1]['units'] = [{
        'player': 1, 'type': 'Cross', 'name': 'x1', 'symbol': 'X',
        'attack': 1, 'health': 5, 'energy': 10, 'x': 0, 'y': 0,
        'state': 0, 'direction': 0, 'destroyed': False, 'on_board': False,
    }]
    server.getPlayers()[1]['types']['Cross'] = {
        'name': 'Cross', 'symbol': 'X', 'attack': 1, 'health': 5, 'energy': 10}
    recorder.calls.clear()
    assert server.serverSave()

    assert recorder.first('clear_commits') < recorder.last('mark_committed'), (
        f'the commit recorded for the loaded player was spent by the same '
        f'resolution that recorded it:\n  {recorder.calls}')


# --- what the ordering is for


def test_a_released_player_reads_the_turn_they_waited_for(tmp_path):
    """The empty board: a player let go before their view was published.

    Driven by asking, at the moment the turn releases them, what they would
    read - which is what the client does the instant `wait_for_turn` returns.
    """
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])

    repository = harness.repository()
    seen = {}

    class ReleasesIntoAView:
        """A repository that reads the player's view as it releases them."""

        def __init__(self, wrapped):
            self._wrapped = wrapped

        def __getattr__(self, name):
            return getattr(self._wrapped, name)

        def clear_orders(self):
            # exactly what a client sees the moment it stops waiting
            seen['view'] = self._wrapped.read_view(1)
            return self._wrapped.clear_orders()

    from board_game_concept import Game
    server = Game(ReleasesIntoAView(repository), 0)
    server.load()
    assert server.serverSave()

    assert seen['view'], 'the player was released before they had any view'
    assert [unit['name'] for unit in seen['view']] == ['x1'], (
        'the view a released player reads is not the one the turn published')


def test_a_session_cannot_load_part_way_through_a_resolution(tmp_path,
                                                             monkeypatch):
    """Stronger than it was, since a game is held while it is resolved.

    This used to assert that a session loading mid-resolution was told its
    orders were still pending, which was the best available when a reader could
    get in at all. It no longer can: a resolution holds the game for writing and
    a reader waits for it. Asserted by giving the reader almost no patience and
    watching it be refused, which is exclusion observed rather than inferred.
    """
    from board_game_concept.storage import lock as lock_module

    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    monkeypatch.setattr(lock_module, 'TIMEOUT', 0.05)

    repository = harness.repository()
    refused = {}

    class LoadsAsItPublishes:
        """Tries to open a session part way through publishing the turn."""

        def __init__(self, wrapped):
            self._wrapped = wrapped

        def __getattr__(self, name):
            return getattr(self._wrapped, name)

        def write_units(self, text):
            result = self._wrapped.write_units(text)
            try:
                harness.session(1)
                refused['excluded'] = False
            except lock_module.GameIsBusy:
                refused['excluded'] = True
            return result

    from board_game_concept import Game
    server = Game(LoadsAsItPublishes(repository), 0)
    server.load()
    assert server.serverSave()

    assert refused['excluded'] is True, (
        'a session read the game part way through a resolution')
    # and once the resolution has finished, it opens and the turn is complete
    client = harness.session(1)
    assert client.getUnprocessedMoves() is False
    assert sorted(unit.name for unit in client.getBoard().units) == ['x1']


def test_a_loaded_players_units_still_reach_the_board(tmp_path):
    """The trap, end to end rather than by call order."""
    from board_game_concept import Game
    from board_game_concept.service.commands import AddType

    harness = GameHarness(tmp_path)
    server = Game(harness.repository(), 0)
    server.load()
    games.perform(server, SetBoard(size_x=4, size_y=4))
    games.perform(server, AddPlayer(number=1))
    server.getPlayers()[1]['units'] = [{
        'player': 1, 'type': 'Cross', 'name': 'x1', 'symbol': 'X',
        'attack': 1, 'health': 5, 'energy': 10, 'x': 2, 'y': 3,
        'state': 0, 'direction': 0, 'destroyed': False, 'on_board': False,
    }]
    server.getPlayers()[1]['types']['Cross'] = {
        'name': 'Cross', 'symbol': 'X', 'attack': 1, 'health': 5, 'energy': 10}

    # the setup resolution seeds the units as next turn's orders...
    assert server.serverSave()
    # ...and the next resolution is what puts them on the board
    assert harness.resolve()

    units = harness.units(0)
    assert 'x1' in units, 'a loaded player never got its units onto the board'
    assert (units['x1'].x, units['x1'].y) == (2, 3)


# --- the barrier is asked where the turn is resolved


def ready_game(tmp_path):
    """A game whose every player has committed, waiting to be resolved."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [CROSS], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [RING], [('Ring', 'o1', 3, 3)])
    return harness


def test_reading_asking_and_resolving_happen_inside_one_hold(tmp_path):
    from board_game_concept import Game

    harness = ready_game(tmp_path)
    recorder = Recorder(harness.repository())
    server = Game(recorder, 0)
    recorder.calls.clear()

    assert server.resolveWhenReady() is True

    held = recorder.first('held')
    assert held is not None, 'the game was never held'
    for asked in ('read_progress', 'committed_players', 'write_view'):
        at = recorder.first(asked)
        assert at is not None and at > held, (
            f'{asked} happened outside the hold:\n  {recorder.calls}')


def test_two_callers_woken_for_one_turn_resolve_it_once(tmp_path):
    """Both find the barrier met. Only one turn is resolved.

    This is the gap: each was woken, each would have acted on what it was told,
    and under the old shape each would have resolved. Asked where the turn is
    resolved, the second is told the barrier is no longer met. Sequential rather
    than nested because the hold makes it so - the second cannot get in until
    the first is done, which is the point.
    """
    from board_game_concept import Game
    from board_game_concept.service import turn as turn_service

    harness = ready_game(tmp_path)
    first = Game(harness.repository(), 0)
    first.load()
    second = Game(harness.repository(), 0)
    second.load()

    # both were woken, and both would have found the barrier met
    assert turn_service.barrier_met(first)
    assert turn_service.barrier_met(second)

    assert first.resolveWhenReady() is True
    assert second.resolveWhenReady() is None, (
        'a second caller resolved a turn the first had already resolved')


def test_the_turn_a_second_caller_did_not_resolve_advanced_once(tmp_path):
    harness = ready_game(tmp_path)
    from board_game_concept import Game

    assert Game(harness.repository(), 0).resolveWhenReady() is True
    after_one = harness.session(0).getTurnNumber()

    # a second caller, with nothing new committed
    assert Game(harness.repository(), 0).resolveWhenReady() is None

    assert harness.session(0).getTurnNumber() == after_one
    # and each player's orders were consumed once, not twice
    assert sorted(unit.name for unit in harness.session(0).getBoard().units) \
        == ['o1', 'x1']


def test_an_unmet_barrier_is_told_apart_from_a_turn_that_cannot_resolve(
        tmp_path):
    """Folded together, the server exits on the one case that is not a failure."""
    from board_game_concept import Game

    harness = ready_game(tmp_path)
    assert Game(harness.repository(), 0).resolveWhenReady() is True

    # nothing more committed: not met, which is another caller having got there
    # first and is the system working
    assert Game(harness.repository(), 0).resolveWhenReady() is None

    # a game that is over cannot resolve a turn, which is a different answer
    decided = harness.session(0)
    decided.setProgress({'turn': 5, 'eliminated': [2],
                         'outcome': {'decided': True, 'winner': 1, 'turn': 5}})
    assert decided.serverSave() is False


def test_ending_setup_is_not_held_to_the_barrier(tmp_path):
    """Nobody has committed when the administrator ends setup."""
    from board_game_concept import Game
    from board_game_concept.service.commands import AddPlayer, SetBoard

    harness = GameHarness(tmp_path)
    server = Game(harness.repository(), 0)
    server.load()
    games.perform(server, SetBoard(size_x=4, size_y=4))
    games.perform(server, AddPlayer(number=1))

    # the barrier is not met - player 1 has committed nothing - and setup
    # still ends
    assert server.serverSave() is True
    assert harness.session(0).getSizeX() == 4
