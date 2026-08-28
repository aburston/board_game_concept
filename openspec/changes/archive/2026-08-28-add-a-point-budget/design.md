## Context

Four facts about the current code decide most of this design.

**A unit already remembers its design.** `UnitType.__init__` keeps
`type_attack`, `type_health` and `type_energy` alongside the `attack`,
`health` and `energy` that play wears down — the comment there says why: "a
unit's current health is not its type's health, and a destroyed one has none
at all". A price computed from the worn values would fall as a unit took
damage and a destroyed unit would be free. The preserved design is exactly the
right number to price from, and it is already on every unit, including one
learned by contact.

**Deployment happens twice, on two different boards.** `games.deploy_unit`
puts a unit onto the client's own board so the player can see it at once;
`turn._apply_orders` puts it onto the authoritative board when the turn is
resolved. Only the second is binding. A budget checked in the client alone is
a suggestion — a hand-written order file, or a player file loaded by the
administrator, reaches `_apply_orders` without passing through `deploy_unit`
at all. So the rule has to hold in both places, which means it has to be
stated in one.

**Elimination is already derived rather than tracked**, and says why:
"Derived from the board every turn rather than tracked, so that who is out
cannot drift out of step with what is standing." A spent-points counter is the
same kind of fact and has the same failure mode — a counter that is not
decremented when a deployment is rejected, or is decremented twice when a
draft is replayed, is a budget that silently stops matching the army. Spend is
derived the same way.

**A session only loads the player records it is entitled to.**
`Game._load_players` reads `read_player(number)` when `mine` is true — the
session's own number, or any number for the administrator and the observer —
and skips it otherwise. Budget privacy therefore needs no filter of its own:
a player simply never reads the record another player's budget is in. What it
does need is a way to say "unknown", because today the code builds a `Player`
object for every registered number whether it read their record or not.

## Goals / Non-Goals

**Goals:**

- A budget fixed when a player is registered, per player, defaulting to 100.
- One price for a type — the sum of its three statistics — computed in one
  place, so the price and the type cannot disagree.
- One rule about affordability, asked by the client's refusal and by the
  turn's rejection, so the two cannot drift.
- Spend derived from the board, so no counter can go stale.
- Determinism preserved: which of several unaffordable deployments survive is
  decided by the rules, not by list order.
- A budget carried through both storage backends and through the HTTP tier
  without either becoming a place where the rule is restated.

**Non-Goals:**

- Spending points on anything but deploying a unit. Moving and attacking cost
  energy, which is a different currency and stays one.
- A budget that changes during play: reinforcement, income, refunds for
  losses, or trading points between players.
- Pricing a type by anything cleverer than the sum of its statistics.
  A weighted formula is a balance decision and this change is a mechanism.
- Refusing to define an unaffordable type. Defining is free; the budget bites
  at deployment, which keeps `add type` a design step and `add unit` the
  commitment.
- A budget for the administrator or the observer. Neither owns units, so
  neither has anything to spend.

## Decisions

### The price of a type is a property of the type, read from its design

`UnitType` gains a `cost` property:

```python
@property
def cost(self):
    """What deploying one unit of this design spends."""
    return self.type_attack + self.type_health + self.type_energy
```

Read from the preserved design rather than from `self.attack`, `self.health`
and `self.energy`, so a unit worn down by combat still reports what it cost
and a destroyed one is not free. Because a unit is a copy of its type, the
same property answers for a type object and for a unit on the board, which is
what lets spend be summed straight off the board's unit list.

Computed, not stored. A stored cost would be a second copy of a number the
type already holds, and the only thing a second copy can do is disagree.

**Alternative rejected:** a `points` field on `UnitType` set at construction.
It reads the same at the prompt and is one more field to serialise, restore,
and keep in step with a type learned by contact.

### `domain/budget.py` is the one place the rule lives

A new domain module, three functions:

```python
def spent(board, player):        # sum of cost over that player's units
def remaining(board, player):    # player.budget - spent(board, player)
def refusal(board, player, unit_type):  # the message, or None if affordable
```

