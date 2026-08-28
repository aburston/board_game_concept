"""Setting a game up is a thing you are still deciding.

Sizing the board and registering seats were both one-way: a board that existed
could not be resized and a player who had been added could not be removed, so
an administrator who typed 6 for 5, or registered a seat nobody turned up for,
had a game to throw away and make again.

Both stand when the setup holding them is committed, and until then both can
be taken back. Nothing standing is dropped in silence: a resize that would
leave a unit off the board is refused, naming it.
"""

import pytest

from board_game_concept.service import games
from board_game_concept.service.commands import (AddPlayer, LoadPlayer,
                                                 RemovePlayer, SetBoard)
from board_game_concept.service.errors import GameError

from game_harness import GameHarness


@pytest.fixture(name='admin')
def _admin(tmp_path):
    """An administrator's session on a game nobody has set up yet."""
    harness = GameHarness(tmp_path)
    return harness, harness.session(0)


def sizes(session):
    return (session.getSizeX(), session.getSizeY())


# --- the board


def test_a_board_can_be_sized_again(admin):
    _, server = admin
    games.perform(server, SetBoard(size_x=6, size_y=6))
    assert sizes(server) == (6, 6)

    games.perform(server, SetBoard(size_x=4, size_y=8))

    assert sizes(server) == (4, 8)


def test_the_last_size_is_the_one_committed(admin):
    harness, server = admin
    games.perform(server, SetBoard(size_x=6, size_y=6))
    games.perform(server, SetBoard(size_x=3, size_y=3))
    games.perform(server, AddPlayer(number=1))
    assert server.serverSave()

    assert sizes(harness.session(0)) == (3, 3)


def test_a_size_the_board_refuses_is_still_refused(admin):
    _, server = admin
    games.perform(server, SetBoard(size_x=5, size_y=5))
    for bad in (SetBoard(size_x=1, size_y=5), SetBoard(size_x=5, size_y=99)):
        with pytest.raises(GameError):
            games.perform(server, bad)

    assert sizes(server) == (5, 5), 'a refused size changed the board'


def test_resizing_after_setup_is_committed_is_refused(admin):
    harness, server = admin
    games.perform(server, SetBoard(size_x=5, size_y=5))
    games.perform(server, AddPlayer(number=1))
    assert server.serverSave()

    later = harness.session(0)
    with pytest.raises(GameError) as refusal:
        games.perform(later, SetBoard(size_x=6, size_y=6))
    assert 'committed' in str(refusal.value)


def a_loaded_army(tmp_path, squares):
    """A player file the administrator can load, with units on it.

    `load player` is how an administrator's own session comes to hold units
    during setup, which is the only way there is anything standing while the
    board can still be resized.
    """
    path = tmp_path / 'player_9.yaml'
    units = [
        f"  - {{ id: {index}, player: 1, type: \"O\", name: \"o{index}\", "
        f"symbol: \"O\", attack: \"1\", health: \"1\", energy: \"10\", "
        f"x: {x}, y: {y}, state: 2, direction: 0, destroyed: False, "
        "on_board: True }"
        for index, (x, y) in enumerate(squares)]
    path.write_text(
        "number: 1\n"
        "types:\n"
        "  O: {attack: '1', energy: '10', health: '1', name: O, symbol: O}\n"
        "units:\n" + "\n".join(units) + "\n", encoding='utf-8')
    return str(path)


def test_a_resize_that_would_leave_a_unit_off_the_board_is_refused(
        admin, tmp_path):
    """Rubbing out a corner of somebody's army is not a resize."""
    _, server = admin
    games.perform(server, SetBoard(size_x=6, size_y=6))
    games.perform(server, LoadPlayer(path=a_loaded_army(tmp_path, [(5, 5)])))

    with pytest.raises(GameError) as refusal:
        games.perform(server, SetBoard(size_x=3, size_y=3))
    assert 'o0' in str(refusal.value)
    assert sizes(server) == (6, 6), 'the board was resized anyway'


def loaded(session, number=1):
    """Where a loaded army stands, by name.

    A loaded player's units are records waiting to be deployed rather than
    units on a board, which is what setup holds until it is committed.
    """
    return {str(unit['name']): (int(unit['x']), int(unit['y']))
            for unit in session.getPlayers()[number].get('units') or []}


