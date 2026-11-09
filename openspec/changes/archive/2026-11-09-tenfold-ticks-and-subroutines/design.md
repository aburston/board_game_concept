# Design

## Context

See proposal.md - Why. What the approach rests on:

- `domain/program.py` holds the whole machine: `TICKS` is the tariff,
  `TICKS_PER_COMPUTE = 10` sizes both the per-turn cap and the meter
  (`cap(compute)`), `_check` refuses a program at set time, and `run` is a
  loop over `program.instructions` with a program counter, `JMP` and `JIF`
  setting it from `program.labels`. Nothing else knows how a program is run.
- The tariff reaches the browser through `GET /_/program` as `ticks` and
  `ticks_per_compute`; `program.js` prices a listing from it and `armoury.js`
  draws the cap line from it, each with a fallback of 10 where the tariff
  has not arrived.
- The unit stores `meter` as an integer between turns. The cap and the
  meter capacity are the same number, so a stored meter is always below the
  capacity it was written under, and below the new one.
- The catalogue's hunter runs four near-identical blocks of `MOV`, `ADD`,
  `MAP`, `SUB`, `JIF` - one per candidate step - because there is no way to
  write the block once; the explorer and the vanguard likewise.
- Forty games of two series show no controller stopped at its cap; the
  halts in the record are all for want of energy.

## Goals / Non-Goals

**Goals:**

- Ten times the thinking per point of compute, at the same point price and
  the same worst case of one energy a turn.
- Subroutines as a plain `CALL`/`RET` pair with a bounded stack, refused
  statically where they can be and deterministic where they cannot.
- The catalogue's programs restated with subroutines and provably unchanged
  in what they order.

**Non-Goals:**

- Arguments, local registers or a data stack: a subroutine reads and writes
  the same eight registers and the same memory as the code that called it.
  That is what the register convention the catalogue already keeps is for.
- Changing any instruction's tick price, the sleep bound, the meter's
  carry, or the point price of compute.
- Making the catalogue's programs do anything new. Same orders, written
  shorter.

## Decisions

**`TICKS_PER_COMPUTE` becomes 100, and nothing else about the meter moves.**
The cap and the meter capacity stay the same number, so a turn's thinking
still costs at most one energy, and the carry across turns is unchanged.
The alternative - ten times the cap but the same meter - would make thinking
ten times dearer per turn, which is the opposite of what is asked.

**`CALL` and `RET` are two instructions and a list.** `run` keeps a return
stack for the duration of one call to `run`; `CALL label` appends the next
program counter and jumps to the label, `RET` pops and jumps, both at 1 tick
in `TICKS` so the listing and the tariff pick them up with no further work.
`_check` refuses `CALL` to an unknown label exactly as it refuses `JMP`. A
`RET` with an empty stack breaks out of the loop like `HALT`, keeping the
order so far, because a stray `RET` is a program that has finished early, not
one that has broken. `CALL_DEPTH = 16`: a seventeenth push sets
`result.halted` to the `CALL`'s line and breaks, the same way the cap does,
so the trace, the dropped order and the browser's reading of a halt are all
already there. Alternatives: a stack in memory words (visible to `LOAD` and
`STORE`, so a program could corrupt its own return address); an unbounded
stack (a recursive program would then run to the cap rather than halting
where it recursed, which is less useful to read); refusing recursion
statically (a check that cannot be exact).

**The stack is not state.** It is not in the unit's record, the state hash,
or the trace, because a run always ends with it discarded: `HALT`, `SLEEP`,
a halt and falling off the end all leave the next run starting fresh. A
program that `SLEEP`s inside a subroutine wakes at its first line, as it
does today.

**The catalogue's programs are restated, not rewritten.** The hunter's four
step checks become one subroutine taking the candidate square in r2 and the
row or column in r3 and answering in r0; the explorer's four candidates the
same; the vanguard's one check stays inline. Each program must give the same
order as before on every snapshot, which three things hold: the mirror test
(every turn of the record is its own reflection), the harness's halt and
movement tests over every doctrine, and a new test that runs the old and new
text of each program against a set of snapshots and requires the same
orders. The old text is kept in the test, not in the catalogue.

**The browser's fallbacks follow.** `program.js` and `armoury.js` each
default `ticks_per_compute` to 10 when the tariff has not loaded; they
default to 100. Nothing else in the page is numeric about the cap.

## Risks / Trade-offs

- [Ten times the ticks lets a program loop ten times longer before the cap
  catches it] → the cap still catches it, and at the same price; the series
  can say whether anybody writes such a program.
- [A stray `RET` ending the run quietly hides a bug in a player's program]
  → the trace shows the run ending at the `RET`'s line with the ticks spent
  there, and the alternative - halting - would drop an order the program
  had already decided on, which is worse for the player and no clearer.
- [Restating the catalogue's programs changes their tick counts, which the
  write-ups quote] → the counts quoted are the seventh and eighth series'
  and stay true of those games; the ninth series, if there is one, will
  quote its own.
- [Stored traces say `halted` with a line number; a halt at `CALL` reads the
  same] → it is the same kind of event, and the trace's `halted` field is a
  line in every reader already.

## Migration Plan

No stored data changes shape. Meters written under the old capacity are
valid under the new. Programs on disk use no instruction that did not exist.
The tariff endpoint's numbers change, and a browser that has cached the old
tariff re-reads it on its next load.

## Open Questions

None that change the specs or the tasks. Whether sixteen is the right depth
is a number to revisit when a program needs more.
