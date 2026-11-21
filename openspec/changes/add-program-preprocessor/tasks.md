# Tasks

## 1. The preprocessor

- [ ] 1.1 Create `domain/preprocess.py` with a tokeniser on assembly's terms (words, numbers, `,`, `(`, `)`, `##`, `;` comments kept verbatim and never expanded) and `expand(text)` yielding `(source_line, macro, text)` triples; verify with `tests/test_preprocess.py` that a program with no directive expands to its own lines one for one
- [ ] 1.2 Implement object-like `#define` / `#undef`, whole-word substitution, the conflicting-redefinition refusal and the no-self-expansion rule; verify with tests for "Naming a register", "Naming a number", "Part of a word is not a macro", "Comments are left alone", "A conflicting redefinition" and "A macro that names itself"
- [ ] 1.3 Implement function-like macros (no space before `(`, arguments expanded first, arity checked) and `##` pasting; verify with tests for "An inline function", "Arguments are expanded", "Too few arguments" and "Pasting a label"
- [ ] 1.4 Implement `\` continuation as one expanded line per physical body line, and `@label` rewriting to `_m<n>_label` with `@` refused outside a body and `_m<digit>` labels reserved; verify with tests for "A multi-instruction macro", "A branching macro used twice" and "A private label outside a macro"
- [ ] 1.5 Implement `#ifdef` / `#ifndef` / `#else` / `#endif` (nested) and `#error`, refusing unclosed or unmatched conditionals at the opening line; verify with tests for "A default a program may override", "A missing endif" and "A deliberate error"
- [ ] 1.6 Implement `#include <name>` from built-in headers only, once per program, refusing quoted or unknown names without touching the filesystem; verify with tests for "Including the unit header" and "Including a file" (assert no `open` is called)
- [ ] 1.7 Enforce the 4096-instruction and depth-64 bounds; verify with "An expansion that explodes" refused quickly and naming its line
- [ ] 1.8 Write `unit.h` (constants, sensor register names, one-`JIF` flow helpers, step/rest helpers, clobbers noted beside each); verify each helper expands to exactly its documented instructions in `tests/test_preprocess.py`, and "Directions and map answers" passes

## 2. The machine reads the expansion

- [ ] 2.1 Make `Program._parse` consume the preprocessor's triples, keep `Instruction.line` as the source line and add `Instruction.macro`; wrap `ProgramError` messages from expanded lines with the macro name; verify `tests/test_program_parser.py` passes unchanged and new tests cover "An unknown instruction from a macro", "A bad directive" and "An error inside a macro"
- [ ] 2.2 Make `Program.listing()` sum ticks per source line and return each line's expansion; verify "Pricing a macro line" and "Listing a macro line" in tests, and that `Program.ticks` equals the sum of the expansion
- [ ] 2.3 Confirm `run()` reports `halted` at the source line; verify with "A halt inside a macro" in `tests/test_program_executor.py`, and that "A helper costs what it replaces" holds by running a `unit.h` program and its hand-written twin on the same snapshot
- [ ] 2.4 Verify the determinism suite (`tests/test_determinism.py`) and the full test suite pass with no other change

## 3. Listings, API and CLI

- [ ] 3.1 Add `expanded` to each line in `service/replay.program_view` and the `/_/program/check` answer, and `headers` to the `/_/program` tariff; verify in `tests/test_http_api.py` ("Reading a header") and that existing keys are unchanged
- [ ] 3.2 Print a macro line's expansion indented beneath it in `cli/render.print_program`; verify in `tests/test_cli_client_surface.py` for `show program` and that `--format json` carries `expanded`
- [ ] 3.3 Verify "Another seat's macros": a turn record read by another seat holds no source or expansion (extend the existing withholding test)

## 4. The armoury

- [ ] 4.1 In `armoury.js`, draw the server check's per-line ticks and expansions when its text matches the editor's; verify by the armoury test path in `tests/test_static_serving.py`
- [ ] 4.2 In `program.js`, treat `#` lines as costing nothing and leave lines whose first word is a name the text or `unit.h` defines unpriced and unmarked; verify by extending the JS/server listing parity test with a directive line, a macro line and a bad macro use
- [ ] 4.3 Add a link that shows `unit.h` from the tariff's `headers`; verify it renders in the armoury page test

## 5. Rewrite the default programs

- [ ] 5.1 Freeze the current HUNTER, EXPLORER, VANGUARD and WARDEN texts (formatted for each catalogue type) as fixtures in `tests/test_default_army.py`, beside the existing OLD_ fixtures
- [ ] 5.2 Rewrite the hunter with `#include <unit.h>`, `#define NEED`, `#ifndef TARGET`, named registers and helpers; replace `str.format` templating in `army.hunter`; verify its expansion's `(op, args)` stream equals the frozen one modulo label names for every hunter type, and the snapshot test gives the same orders, sleeps and ticks
- [ ] 5.3 Rewrite the explorer the same way, its two memory words given names; verify stream equality and the existing three-turn snapshot test including memory
- [ ] 5.4 Rewrite the vanguard and the warden; verify stream equality and a new snapshot-equivalence test for the vanguard
- [ ] 5.5 Add tests for "A default program reads as words" (each includes `<unit.h>`, no direction or map answer by bare number in its own text) and "A player copies a default program" (set the read-back text on a new type)
- [ ] 5.6 Verify the stock-army tests ("A seat that changes nothing plays", "The whole army gets out", the mirror test, "A blocked hunter costs nothing") pass unchanged

## 6. Documentation

- [ ] 6.1 Add a "Macros" chapter to `PROGRAMMING_GUIDE.md`: the directives, the multi-line divergence from C stated first, `@labels`, bounds, `unit.h` printed in full, and the rewritten hunter walked through; verify every example in it is accepted by `Program` (a test that extracts and parses the guide's code blocks)
- [ ] 6.2 Update `GAME_RULES.md` R10, `MODULE_DESCRIPTION.md` (new module), `README.md` where programs are described, and `SPEC_COVERAGE.md`; verify `openspec validate add-program-preprocessor --strict` passes

## 7. Integration

- [ ] 7.1 Run the full test suite and `python -m board_game_concept.test_suite`, and play one stock-army game end to end through `matches/arena.py`, confirming the record matches a game played before the change on the same seed setup
