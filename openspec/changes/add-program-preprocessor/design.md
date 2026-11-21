# Design

## Context

`domain/program.py` turns a program's text into `Instruction(op, args, line)`
records in one pass (`_parse`), checks each against the tariff, resolves
labels, and runs them in `run()`. `line` is used three ways outside parsing:
`ProgramError.line` (refusals), `Program.listing()` (ticks per source line,
read by `service/replay.program_view`, the HTTP check endpoint and
`cli/show`), and `Result.halted` (the trace). A type stores its program as
plain text in the player's YAML; `Program(text)` is rebuilt from it wherever
needed. The catalogue's programs in `domain/army.py` are Python strings
templated with `str.format` (`{need}`, `{target}`), and
`tests/test_default_army.py` already holds rewritten programs to older ones
by running both on a set of snapshots.

The project invariant - resolution is a pure function of board and orders -
extends to anything between the text and the instructions.

## Goals / Non-Goals

**Goals:**
- A preprocessor that anyone who has seen C's recognises on sight, with the
  few divergences an assembly needs stated plainly.
- No change to the machine: the tariff, executor, meter and cap untouched.
- Source-line fidelity everywhere a player is told about their program.
- Default programs that read top to bottom as a description of behaviour,
  and expand to the same instruction stream they replace.

**Non-Goals:**
- `#if` with expressions, `defined()`, `#line`, `#pragma`, stringising (`#x`),
  variadic macros. Programs have no strings and little need for arithmetic at
  expansion time; each can be added later without changing what is here.
- Including user files, or headers shared between a player's own types.
- Rewriting the match-harness doctrines in `matches/bots/programs/`.
- Any new instruction, or any compile-time optimisation of the expansion.

## Decisions

### A hand-written cpp subset, not the system `cpp` and not a library

The system preprocessor is not guaranteed to exist, varies by platform, and
reads files - all three unacceptable for something on the commit path of a
deterministic game. `pcpp` (pure-Python) would add a dependency and brings
the full C lexer: `'` in a `;` comment ("I'm blocked") opens a character
literal and breaks the line, which every existing default program would
trip. A ~300-line `domain/preprocess.py` tokenising on assembly's own terms
(words, numbers, `,`, `(`, `)`, `##`, `;` comments) is smaller than the
workaround for either. Alternatives considered: m4 (well known, but its
quoting is famously hostile to newcomers) and NASM-style `%macro` blocks
(closer to assemblers, but the user asked for the C preprocessor and it is
the one most people already read).

### Multi-line bodies keep their line breaks

In C, `\` continuation joins lines into one. Here a macro must be able to
stand for several instructions and the language has one instruction per
line, so each physical line of a continued body expands to its own line.
This is the one divergence a C reader will notice; the guide says it first.
Alternative: a statement separator (`|`) inside a single line. Rejected
because it changes the base assembly's grammar for everyone.

### `@label` for expansion-private labels

Each expansion gets a counter `n`; `@skip` in its body becomes `_m<n>_skip`
both where defined and where named. The rewritten name matches the existing
label grammar and cannot collide with a player's label because players
cannot write `@` outside a body (refused) and the `_m<n>_` prefix is
reserved (a player label starting `_m<digit>` is refused). Alternative:
`__COUNTER__` with `##` - correct but unreadable, which defeats the point.

### Expansion output carries provenance

