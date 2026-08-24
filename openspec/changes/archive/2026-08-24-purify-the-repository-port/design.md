## Context

See `proposal.md` — Why, and `put-a-rest-api-under-the-cli` — step 0b. What
shapes the change is what a SQLite backend has to be handed.

The four write callsites in `service/turn.py`:

```
   publish()  repository.write_orders(number,
                                      serialise_orders(board, player))     text
   resolve()  repository.write_units(serialise_units(board, turn=t))       text
   resolve()  repository.write_view(n, serialise_units(board, obj, turn))  text
   resolve()  repository.write_orders(n, _as_orders(player['units']))      text
```

Each hands the port a string built by a storage-module helper. To swap the
backend for SQLite, either the SQLite backend re-parses those strings or the
port takes something else. The port takes something else.

The FIFO transport is even clearer. `wake`/`waiter` are on the port today
because `YamlGameRepository` implements them; `notify.py`'s own docstring
says they wake "the other side of the file transport", which is not what a
storage port promises. Step 5 replaces them with long-poll. Between now and
then, they belong on a `Notifier` of their own.

## Goals / Non-Goals

**Goals:**
- The port takes data; the emitter that turns it into YAML lives behind the
  YAML backend.
- The bus is not on the port. `Game` gains a `notifier` alongside its
  `repository`; nothing outside the change has to be told about the split.
- The YAML backend produces byte-identical files. No game a user or a test
  opens changes shape.

**Non-Goals:**
- SQLite itself, HTTP, any behaviour change.
- Changing the emitter's hand-crafted YAML output. That is what makes this
  step byte-identical.
- Editing what any test *asserts*. Test edits are limited to how they express
  their inputs.

## Decisions

### 1. Documents are the port's payload; the shape is what the file already held

The three write methods take a dict `{board, turn, player, units}` — the same
shape `serialise_units` currently encodes as text. The read side is left as it
is (`read_units` returns just the units list; `read_view` and `read_orders`
return their parsed dicts): the writes gain symmetry with what the file holds,
which is what the SQLite backend needs, and the reads already return data.

Full symmetry (reads returning the same document shape as writes take) is
worth doing when the SQLite backend arrives — it can shape its return however
is cleanest. Doing it now costs a broader edit for no immediate gain, so the
scope is the writes.

### 2. `units_document` is the new construction; the YAML text is inside the
### YAML backend

`storage/serialise.py::units_document(board, player, in_play_only, turn) ->
dict` returns the document. `serialise_units`/`serialise_orders`/`_as_orders`
are gone from the service layer; the YAML emitter that turns a document into
today's hand-crafted YAML text moves into `yaml_repository.py`, called from
each write method.

*Why hand-crafted, still*: `yaml.safe_dump(document)` would produce
block-style YAML rather than the flow-style `- { id: 0, player: 1, ... }` the
files use today. Several tests read those files with `yaml.safe_load`; that
does not care about style, but they read exact keys and values, and other
tests use `read_text()` and pattern-match. Byte-identical is the honest
guarantee, and it costs a small helper.

### 3. `Notifier` is a small ABC; `Game` bridges compatibility

`storage/notify.py` gains:

```
   class Notifier(ABC):    wake(name)   waiter(name)
   class FifoNotifier:     the current wake/waiter over FIFOs
   class NullNotifier:     no-ops, for storage that carries no bus
```

`YamlGameRepository` still has `wake`/`waiter` methods — they use the FIFO
helpers `notify.py` already had — but they are not part of the
`GameRepository` contract any more. `Game.__init__(repository, player_number,
notifier=None)` takes an optional `Notifier`. When one is not passed, `Game`
derives it: if the repository has `wake`/`waiter` (the YAML case), a
`FifoNotifier` bound to its data path is used; otherwise a `NullNotifier`.
`service/turn.py` reads `game.notifier` and never `repository.wake`.

This bridge means every existing callsite — every test constructing
`Game(YamlGameRepository(...))`, every place in the code — keeps working with
no change. The split is real: the ABC no longer promises the bus; `Game`
knows how to find one anyway.

### 4. Tests get updated where they built text or called the emitter

Not what they assert; only how they express their inputs.

- `test_repository.py`: `write_units('units: None\n')` becomes
  `write_units({'units': None})` or `write_units(units_document(board=None))` —
  the empty document its string encoded.
- `test_storage_safety.py`: same. The two atomic-write tests care about read-
  through-write behaviour, not YAML strings; both work with documents.
- `test_turn_publication.py`: the recorder wrappers take documents rather
  than text, which changes their signatures but not what they record.
- `test_rules_defects.py`, `test_turn_events.py`, `test_combat_stalemate.py`,
  `test_board_conventions.py`: `serialise_units(board)` becomes
  `units_document(board)`; where the tests then round-tripped through
  `yaml.safe_load`, they can consume the document directly.

No test changes what it asserts.

## Risks / Trade-offs

- **The YAML backend has to keep emitting the hand-crafted format** →
  Decision 2 says so and the reason is byte-identical files. If a future
  change wants to move the format to `yaml.safe_dump`, it is a separate,
  visible change that opts into edited test expectations.

- **The `Game` bridge is a bit of magic** → the two-line inference "if the
  repository has wake and waiter, wrap it in a `FifoNotifier`" is exactly the
  price of not making every caller pass a notifier. It is documented, and it
  goes away when a caller opts to pass its own.

- **Symmetry is only on the writes** → the reads still return partial
  documents. Named as a trade-off in Decision 1: the SQLite backend does not
  need it to land now, and full symmetry deserves the read-side rework SQLite
  will bring anyway.

## Migration Plan

Within this change:

1. Add `units_document` to `serialise.py`; keep the existing string emitters
   there for one commit. Turn.py switches to documents; writes to the port
   still take text and the YAML backend still uses the string emitters, but
   internally.
2. Change the port and YAML backend signatures to take documents; the emitter
   moves into the YAML backend.
3. Update the tests that hand text or call `serialise_units` — the smallest
   possible per-file edits.
4. Split `Notifier` out. Add the ABC and `FifoNotifier`/`NullNotifier`; wire
   `Game` to bridge; move `turn.py`'s callsites off the repository.
5. Remove `wake`/`waiter` from `GameRepository` (the ABC). `YamlGameRepository`
   keeps its methods, no longer promised by the port.
6. Delete `serialise_units`/`serialise_orders`/`_as_orders` from the service
   surface if nothing else calls them.

## Open Questions

None.
