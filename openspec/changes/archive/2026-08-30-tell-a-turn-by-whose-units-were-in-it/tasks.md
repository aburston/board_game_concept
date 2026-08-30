## 1. Events say whose units they name

- [x] 1.1 Add `owners()` and `players_in()` to `domain/events.py` and verify
      the owners of several units come back sorted and deduplicated
- [x] 1.2 Put `players` on every event in `domain/board.py` that names a unit
      - deployed, moved, joined, engaged, refused, held, removed, rested,
      flag_fallen - and verify none of the sentences a person reads changed
- [x] 1.3 Put `players` on every event in `domain/unit.py` that names a unit -
      attacked, destroyed, retreated, collided, held, undecided - and verify
      an attack carries both players and a deployment one

## 2. The seat filter decides from it

- [x] 2.1 Change `turn_feed.for_seat` to take the seat's number and keep an
      entry where that number is among the players the entry carries, and
      verify the existing feed suite still passes
- [x] 2.2 Stop `service/turn.py` gathering unit names to pass in, and verify a
      resolved turn writes each seat the entries it is entitled to

## 3. The case it was all for

- [x] 3.1 Verify two players who both name a unit `scout` are each told only
      where their own was placed
- [x] 3.2 Verify a fight between two units of the same name reaches both
      players as their own half of it and no more
- [x] 3.3 Verify a default two-player game - which hands both seats the same
      fifteen names - leaves each seat reading fifteen entries and not thirty

## 4. Everything else still holds

- [x] 4.1 Verify the whole suite passes on the YAML and the SQLite backends
- [x] 4.2 Verify `openspec validate --specs --strict` passes
