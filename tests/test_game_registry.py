"""Which games exist, read off the games tree rather than out of a record.

Not pinned to a backend: the registry reads whichever one the games are in,
and the point of it is that it cannot disagree with what is on disk.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from game_harness import GameHarness, DEFAULT_BACKEND       # noqa: E402
from board_game_concept.service import games as game_ops    # noqa: E402
from board_game_concept.service import registry             # noqa: E402
from board_game_concept.service.commands import (           # noqa: E402
    AddType, AddUnit, SetFlag)
from board_game_concept.service.errors import GameError     # noqa: E402


def _harness(base_path, gameno):
    return GameHarness(base_path, gameno=gameno, backend=DEFAULT_BACKEND)


def _play_a_turn(harness, players=(1, 2)):
    harness.session(0).serverSave()
    for index, number in enumerate(players):
        session = harness.session(number)
        game_ops.perform(session, AddType(name='Cross', symbol='X', attack=1,
                                          health=1, energy=10))
        game_ops.perform(session, AddUnit(type_name='Cross',
                                          name=f'u{number}', x=index, y=index))
        game_ops.perform(session, SetFlag(unit=f'u{number}'))
        session.clientSave()
    harness.session(0).resolveWhenReady()


def _find(records, gameno):
    return [record for record in records if record['gameno'] == gameno][0]


def test_an_empty_tree_lists_nothing(tmp_path):
    assert registry.games(DEFAULT_BACKEND, str(tmp_path)) == []
    assert registry.game_numbers(str(tmp_path)) == []


def test_a_game_made_by_a_role_is_listed_without_registration(tmp_path):
    """Nothing was told about it; the directory listing is the registry."""
    _harness(tmp_path, 'made-elsewhere').create(5, 5, [1, 2])

    listed = registry.games(DEFAULT_BACKEND, str(tmp_path))

    assert [record['gameno'] for record in listed] == ['made-elsewhere']
    assert listed[0]['players'] == [1, 2]


def test_a_game_with_no_board_reports_no_size(tmp_path):
    registry.create('fresh', DEFAULT_BACKEND, str(tmp_path))

    record = _find(registry.games(DEFAULT_BACKEND, str(tmp_path)), 'fresh')

    assert record['state'] == registry.SETTING_UP
    assert record['size_x'] is None
    assert record['size_y'] is None
    assert record['players'] == []


def test_a_game_being_set_up_says_so(tmp_path):
    _harness(tmp_path, 'one').create(5, 5, [1, 2])

    record = _find(registry.games(DEFAULT_BACKEND, str(tmp_path)), 'one')

    assert record['state'] == registry.SETTING_UP
    assert record['turn_number'] == 0
    assert (record['size_x'], record['size_y']) == (5, 5)


def test_a_game_is_still_being_set_up_after_the_setup_commit(tmp_path):
    """The administrator's commit is not a turn and does not number one."""
    harness = _harness(tmp_path, 'one')
    harness.create(5, 5, [1, 2])
    harness.session(0).serverSave()

    record = _find(registry.games(DEFAULT_BACKEND, str(tmp_path)), 'one')

    assert record['state'] == registry.SETTING_UP


def test_a_game_with_a_resolved_turn_is_being_played(tmp_path):
    harness = _harness(tmp_path, 'one')
    harness.create(5, 5, [1, 2])
    _play_a_turn(harness)

    record = _find(registry.games(DEFAULT_BACKEND, str(tmp_path)), 'one')

    assert record['state'] == registry.BEING_PLAYED
    assert record['turn_number'] >= 1


def test_many_games_are_all_listed_in_order(tmp_path):
    for gameno in ('c', 'a', 'b'):
        _harness(tmp_path, gameno).create(4, 4, [1])

    listed = registry.games(DEFAULT_BACKEND, str(tmp_path))

    assert [record['gameno'] for record in listed] == ['a', 'b', 'c']


def test_a_removed_game_stops_being_listed(tmp_path):
    import shutil

    _harness(tmp_path, 'one').create(5, 5, [1, 2])
    assert registry.game_numbers(str(tmp_path)) == ['one']

    shutil.rmtree(os.path.join(str(tmp_path), 'games', '_one'))

    assert registry.game_numbers(str(tmp_path)) == []


def test_the_listing_reports_the_state_a_change_left(tmp_path):
    """No record of the old state survives to be reported."""
    harness = _harness(tmp_path, 'one')
    harness.create(5, 5, [1, 2])
    assert _find(registry.games(DEFAULT_BACKEND, str(tmp_path)),
                 'one')['state'] == registry.SETTING_UP

    _play_a_turn(harness)

    assert _find(registry.games(DEFAULT_BACKEND, str(tmp_path)),
                 'one')['state'] == registry.BEING_PLAYED


def test_an_unreadable_game_does_not_stop_the_others_being_listed(tmp_path):
    _harness(tmp_path, 'good').create(5, 5, [1, 2])
    broken = os.path.join(str(tmp_path), 'games', '_broken')
    os.makedirs(broken)
    with open(os.path.join(broken, 'not-a-game'), 'w', encoding='utf-8') as f:
        f.write('rubbish')

    listed = registry.games(DEFAULT_BACKEND, str(tmp_path))

    assert {record['gameno'] for record in listed} == {'good', 'broken'}
    assert _find(listed, 'good')['state'] != registry.UNREADABLE


def test_creating_a_game(tmp_path):
    record = registry.create('new-one', DEFAULT_BACKEND, str(tmp_path))

    assert record['gameno'] == 'new-one'
    assert record['state'] == registry.SETTING_UP
    assert record['size_x'] is None
    assert record['players'] == []
    assert registry.exists('new-one', str(tmp_path))


def test_creating_a_game_whose_number_is_in_use(tmp_path):
    _harness(tmp_path, 'one').create(5, 5, [1, 2])

    with pytest.raises(GameError, match='already exists'):
        registry.create('one', DEFAULT_BACKEND, str(tmp_path))

    record = _find(registry.games(DEFAULT_BACKEND, str(tmp_path)), 'one')
    assert (record['size_x'], record['size_y']) == (5, 5)
    assert record['players'] == [1, 2]


def test_creating_a_game_with_no_number(tmp_path):
    with pytest.raises(GameError):
        registry.create('  ', DEFAULT_BACKEND, str(tmp_path))


def test_a_created_game_is_set_up_by_the_same_commands(tmp_path):
    registry.create('new-one', DEFAULT_BACKEND, str(tmp_path))

    harness = _harness(tmp_path, 'new-one')
    harness.create(6, 6, [1, 2])

    record = _find(registry.games(DEFAULT_BACKEND, str(tmp_path)), 'new-one')
    assert (record['size_x'], record['size_y']) == (6, 6)
    assert record['players'] == [1, 2]
