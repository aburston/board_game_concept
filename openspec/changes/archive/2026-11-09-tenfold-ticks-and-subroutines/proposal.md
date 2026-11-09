# Proposal

## Why

A point of compute buys ten ticks of thinking a turn, and the catalogue's
programs are written to the last tick of it: the vanguard fits a Pawn's cap
with one to spare, the explorer gives up its fourth candidate step and its
staleness check to stay under sixty, and the hunter's four map checks are
written out four times because the language has no way to write them once.
Two series of games show the cap never bit in play - no controller was
stopped at it in forty games - so the price is paid in what can be written,
not in what is played. A player should be able to write a program that does
something, and write it once.

## What Changes

- **A point of compute buys a hundred ticks, not ten.** The per-turn cap is
  `100 × compute` ticks and the meter charges one energy for every
  `100 × compute` ticks thought. The point price of compute is unchanged,
  and so is the most a turn's thinking can cost - one energy - so a unit's
  cost and its worst case are what they were; what changes is how much
  thinking an energy buys. **BREAKING** for anybody reading the numbers: the
  tariff the server publishes, the listings, and every statement of ten
  ticks a point.
- **The language gains subroutines.** `CALL label` (1 tick) runs the code at
  a label and `RET` (1 tick) comes back to the line after the call, through
  a return stack of up to sixteen calls. A `CALL` to a label the program does
  not define is refused when the program is set, like a jump to nowhere; a
  `RET` with nothing to return to ends the run, as `HALT` does; a seventeenth
  nested `CALL` halts the controller, as the cap does, and the trace says
  where. The stack lives for one run of the program, like the registers'
  working values.
- **The catalogue's programs say what they do once.** The hunter's and the
  explorer's repeated step checks become one subroutine each; the programs
  give the same orders on the same boards, held by the mirror test and the
  series harness.
- The web armoury's listing prices `CALL` and `RET` as it prices everything,
  from the tariff the server publishes, and its cap line shows the new cap.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `unit-program`: the two new instructions and what a bad `CALL` or a stray
  `RET` does; a hundred ticks a point for the meter and the cap.

## Impact

- `domain/program.py`: `TICKS_PER_COMPUTE`, `TICKS` (two rows), `_check`,
  the executor's return stack and `CALL_DEPTH`.
- `domain/army.py`: the hunter, the explorer and the vanguard restated with
  subroutines, the same orders on the same boards.
- `http/static/program.js`, `armoury.js`: nothing but the tariff they already
  read; a fallback of 10 in two places becomes 100.
- `GAME_RULES.md` R2.4, R9, R10; `README.md`; `MODULE_DESCRIPTION.md`;
  `SPEC_COVERAGE.md`.
- `tests/test_program_parser.py`, `test_program_executor.py`,
  `test_default_army.py`, `test_static_serving.py`, `test_cli_client_surface.py`
  and `test_http_api.py` wherever a listing's cap or ticks-per-energy line is
  asserted.
- Stored games are unaffected: a meter value written under the old capacity
  is a valid value under the new one, and no program on disk uses an
  instruction that did not exist.
