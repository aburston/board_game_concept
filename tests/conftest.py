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


# --- authenticating against the HTTP tier
#
# Every suite that drives the served game needs an account now, so the
# machinery for making one lives here rather than in each of them. The point
# is that a suite changes by asking for a fixture, not by being rewritten.

import pytest  # noqa: E402


ADMIN_PASSWORD = 'admin-secret'
OBSERVER_PASSWORD = 'observer-secret'
PLAYER_PASSWORD = 'player-secret'


def _store_of(app):
    """A store for the test's own thread.

    The app builds one per request for thread-safety, so a test that reaches
    round the outside builds its own the same way rather than borrowing a
    connection that belongs to a request.
    """
    return app.config['ACCOUNT_STORE_FACTORY']()


def make_admin(app, password=ADMIN_PASSWORD):
    """The administrator, with its password changed so it may act.

    A store creates `admin` needing a change, and an account needing one may
    do nothing but change it - so every suite that acts as the administrator
    has to get past that first.
    """
    from board_game_concept.service import accounts

    store = _store_of(app)
    administrator = store.read_account_by_name('admin')
    if administrator.must_change:
        accounts.change_password(store, administrator, 'admin', password)
    return store.read_account_by_name('admin')


def make_observer(app, password=OBSERVER_PASSWORD):
    """The observer, with its password changed so it may act."""
    from board_game_concept.service import accounts

    store = _store_of(app)
    observer = store.read_account_by_name('observer')
    if observer.must_change:
        accounts.change_password(store, observer, 'observer', password)
    return store.read_account_by_name('observer')


def make_player(app, username, password=PLAYER_PASSWORD):
    """A registered account, or the one already registered under that name."""
    from board_game_concept.service import accounts

    store = _store_of(app)
    existing = store.read_account_by_name(username)
    if existing is not None:
        return existing
    return accounts.register(store, username, password)


def token_for(app, account, label=None):
    """A token identifying this account."""
    from board_game_concept.service import accounts

    return accounts.mint_token(_store_of(app), account, label=label)


def authorise(app, gameno, number, username=None):
    """Bearer headers for an account entitled to act as this number.

    0 is the administrator and 1000 the observer, each with its password
    changed; anything else is a registered account holding that seat. The
    seat is claimed directly through the store rather than through
    `service.accounts.claim_seat`, so that a suite can set up a game that has
    already started - which claiming would rightly refuse.
    """
    from board_game_concept.service import identity

    if number == identity.ADMINISTRATOR:
        account = make_admin(app)
    elif number == identity.OBSERVER:
        account = make_observer(app)
    else:
        account = make_player(app, username or f'player{number}')
        store = _store_of(app)
        if store.read_membership(str(gameno), number) is None:
            store.claim_seat(str(gameno), number, account.account_id)
    return {'Authorization': f'Bearer {token_for(app, account)}'}


@pytest.fixture(name='authorise')
def _authorise():
    """`authorise(app, gameno, number)` -> headers proving that identity."""
    return authorise


@pytest.fixture(name='make_token')
def _make_token():
    """`make_token(app, gameno, number)` -> a bare token for a subprocess.

    What the end-to-end suites need: they run a role as a subprocess with
    `BOARD_GAME_TOKEN` in its environment rather than making requests
    themselves.
    """
    def make(app, gameno, number, username=None):
        headers = authorise(app, gameno, number, username=username)
        return headers['Authorization'].split(' ', 1)[1]
    return make


class _AuthorisingClient:
    """A test client that proves whatever identity the path names.

    The number a request is for is already in the path - which is the whole
    reason the guard checks it rather than looking it up - so a client can
    read it back out and present a credential for it. That keeps a suite
    about the game about the game: it makes the same calls it always made,
    and the entitlement it needs is arranged around it.

    Whether the guard actually refuses is not this client's business and is
    not tested through it. `test_http_auth.py` drives the raw client for
    that, and each suite that uses this one keeps a case proving its own
    surface is guarded.
    """

    _PATH = None  # set below, once `re` is imported

    def __init__(self, app):
        self._app = app
        self._client = app.test_client()

    def _headers_for(self, path, given):
        import re

        headers = dict(given or {})
        if 'Authorization' in headers:
            return headers
        match = re.match(r'/games/([^/]+)/players/(\d+)(/|$)', path)
        if match is None:
            # a route that names no number still needs an account; the
            # administrator is the identity entitled to every game
            match_game = re.match(r'/games/([^/]+)', path)
            if match_game is None:
                return headers
            headers.update(authorise(self._app, match_game.group(1), 0))
            return headers
        gameno, number = match.group(1), int(match.group(2))
        headers.update(authorise(self._app, gameno, number))
        return headers

    def _call(self, method, path, **kwargs):
        kwargs['headers'] = self._headers_for(path, kwargs.get('headers'))
        return getattr(self._client, method)(path, **kwargs)

    def get(self, path, **kwargs):
        return self._call('get', path, **kwargs)

    def post(self, path, **kwargs):
        return self._call('post', path, **kwargs)

    def delete(self, path, **kwargs):
        return self._call('delete', path, **kwargs)

    def put(self, path, **kwargs):
        return self._call('put', path, **kwargs)

    @property
    def raw(self):
        """The unauthenticated client, for testing that the guard refuses."""
        return self._client

    @property
    def app(self):
        return self._app


def authorising_client(app):
    """A test client that carries the entitlement each path calls for."""
    return _AuthorisingClient(app)


@pytest.fixture(name='authorising_client')
def _authorising_client():
    return authorising_client


def make_token_for(app, gameno, number, username=None):
    """A bare token proving this identity, for a subprocess or a session.

    The same arrangement `authorise` makes, handed back as the token string
    rather than as a header - which is what a role reads from
    `BOARD_GAME_TOKEN`, and what `HttpSession` takes directly.
    """
    return authorise(app, gameno, number,
                     username=username)['Authorization'].split(' ', 1)[1]