The preprocessor yields `(source_line, macro_name_or_None, text)` triples
rather than text. `_parse` consumes those instead of `splitlines()`, so
`Instruction.line` is always the source line, and a new
`Instruction.macro` names the outermost macro for refusals ("line 12: in
STEP_TOWARD: MOVE takes north, east, south, west or a register"). `run()`
is untouched: `halted` already reports `instruction.line`.
`Program.listing()` sums ticks by source line and also returns each line's
expanded instructions, which `program_view`, the check endpoint and
`render.print_program` show indented under a macro line. The JSON of each
listed line gains an `expanded` array (empty for plain lines); nothing that
reads the old keys changes.

### `<unit.h>` is plain text shipped in the package

Headers live in a dict in `domain/preprocess.py` (or a `headers/` package
data directory read once at import, never per program). `/_/program`
already publishes the tariff; it gains `headers: {"unit.h": text}`, which
is what the armoury's "show header" link and the guide print. Draft
contents:

```
; unit.h - names for the machine. Every helper expands to exactly the
; instructions named beside it, so using one costs what writing it costs.
#define NORTH 1
#define EAST 2
#define SOUTH 3
#define WEST 4
#define UNKNOWN 0
#define EMPTY 1
#define FRIEND 2
#define ENEMY 3
#define OFF_BOARD 4
; what SELF writes
#define MY_X r0
#define MY_Y r1
#define MY_HEALTH r2
#define MY_ENERGY r3
#define HAVE_FLAG r4
#define MY_NUMBER r5
; what FLAG, NEAREST and MAP write
#define FOUND_X r0
#define FOUND_Y r1
#define FOUND_DIST r2
#define SEEN r0
; flow: one JIF each
#define GOTO(where) JMP where
#define IF_NEG(r, where) JIF neg r, where
#define IF_POS(r, where) JIF pos r, where
#define IF_ZERO(r, where) JIF zero r, where
#define IF_NONZERO(r, where) JIF notzero r, where
#define IF_EQ(a, b, where) JIF eq a, b, where
#define IF_BELOW(a, b, where) JIF lt a, b, where
#define IF_NONE(r, where) JIF neg r, where   ; sensors answer -1 for none
; SELF, then off to `where` unless energy covers `need` (clobbers r0-r5)
#define UNLESS_AFFORD(need, where) SELF \
    SUB MY_ENERGY, need \
    JIF neg MY_ENERGY, where
#define STEP(dir) MOVE dir \
    HALT
#define REST SLEEP 1
#define REST_LONG SLEEP 100
```

The final header is settled during implementation by what the four default
programs need; the spec fixes only the constants and the "costs what it
replaces" rule. Helpers that clobber registers say so beside them.

### Default programs: readability first, doctrine held

Each catalogue program becomes source text that begins `#include <unit.h>`,
`#define`s its parameters (`NEED`, `TARGET`) and register roles, and reads
top to bottom as a description of what the unit does. `army.hunter(need)`
becomes `"#define NEED %d\n" % need + HUNTER` - a line the player can read
and edit - instead of `str.format`.

The rewrites are free to restructure: subroutines with speaking names
(`step_round_friends`, `can_afford`), one decision per labelled block,
helpers from `unit.h` for every test, and comments that say why rather than
what a register holds. Where the old program's exact tie-breaks or ordering
of checks got in the way of a clear shape, the clear shape wins. What is
held fixed is the **doctrine** the catalogue table states for each program,
and the measurable consequences the stock-army tests already pin down:
determinism, fitting the cap on every turn, a blocked hunter sleeping, the
whole army leaving its squares within twenty turns, and the two seats
mirroring each other. Each doctrine clause gets a direct unit test on a
hand-built snapshot (e.g. "friend ahead, flag beyond: steps aside").

Consequence accepted: a stock-army game may no longer resolve turn for turn
as it did. The determinism suite is unaffected (it compares a game with
itself), but any test that compares a replay against a recorded fixture of
the old programs is rewritten to assert properties instead. `matches/`
results stand as history of the programs they name. Sketch of the hunter:

```
#define NEED 3
#include <unit.h>
; hunter: walk at the nearest enemy flag, round my own units, and fight
; what is there. Sleep when a step and a strike are not both affordable.
#ifndef TARGET
#define TARGET FLAG enemy
#endif
#define here_x r6
#define here_y r7
#define goal_x r4
#define goal_y r5

        UNLESS_AFFORD(NEED, rest)        ; SELF, then sleep if too poor
        MOV here_x, MY_X
        MOV here_y, MY_Y
        TARGET
        IF_NONE(FOUND_X, rest)           ; no flag left to hunt
        MOV goal_x, FOUND_X
        MOV goal_y, FOUND_Y
        CALL step_towards_goal           ; MOVEs and HALTs if a way is clear
rest:   REST                             ; both ways are mine: wait a turn
...
```

### The armoury: the server's listing wins, the local pass stays honest

`armoury.js` already sends the text to `/_/program/check` a moment after
typing. When that answer matches the current text, its per-line ticks and
`expanded` arrays are drawn. Until it arrives, `program.js`'s local listing
treats `#` lines as costing nothing and leaves any line whose first word is
a name the text `#define`s, or `unit.h` defines, unpriced and unmarked
rather than marking it "not an instruction". No preprocessor is duplicated
in JavaScript.

### Bounds

4096 expanded instructions and nesting depth 64 are generous - the longest
default program expands to about 70 - and stop a program from making the
check endpoint or commit path do unbounded work. Self-reference follows C's
"painted blue" rule, so recursion cannot occur; the bounds catch only
exponential fan-out.

## Risks / Trade-offs

- [Two parsers' notions of a line drift (server, `program.js`)] → the local
  pass no longer tries to judge macro lines; the server listing is drawn
  whenever it is current, and `test_static_serving`'s parity test is
  extended with a directive and a macro line.
- [A player's existing program has a line starting `#`] → it was already
  refused as "not an instruction", so no stored program can contain one; old
  games reload unchanged.
- [Expanded listings get long] → only macro lines show expansions, indented,
  and the CLI prints them beneath the line, not inline.
- [Helpers hide register clobbering] → every helper that writes a register
  says which beside its definition; the guide's chapter opens with the
  register table.
- [Rewrites drift from doctrine] → a unit test per doctrine clause on
  hand-built snapshots, plus the existing cap, mirror, "blocked hunter" and
  "whole army gets out" tests unchanged; a short stock-army series is played
  and read before the change lands, as earlier program changes were.
- [Stock games resolve differently from recorded ones] → accepted; the
  records under `matches/` are kept as history and any fixture-replay test
  asserts properties instead of turns.

## Migration Plan

No data migration: types already store text, and text with no directive
expands to itself. Games created before the change keep the old default
program text in their players' files and run it unchanged; games created
after get the rewritten text. Rollback is reverting the code: a game created
under the change holds programs with directives, which the old parser would
refuse to reload, so roll back only before such games matter, or keep
`preprocess.py` when reverting anything else.
