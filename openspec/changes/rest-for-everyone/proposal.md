# Proposal

## Why

A unit recovers one energy a turn, and only on a turn it did nothing: gave no
order, paid for nothing, and was not charged by its meter. Two series of
programmed games show what that makes of the game. A unit that acts never
recovers, so every hunter walks two or three squares, strikes once, and then
sleeps for turns at a time to afford the next step; a Pawn with two energy
moves every other turn at best; and a fight is decided less by what the
units are than by which side ran dry first. The rule was written when a
person ordered each unit by hand and holding was a choice; now that every
unit thinks every turn, a rule that pays only for doing nothing is a rule
against playing.

## What Changes

- **Every unit on the board recovers 2 energy at the end of every turn**,
  whatever it did during the turn - moved, struck, thought, slept or stood
  still - and whether or not it paid for anything. **BREAKING**: the three
  conditions on resting are gone, and the amount is 2 rather than 1.
- What does not change: a unit never recovers past the energy its type was
  designed with, a destroyed unit recovers nothing, and a Wall - designed
  with no energy - recovers nothing. Regeneration still happens after combat
  and before elimination is judged.
- The `rested` event is reported only where energy actually rose, so a
  full-energy army at rest does not fill the feed with a line per unit per
  turn.
- The rules, the documents and the tests follow; the two series write-ups
  carry a notice that they were played under the old rule.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `turn-commit`: the Energy Regeneration requirement, its amount and its
  conditions.
- `unit-program`: the sleep requirement's statement of what a sleeper
  recovers, which follows the rest rule.

## Impact

- `domain/unit.py`: `REST_GAIN`; `domain/board.py`: the rest step and the
  bookkeeping that decided who had acted.
- `GAME_RULES.md` R3.9 and every rule that cites it (R2.5, R2.10, R3.4,
  R6.x, R7.1, R9, R10.6); `README.md`; `MODULE_DESCRIPTION.md`;
  `SPEC_COVERAGE.md`.
- `tests/test_energy_regeneration.py` rewritten; `test_think_phase.py`,
  `test_sleep.py`, `test_walls.py`, `test_turn_events.py`,
  `test_turn_feed.py` and `test_resolve_game.py` wherever a fixture counted
  on a unit not resting or on resting one point.
- `matches/RESULTS-PROGRAMMED.md` and `RESULTS-ARMY-THAT-PLAYS.md`: a
  superseded notice; the games themselves are not replayed by this change.
- Stored games are unaffected: energy is a number, and the rule applies from
  the next turn resolved.
