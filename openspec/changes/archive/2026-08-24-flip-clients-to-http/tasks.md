## 1. `bgcserver` accepts `--server URL`

- [x] 1.1 Remove the "step 3" `sys.exit(2)` block from `bgcserver.py`.
      Construct the session via `make_session(args.game_number,
      player_number, server=args.server, backend=args.backend)`.
- [x] 1.2 Skip the unattended resolver loop in HTTP mode. After the
      interactive setup commit, if the session is an `HttpSession` the
      binary exits with code 0 (design.md — Decision 1).
- [x] 1.3 Gate the `dump_units(units_document(board))` print on
      `isinstance(data, LocalSession)`. HTTP mode does not print the
      raw units block after resolution.

## 2. Docs

- [x] 2.1 Add a "Run over HTTP" section to `README.md`: start
      `bgcapiserver`, `export BOARD_GAME_SERVER=http://127.0.0.1:8080`,
      run the roles as usual.
- [x] 2.2 Update `MODULE_DESCRIPTION.md`'s CLI section: the three
      roles honour `BOARD_GAME_SERVER`; HTTP mode is what a real
      deployment uses.

## 3. Test the flipped shape

- [x] 3.1 Add `tests/test_server_over_http.py` — an admin session
      driven against a Flask thread. Set the board, register a
      player, `load player` (or the direct commands), `commit`.
      Verify: the server exits after commit (return code 0); a fresh
      client can now connect and read the board over HTTP.
- [x] 3.2 Verify the local `test_cli_server_surface.py` still runs
      green: nothing about the local-mode flow changed.

## 4. Finish

- [x] 4.1 Run the full suite under both backends, `flake8`, `pylint`.
- [x] 4.2 Run the full suite three times over.
