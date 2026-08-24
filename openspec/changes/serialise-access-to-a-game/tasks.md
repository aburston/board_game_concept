## 1. Replace a file rather than emptying it

Independent of the lock, and additive: nothing changes about who may write, only
what a reader can catch. The suite must be green at the end of the group with no
test edited.

- [ ] 1.1 Route every write in `YamlGameRepository` through a helper that writes
      to a temporary name in the same directory and renames it over the target
      (design.md — Decision 6). Same directory, so the rename is atomic. Verify
      a game written before this change still reads, and the files written are
      byte-identical to the ones written before it.
- [ ] 1.2 Verify what a write leaves behind is invisible to the three places
      that classify a game's files by name: `player_numbers()`,
      `committed_players()` and `clear_orders()`. A temporary beside
      `1.yaml`, `commit_1` and `1_units.yaml` must be read as none of them.
- [ ] 1.3 Verify a write that does not finish leaves the previous contents
      readable — drive the helper to fail part way and confirm the target still
      holds what it held and the game still opens.

## 2. Holding a game

- [ ] 2.1 Add `held(read=False)` to `GameRepository` as the operation a caller
      uses, and implement it in `YamlGameRepository` over an advisory lock on
      `<root>/.lock` (design.md — Decisions 1 and 2). Verify the lock file is in
      the game's root and is read as none of the game's own files.
- [ ] 2.2 Make it re-entrant within a repository and bounded rather than
      indefinite (design.md — Decision 5). Verify holding a game inside a hold
      of the same game does not deadlock, and that a hold which cannot be had
      is reported rather than waited on for ever.
- [ ] 2.3 Verify the sharing rules from two processes: two writers do not
      overlap, a reader waits for a writer, and two readers hold it together.
      Two processes rather than two threads, because an advisory lock is per
      open file description and threads would not prove it.
- [ ] 2.4 Verify a hold is released when its caller finishes, including when it
      finishes because of an error.
- [ ] 2.5 Verify that where the platform offers no lock the repository carries
      on unheld and says so, rather than claiming a game was held
      (design.md — Decision 7).

## 3. Holding it where it matters

- [ ] 3.1 Have `turn.resolve` and `turn.publish` hold the game for writing
      (design.md — Decision 3). Verify with the recorder shape
      `tests/test_turn_publication.py` uses that the whole of a resolution
      happens inside one hold, and that `tests/test_turn_publication.py` itself
      still passes — the publication order must survive being wrapped.
- [ ] 3.2 Have the shared reads in `Game.load` hold the game for reading, and
      leave the draft replay outside that hold (design.md — Decision 4). Verify
      a session still restores its own draft, and that loading does not deadlock
      against itself.
- [ ] 3.3 Verify neither `wait_for_all_commits` nor `wait_for_turn` holds the
      game: a player must be able to commit while the server is waiting for
      them, which is the whole game. This is the one that would break
      everything, so it gets a test that would hang without the fix rather than
      one that inspects code.
- [ ] 3.4 Verify a turn still resolves, a game is still played end to end, and
      resolution is unchanged: `tests/test_full_game.py`,
      `tests/test_determinism.py` and
      `tests/test_server_client_integration.py` pass unedited.

## 4. Finish

- [ ] 4.1 Update `MODULE_DESCRIPTION.md`'s account of storage to say a game can
      be held and that a write replaces rather than truncates. Verify every path
      it names exists.
- [ ] 4.2 Record in `SPEC_COVERAGE.md` that the race divergence 10 tolerated,
      and the exposure 27 left open, are now closed by holding a game rather
      than by tolerating the loss. Name the tests. Say plainly what advisory
      locking does not cover.
- [ ] 4.3 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does, and
      `pylint` against the configured `.pylintrc`. Verify the suite is green and
      lint reports no message kind in a file that it did not report before.
- [ ] 4.4 Run the full suite ten times over and verify it is green every time.
      This change adds waiting between processes, which is the kind of thing
      that is green once and wedged on the eleventh.
