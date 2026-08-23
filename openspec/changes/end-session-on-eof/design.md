## Context

See `proposal.md` — Why.

`cli/session.py` holds `read_command`, which every role calls. It prints the
prompt, reads a line, parses it, and returns either a command the role may run
or `None` meaning "nothing to do". Every role treats `None` by looping round.

`sys.stdin.readline()` returns `''` at end of input and `'\n'` for a blank line.
After `.rstrip()` these are the same string, so the reader cannot tell them
apart and the roles are given the answer that means "carry on".

## Goals / Non-Goals

**Goals:**

- End of input ends the session, with a success status, in all three roles.
- No change to any role's own loop.

**Non-Goals:**

- Making the roles scriptable in any wider sense. A piped script still races the
  commit barrier, because a client that has committed blocks until the server
  resolves the turn; that is the barrier working, not a defect.
- Reading input any other way. `readline` on `sys.stdin` stays.

## Decisions

### 1. End of input is reported as the `exit` command, not as a new answer

`read_command` returns `commands.Exit()` when the read comes back empty. All
three roles already have a branch for `exit` that ends the session, so the fix
reaches every role without touching one of them, and a role that gains a
different way of ending will get it for free.

*Alternative considered:* call `sys.exit(0)` inside `read_command`. Fewer moving
parts, but it puts process control inside a function whose job is to read a
line, and it makes the reader untestable without catching `SystemExit`.

*Alternative considered:* a third return value — a sentinel, or an exception —
that each role handles. That is three more branches to keep in step, for a case
that is already exactly "the session is over".

### 2. A newline is printed before ending

The prompt has already been written when the read comes back empty, so ending
there would leave the cursor after it. One newline puts the shell prompt on a
line of its own, which is what a terminal does for Ctrl-D.

## Risks / Trade-offs

**A role could gain a code path where `exit` is refused but end of input should
still stop it** → None has one today: `exit` is in every role's command set in
`cli/roles.py`, and `read_command` returns the node directly rather than putting
it through the role's own filter. If a role ever refused `exit`, end of input
would be refused with it, and the spin would come back. The three surface tests
would catch it.

**Nothing else distinguishes a closed pipe from an empty line** → That is the
whole defect, and it is fixed at the one place that can tell: the call that
performs the read.