`refusal` returns the message rather than a boolean, so the client's
`GameError` and the turn's `reject(...)` reason are the same sentence built
once. Two enforcers with two messages is two rules as far as a player reading
them is concerned.

`spent` counts every unit the board holds for that player — `destroyed` and
`on_board` are not consulted. That is the no-refund rule, expressed as an
absence rather than as a condition.

It lives in `domain/` because it is a rule about the game, not about a
session: it takes a board and a player and consults nothing else. `service/`
would put it above the layer that has to obey it.

### Spend is derived from the board, on whichever board is asking

`games.deploy_unit` asks against the client's board, which during setup holds
that player's own deployed units — their own view always shows all of their
own units, destroyed ones included, so the sum is complete. `_apply_orders`
asks against the authoritative board, which holds everything. Both get the
right answer from the same function without either being told which board it
is looking at.

Because `_apply_orders` adds units to the board as it goes, `remaining` falls
as each deployment lands, and the next deployment is judged against what is
actually left. No accumulator is threaded through the loop.

### `Player.budget` is `None` when the session may not know it

```python
DEFAULT_BUDGET = 100
MIN_BUDGET = 1
MAX_BUDGET = 1000

def __init__(self, number, budget=DEFAULT_BUDGET):
```

`Player` states the range the way it already states the number's range, and
for the same reason its docstring gives: a budget arrives by more than one
door — typed at the prompt, read from a player configuration file, read back
from a stored record, and over HTTP — and a check at one door is a check the
others do not get.

`budget=None` is the fourth case: a player this session is not entitled to
read. `Game._load_players` passes `None` for a player whose record it did not
read. `spent` still answers for such a player from the board, but `remaining`
raises rather than returning a number, and the views draw `-`. Asking what an
unknown budget has left is a bug in the caller, not a value.

The range 1 to 1000: the cheapest type a player can define costs 3 and the
dearest costs 120, so 1000 buys eight of the dearest and a budget of 1 buys
nothing at all — deliberately, because a budget too small to deploy with is a
legal way to set up a player who has already lost, and refusing it would be
the rules second-guessing the administrator.

### Both enforcers, one rule; the turn rejects rather than refuses

The client refuses at `add unit` with a `GameError`, which is how every other
deployment problem is reported and leaves the session running. The turn
rejects at `_apply_orders` through the existing `reject(p_number, unit,
reason)` channel, which writes the reason to that player's rejections file and
reports it at the top of their next turn — the same road a deployment onto a
contended square already travels.

Nothing new is invented for the server side. A budget failure is an order the
server would not carry out, and that is what the rejection channel is.

### Deployments are charged in unit-name order

`_published_orders` returns each player's orders in the order their document
lists them, which is the order the board holds them in. The determinism
invariant forbids deciding a rule by "the order a list happens to hold its
members in", so the deployments in one turn are sorted by unit name before
they are charged, the way `resolveCollision` sorts the two units it names in
an event.

This only bites where a player publishes more deployments than they can
afford, which the client already prevents. The route that reaches it is a
loaded player file or a hand-written order file — and for those, a rule
stated in the spec beats a rule that is whatever `yaml.safe_load` returned.

**Alternative rejected:** refusing all of a player's deployments for the turn
when the total is unaffordable. Simpler to state, but it turns one typo in a
player file into a player who deployed nothing, and the rejection messages
would name every unit rather than the ones that actually did not fit.

### The grammar needs an optional slot, not an optional word

`grammar.py` has `Optional`, but it wraps a fixed word — it exists for the
trailing `json` — and renders as `[json]`. `add player <number> [budget]`
needs an optional *slot*: something with a display name and a kind, that
renders as `[<budget>]` and that completion offers nothing for, because a
budget is a number the person chooses.

`Optional` is widened to wrap either a word or a `Slot`, `word_text` renders
whichever it holds, and `complete.py` offers candidates for an optional slot
the same way it does for a required one — which for the `NUMBER` kind is
nothing. One new shape in the grammar table, and `help` regenerates from it.

