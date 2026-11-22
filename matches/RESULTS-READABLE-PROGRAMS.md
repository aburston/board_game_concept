# Five games under the readable default programs

The `add-program-preprocessor` change put a C-style macro preprocessor in
front of the program parser and rewrote the four default programs - the
hunter, the explorer, the vanguard and the warden - to read as words:
`#include <unit.h>`, named registers, inline helpers, one decision per
labelled block. The rewrite was allowed to change what the programs do as
long as it kept their doctrine; these games were played to see whether it
did, and what the stock army does under the current rules either way.

## What was played

**The code.** Branch `ccr-ab4868e2-ax1gla` with the change applied, on top of
commit `b7bc68d`. Nothing under `src/` was changed to play these games.

**The board and the seats.** As in every series since the seventh:
`bgcserver` registers player 1 and player 2 and commits, and that is the
whole of the administrator's setup. 8 x 8 board, 320 points a seat, the
stock array with the catalogue's programs, flag on `keep1`. The rest rule is
`rest-for-everyone`: every standing unit recovers 2 energy a turn.

**The draw.** The five pairings with a stock seat from the eighth series,
numbered 281 to 285.

## Results

| Game | Player 1 | Player 2 | Outcome |
|---|---|---|---|
| 281 | Flag Hunt | Flag Hunt | undecided on turn 73: nothing happened for fifty turns (since turn 23) |
| 282 | Flag Hunt | Garrison | undecided on turn 73: nothing happened for fifty turns (since turn 23) |
| 283 | Advance | Flag Hunt | player 2 wins on turn 14 |
| 284 | Flag Hunt | Lancers | a draw on turn 14 |
| 285 | Flag Hunt | Heavies | player 2 wins on turn 12 |

No controller halted in any of the five games: every trace is within its
type's cap, as `tests/test_default_army.py` also holds.

## Did the rewrite change anything?

No. Alongside the series, the mirror of two stock armies was played twice
through the test harness under the current rules - once with the programs
as they stood before the change (`git show b7bc68d:src/board_game_concept/domain/army.py`)
and once with the rewritten ones - and the two records are identical, every
unit's square, health, energy and state on every one of the 74 turns. The
freedom to restructure was used - the hunter and the explorer are organised
round named subroutines (`row_is_clear`, `may_step`) and helpers from
`<unit.h>` rather than register juggling - but on every board the stock army
reaches, the new programs make the choices the old ones made. The doctrine
tests in `tests/test_default_army.py` pin each clause of each program on a
hand-built board, and the old-versus-new snapshot tests from the
`tenfold-ticks-and-subroutines` change still pass as well.

## What the games show about the stock army

Game 281 (the mirror) ends quiet on turn 73 where game 269, the same mirror
under the previous rest rule, ran to turn 109. That is the rest rule, not
the programs: with 2 energy a turn back, the hunters pause less between
steps, meet sooner and are spent sooner. Both Keeps stand untouched at the
end with their flags. In game 282 the Flag Hunt seat walks into a Garrison
that gives no orders, loses its Runners and a Scout to the standing Heavies
and Lines, and gets its enemy's flag-carrying Keep down to 2 health before
nothing is left that can reach it; the quiet stop takes the game on turn 73.
Games 283 to 285 are decided quickly, as the eighth series' were: the
hunters take Advance's Keep on turn 14, trade Keeps with eleven Lances for a
draw on turn 14, and lose their own Keep to seven Heavies on turn 12.

## Reproducing

```
matches/series.sh 281 282 283 284 285
```

Each game's log is `matches/logs/game_<n>.log`.
