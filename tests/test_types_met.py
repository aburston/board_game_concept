"""What a player has met, which outlives contact with it.

A sighting lasts one turn: an enemy nobody touched this turn is off your board
and out of your list of types by the next resolution, which is `visibility`
working as it should. It took the design with it, so a player who had fought a
unit could not afterwards say what it had been built with - and deciding
whether to attack is exactly the moment you want to know.

What is kept is the design and the turn it was met on. Where it was is not
kept, then or ever: a memory of a design is not a memory of a position.
"""

from board_game_concept.domain import Player, UnitType, army

from game_harness import GameHarness


def a_meeting(tmp_path, mine=(2, 4, 3), theirs=(1, 6, 3)):
    """Two units a square apart, each too spent to finish the other."""
    harness = GameHarness(tmp_path)
    # four rows: player 1 owns rows 0 and 1 and player 2 rows 2 and 3, so the
    # two meet across the line the halves meet on rather than side by side
    harness.create(5, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', *mine)], [('X', 'x1', 1, 1)])
    harness.deploy(2, [('O', 'O', *theirs)], [('O', 'o1', 1, 2)])
    harness.resolve()
    return harness


def met(harness, number):
    return harness.repository().read_known_types(number)


def types_in_contact(harness, number):
    """What `show types` lists, less the catalogue every player is given.

    These tests are about what contact teaches a player, and the default
    catalogue teaches them nothing: they were registered with it. It is left
    out here so that the designs in this game - which are named for it, `X`
    and `O` - are what the assertions are about.
    """
    session = harness.session(number)
    catalogue = set(army.types())
    return sorted(
        name for player in session.getPlayers().values()
        for name in player.get('types', {})
        if name not in catalogue)


def test_nothing_is_known_before_contact(tmp_path):
    harness = a_meeting(tmp_path)
    assert met(harness, 1) == []
    assert met(harness, 2) == []


def test_a_design_met_is_kept(tmp_path):
    harness = a_meeting(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})

    known = met(harness, 1)
    assert [entry['name'] for entry in known] == ['O']
    assert known[0]['owner'] == 2
    assert (known[0]['attack'], known[0]['health'], known[0]['energy']) \
        == (1, 6, 3)


def test_it_is_kept_as_designed_rather_than_as_met(tmp_path):
    """A wounded enemy is not a weaker type, and reading it as one misleads."""
    harness = a_meeting(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})

    hurt = harness.units(1).get('o1')
    assert hurt is not None and hurt.health < 6, 'the fixture drew no blood'
    assert met(harness, 1)[0]['health'] == 6


def test_it_outlives_the_contact(tmp_path):
    """The types in contact go; what has been met stays."""
    harness = a_meeting(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})
    assert types_in_contact(harness, 1) == ['O', 'X']

    harness.turn({1: [], 2: []})

    assert types_in_contact(harness, 1) == ['X'], 'contact was not lost'
    assert [entry['name'] for entry in met(harness, 1)] == ['O']


def test_what_is_kept_says_nothing_about_where(tmp_path):
    """The one thing a player may not remember is a position."""
    harness = a_meeting(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})

    for entry in met(harness, 1):
        assert 'x' not in entry and 'y' not in entry
        assert 'unit' not in entry
        assert set(entry) == {'owner', 'name', 'symbol', 'attack', 'health',
                              'energy', 'first_seen', 'last_seen'}


def test_the_turn_it_was_met_on_is_kept(tmp_path):
    harness = a_meeting(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})
    first = met(harness, 1)[0]['first_seen']

    harness.turn({1: [], 2: []})

    assert met(harness, 1)[0]['first_seen'] == first, (
        'a turn out of contact rewrote when the design was met')


def test_a_player_is_not_given_a_design_they_never_met(tmp_path):
    """Two units that never touch teach each other nothing."""
    harness = GameHarness(tmp_path)
    harness.create(5, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 1, 4, 8)], [('X', 'x1', 0, 0)])
    harness.deploy(2, [('O', 'O', 1, 4, 8)], [('O', 'o1', 4, 3)])
    harness.resolve()
    harness.turn({1: [], 2: []})

    assert met(harness, 1) == []
    assert met(harness, 2) == []


def test_both_sides_of_a_meeting_learn(tmp_path):
    harness = a_meeting(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})

    assert [entry['name'] for entry in met(harness, 1)] == ['O']
    assert [entry['name'] for entry in met(harness, 2)] == ['X']
