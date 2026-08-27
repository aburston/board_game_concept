"""Where games and accounts are kept.

An installed command is run from wherever the operator happens to be. Left to
the working directory, `bgcapiserver` put a credentials database in whatever
directory it was started in - and a different, empty one tomorrow, each
handing out the default passwords again.

The working directory is still the default, so nothing a person already does
changes. `$BOARD_GAME_HOME` moves games and accounts together, because a
deployment that moved one and not the other would be worse than either.
"""

import os

import pytest

from board_game_concept.cli import session as session_module
from board_game_concept.cli.session import HOME_ENV, default_base_path
from board_game_concept.service import registry
from board_game_concept.storage.account_store import make_account_store
from board_game_concept.storage.sqlite_repository import SqliteGameRepository
from board_game_concept.storage.yaml_repository import YamlGameRepository


@pytest.fixture(name='home')
def _home(tmp_path, monkeypatch):
    monkeypatch.setenv(HOME_ENV, str(tmp_path))
    return str(tmp_path)


@pytest.fixture(name='no_home')
def _no_home(monkeypatch):
    monkeypatch.delenv(HOME_ENV, raising=False)


def test_the_working_directory_is_the_default(no_home):
    assert default_base_path() == os.getcwd()


def test_the_environment_moves_it(home):
    assert default_base_path() == home


def test_an_empty_setting_is_not_a_location(monkeypatch):
    """An exported-but-blank variable means "unset", not "the root"."""
    monkeypatch.setenv(HOME_ENV, '')
    assert default_base_path() == os.getcwd()


@pytest.mark.parametrize('backend', ['sqlite', 'yaml'])
def test_the_account_store_follows_it(home, backend):
    store = make_account_store(backend, None)
    assert store.base_path == home


@pytest.mark.parametrize('repository', [SqliteGameRepository,
                                        YamlGameRepository])
def test_a_game_repository_follows_it(home, repository):
    assert repository('1').root == os.path.join(home, 'games', '_1')


def test_the_registry_follows_it(home):
    assert registry.game_numbers() == []
    registry.create('1', 'sqlite', None)
    assert registry.game_numbers() == ['1']
    assert os.path.isdir(os.path.join(home, 'games', '_1'))


def test_games_and_accounts_move_together(home):
    """One setting, or the deployment is split between two places."""
    registry.create('1', 'sqlite', None)
    store = make_account_store('sqlite', None)
    store.ensure()

    assert os.path.isdir(os.path.join(home, 'games', '_1'))
    assert os.path.isfile(os.path.join(home, 'accounts.sqlite3'))
    assert os.path.commonpath([store.base_path,
                               SqliteGameRepository('1').root]) == home


def test_an_explicit_path_still_wins(home, tmp_path):
    """`--base-path` is what a caller names, and it beats the environment."""
    named = str(tmp_path / 'named')
    assert make_account_store('sqlite', named).base_path == named
    assert SqliteGameRepository('1', base_path=named).root.startswith(named)


def test_the_served_app_follows_it(home):
    from board_game_concept.http.app import create_app

    app = create_app(backend='sqlite')
    assert app.config['BASE_PATH'] == home
    assert os.path.isfile(os.path.join(home, 'accounts.sqlite3'))