def test_a_resize_that_fits_keeps_every_unit_where_it_stood(
        admin, tmp_path):
    _, server = admin
    games.perform(server, SetBoard(size_x=6, size_y=6))
    games.perform(server,
                  LoadPlayer(path=a_loaded_army(tmp_path, [(1, 1), (2, 3)])))

    games.perform(server, SetBoard(size_x=8, size_y=4))

    assert loaded(server) == {'o0': (1, 1), 'o1': (2, 3)}
    assert sizes(server) == (8, 4)


def test_units_keep_their_squares_across_a_resize(tmp_path):
    """A board that grows is the same board, with more of it."""
    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])
    harness.deploy(1, [('X', 'X', 1, 4, 8)], [('X', 'x1', 3, 3)])
    harness.resolve()

    standing = harness.units(1)['x1']
    assert (standing.x, standing.y) == (3, 3)


# --- the seats


def test_a_player_can_be_removed(admin):
    _, server = admin
    games.perform(server, SetBoard(size_x=5, size_y=5))
    games.perform(server, AddPlayer(number=1))
    games.perform(server, AddPlayer(number=2))

    games.perform(server, RemovePlayer(number=2))

    assert sorted(server.getPlayers()) == [1]


def test_removing_a_player_who_is_not_there_is_refused(admin):
    _, server = admin
    games.perform(server, SetBoard(size_x=5, size_y=5))
    with pytest.raises(GameError) as refusal:
        games.perform(server, RemovePlayer(number=3))
    assert 'no player 3' in str(refusal.value)


def test_a_removed_player_is_not_committed_into_the_game(admin):
    harness, server = admin
    games.perform(server, SetBoard(size_x=5, size_y=5))
    games.perform(server, AddPlayer(number=1))
    games.perform(server, AddPlayer(number=2))
    games.perform(server, RemovePlayer(number=2))
    assert server.serverSave()

    assert harness.repository().player_numbers() == [1]


def test_a_seat_number_can_be_reused_after_being_removed(admin):
    """Removing is not a ban: it is taking back a decision."""
    _, server = admin
    games.perform(server, SetBoard(size_x=5, size_y=5))
    games.perform(server, AddPlayer(number=2, budget=50))
    games.perform(server, RemovePlayer(number=2))
    games.perform(server, AddPlayer(number=2, budget=120))

    assert server.getPlayers()[2]['obj'].budget == 120


def test_removing_a_player_after_setup_is_committed_is_refused(admin):
    harness, server = admin
    games.perform(server, SetBoard(size_x=5, size_y=5))
    games.perform(server, AddPlayer(number=1))
    games.perform(server, AddPlayer(number=2))
    assert server.serverSave()

    later = harness.session(0)
    with pytest.raises(GameError):
        games.perform(later, RemovePlayer(number=2))


def test_a_removed_player_takes_their_units_with_them(admin, tmp_path):
    """A seat removed leaves nothing of itself standing on the board."""
    _, server = admin
    games.perform(server, SetBoard(size_x=5, size_y=5))
    games.perform(server,
                  LoadPlayer(path=a_loaded_army(tmp_path, [(1, 1), (2, 2)])))
    assert len(loaded(server)) == 2

    games.perform(server, RemovePlayer(number=1))

    assert 1 not in server.getPlayers()
    assert server.getBoard().units == []


# --- both, replayed


def test_the_draft_replays_a_setup_that_was_changed(admin):
    """A session's uncommitted work is replayed the way it was done.

    Sizing twice and removing a seat are commands like any other, so what a
    session comes back to is what it left rather than what it first typed.
    """
    harness, server = admin
    games.perform(server, SetBoard(size_x=6, size_y=6))
    games.perform(server, AddPlayer(number=1))
    games.perform(server, AddPlayer(number=2))
    games.perform(server, RemovePlayer(number=1))
    games.perform(server, SetBoard(size_x=3, size_y=7))

    again = harness.session(0)

    assert sizes(again) == (3, 7)
    assert sorted(again.getPlayers()) == [2]
