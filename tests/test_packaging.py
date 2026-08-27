"""What an install has to carry beside the code.

`accounts.sql` was added to `storage/` and `pyproject.toml` was not updated,
so `pip install .` produced a package with no schema to apply: the account
store was created with no tables and every request to a served game failed.
An editable install could not show it, because the file was still there in
the source tree.

It happened again one directory over: `http/static/` was written and not
declared, so an installed server started, said where it had put your games,
and answered the front page with a 500 - and answered every other address
with one too, because the handler for an unknown address serves the same
missing file. So the suffixes below are every kind of file the code opens
at runtime, not only the schemas.

These hold the declaration to the directory rather than to a remembered list.
"""

import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = os.path.join(ROOT, 'src', 'board_game_concept')
PYPROJECT = os.path.join(ROOT, 'pyproject.toml')

# what counts as a file the code needs at runtime rather than source:
# the schemas, and the web interface, which is served as it was written
DATA_SUFFIXES = ('.sql', '.html', '.js', '.css')


def _owning_package(directory):
    """The package a file in `directory` is packaged with, and the way in.

    `static/` holds no `__init__.py`, so it is not a package of its own and
    setuptools carries its files as data of the package above it. Walk up to
    the nearest directory that is a package, and the rest of the path is what
    the glob has to match.
    """
    parts = []
    while not os.path.isfile(os.path.join(directory, '__init__.py')):
        directory, tail = os.path.split(directory)
        parts.insert(0, tail)
    package = os.path.relpath(directory, os.path.dirname(PACKAGE))
    return package.replace(os.sep, '.'), parts


def _data_files():
    """Every runtime data file under the package, as (package, name).

    `name` is the path the package's own globs are matched against, so a
    file in a subdirectory arrives as `static/app.js` rather than `app.js`.
    """
    found = []
    for directory, _subdirs, files in os.walk(PACKAGE):
        if '__pycache__' in directory.split(os.sep):
            continue
        package, prefix = _owning_package(directory)
        for name in files:
            if not name.endswith(DATA_SUFFIXES):
                continue
            found.append((package, '/'.join(prefix + [name])))
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


def test_the_web_interface_files_are_present_where_the_app_serves_them():
    """The front page has to be beside the code that sends it.

    In a source tree this is trivially true; run against an installed
    package it is what says the wheel carried the interface, rather than
    leaving `bgcapiserver` to answer every address with a 500.
    """
    from board_game_concept.http import app as app_module

    static = os.path.join(os.path.dirname(app_module.__file__), 'static')
    assert os.path.isfile(os.path.join(static, 'index.html')), (
        f'no index.html in {static}: the page cannot be served')

    with open(os.path.join(static, 'index.html'), encoding='utf-8') as file:
        page = file.read()
    for reference in re.findall(r'"/static/([\w./]+)"', page):
        assert os.path.isfile(os.path.join(static, reference)), (
            f'index.html asks for {reference} and the install has not got it')
