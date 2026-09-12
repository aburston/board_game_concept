"""What `bgcapiserver` says as it starts.

The banner exists so that a person who has just installed this does not have
to read the source to find out where the server is. Bound to `0.0.0.0` it
used to print `http://0.0.0.0:45678/`, which is the one address nobody can
type - so a host who wanted friends to join from their phones had to read
the source after all. Now it prints the address another device can reach,
and draws it as a QR code to scan.

These drive `_announce` directly rather than `main`, because `main` binds a
port. The address finder is monkeypatched, so nothing here opens a socket
and the result does not depend on the network the tests run on.
"""

import pytest

from board_game_concept.http import bgcapiserver
from board_game_concept.http.app import create_app


PORT = 45678
NETWORK_ADDRESS = '192.168.1.23'

# what `segno` draws a code with. The banner has no other reason to print
# any of these, so their presence is the code and their absence is its
# absence
BLOCKS = ('▀', '▄', '█')


@pytest.fixture(name='app')
def _app(tmp_path):
    return create_app(base_path=str(tmp_path), backend='sqlite')


@pytest.fixture(name='announce')
def _announce(app, tmp_path, capsys):
    def announce(host):
        bgcapiserver._announce(app, str(tmp_path), host, PORT)
        return capsys.readouterr().err
    return announce


def _has_code(text):
    return any(block in text for block in BLOCKS)


def test_bound_to_loopback_the_banner_names_loopback_and_draws_no_code(
        announce, monkeypatch):
    """The case that does not change: local by default, and nothing to scan.

    The finder is patched to raise so that a loopback bind provably never
    goes looking for a network address - there is nothing to find for it.
    """
    monkeypatch.setattr(bgcapiserver, 'reachable_address',
                        lambda: pytest.fail('looked for an address'))

    text = announce('127.0.0.1')

    assert f'http://127.0.0.1:{PORT}/' in text
    assert 'admin / admin' in text
    assert not _has_code(text)


def test_bound_to_the_wildcard_the_banner_names_the_network_address(
        announce, monkeypatch):
    """`0.0.0.0` is what was bound; the network address is what is printed."""
    monkeypatch.setattr(bgcapiserver, 'reachable_address',
                        lambda: NETWORK_ADDRESS)

    text = announce('0.0.0.0')

    assert f'http://{NETWORK_ADDRESS}:{PORT}/' in text
    assert '0.0.0.0' not in text
    assert _has_code(text)


def test_the_code_encodes_the_address_that_was_printed(announce, monkeypatch):
    """What the picture says, pinned without reading the picture.

    Decoding the drawn code is a camera's job (and a manual verification
    task); this holds the encoder to having been given the printed URL,
    scheme and port and all, exactly once.
    """
    monkeypatch.setattr(bgcapiserver, 'reachable_address',
                        lambda: NETWORK_ADDRESS)
    encoded = []
    monkeypatch.setattr(bgcapiserver, '_qr', encoded.append)

    announce('0.0.0.0')

    assert encoded == [f'http://{NETWORK_ADDRESS}:{PORT}/']


def test_when_no_address_can_be_found_the_banner_says_so_and_where_to_look(
        announce, monkeypatch):
    """No route out - a hotspot with no upstream, say.

    Printing the wildcard would be wrong and printing nothing would be
    worse; the banner says it could not tell, and where the operator can.
    """
    monkeypatch.setattr(bgcapiserver, 'reachable_address', lambda: None)

    text = announce('0.0.0.0')

    assert 'could not tell which address' in text
    assert 'settings' in text and 'ip addr' in text
    assert f'http://0.0.0.0:{PORT}/' not in text
    assert not _has_code(text)


def test_a_named_address_is_printed_as_given_with_a_code(
        announce, monkeypatch):
    """The operator chose the address; the banner does not second-guess it."""
    monkeypatch.setattr(bgcapiserver, 'reachable_address',
                        lambda: pytest.fail('looked for an address'))

    text = announce(NETWORK_ADDRESS)

    assert f'http://{NETWORK_ADDRESS}:{PORT}/' in text
    assert _has_code(text)


def test_the_finder_returns_an_address_or_nothing():
    """The one test that touches the network, held only to its contract.

    Whatever machine this runs on, the finder either names an IPv4 address
    that is not loopback or admits it could not - it never raises, and it
    never answers `127.0.0.1`, which a guest could not use.
    """
    found = bgcapiserver.reachable_address()

    assert found is None or (
        found.count('.') == 3 and found not in bgcapiserver.LOOPBACK)
