## 1. The dependency

- [ ] 1.1 Add `segno` to `dependencies` in `pyproject.toml`, with a comment
      beside it saying it draws the banner's QR code and is pure Python so a
      phone can install it; verify with `pip install -e '.[dev]'` in a fresh
      venv that it installs without a compiler and `python -c "import segno"`
      succeeds
- [ ] 1.2 Extend `tests/test_packaging.py` with a test that imports `segno`
      and says, in its docstring, that the banner needs it and a wheel
      without it starts and then fails at the first `--host 0.0.0.0`; verify
      it passes

## 2. Finding the address

- [ ] 2.1 In `src/board_game_concept/http/bgcapiserver.py`, add
      `reachable_address()`: open a UDP socket, `connect` it to a public
      IPv4 address on a high port, return `getsockname()[0]`, and return
      `None` on any `OSError`, closing the socket either way; comment that a
      UDP connect sends nothing and only picks a route, which is why it needs
      no permission and works under Termux. Verify by running it on this
      machine that it returns the machine's network address and not
      `127.0.0.1`
- [ ] 2.2 Add `WILDCARDS = ('0.0.0.0', '::', '')` beside it and a helper
      `addresses_to_announce(host)` that returns `[host]` for anything not in
      it, `[found]` when `reachable_address()` finds one, and `[]` when it
      does not; verify with a quick `python -c` that `127.0.0.1` and
      `192.168.1.23` come back unchanged and `0.0.0.0` comes back as the
      found address

## 3. The banner

- [ ] 3.1 Rewrite `_announce` to take its addresses from
      `addresses_to_announce(host)`: print one `http://<address>:<port>/`
      line per address; when the list is empty, print that the server is
      bound to every interface but it could not tell which address to give
      out, and that it can be read from the phone's Wi-Fi or hotspot
      settings, or from `ip addr` on a laptop. Keep the games-and-accounts
      lines and the sign-in hint as they are. Verify by starting with no
      flags that the banner still reads as the README shows it, and with
      `--host 0.0.0.0` that a network address is printed and `0.0.0.0` is
      not
- [ ] 3.2 Add `_qr(url)` that prints `segno.make(url).terminal(compact=True)`
      to stderr with a blank line above and below, and call it from
      `_announce` for the first address when that address is not loopback -
      preceded, when more than one address was printed, by a line saying
      which address the code is for. Verify by starting with `--host
      0.0.0.0` that a code appears beneath the address, and with no flags
      that none does
- [ ] 3.3 Update the docstring of `_announce` and the module docstring so
      they say the banner gives out an address another device can use and a
      code to scan, and why the code is on the terminal rather than the
      page; verify by reading them that nothing still says the banner prints
      the bound host verbatim

## 4. Tests

- [ ] 4.1 Add `tests/test_api_server_banner.py` with a fixture that builds
      an app against `tmp_path` via `create_app` and a helper that calls
      `_announce` and returns `capsys` stderr; test that with host
      `127.0.0.1` the output names `http://127.0.0.1:<port>/`, contains no
      block characters (`▀`, `▄`, `█`), and mentions `admin / admin`; verify
      it passes against the current banner (this case does not change)
- [ ] 4.2 In the same file, monkeypatch `reachable_address` to return
      `192.168.1.23` and test that with host `0.0.0.0` the output names
      `http://192.168.1.23:<port>/`, does not contain `0.0.0.0`, and contains
      block characters; and, in a second test with `_qr` monkeypatched to
      record its argument, that it was called exactly once with that same
      URL - which pins what was encoded without decoding the picture, and
      leaves reading it to 6.2. Verify both fail against the current banner
      and pass after 3.1 and 3.2
- [ ] 4.3 In the same file, monkeypatch `reachable_address` to return `None`
      and test that with host `0.0.0.0` the output says it could not tell
      which address to give out, names where to look, and contains no block
      characters; and that with host `192.168.1.23` the finder is never
      called (patch it to raise) and that address is printed with a code.
      Verify both pass after 3.1 and 3.2
- [ ] 4.4 Run `pytest tests/test_api_server_banner.py tests/test_packaging.py
      tests/test_base_path.py tests/test_local_api_guard.py` and then the
      full `pytest` under both `BOARD_GAME_BACKEND=yaml` and `sqlite`, and
      `pylint` as CI runs it; verify all green

## 5. Documentation

- [ ] 5.1 Add a `## Playing in the same room` section to `README.md` under
      "The web interface", between "Where it keeps things" and "Serving it
      properly", covering: `bgcapiserver --host 0.0.0.0`; what the banner
      then prints and that the code beneath it is the address to scan; that
      a guest opens it, taps "Register instead", signs in and takes a seat;
      that a home Wi-Fi is the trusted network the TLS note exempts, so
      plain HTTP is fine there and not beyond it; that `--host <address>`
      picks the address when the machine has several; and that a guest or
      public network often stops phones seeing each other, in which case
      the host's phone can be the hotspot and everyone joins that. Verify
      by reading it that each fact traces to something the code does
- [ ] 5.2 Add a `### Hosting from an Android phone` subsection under it:
      install Termux (from F-Droid, not the Play Store build, which is
      abandoned), `pkg install python git`, clone or copy the repository,
      `pip install .`, `export BOARD_GAME_HOME=~/board-games`, `bgcapiserver
      --host 0.0.0.0`; then what keeps it alive - `termux-wake-lock` (from
      the `termux-api` package or the Termux notification), and turning off
      battery optimisation for Termux in Android's settings - and that the
      game is lost mid-turn without them; that if the code wraps on a narrow
      terminal, turn the phone sideways; and that an iPhone cannot host this
      way and should join a laptop or Android host instead. Verify by
      following the steps on an Android phone, or, failing one to hand, by
      checking each command against Termux's package list
- [ ] 5.3 Reword the TLS entry under "Web service - what's next" to say
      that a home or club network is the trusted one and point at the new
      section, and update the `bgcapiserver.py` entry in
      `MODULE_DESCRIPTION.md` to mention the banner and the QR code; verify
      with `grep -n "0.0.0.0\|same room" README.md MODULE_DESCRIPTION.md`
      that both documents name the section and the flag

## 6. Verification

- [ ] 6.1 On a laptop on a home Wi-Fi, run `bgcapiserver --host 0.0.0.0`,
      scan the code with a phone's camera, and verify the page opens, a new
      account can be registered from it, and a seat taken; then verify
      from a second phone that the game plays a turn end to end
- [ ] 6.2 Verify the code scans from both a light and a dark terminal, and
      from a phone's Termux screen if one is to hand; if a scanner refuses
      the dark one, pass colours to `terminal()` and add the reason as a
      comment
- [ ] 6.3 Run `bgcapiserver` with no flags and verify that nothing about the
      loopback banner changed from what the README shows, and that a phone
      on the same network cannot reach it - the default is still local
