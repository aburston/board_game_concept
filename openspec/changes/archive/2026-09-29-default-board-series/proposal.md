# Proposal

## Why

Every played game in `matches/` was played under rules the game no longer has.
The last series, games 181–200 (`matches/RESULTS-QUARTER-FARE.md`), was played
on 26 August against a ten-by-ten board, two hundred points a player, a
house-refereed split, fights ground out in rounds until one side died, and no
flag. Since then the game gained one strike a turn (**R5.2**), a flag whose
square everybody can see and whose fall ends its owner's game (**R2.11**,
**R6.5**, **R7.1a**), a default board of eight by eight (**R2.1**), a
250-point budget and a sixteen-unit stock army every seat opens with
(**R2.13**), halves the game itself enforces (**R2.6a**), a setup commit that
is refused for a clash or a missing flag, and a square that never holds two
units at the end of a turn (**R5.8a**). None of the nineteen bots plays that
game — their doctrines reason about rounds per fight and armies of two hundred
points on a ten-wide frontier — and the harness that drives them sizes the
board itself, referees a split the game now referees, and never asks for the
flags every player is entitled to see. There is no evidence anywhere of how
the game as it stands actually plays: whether the stock army is a fair start,
whether a visible flag ends the hunt that used to fill sixty turns, or what
one strike a turn does to attack against health.

## What Changes

- **A sixth series of bot games, played on the default 1v1 board.** No `set
  board`, no budget named: eight by eight, two seats at 250 points, each seat
  opening with the stock army and its flag on `keep1`, halves as the game
  publishes them. Games are numbered on from 200. This is the series the
  repository points to as current; the five before it are marked as played
  under superseded rules, as `RESULTS.md` and `RESULTS-FRONTIER.md` already
  are.
- **A new set of doctrines written for the rules as they stand.** Two families:
  doctrines that keep the stock army as given and differ only in how they
  play it, and doctrines that take some or all of it back and redesign within
  the 250 points. The old nineteen are retired rather than patched: their
  arithmetic is about a fight that no longer exists.
- **The harness is brought to the current build.** It stops sizing the board
  and naming budgets, stops refereeing placement (the game refuses a
  deployment outside a half and the client reports it), reads the flags,
  placement and players subjects into the view a bot is given, handles a
  seat that opens with sixteen units already standing, lets a bot designate
  its flag, and reads elimination from the players subject rather than
  counting units with attack. It launches the roles through the interpreter
  running it rather than a hard-coded `venv/bin`.
- **The rule the harness exists to keep is stated as a spec**, so that the
  next series is held to it rather than trusting a docstring: a bot is handed
  its own player's view and nothing else, and every order in every game goes
  through a real role's prompt.
- **The results are written up** as `matches/RESULTS-DEFAULT-BOARD.md`, with
  the same anatomy as the earlier write-ups: what was played, the table of
  decisions, what decided them, and what the series says about the open
  questions in `GAME_RULES.md` Part 2 — without answering any of them here.
  A rule change argued for by this series is its own change.

## Capabilities

### New Capabilities

- `match-series`: how a series of bot-played games is run so that its results
  are evidence about the rules — through the real roles, each bot given only
  its own view, on the game's own defaults, recorded turn by turn — and what
  a series write-up must carry to be read beside the earlier ones.

### Modified Capabilities

(none — no rule of the game changes. The series is played against the rules
as specified; anything it argues for is proposed separately.)

## Impact

- **`matches/arena.py`**: rewritten around the current CLI — default board
  and budget, the seeded army, `set flag`, the `flags`, `placement` and
  `players` subjects, elimination from `status`, interpreter-relative role
  launch, no referee. The long-lived-session shape, the transcript files and
  the `game_<n>_history.json` record stay as they are.
- **`matches/bots/`**: `common.py` and `base.py` gain what a bot needs under
  the current rules (flag squares, the seeded army, a fare table that already
  matches **R4.3**, one-strike arithmetic); the nineteen old doctrines are
  removed and a new set written. Nothing under `src/` changes.
- **`matches/RESULTS-DEFAULT-BOARD.md`** is new; the five earlier write-ups
  gain the same "played under superseded rules" banner two of them already
  carry; `matches/logs/` gains the new games' logs and transcripts.
- **`SPEC_COVERAGE.md`** gains the `match-series` capability in its table and
  a note on how the harness is held to it. `README.md` gains a line on how a
  series is played. `GAME_RULES.md` is untouched.
- **Tests**: a small suite under `tests/` holds the harness's view boundary
  and its reading of the players subject, without playing a game; the games
  themselves are evidence, not tests, and are not run under `pytest`.
