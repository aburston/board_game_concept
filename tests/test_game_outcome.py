"""Elimination, victory, draw, and the turn number they are recorded against.

None of this existed: the server's turn cycle ran forever, a wiped-out player
still held the commit barrier open, and nothing anywhere counted turns.
"""

import pytest

from board_game_concept.domain import Player, UnitType

from game_harness import GameHarness


def duel(tmp_path, mine=(5, 5, 50), theirs=None, my_units=None, their_units=None):
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', *mine)], my_units or [('X', 'x1', 0, 0)])
    harness.deploy(2, [('O', 'O', *(theirs or mine))],
                   their_units or [('O', 'o1', 1, 0)])
    harness.resolve()
    return harness


def outcome(harness):
    return harness.session(0).getOutcome()


# --- turn numbering


def test_the_setup_commit_is_not_a_turn(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2], budget=Player.MAX_BUDGET)
    assert harness.session(0).getTurnNumber() == 0


def test_turns_are_numbered_from_one(tmp_path):
    harness = duel(tmp_path, mine=(1, 10, 50))
    assert harness.session(0).getTurnNumber() == 1
    harness.turn({1: [], 2: []})
    assert harness.session(0).getTurnNumber() == 2
    harness.turn({1: [], 2: []})
    assert harness.session(0).getTurnNumber() == 3


def test_the_turn_number_survives_a_reload(tmp_path):
    harness = duel(tmp_path, mine=(1, 10, 50))
    harness.turn({1: [], 2: []})
    for number in (0, 1, 2):
        assert harness.session(number).getTurnNumber() == 2


@pytest.mark.backend('yaml')
def test_published_records_name_their_turn(tmp_path):
    import yaml

    harness = duel(tmp_path, mine=(1, 10, 50))
    harness.turn({1: [], 2: []})
    repository = harness.repository()
    root = repository.data_path
    units = yaml.safe_load(open(f'{root}/units.yaml'))
    assert units['turn'] == 2
    view = yaml.safe_load(open(f'{repository.player_path}/1_units_seen.yaml'))
    assert view['turn'] == 2
    rejected = yaml.safe_load(open(f'{repository.player_path}/1_rejected.yaml'))
    assert rejected['turn'] == 2


# --- elimination


def test_a_player_who_loses_their_last_unit_is_eliminated(tmp_path):
    harness = duel(tmp_path, mine=(10, 10, 50), theirs=(1, 1, 50))
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert harness.session(0).getEliminated() == [2]
    assert harness.session(0).isEliminated(2)
    assert not harness.session(0).isEliminated(1)


def test_an_inert_unit_keeps_its_owner_in_the_game(tmp_path):
    # attack 5 on energy 1: o1 can neither attack nor move, but is not lost
    harness = duel(tmp_path, mine=(1, 10, 50), theirs=(5, 10, 1),
                   their_units=[('O', 'o1', 5, 2)])
    harness.turn({1: [], 2: []})
    assert harness.session(0).getEliminated() == []
    assert outcome(harness) is None


def test_a_player_who_deployed_nothing_is_eliminated(tmp_path):
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 1, 5, 50)], [('X', 'x1', 0, 0)])
    harness.deploy(2, [('O', 'O', 1, 5, 50)], [])
    harness.resolve()
    assert harness.session(0).getEliminated() == [2]


# --- victory and draw


def test_the_last_player_standing_wins(tmp_path):
    harness = duel(tmp_path, mine=(10, 10, 50), theirs=(1, 1, 50))
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert outcome(harness) == {'decided': True, 'winner': 1, 'turn': 2}


def test_mutual_destruction_is_a_draw(tmp_path):
    harness = duel(tmp_path)
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    assert outcome(harness) == {'decided': True, 'winner': None, 'turn': 2}


def test_an_undecided_game_reports_no_outcome(tmp_path):
    harness = duel(tmp_path, mine=(1, 10, 50), their_units=[('O', 'o1', 5, 2)])
    harness.turn({1: [], 2: []})
    assert outcome(harness) is None


def test_a_one_player_game_is_never_decided(tmp_path):
    # there is nobody to be the last player standing against, which is what
    # keeps a solo game usable as a sandbox
    harness = GameHarness(tmp_path)
    harness.create(6, 3, [1], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 1, 5, 50)], [('X', 'x1', 0, 0)])
    harness.resolve()
    harness.turn({1: []})
    assert outcome(harness) is None
    assert harness.session(0).getEliminated() == []


def test_every_role_reads_the_same_outcome(tmp_path):
    harness = duel(tmp_path, mine=(10, 10, 50), theirs=(1, 1, 50))
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    results = {number: harness.session(number).getOutcome()
               for number in (0, 1, 2)}
    assert results[0] == results[1] == results[2]
    assert results[0]['winner'] == 1


def test_a_decided_game_resolves_no_further_turns(tmp_path):
    harness = duel(tmp_path, mine=(10, 10, 50), theirs=(1, 1, 50))
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    decided_on = harness.session(0).getTurnNumber()

    assert harness.session(0).serverSave() is False
    assert harness.session(0).getTurnNumber() == decided_on


# --- the commit barrier


def test_an_eliminated_player_is_not_waited_for(tmp_path):
    from board_game_concept.service.turn import _awaited_players

    harness = duel(tmp_path, mine=(10, 10, 50), theirs=(1, 1, 50),
                   my_units=[('X', 'x1', 0, 0), ('X', 'x2', 0, 2)])
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})

    server = harness.session(0)
    assert server.getEliminated() == [2]
    assert _awaited_players(server) == {1}
