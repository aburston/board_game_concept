"""What each seat is told the turn did.

A player could see the board a turn left behind and nothing about how it got
there. A unit that lost eight of its ten health looked exactly like one
nobody had touched, a square that had been fought over looked exactly like
one that had not, and the only thing the interface said about a resolution
was which orders had been refused - so "my wall is one blow from dead" was a
fact the server knew, the engine had reported, and nobody was told.

The engine's events are kept now, per turn and per seat. These are about the
two decisions that makes: which events a seat is entitled to read, and where
each of them happened.
"""

from board_game_concept.domain import Player, UnitType
from board_game_concept.domain.events import Event
from board_game_concept.service import turn_feed

from game_harness import GameHarness


# who owns a unit in these hand-built events, by the letter it is named with:
# `x1` is player 1's, `o1` player 2's, `p1` player 3's. The engine puts this
# on every event it reports; here it is written out, because these events are
# built by hand rather than resolved
OWNERS = {'x': 1, 'o': 2, 'p': 3}


def owned_by(*names):
    """The `players` an event carries, for the units it names.

    A name the convention says nothing about belongs to player 1, which is
    what a test about something other than who owns what wants.
    """
    return ','.join(sorted(
        {str(OWNERS.get(name[0], 1)) for name in names}, key=int))


def entries_of(*events):
    return turn_feed.entries(list(events))


def kinds(made):
    return [entry['kind'] for entry in made]


def squares(made, kind):
    return [(entry['detail'].get('x'), entry['detail'].get('y'))
            for entry in made if entry['kind'] == kind]


# --- what an entry is


def test_an_entry_carries_the_domain_s_own_wording():
    """One sentence per event, said the way the engine says it.

    The wording is not stored beside the event and not written again in the
    browser: the CLI, the feed and a log all read the same event the same way
    because they all ask the domain.
    """
    made = entries_of(
        Event('moved', unit='x1', x=1, y=2, players=owned_by('x1')))
    assert made[0]['text'] == 'x1 moves to (1, 2)'
    assert made[0]['kind'] == 'moved'
    assert made[0]['detail'] == {'unit': 'x1', 'x': 1, 'y': 2,
                                 'players': '1'}


def test_a_blow_is_marked_as_one():
    """The board marks fighting, and what counts as fighting is not its call."""
    fought = entries_of(Event('attacked', unit='x1', target='o1',
                              damage=3, players=owned_by('x1', 'o1')))
    quiet = entries_of(Event('rested', unit='x1', energy=4, players=owned_by('x1')))
    assert fought[0]['fighting'] is True
    assert quiet[0]['fighting'] is False


# --- where it happened


def test_an_attack_is_given_the_square_of_the_contest_it_was_thrown_in():
    """The engine reports an attack from inside a contest that said where.

    Without this the feed can say a unit was hit for eight and not where, and
    a board cannot draw "somewhere".
    """
    made = entries_of(
        Event('contested', x=2, y=1, units=2),
        Event('attacked', unit='o1', target='x1', damage=3, players=owned_by('o1', 'x1')),
        Event('destroyed', unit='x1', players=owned_by('x1')))
    assert squares(made, 'attacked') == [(2, 1)]
    assert squares(made, 'destroyed') == [(2, 1)]


def test_a_unit_resting_elsewhere_is_not_given_the_square_of_a_fight():
    """Resting happens where the unit is standing, which is nowhere near."""
    made = entries_of(
        Event('contested', x=2, y=1, units=2),
        Event('rested', unit='far-away', energy=5, players=owned_by('far-away')))
    assert squares(made, 'rested') == [(None, None)]


def test_a_unit_taken_off_the_board_is_not_placed_at_the_last_fight():
    """Every destroyed unit is removed together, after the fighting.

    By then the contest being spoken of is whichever was fought last, and
    that is somebody else's square.
    """
    made = entries_of(
        Event('contested', x=0, y=0, units=2),
        Event('destroyed', unit='a1', players=owned_by('a1')),
        Event('contested', x=9, y=9, units=2),
        Event('removed', unit='a1', players=owned_by('a1')))
    assert squares(made, 'removed') == [(None, None)]


# --- who may read it


def test_a_seat_is_told_what_happened_to_its_own_units():
    made = entries_of(Event('attacked', unit='o1', target='x1', damage=3,
                            players=owned_by('o1', 'x1')))
    mine = turn_feed.for_seat(made, 1)
    assert kinds(mine) == ['attacked']


def test_a_seat_is_not_told_about_a_fight_between_units_it_cannot_see():
    """Two other players meeting out of sight is not this seat's news.

    Being told would hand a player the one thing `visibility` withholds: that
    somebody is somewhere, and that it is worth going to look.
    """
    made = entries_of(Event('attacked', unit='o1', target='p1', damage=3,
                            players=owned_by('o1', 'p1')))
    mine = turn_feed.for_seat(made, 1)
    assert mine == []


