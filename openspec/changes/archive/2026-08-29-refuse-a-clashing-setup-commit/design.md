## Context

See `proposal.md` — Why.

A player's setup reaches the server through `service/turn.py`'s `publish`,
which takes the repository's write lock and then writes three things: the
player's types, a commit marker, and the orders themselves. Nothing is written
before the lock is taken, and `setup_refusal` already raises out of `publish`
before any of it — a setup with no flag carrier is refused exactly this way,
and leaves the player's setup untouched. This rule follows it.

A player's session holds only its own view, so it cannot see where anybody
else's units are. What it can read is the repository: the orders another
player published when they committed. That is what "already committed to this
square" means, and it is a read of what is on disk rather than of any state
this session carries.

## Goals / Non-Goals

**Goals:**

- A clashing setup commit is refused, and the player can fix it and commit
  again with nothing lost.
- The check runs under the same lock as the writes it guards, so two commits
  racing cannot both be accepted onto one square.

**Non-Goals:**

- Later turns. Deployments only happen at setup — `deploy_unit` refuses once
  setup is closed — so a commit-time check on any other turn would guard
  nothing.
- Removing the resolution-time refusal. It is the backstop for orders that
  never went through a commit, and it keeps refusing every claimant there.
- Hiding which square clashed. The player cannot deploy elsewhere without
  being told, and the square is the least that says it.

## Decisions

**The check lives in `publish`, inside the held lock, before the first write.**
It reads every other player's published orders from the repository, collects
the squares their deployments claim, and refuses this commit if any of this
player's deployments wants one of them. Because the lock is held across the
check and the writes, two players committing at the same moment are serialised:
the first writes its orders, the second reads them and is refused.

*Alternative considered:* check in the HTTP layer before calling `publish`. It
would leave the CLI unchecked and the race open, since the lock is taken inside
`publish`.

**Only a setup commit is checked**, which is `game.getNewGame()` — the same
condition `setup_refusal` uses to decide whether a flag is required. On any
later turn the check is skipped, and the published orders hold moves rather
than deployments anyway.

**What counts as a claimed square** is a published unit that is a deployment:
one in the `INITIAL` state, or one the board does not hold yet. That is the
same test `_refused_deployments` applies at resolution, so the two agree on
what a deployment is.

**The refusal is a `GameError`**, raised the way `setup_refusal`'s is, so every
client already reports it: the CLI prints it and returns to the prompt, and the
browser shows it and leaves the armoury as it was.

## Risks / Trade-offs

- **Commit order decides a contested square** → Stated in the proposal and in
  the spec. It is the cost of letting the refused player do something about
  it; refusing both would leave neither able to act, which is the behaviour
  being replaced.
- **The refusal discloses that a square is occupied** → The minimum needed to
  deploy elsewhere. It names the square and neither the unit nor its owner.
- **A player could probe the board by committing repeatedly** → They learn only
  which of their own squares are taken, one commit at a time, and only during
  setup. Left as it is rather than paid for with a rule nobody could act on.
