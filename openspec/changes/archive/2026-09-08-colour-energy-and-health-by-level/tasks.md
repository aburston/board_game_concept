## 1. The bands

- [x] 1.1 Add `band(share)` to `http/static/board.js`, returning `'full'`
  above two thirds, `'low'` above a third, and `'spent'` at a third or below,
  with a comment saying a boundary belongs to the worse band; verify with a
  test that runs the shipped function under `node` over the boundaries
  themselves — 1, 2/3, just under 2/3, 1/3, just under 1/3 and 0.
- [x] 1.2 Add `--level-full`, `--level-low` and `--level-spent` to
  `http/static/style.css`, on `:root` and again in the
  `prefers-color-scheme: dark` block beside the tokens already there; verify
  with a test asserting all three are defined in both schemes.

## 2. The energy arc

- [x] 2.1 Draw the arc at `RING + 3` instead of `RING`, and set its
  `stroke-width` to 3 in the stylesheet, so it occupies 12.5 to 15.5 from the
  centre — clear of the ring's outer edge at 12 and of the health bar's lower
  edge at `y = 6`; verify with a test asserting the radius expression and the
  width, and that the arithmetic leaves the arc inside its square.
- [x] 2.2 Give the arc its class from `band(share)` rather than from
  `share <= 0.25`, and replace the `.energy` colour rules — the owner-coloured
  `.mine` / `.theirs` pair and `.spent` — with the three band rules using the
  new tokens; verify with a test asserting no `.energy` rule mentions `--mine`
  or `--theirs` and that each band rule exists.
- [x] 2.3 Move the order arrow's start from `RING + 2` to `RING + 6` so an
  ordered unit's arrow no longer crosses its own energy arc; verify with a
  test asserting the start is outside the arc's outer edge.

## 3. The health bar

- [x] 3.1 Give `health-left` its class from the same `band(share)`, dropping
  the `critical` state; verify with a test asserting both the arc and the bar
  take their class from the one function.
- [x] 3.2 Replace the `.health-left` colour rules — the owner-coloured pair
  and `.critical` — with the three band rules, and drop the `health-left`
  entries from the watched board's player-numbered rules so a watched board
  reads levels the same way; verify with a test asserting no `health-left`
  rule mentions `--mine`, `--theirs` or a player colour.

## 4. Verification

- [x] 4.1 Update whatever in `tests/test_static_serving.py` and
  `tests/test_board_selection.py` asserts on the shapes this change replaces,
  preserving what each test was guarding; verify by running both files.
- [x] 4.2 Add the assertions above as `tests/test_unit_levels.py`, one test per
  spec scenario it can reach, including the `node` run of `band`; verify with
  `python -m pytest tests/test_unit_levels.py`.
- [x] 4.3 Run the whole suite — `python -m pytest` — and confirm nothing below
  `http/static/` changed behaviour.
- [x] 4.4 Look at a board in a browser, in both the light and the dark scheme:
  a unit's ring is drawn whole and in the colour that says whose it is at
  every level of energy; the arc sits outside it touching nothing, including
  on an ordered unit whose arrow is drawn; the arc and the bar agree in
  colour at the same share; and an enemy's read the same way as your own.
- [x] 4.5 Update `SPEC_COVERAGE.md` for the two modified `web-interface`
  requirements; verify the requirement names appear there.
