## Context

See `proposal.md` — Why. What shapes the approach is where the number is asked
about today.

`Game` tests the session's number in seven places, and every one of them asks
`== 0` or `!= 0` when what it means is one of three different questions:

| `game.py` | asks | means |
|---|---|---|
| `sees_everything = player_number == 0` | is it zero | may this session see the whole game |
| `new_game = player_number != 0` | is it zero | is this session one that joins a game rather than sets one up |
| `load`: `if self.player_number == 0` on a missing board | is it zero | may this session open a game that has no board yet |
| `getPlayerObj`: `if self.player_number == 0: return None` | is it zero | does this session own units |
| `NoSuchPlayer` unless `player_number != 0` | is it zero | must this number be a registered player |

Three questions wearing one test. Adding a second privileged number breaks every
one of them differently, which is why the answer is to ask the question rather
than to widen the test to `in (0, 1000)`.

There is also a precedent for where a numeric limit lives. `set_board_size`
does not check the board's maximum itself:

```python
try:
    # the board has its own limits beyond the minimum, and states them
    board = Board(command.size_x, command.size_y)
except AssertionError as e:
    raise GameError(str(e)) from e
```

The domain object states its own limits; the service turns the refusal into one
a caller can act on. Player numbering follows the same shape.

## Goals / Non-Goals

**Goals:**
- Three identities, distinguishable below the CLI, so a single caller-facing
  entry point could decide what a request may do from the identity alone.
- The numbering stated in one place, with each of the three questions above
  named for what it asks.
- An out-of-range number refused as a refusal, never as an escaping
  `AssertionError`.

**Non-Goals:**
- Accounts, credentials, sessions, tokens. The number is still the whole of
  identity; this only makes it say enough.
- Any change to what a player may see, to the commit barrier, or to the roles'
  command surfaces beyond the new refusals.
- Making the observer number configurable. 1000 is a constant, named once.

## Decisions

### 1. The range is the domain's; the reserved numbers are the service's

`domain/player.py` gains `Player.FIRST = 1` and `Player.LAST = 999`, and asserts
the range as it already asserts integer-and-non-negative. A `Player` is a player
of the game, so "1 to 999" is exactly its invariant, and it becomes impossible to
construct an out-of-range one anywhere — including from a loaded player file,
which is the path no service-layer check would cover on its own.

The reserved numbers are not players. `Player(0)` and `Player(1000)` must not
exist, so the administrator and the observer cannot be described by the domain
class at all. They belong a layer up, in a new `service/identity.py`:

```
   domain/player.py       Player.FIRST = 1, Player.LAST = 999   what a player number is
                                    │
                                    ▼   (imports the range; never restates it)
   service/identity.py    ADMINISTRATOR = 0
                          OBSERVER      = 1000
                          is_player(n) · sees_everything(n) · may_change(n)
```

*Why not put all of it in the domain*: the administrator and the observer are
roles a caller takes, not things the rules of the game know about. The engine
resolves turns for players; it has never heard of an administrator.

*Why not put all of it in the service*: a player number also arrives through
`load_player` from a file, and through `_load_players` reading a game off disk.
A service-layer check would have to be repeated at each, and the one that was
forgotten is the one that lets a bad number in.

### 2. Each `== 0` becomes the question it was standing for

```
   sees_everything = player_number == 0     →  identity.sees_everything(number)
   new_game        = player_number != 0     →  not identity.sees_everything(number)
   missing board   : player_number == 0     →  identity.sees_everything(number)
   getPlayerObj    : player_number == 0     →  not identity.is_player(...)
   NoSuchPlayer    : player_number != 0     →  identity.is_player(number)
```

The middle two matter more than they look. `new_game` gates deployment and
movement, and an observer for which it flipped to `True` would be a session the
rules considered mid-setup. The missing-board branch is what lets the observer
open a game that has no board and be told `must create board - set size and
commit`, rather than being refused with `NoSuchGame` — behaviour
`game-observer` already has a scenario for.

