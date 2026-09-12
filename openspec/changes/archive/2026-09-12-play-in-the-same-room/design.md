## Context

See proposal.md - Why. The server's start-up is one function, `main` in
`http/bgcapiserver.py`: parse `--host` (default `127.0.0.1`), `--port`,
`--base-path`, `--backend`; build the app; call `_announce`; call `app.run`.
`_announce` prints `http://{host}:{port}/` with whatever `--host` was given,
so `--host 0.0.0.0` prints `http://0.0.0.0:45678/`. Nothing tests
`_announce` today.

`app.run` is Flask's development server, threaded, and only this entry point
runs it - a deployment under gunicorn imports `create_app` and never sees the
banner. So everything here is for the laptop, club and phone case the README
already says the dev server is for.

The page needs nothing: every request in `static/api.js` is a relative path
with same-origin credentials, the session cookie is `HttpOnly` and
`SameSite=Lax` without `Secure`, so it works over plain HTTP on a network,
and the stylesheet already has `pointer: coarse` and narrow-width rules. A
guest registers from the sign-in screen's "Register instead" and takes a seat
from the lobby. The three dependencies are Flask, requests and PyYAML; the
first two are pure-Python wheels and PyYAML falls back to pure Python without
libyaml, so the package installs on Termux without a compiler.

The web-interface spec forbids the page any route not equally available to
other clients, which shapes where the QR code can live.

## Goals / Non-Goals

**Goals:**

- A host who types `bgcapiserver --host 0.0.0.0` on a laptop or an Android
  phone sees an address to read out and a code to scan, and nothing else
  about the flow changes.
- Discovery of the address needs no new permission, no shelling out, and no
  compiled dependency, so it works under Termux as well as on a laptop.
- A test that holds the banner to the spec without binding a port.

**Non-Goals:**

- Discovering the address on a machine with no route out (a phone that is
  the hotspot and has no upstream). The banner says it could not tell and
  where to look; the README says what to do.
- A QR code on the web page. See the decision below.
- mDNS names (`myphone.local`), TLS, gunicorn, or any change to which
  addresses the server binds by default.
- iPhone as host.

## Decisions

**The QR code is drawn on the terminal, not on the page.** The host is
looking at the terminal the moment after typing the command; that screen is
what guests scan, on a laptop or a phone alike. The alternative - a code on
the administrator's lobby - was rejected for three reasons: the page does not
know the server's network address any better than the banner does, so it
would need a route for it; that route would be a contract addition to a page
the spec holds to the contract, for one screen's benefit; and drawing a QR
in the browser means vendoring a JavaScript encoder into `static/`, which the
README's "no build step and no package manager" rule tolerates but does not
welcome. On the terminal the code costs one pure-Python dependency.

**`segno` encodes the QR.** Pure Python, no dependencies of its own, and
`make(url).terminal(compact=True)` draws with half-block characters, which
halves the height - a `http://192.168.1.23:45678/` code is a 25-module
version 2 and prints in about fifteen lines, small enough for a phone's
terminal. `qrcode` was considered and works the same way (`print_ascii`), but
pulls in `colorama` on Windows and its terminal output is an afterthought of
an image library. Hand-rolling an encoder was rejected: Reed-Solomon is a few
hundred lines to get wrong.

**The reachable address is the one the host uses to reach the world.** Bound
to the wildcard, `_announce` opens a UDP socket, `connect`s it to a public
address, and reads its own address back with `getsockname`. No packet is
sent - a UDP connect only picks a route - so it needs no reachability and no
permission, and it works on Termux, where there is no `ifconfig` by default
and `/proc/net` is closed to apps. It gives one address: the interface with
the default route, which on a home Wi-Fi is the one a guest is on. When the
connect fails (no default route), the banner says it could not tell and
points at the phone's Wi-Fi or hotspot settings, or `ip addr` on a laptop.

Alternatives: `socket.getaddrinfo(gethostname())` returns `127.0.0.1` on
Termux and on many laptops; `psutil` and `netifaces` list every interface
but are compiled; parsing `ip addr` or `ifconfig` output is per-platform and
the commands are absent on a fresh Termux; netlink from Python is possible
and far too clever for a banner. The proposal's "address or addresses" is
kept in the spec because a later, better finder may return several; this
one returns one.

**A named non-loopback address is printed as given.** `--host 192.168.1.23`
already says what to print; discovery is only for the wildcard. `--host ::`
and other IPv6 wildcards are treated like `0.0.0.0` for the purpose of "look
for an address", and the finder looks for IPv4 first because that is what a
guest can type.

**The QR encodes exactly the printed address, scheme and port and all.** A
phone camera opens `http://…` as a link; a bare `192.168.1.23:45678` is
offered as text to copy. The trailing slash matches what is printed.

**The README section sits under "The web interface", before "Serving it
properly".** It is the step between "start it" and "serve it properly", and
a reader who wants only to play with friends stops before gunicorn and TLS.
The "what's next" entry on TLS keeps its point and gains a pointer back: a
home network is the trusted one it exempts.

**The test drives `_announce` directly, not `main`.** `main` binds a port.
`_announce` takes the app, base path, host and port and prints; the test
calls it with `127.0.0.1` and asserts no code and the loopback URL, then
with `0.0.0.0` and a monkeypatched finder returning a fixed address and
asserts that address in the output, the wildcard absent, and the QR's block
characters present. The finder is a separate function so it can be replaced,
and a third test patches it to return nothing and asserts the "could not
tell" text. Nothing here opens a socket in CI.

## Risks / Trade-offs

- [The UDP trick returns a VPN or wired address on a laptop with several
  routes] → It is the address with the default route, which is the right one
  more often than not; when it is wrong the operator has `--host <address>`,
  and the README says so.
- [A dark terminal draws the code light-on-dark] → `segno` draws a quiet
  zone in the same inverted sense, and phone scanners read inverted codes;
  the manual verification task checks both a light and a dark terminal. If a
  scanner will not, `terminal()` takes colours.
- [A small phone terminal wraps the code] → `compact=True` is 25 characters
  wide for a version 2 code, under any terminal's width; a longer address
  (a named `--host` with a hostname) grows the code, and wrapping breaks it.
  The README says to turn the phone sideways if it wraps.
- [Android suspends Termux when the screen is off] → Documentation, not
  code: `termux-wake-lock`, and turning off battery optimisation for Termux.
  The section says so, because a host who does not know loses the game at
  the first dark screen.
- [Guest or public Wi-Fi isolates clients and no phone can reach another]
  → Documentation: the section names it and says the host's phone can be the
  hotspot instead, with everyone joining that.
- [A second dependency to keep installable on a phone] → `segno` is pure
  Python with no dependencies; `tests/test_packaging.py` already checks what
  an install carries and a task extends it to import `segno`.
