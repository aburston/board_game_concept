# Proposal

## Why

A unit program is raw register assembly: `MOV r6, r0`, `SUB r0, 2`,
`JIF lt r0, r3, gocol`. Every reader has to hold in their head that r6 is
"my x", that 2 means "a friend" on the map, and that 3 is "south", and the
catalogue's own programs carry that burden in end-of-line comments because
the language has no way to give anything a name. Players who want to write a
controller start by reading the defaults, so the defaults are the language's
first lesson - and right now they teach register numbers.

A macro preprocessor in the style of the C preprocessor - the most widely
known one - lets a program name its registers and constants and wrap a
recurring idiom in a readable inline "function", without changing the
machine, the tariff, or what any instruction costs.

## What Changes

- **Programs are run through a preprocessor before they are checked.** It
  is a deterministic, self-contained subset of the C preprocessor:
  `#define` for object-like and function-like macros, `#undef`, `#ifdef` /
  `#ifndef` / `#else` / `#endif`, `#error`, `##` token pasting, and
  `#include` of built-in headers only (never a file). A macro body
  continued with `\` expands to several lines - one instruction each - which
  is how a macro stands for more than one instruction. Labels written
  `@name` inside a macro body are private to each expansion, so a macro can
  branch without clashing with itself.
- **A built-in header, `<unit.h>`,** names the machine's numbers - the four
  directions, the five things `MAP` answers - and provides inline helpers
  for the sensors' outputs and common tests (e.g. "go to `label` if this
  register is below that one", "step the way this register says"). Every
  helper expands to exactly the instructions it replaces, so using one costs
  what writing it out costs.
- **Macros are free; what they expand to is paid for.** The tariff, the
  meter, the cap and the executor are unchanged; a program is priced by its
  expansion. A type still carries the program's source text, which is what
  its owner reads back and what is fixed at commit.
- **Errors, listings and traces speak of the source.** A refusal names the
  line the player wrote (and the macro it came from), a listing gives each
  source line the ticks of what it expands to, and a halt is traced at the
  source line. A listing also shows what each macro line expands to.
- **The catalogue's default programs are rewritten to read as prose** -
  the hunter, the explorer, the vanguard and the warden - using `<unit.h>`
  and named registers. They give the same orders, sleeps and memory and
  spend the same ticks on every board as the programs they replace, so no
  game played with the stock army changes.
- The web armoury prices a program through the server's check, so a line
  that uses a macro shows the ticks of its expansion and a directive costs
  nothing.
- Existing programs are unaffected: a program with no `#` line and no
  defined name in it reads exactly as before.

## Capabilities

### New Capabilities

- `program-preprocessor`: the macro language a program's text is written
  in - its directives, how macros expand, built-in headers and `<unit.h>`,
  local labels, limits, and how expanded instructions are traced back to
  the source lines that produced them.

### Modified Capabilities

- `unit-program`: a program's text may hold directives and macro uses and
  is expanded before it is checked; refusals name the source line.
- `default-army`: the catalogue's default programs are written with the
  preprocessor for readability, and must behave exactly as before.
- `web-interface`: the armoury's per-line tick listing prices a line by its
  expansion and accepts directive lines.

## Impact

- New `domain/preprocess.py` (the preprocessor and the built-in headers);
  `domain/program.py` runs it before `_parse` and keeps a map from
  instruction to source line for errors, `listing()` and `halted`.
- `domain/army.py`: the four default programs rewritten; `str.format`
  templating replaced by `#define` lines.
- `service/replay.py`, `http/app.py` (program check/view), `cli/show.py`:
  listings gain each line's expansion.
- `http/static/program.js`, `armoury.js`: listing from the server check;
  the local pass skips directive lines and defined names.
- `PROGRAMMING_GUIDE.md` (new chapter, `<unit.h>` printed in full),
  `GAME_RULES.md` R10, `MODULE_DESCRIPTION.md`, `SPEC_COVERAGE.md`.
- Tests: new `tests/test_preprocess.py`; `test_default_army.py` holds the
  rewritten programs to the old ones' orders and ticks.
- No new dependency, no storage change: types already store program text.
- Out of scope: the match-harness doctrines under `matches/bots/programs/`,
  which are experiment fixtures whose recorded results cite them as written.