def test_a_seat_is_not_told_about_a_fight_it_can_see_but_is_not_in():
    """Seeing two units is not being in their fight.

    A seat standing beside a contest it took no part in used to read every
    blow struck in it, because it could see both fighters. What they did to
    each other is theirs.
    """
    made = entries_of(Event('attacked', unit='o1', target='p1', damage=3,
                            players=owned_by('o1', 'p1')))
    mine = turn_feed.for_seat(made, 1)
    assert mine == []


def test_a_seat_is_told_of_the_kill_it_made():
    """`destroyed` names the unit that fell and nobody else."""
    made = entries_of(
        Event('contested', x=2, y=1, units=2),
        Event('attacked', unit='x1', target='o1', damage=5, players=owned_by('x1', 'o1')),
        Event('destroyed', unit='o1', players=owned_by('o1')))
    mine = turn_feed.for_seat(made, 1)
    assert kinds(mine) == ['contested', 'attacked', 'destroyed']


def test_a_kill_in_a_fight_the_seat_was_not_in_is_not_told():
    made = entries_of(
        Event('contested', x=9, y=9, units=2),
        Event('attacked', unit='o1', target='p1', damage=5, players=owned_by('o1', 'p1')),
        Event('destroyed', unit='p1', players=owned_by('p1')))
    assert turn_feed.for_seat(made, 1) == []


def test_a_seat_in_a_three_way_reads_its_own_blows_and_no_others():
    made = entries_of(
        Event('contested', x=2, y=1, units=3),
        Event('attacked', unit='o1', target='x1', damage=3, players=owned_by('o1', 'x1')),
        Event('attacked', unit='x1', target='o1', damage=2, players=owned_by('x1', 'o1')),
        Event('attacked', unit='o1', target='p1', damage=3, players=owned_by('o1', 'p1')),
        Event('attacked', unit='p1', target='o1', damage=1, players=owned_by('p1', 'o1')))
    mine = turn_feed.for_seat(made, 1)
    struck = [(e['detail']['unit'], e['detail']['target']) for e in mine
              if e['kind'] == 'attacked']
    assert struck == [('o1', 'x1'), ('x1', 'o1')]
    # and the square it was in, as context for the marks on its board
    assert 'contested' in kinds(mine)
    # but nothing of what the other two did to one another
    assert not any(e['detail'].get('target') == 'p1' for e in mine)


def test_the_square_of_a_fight_the_seat_was_in_comes_with_it():
    """`contested` and `emptied` name nobody, and are context for the fight."""
    made = entries_of(
        Event('contested', x=2, y=1, units=2),
        Event('attacked', unit='o1', target='x1', damage=3, players=owned_by('o1', 'x1')),
        Event('emptied', x=2, y=1))
    mine = turn_feed.for_seat(made, 1)
    assert kinds(mine) == ['contested', 'attacked', 'emptied']


def test_a_square_from_a_fight_the_seat_was_not_in_is_not_named():
    made = entries_of(
        Event('contested', x=9, y=9, units=2),
        Event('attacked', unit='o1', target='p1', damage=3, players=owned_by('o1', 'p1')),
        Event('emptied', x=9, y=9))
    assert turn_feed.for_seat(made, 1) == []


def test_the_order_events_happened_in_is_the_order_they_are_read_in():
    """A fight read out of order is a different fight."""
    made = entries_of(
        Event('engaged', unit='x1', target='o1', x=2, y=1, players=owned_by('x1', 'o1')),
        Event('contested', x=2, y=1, units=2),
        Event('attacked', unit='x1', target='o1', damage=5, players=owned_by('x1', 'o1')),
        Event('destroyed', unit='o1', players=owned_by('o1')),
        Event('held', unit='x1', x=2, y=1, players=owned_by('x1')))
    mine = turn_feed.for_seat(made, 1)
    assert kinds(mine) == ['engaged', 'contested', 'attacked', 'destroyed',
                           'held']


# --- through a real resolution


def a_contested_game(tmp_path, stats=(5, 5, 50), enemy=(3, 6, 50)):
    """Two units a square apart, so ordering one south starts a fight.

    Four rows: a two-player board is halved by rows, so the two cannot stand
    side by side in one row. Player 1 owns rows 0 and 1 and player 2 rows 2
    and 3, and they face each other across the line the halves meet on.
    """
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', *stats)], [('X', 'x1', 1, 1)])
    harness.deploy(2, [('O', 'O', *enemy)], [('O', 'o1', 1, 2)])
    harness.resolve()
    return harness


def feed(harness, number):
    return harness.repository().read_events(number)


