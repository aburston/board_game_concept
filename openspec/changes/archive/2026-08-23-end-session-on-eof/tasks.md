## 1. Reproduce the spin

- [x] 1.1 Add one test per role that starts it with its input closed and asserts it exits; verify all three fail today by timing out or by filling the pipe with prompts

## 2. End the session at end of input

- [x] 2.1 Have `read_command` return the `exit` command when the read comes back empty, printing a newline first; verify the three tests from 1.1 pass
- [x] 2.2 Verify the existing blank-input scenarios still pass for all three roles, so an empty line is still a no-op and not an ending

## 3. Reconcile the documents

- [x] 3.1 Note in `GAME_RULES.md` R8 that a session also ends when its input runs out; verify the file describes what each role accepts

## 4. Verify

- [x] 4.1 Run `pytest` and verify the full suite passes
- [x] 4.2 Pipe a script of commands into each console script and verify each runs them and exits rather than spinning
- [x] 4.3 Run `openspec validate end-session-on-eof --strict` and verify it reports the change valid
