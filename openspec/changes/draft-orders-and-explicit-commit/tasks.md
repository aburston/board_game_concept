## 1. Draft storage

Nothing reads a draft yet. The whole group is additive, and the suite must be
green at the end of it with no test edited.

- [x] 1.1 Add a kind-to-class lookup in `service/commands.py` so a command can
      be rebuilt from its kind and fields, and command serialisation in
      `storage/serialise.py` alongside the existing writers (design.md —
      Decision 1). Verify with a round-trip test that every production in
      `grammar.USAGES` survives being written and read back as the command it
      parsed to, compared with the `__eq__` `Node` already has.
- [x] 1.2 Add `read_draft`, `write_draft` and `clear_draft` to
      `GameRepository`, and implement them in `YamlGameRepository` over
      `players/<number>_draft.yaml`, recording the turn the draft was made for
      (design.md — Decision 5). Verify in `tests/test_repository.py` that a
      draft round-trips, that an absent draft reads as empty rather than as an
      error, and that clearing one twice is not an error.
- [x] 1.3 Verify the new file is invisible to the two places that classify
      files by name: `player_numbers()` must not read `1_draft.yaml` as a
      player, and `committed_players()` must not count it as published orders.
      Add both as explicit tests — this is the class of mistake that produced
      divergence 10 in `SPEC_COVERAGE.md`.

## 2. Recording

- [x] 2.1 Add `games.perform(data, command)`: carry the command out through the
      existing function for its kind, and append it to the draft only if that
      does not raise (design.md — Decision 2). The individual functions stay
      public and stay unrecording, because replay calls them. Verify a refused
      command leaves the draft as it was.
- [x] 2.2 Route `cli/bgcclient.py` and `cli/bgcserver.py` through `perform`,
      replacing the two hand-rolled `if command.kind == ...` ladders. Verify
      `tests/test_cli_client_surface.py` and `tests/test_cli_server_surface.py`
      pass with no edit, and that a session which types a type, a deployment
      and a move leaves all three in its draft file in that order.
- [x] 2.3 Verify no write command reaches a service function except through
      `perform`, so drafting cannot be forgotten by a future caller. A test that
      drives every write production in `grammar.USAGES` through a session and
      asserts the draft holds it is the check that survives refactoring.

## 3. Replay

The step that changes observable behaviour, and the one to review hardest.

- [x] 3.1 Replay the loading session's own draft at the end of `Game.load()`,
      after `_load_players` has set the setup gate the deployment and movement
      rules read (design.md — Decision 3). Verify that a draft of several
      deployments produces the same board as typing them in the same order —
      `deploy_unit` calls `board.commit()` per unit, so replay must not
      short-circuit it — and that a game with no draft loads byte-identically
      to before.
- [x] 3.2 Read only the draft belonging to the loading session, never another's
      (design.md — Decision 6). Verify an administrator's and an observer's
      session opened against a game where a player holds a draft show nothing
      of it in `show units`, `show board` or `show pending`, and that `show
      pending` still lists committed orders as it does today.
- [x] 3.3 Discard a draft whose recorded turn is not the game's current turn,
      rather than applying it. Verify a draft left from an earlier turn is
      dropped and the game opens with the published view alone.
- [x] 3.4 Drop a drafted command that can no longer be carried out, report it to
      its owner, and continue with the rest of the draft. Verify a draft holding
      one now-illegal command and two legal ones opens the game with the two
      applied, and that no draft can prevent a game from being opened.
- [x] 3.5 Clear the draft when its owner commits, the work having become their
      published orders (design.md — Decision 4). Verify the file written to
      `players/<number>_units.yaml` is unchanged from before this change for the
      same sequence of commands, and that reopening after a commit restores
      nothing.

## 4. The commit record

Independent of groups 1–3 (design.md — Decision 7). Implementing it showed the
claim that it was cuttable to be wrong: see design.md — Decision 7a. A recorded
commit has to be spent when its turn resolves, or a turn that advances nothing
resolves itself for ever, and `load player` turned out to depend on writing an
order file being what committing meant.

- [x] 4.1 Give `players/commit_<number>` a body recording the turn committed
      for, and have `committed_players()` read the markers and return those
      whose turn is the one now open, instead of listing order files. Verify
      the commit barrier still holds a turn open for a player who has not
      committed, still does not wait for an eliminated one, and that a player
      whose last commit was for an earlier turn is not counted.
- [x] 4.2 Verify `has_committed` still answers "has ever committed" from the
      same marker, so the setup gate that reads it is unchanged, and that a game
      created before this change — whose marker file is empty — still opens and
      resolves.

## 5. The behaviour this change exists for

- [x] 5.1 Add a test to `tests/test_server_client_integration.py` that kills a
      client mid-setup and runs it again for the same game. Verify the types it
      defined and the units it deployed are restored, and that it can commit
      from there and have the server resolve the turn.
- [x] 5.2 Add the same for a client killed mid-turn holding a move order.
      Verify the order is restored and listed against the unit, and that
      changing it before committing leaves only the later order in the turn.
- [x] 5.3 Add the same for the administrator killed during setup after sizing a
      board and registering players. Verify both are restored and setup can be
      committed from there.
- [x] 5.4 Verify a player who has drafted and not committed does not hold the
      turn open as though they had, and is still waited for: the barrier counts
      commits, and a draft is not one.

## 6. Finish

- [ ] 6.1 Update `MODULE_DESCRIPTION.md` to describe drafting as part of what
      `service/` and `storage/` hold. Verify every path it names exists.
- [ ] 6.2 Mark `ARCHITECTURE_OPTIONS.md` as predating the layer split, naming
      which of its steps have since landed, so it is read as the history it is
      rather than as a plan. Verify no step it lists as pending is one the code
      already has.
- [ ] 6.3 Record in `SPEC_COVERAGE.md` that a session's uncommitted work used to
      be lost when the session ended, in the style of the existing entries, and
      name the test that now holds it. Verify every entry listed has a test.
- [ ] 6.4 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does, and
      `pylint` against the configured `.pylintrc`. Verify the suite is green and
      lint reports nothing that was not already reported before the change.