def test_a_resolution_records_what_each_seat_may_read(tmp_path):
    harness = a_contested_game(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})

    for number in (1, 2):
        told = feed(harness, number)
        assert [entry['kind'] for entry in told].count('attacked') > 0, (
            f'seat {number} was told nothing about a fight it was in')
        assert any('attacks' in entry['text'] for entry in told)


def test_a_seat_is_told_the_damage_and_the_square(tmp_path):
    harness = a_contested_game(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})

    attacks = [entry for entry in feed(harness, 1)
               if entry['kind'] == 'attacked']
    assert attacks, 'no attack was recorded'
    for attack in attacks:
        assert attack['detail']['damage'] > 0
        assert (attack['detail']['x'], attack['detail']['y']) == (1, 2)


def test_a_seat_is_not_told_about_a_deployment_it_could_not_see(tmp_path):
    """Setup is resolved like any turn, and the armies are out of contact."""
    harness = a_contested_game(tmp_path)
    told = feed(harness, 1)
    deployed = [entry['detail']['unit'] for entry in told
                if entry['kind'] == 'deployed']
    assert deployed == ['x1']


def test_the_whole_log_is_kept_for_a_session_entitled_to_it(tmp_path):
    """The observer and the administrator see the game, so they see the log."""
    harness = a_contested_game(tmp_path)
    harness.turn({1: [('x1', UnitType.SOUTH)], 2: []})

    log = harness.repository().read_turn_events()
    deployed = {entry['detail']['unit'] for entry in log
                if entry['kind'] == 'deployed'}
    assert deployed == {'x1', 'o1'}


def a_march(tmp_path):
    """Two turns of moving, out of contact, so each turn has something to say."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 1, 4, 50)], [('X', 'x1', 0, 0)])
    harness.deploy(2, [('O', 'O', 1, 4, 50)], [('O', 'o1', 3, 3)])
    harness.resolve()
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    harness.turn({1: [('x1', UnitType.EAST)], 2: []})
    return harness


def test_a_feed_is_a_history_rather_than_a_snapshot(tmp_path):
    """Every turn is kept, so "how did I get here" has an answer.

    The board only ever shows the position now. A player who wants to know
    which turn cost them the wall has nothing to read it off, and "look at
    the board" is not an answer to a question about the past.
    """
    harness = a_march(tmp_path)

    turns = {entry['turn'] for entry in feed(harness, 1)}
    assert len(turns) >= 3, f'only {turns} kept'


def test_a_feed_can_be_read_from_a_turn_onwards(tmp_path):
    """A screen that wants the last turn asks for the last turn."""
    harness = a_march(tmp_path)
    last = max(entry['turn'] for entry in feed(harness, 1))

    since = harness.repository().read_events(1, since=last)
    assert since, f'nothing was kept for turn {last}'
    assert all(entry['turn'] >= last for entry in since)


# --- two players who chose the same name


def a_game_with_one_name(tmp_path):
    """Both players call their unit `scout`, which the rules allow.

    A name has only to be unique within one player's own units (`R2.7`), and
    two players setting up in secret cannot avoid choosing alike - the default
    army hands them the same names on purpose.
    """
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2], budget=Player.MAX_BUDGET)
    harness.deploy(1, [('X', 'X', 5, 5, 50)], [('X', 'scout', 1, 1)])
    harness.deploy(2, [('O', 'O', 3, 6, 50)], [('O', 'scout', 1, 2)])
    harness.resolve()
    return harness


def test_a_seat_is_not_told_where_the_other_players_unit_was_placed(tmp_path):
    """The leak this was: both entries named `scout`, so both were kept."""
    harness = a_game_with_one_name(tmp_path)

    mine = feed(harness, 1)

    placed = [entry for entry in mine if entry['kind'] == 'deployed']
    assert len(placed) == 1, 'their own, and not the other player\'s'
    assert placed[0]['detail']['x'], placed[0]['detail']['y'] == (1, 1)


def test_each_seat_reads_only_its_own_half_of_a_fight(tmp_path):
    """Ordering one into the other starts a fight both are entitled to."""
    harness = a_game_with_one_name(tmp_path)
    harness.turn({1: [('scout', UnitType.SOUTH)], 2: []})

    for number in (1, 2):
        read = feed(harness, number)
        assert read, f'seat {number} was told about its own fight'
        for entry in read:
            told = entry['detail'].get('players')
            if told is None:
                continue                   # square-only context
            assert str(number) in told.split(','), (number, entry)


def test_an_event_says_whose_units_it_names(tmp_path):
    """Which is what makes the two rules above possible."""
    harness = a_game_with_one_name(tmp_path)
    harness.turn({1: [('scout', UnitType.SOUTH)], 2: []})

    struck = [entry for entry in harness.repository().read_turn_events()
              if entry['kind'] == 'attacked']

    assert struck, 'they fought'
    for entry in struck:
        assert entry['detail']['players'] == '1,2', (
            'an attack involves the two players whose units traded it')