### 3. 1000 is reserved, not registered

The observer is never in `game.players`. That is what keeps this change small:
`_awaited_players`, `eliminated_players`, `decide` and `committed_players` all
walk the registered players, and none of them needs to learn about an identity
that is never in the list. The commit barrier cannot wait for the observer
because the observer is not something it can see.

It also means no stored file ever names 1000, so there is nothing to migrate.

### 4. The observer is refused at the service layer, not only by its grammar

`games.perform` refuses a command from an identity that may not change the game.
Today `cli/roles.py` is the only thing stopping the observer writing, and it
stops it by not offering the commands — which is enough for a REPL and nothing
at all for a caller that does not go through one.

This is deliberately not "only players may change a game": the administrator
drafts and commits setup, and must keep doing so. The rule is that the observer
may not, which `identity.may_change` states.

### 5. An out-of-range number is a refusal wherever it arrives

Three doors, one answer at each:

| arrives via | today | after |
|---|---|---|
| `add player -1` | `AssertionError` kills the session | `GameError`, reported at the prompt |
| `load player` naming a bad number | `AssertionError` kills the session | `GameError`, reported at the prompt |
| a game on disk holding a bad number | `AssertionError` kills the session | `GameDataError`, reported and the session exits |

The first two follow `set_board_size`'s pattern exactly. The third is different
in kind: a game that cannot be read is not a command that can be refused, so it
raises the error `load` already raises for a game it cannot make sense of, and
the session ends the way it already ends for one.

### 6. The client checks its argument before opening a session

`bgcclient <gameno> <player_number>` already refuses a non-integer with usage
and exit 1. A number outside 1 to 999 joins it. Checking before the session is
opened means a caller is told they cannot be that player, rather than being
opened as one and refused by every subsequent command.

## Risks / Trade-offs

- **A game whose player list holds 0 or a number above 999 stops loading** →
  no game made by the shipped commands can hold one, because a player number
  has only ever come from `add player` or `load player`. A hand-written file
  can, and its owner is told which number is wrong rather than shown a
  traceback. This is the change's one breaking edge and it is stated in the
  proposal.

- **`identity.py` is a service module the CLI also needs** → `bgcobserver` and
  `bgcclient` both import it, which is the layering already in use (`cli/`
  imports `service/` throughout). It is not a new direction of dependency.

- **Two constants could drift from the specs** → the numbers appear once in
  code and once in `player-numbering`, and the tests assert the boundaries
  (0, 1, 999, 1000) rather than the middle, so a change to either without the
  other fails.

- **`may_change` is a second gate over `roles.py`** → they can disagree, and if
  they do the service layer wins and the CLI reports a refusal for a command it
  offered. The observer's role table offers no writing command at all, so the
  two can only disagree if someone adds one, which is when a disagreement is
  worth having.

## Migration Plan

No data migration: nothing on disk names the observer, and no game made by the
commands holds an out-of-range player. A game in progress keeps playing across
the change, and the observer picks up its new number with no file changing.

Order of work:

1. `Player` gains the range; `service/identity.py` names the reserved numbers
   and the three questions. Nothing calls the questions yet.
2. The seven tests in `game.py` become those questions. Behaviour unchanged,
   because the observer is still launched as 0 at this point.
3. `add_player` and `load_player` convert the assertion into a refusal; `load`
   converts it into a game that cannot be read.
4. `bgcobserver` is launched as `OBSERVER`, and `bgcclient` checks its argument.
   This is the step that changes what anyone can observe.
5. `perform` refuses a command from an identity that may not change the game.

Step 2 is separately revertable and should be green on its own. Step 4 is the
one to review hardest.

## Open Questions

None. The one the proposal left open — whether the range belongs to the domain
or the service — is settled by Decision 1, and the reason it was open (that both
were defensible) is answered by the loaded-file path, which only the domain
placement covers.
