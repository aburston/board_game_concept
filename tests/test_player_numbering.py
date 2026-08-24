"""Who the numbers in a game belong to.

The boundaries are what these assert - 0, 1, 999, 1000 - rather than the middle,
so that the numbers in `player-numbering` and the numbers in the code cannot be
changed apart from each other without something failing.
"""

import pytest

from board_game_concept.domain import Player
from board_game_concept.service import identity


# --- what a player's number may be


@pytest.mark.parametrize('number', [Player.FIRST, 2, 500, Player.LAST])
def test_a_player_may_have_a_number_in_range(number):
    assert Player(number).number == number
    assert identity.is_player(number)


@pytest.mark.parametrize('number', [-1, 0, 1000, 1001, 1000000])
def test_a_player_may_not_have_a_number_out_of_range(number):
    with pytest.raises(AssertionError):
        Player(number)
    assert not identity.is_player(number)


def test_the_range_is_the_one_the_spec_names():
    assert (Player.FIRST, Player.LAST) == (1, 999)


def test_a_player_number_must_still_be_a_whole_number():
    for number in ('1', 1.5, None):
        with pytest.raises(AssertionError):
            Player(number)
        assert not identity.is_player(number)


# --- the three identities


def test_the_reserved_numbers_are_the_ones_the_spec_names():
    assert identity.ADMINISTRATOR == 0
    assert identity.OBSERVER == 1000


def test_a_reserved_number_is_not_a_player():
    for number in identity.RESERVED:
        assert not identity.is_player(number)


def test_no_two_identities_are_the_same():
    assert identity.ADMINISTRATOR != identity.OBSERVER
    assert not identity.is_player(identity.ADMINISTRATOR)
    assert not identity.is_player(identity.OBSERVER)


@pytest.mark.parametrize('number', [-1, 1001, 1000000])
def test_a_number_outside_them_all_identifies_nobody(number):
    assert not identity.identifies_anyone(number)


@pytest.mark.parametrize('number', [0, 1, 999, 1000])
def test_every_number_the_game_uses_identifies_somebody(number):
    assert identity.identifies_anyone(number)


# --- what each identity is entitled to


def test_both_reserved_identities_see_the_whole_game():
    """The reason this is a question and not a comparison with zero."""
    assert identity.sees_everything(identity.ADMINISTRATOR)
    assert identity.sees_everything(identity.OBSERVER)


@pytest.mark.parametrize('number', [1, 500, 999])
def test_a_player_does_not_see_the_whole_game(number):
    assert not identity.sees_everything(number)


def test_only_the_observer_may_not_change_a_game():
    assert not identity.may_change(identity.OBSERVER)
    # the administrator sets a game up and commits it, so it may
    assert identity.may_change(identity.ADMINISTRATOR)
    for number in (1, 500, 999):
        assert identity.may_change(number)


def test_an_identity_says_what_it_is_called():
    assert identity.describe(0) == 'the administrator'
    assert identity.describe(1000) == 'the observer'
    assert identity.describe(7) == 'player 7'


def test_a_reserved_number_is_refused_as_reserved_and_not_as_out_of_range():
    """The two are different mistakes and deserve different messages."""
    assert 'reserved' in identity.out_of_range(0)
    assert 'reserved' in identity.out_of_range(1000)
    assert 'reserved' not in identity.out_of_range(1001)
    assert '999' in identity.out_of_range(1001)


# --- what the three identities see of each other


def test_the_observer_does_not_see_the_administrators_uncommitted_setup(
        tmp_path):
    """The leak that made the shared identity visible.

    An observer running as the administrator read the administrator's draft and
    held it as its own - so it saw setup nobody had published, and a session
    meant to write nothing was one recorded command away from writing into
    somebody else's draft.
    """
    from board_game_concept import Game, YamlGameRepository
    from board_game_concept.service import games
    from board_game_concept.service.commands import AddPlayer, SetBoard

    def session(number):
        game = Game(YamlGameRepository('watched', str(tmp_path)), number)
        game.load()
        return game

    admin = session(identity.ADMINISTRATOR)
    games.perform(admin, SetBoard(size_x=6, size_y=7))
    games.perform(admin, AddPlayer(number=1))

    observer = session(identity.OBSERVER)

    assert observer.getBoard() is None
    assert observer.getPlayers() == {}
    assert observer.getDraft() == []


def test_the_administrator_still_gets_its_own_setup_back(tmp_path):
    from board_game_concept import Game, YamlGameRepository
    from board_game_concept.service import games
    from board_game_concept.service.commands import SetBoard

    def session(number):
        game = Game(YamlGameRepository('watched', str(tmp_path)), number)
        game.load()
        return game

    games.perform(session(identity.ADMINISTRATOR),
                  SetBoard(size_x=6, size_y=7))
    reopened = session(identity.ADMINISTRATOR)

    assert (reopened.getSizeX(), reopened.getSizeY()) == (6, 7)


def test_both_reserved_identities_are_shown_the_whole_board(tmp_path):
    from game_harness import GameHarness

    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1, 2])
    harness.deploy(1, [('Cross', 'X', 1, 5, 10)], [('Cross', 'x1', 0, 0)])
    harness.deploy(2, [('Ring', 'O', 1, 5, 10)], [('Ring', 'o1', 3, 3)])
    harness.resolve()

    for number in (identity.ADMINISTRATOR, identity.OBSERVER):
        session = harness.session(number)
        assert sorted(unit.name for unit in session.getBoard().units) == [
            'o1', 'x1'], f'{identity.describe(number)} was shown the wrong board'


def test_a_session_is_not_refused_for_being_an_identity_that_holds_no_units(
        tmp_path):
    """Neither reserved identity is registered, so neither is looked for."""
    from game_harness import GameHarness

    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])

    for number in (identity.ADMINISTRATOR, identity.OBSERVER):
        harness.session(number)

    # a player number the game does not have is still refused
    from board_game_concept.service.errors import NoSuchPlayer
    with pytest.raises(NoSuchPlayer):
        harness.session(2)


def test_the_commit_barrier_never_waits_for_a_reserved_identity(tmp_path):
    from game_harness import GameHarness

    harness = GameHarness(tmp_path)
    harness.create(4, 4, [1])

    server = harness.session(identity.ADMINISTRATOR)
    assert sorted(server.getPlayers()) == [1]
    assert identity.ADMINISTRATOR not in server.getPlayers()
    assert identity.OBSERVER not in server.getPlayers()
