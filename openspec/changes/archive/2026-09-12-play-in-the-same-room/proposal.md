## Why

Everything needed to play with people in the same room already exists:
`bgcapiserver` takes `--host`, the page works from a phone, and a newcomer
can register from the sign-in screen. What is missing is the last yard - the
server, bound wide, announces itself as `http://0.0.0.0:45678/`, which is the
one address nobody can type, and the README never says that a home Wi-Fi is
the trusted network its TLS note exempts. A host who wants to run the game on
an Android phone and have friends join from theirs has to work all of this out
from the source, which the banner exists to make unnecessary.

## What Changes

- **The banner says where the server can actually be reached.** When
  `bgcapiserver` is bound to every interface, it prints the address or
  addresses another machine on the network can use, rather than the wildcard
  it was given. When it cannot tell, it says so and where to look.
- **The banner shows a QR code of that address**, drawn on the terminal, when
  the server is reachable from other machines - so a guest scans the host's
  screen instead of typing an IP. It is not shown when the server is bound to
  loopback only, where there is nothing another device could reach.
- **A "Playing in the same room" section in the README**: the one flag, what
  the banner then shows, how a guest joins, and how to host from an Android
  phone under Termux - including what stops the phone killing the server. It
  says plainly that a home network is the trusted network the TLS note
  already exempts, and names the guest-network trap (client isolation) and
  the way round it (the phone as the hotspot).
- One new dependency for the QR code, pure Python, so a phone can still
  `pip install` the package without a compiler.
- No change to the web interface, the contract, the CLI roles, the rules, or
  where anything is stored.

Assumptions recorded here rather than asked: the host is an Android phone or a
laptop and the network is usually a home Wi-Fi with a router, so the address
to show is the one the host uses to reach the world; an iPhone as host is out
of scope because nothing keeps a Python server alive in the background there.

## Capabilities

### New Capabilities

- `api-server`: the HTTP server as a process - what `bgcapiserver` binds when
  not told, what it says as it starts so that a person can reach it from
  another device, and when it offers that as a QR code. Nothing specs the
  server process today; `game-server` is the administrator role and
  `web-interface` is the page.

### Modified Capabilities

(none - the page, the contract and the roles are as they were)

## Impact

- `src/board_game_concept/http/bgcapiserver.py`: `_announce` gains the
  reachable addresses and the QR code; a small helper finds the addresses.
- `pyproject.toml`: one dependency added for the QR code.
- `README.md`: a new section under "The web interface", before "Serving it
  properly", and the "what's next" TLS entry reworded to point at it.
- `MODULE_DESCRIPTION.md`: the `bgcapiserver.py` entry mentions the banner.
- Tests: `_announce` has no test today. A new `tests/test_api_server_banner.py`
  holds the banner to the spec for the loopback and wildcard cases without
  binding a port.
- Not affected: `http/app.py`, the static page, `cli/`, the storage
  backends, saved games, the account store, and every existing test.