`parser._parse_add_player` moves off the exact `_arity(1, ...)` to accepting
one argument or two. The second, when present, is read with `_integer` so a
non-number is a parse error naming the budget, not a service-layer refusal.

### `AddPlayer` gains a defaulted field, so drafts still replay

`commands.AddPlayer` becomes `fields = ('number', 'budget')` with
`values.setdefault('budget', Player.DEFAULT_BUDGET)` in `__init__`, exactly
as `Show` does for `format`. A draft written before this change replays into
a default budget rather than raising "command add_player cannot be read back",
and the HTTP command endpoint carries the budget with no change of its own —
`as_record` and `from_record` walk `fields`.

### A stored record must carry a budget; a `load player` file need not

These look like the same YAML and are not. `players/<number>.yaml` written by
`write_player` is state the game produced; `tests/player_1.yaml` handed to
`load player` is configuration a person wrote.

A stored record with no budget means one of two things — a game set up under
another version, or a record edited by hand — and in both the game is about to
be played by rules it was not set up under. That is `UnreadableGame`, raised
by `_load_players` naming the player, and it lands in the same place
`player-numbering`'s out-of-range check already lands.

A configuration file with no budget means the author did not choose one, which
is what a default is for. `games.load_player` reads `budget` with the default
and validates it through the same `Player` construction the prompt goes
through.

### Storage carries it as a column, not as a blob

`write_player(number, types)` becomes `write_player(number, types, budget)` on
the port. The YAML backend writes `budget:` beside `number:` and `types:`; the
SQLite backend puts a `budget INTEGER NOT NULL` on `memberships`, which is the
table that is already one row per registered player.

An existing SQLite game has a `memberships` table without the column —
`ensure()` runs `CREATE TABLE IF NOT EXISTS`, so it is not added under it. The
read raises, and the raise is turned into the same `UnreadableGame` the YAML
side raises for a missing key. No migration: the decision on old games is that
they are not carried forward.

## Risks / Trade-offs

**Every existing saved game becomes unreadable.** That is the chosen
behaviour, not a side effect — the alternative was defaulting a missing budget
to 100 and playing a game by rules it was not set up under. `games/` is
gitignored, so nothing in the repository breaks; a developer with games on
disk deletes the directory. The test suite builds its games from scratch, so
no fixture needs a budget added, though one gets one to prove the round trip.

*Mitigation:* the error names the player and says the record has no budget, so
the cause is readable rather than a `KeyError` traceback.

**Charging by unit name will surprise somebody once.** A player file listing
its units in priority order gets them charged alphabetically instead. The
determinism invariant leaves no honest alternative — priority order is list
order, which is exactly what the invariant forbids a rule from depending on —
and the rejection messages name each unit that did not fit.

**A budget of 100 cannot afford the strongest type.** `attack 10 health 10
energy 100` costs 120. This is the mechanism working, not a bug: energy is
priced at par with attack and health, so a hundred points of energy costs a
hundred points. Whether par is the right weighting is a balance question this
change deliberately does not answer, and the per-player budget argument is the
lever for anyone who wants a game where it is affordable.

**Two enforcement points is two chances to diverge.** Bounded by both asking
`budget.refusal` and neither restating the arithmetic; a test asserts the
client's refusal and the turn's rejection reason are the same sentence for the
same overspend.

## Migration Plan

None for stored games: an old game is refused, by decision. In order:

1. `domain/` first — `cost`, `Player.budget`, `budget.py` — with tests, since
   everything below depends on the arithmetic and nothing yet calls it.
2. Storage next, both backends together, so a game written by one is readable
   by the other and the round-trip test can be written once.
3. Then the service layer: registration, the client refusal, the turn's
   rejection.
4. Then the CLI and HTTP surfaces, which are display and wire only.
5. Docs last, once the numbers in them are the numbers the code produces.

## Open Questions

None. The two that were open — how a budget is set, and what happens to games
saved before this change — were settled when the change was proposed: an
optional argument on `add player` defaulting to 100, and an old game is
refused rather than defaulted.
