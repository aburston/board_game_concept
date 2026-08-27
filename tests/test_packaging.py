"""What an install has to carry beside the code.

`accounts.sql` was added to `storage/` and `pyproject.toml` was not updated,
so `pip install .` produced a package with no schema to apply: the account
store was created with no tables and every request to a served game failed.
An editable install could not show it, because the file was still there in
the source tree.

These hold the declaration to the directory rather than to a remembered list.
"""

import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = os.path.join(ROOT, 'src', 'board_game_concept')
PYPROJECT = os.path.join(ROOT, 'pyproject.toml')

# what counts as a file the code needs at runtime rather than source
DATA_SUFFIXES = ('.sql',)


def _data_files():
    """Every runtime data file under the package, as (package, filename)."""
    found = []
    for directory, _subdirs, files in os.walk(PACKAGE):
        for name in files:
            if not name.endswith(DATA_SUFFIXES):
                continue
            relative = os.path.relpath(directory, os.path.dirname(PACKAGE))
            found.append((relative.replace(os.sep, '.'), name))
    return found


def _declared():
    """The package-data globs `pyproject.toml` declares, by package."""
    with open(PYPROJECT, encoding='utf-8') as file:
        text = file.read()
    section = re.search(
        r'\[tool\.setuptools\.package-data\](.*?)(?=\n\[|\Z)', text, re.S)
    assert section, 'pyproject.toml declares no package-data'
    declared = {}
    for package, globs in re.findall(
            r'"([\w.]+)"\s*=\s*\[([^\]]*)\]', section.group(1)):
        declared[package] = re.findall(r'"([^"]+)"', globs)
    return declared


def _matches(name, patterns):
    import fnmatch
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def test_there_is_at_least_one_data_file_to_check():
    """Otherwise the tests below would pass by having nothing to say."""
    assert _data_files()


@pytest.mark.parametrize('package,name', _data_files())
def test_every_data_file_is_declared_for_packaging(package, name):
    """A file the code opens at runtime has to be in the wheel.

    Held to the directory rather than to a list, so adding a second `.sql`
    cannot repeat the mistake that made `accounts.sql` absent.
    """
    declared = _declared()
    assert package in declared, (
        f'{package} has data files ({name}) and no package-data entry')
    assert _matches(name, declared[package]), (
        f'{name} is not matched by {declared[package]} for {package}')


def test_every_data_file_the_storage_modules_open_exists():
    """The paths `_schema_path()` and its like build must resolve.

    In a source tree this is trivially true; run against an installed
    package it is what says the wheel carried them.
    """
    from board_game_concept.storage import sqlite_account_store
    from board_game_concept.storage import sqlite_repository

    for module in (sqlite_account_store, sqlite_repository):
        path = module._schema_path()
        assert os.path.isfile(path), f'{module.__name__}: {path} is missing'


def test_the_schema_files_are_applicable():
    """A packaged schema that will not run is no better than a missing one."""
    import sqlite3
    from board_game_concept.storage import sqlite_account_store
    from board_game_concept.storage import sqlite_repository

    for module in (sqlite_account_store, sqlite_repository):
        with open(module._schema_path(), encoding='utf-8') as file:
            sql = file.read()
        connection = sqlite3.connect(':memory:')
        connection.executescript(sql)
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        assert tables, f'{module.__name__}: schema created no tables'
