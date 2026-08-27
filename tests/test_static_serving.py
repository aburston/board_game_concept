"""The page and its modules, served as plain files.

No build step and no package manager: everything under `http/static/` is a
file that is served as it was written.
"""

import os
import re

import pytest

from board_game_concept.http.app import create_app


STATIC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'src', 'board_game_concept', 'http', 'static')

MODULES = ['app.js', 'api.js', 'board.js', 'lobby.js', 'armoury.js', 'play.js']


@pytest.fixture(name='client')
def _client(tmp_path):
    return create_app(base_path=str(tmp_path), backend='sqlite').test_client()


def test_the_page_is_served_without_a_credential(client):
    """It is what a person signs in through, so it cannot need one."""
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers['Content-Type']
    assert b'<title>Board Game Concept</title>' in response.data


def test_the_page_holds_no_game_state(client):
    """Everything it draws it fetches through the guarded contract."""
    body = client.get('/').data.decode()
    for leaked in ('units', 'password_hash', 'seats', 'board.rows'):
        assert leaked not in body


@pytest.mark.parametrize('name', MODULES)
def test_each_module_is_served_as_javascript(client, name):
    response = client.get(f'/static/{name}')
    assert response.status_code == 200
    assert 'javascript' in response.headers['Content-Type']


def test_the_stylesheet_is_served(client):
    response = client.get('/static/style.css')
    assert response.status_code == 200
    assert 'text/css' in response.headers['Content-Type']


@pytest.mark.parametrize('path', [
    '/static/../app.py',
    '/static/%2e%2e/app.py',
    '/static/../../../etc/passwd',
    '/static/nothing-here.js',
])
def test_a_path_outside_the_static_directory_is_refused(client, path):
    assert client.get(path).status_code == 404


def test_there_is_no_build_step(client):
    """Nothing under `static/` is generated, and nothing needs installing."""
    names = set(os.listdir(STATIC))
    for artefact in ('node_modules', 'package.json', 'package-lock.json',
                     'dist', 'build', '.cache'):
        assert artefact not in names
    assert names == set(MODULES) | {'index.html', 'style.css'}


def test_every_module_the_page_imports_exists(client):
    """A missing sibling is a blank page, and nothing else would catch it."""
    for name in MODULES + ['index.html']:
        with open(os.path.join(STATIC, name), encoding='utf-8') as file:
            source = file.read()
        for imported in re.findall(r"""from\s+'\./([\w.]+)'""", source):
            assert client.get(f'/static/{imported}').status_code == 200, (
                f'{name} imports {imported}')
        for src in re.findall(r'src="(/static/[\w./]+)"', source):
            assert client.get(src).status_code == 200, f'{name} loads {src}'


def test_the_page_loads_its_entry_module(client):
    body = client.get('/').data.decode()
    assert 'type="module"' in body
    assert '/static/app.js' in body
