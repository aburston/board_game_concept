"""Pytest wiring shared by the suite.

The `backend` marker names which of the two storage backends a test is
about. A test that reaches into `data/*.yaml` files, reads
`repository.player_path`, or otherwise depends on the YAML file layout is
marked `@pytest.mark.backend('yaml')`; one that asserts on rows or on
`SqliteGameRepository` state is marked `@pytest.mark.backend('sqlite')`.
An unmarked test is meant to pass on either backend.

The active backend comes from the `BOARD_GAME_BACKEND` environment
variable (default: `yaml`, so `pytest` on its own runs the same suite it
always ran). A test whose marker names another backend is skipped for
this run.
"""

import os


BACKEND_ENV = 'BOARD_GAME_BACKEND'
ACTIVE_BACKEND = os.environ.get(BACKEND_ENV, 'yaml')


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        "backend(name): the storage backend this test is about "
        "('yaml' or 'sqlite'). An unmarked test runs on either backend.")


def pytest_collection_modifyitems(config, items):
    import pytest

    for item in items:
        marker = item.get_closest_marker('backend')
        if marker is None:
            continue
        pinned = marker.args[0] if marker.args else marker.kwargs.get('name')
        if pinned != ACTIVE_BACKEND:
            item.add_marker(pytest.mark.skip(
                reason=f"pinned to {pinned!r}; running under "
                       f"{ACTIVE_BACKEND!r}"))
