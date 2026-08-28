-- The SQLite schema for a game.
--
-- One file per game, one game per file. Tables map nearly one-to-one to the
-- YAML files the file-per-directory backend held; `sightings` and
-- `turn_events` are the two the schema adds. Everything else is what
-- `data/*.yaml` and `players/*.yaml` were, expressed as rows.

PRAGMA foreign_keys = ON;

-- one game per file. `id = 1` is the sentinel row that always exists once
-- `ensure()` has run; `size_x` and `size_y` are NULL until the board is set.
CREATE TABLE IF NOT EXISTS games (
    id           INTEGER PRIMARY KEY CHECK (id = 1),
    size_x       INTEGER,
    size_y       INTEGER,
    turn_no      INTEGER NOT NULL DEFAULT 0,
    outcome      TEXT
);

-- progress splits: `turn_no` and `outcome` are one row on `games`;
-- `eliminated` is a list and is its own table, one row per eliminated player.
CREATE TABLE IF NOT EXISTS eliminated (
    player_number INTEGER PRIMARY KEY
);

-- registered players. 0 (admin) and 1000 (observer) are sessions rather than
-- seats, so they are not memberships.
-- `budget` is the point budget the player was registered with, and is NOT
-- NULL because a game set up without one is a game played by rules it was not
-- set up under. An older database whose `memberships` has no such column is
-- not migrated: `CREATE TABLE IF NOT EXISTS` will not add it, and the read
-- that fails is turned into the same refusal the YAML backend gives.
CREATE TABLE IF NOT EXISTS memberships (
    player_number INTEGER PRIMARY KEY
        CHECK (player_number BETWEEN 1 AND 999),
    budget        INTEGER NOT NULL
        CHECK (budget BETWEEN 1 AND 1000)
);

-- each player designs their own types; the (player, name) pair is the key.
CREATE TABLE IF NOT EXISTS unit_types (
    player_number INTEGER NOT NULL,
    name          TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    attack        INTEGER NOT NULL,
    health        INTEGER NOT NULL,
    energy        INTEGER NOT NULL,
    PRIMARY KEY (player_number, name)
);

-- the authoritative board. `flag` is whether the unit carries its player's
-- flag. `type_attack`/`type_health`/`type_energy` are
-- the design of the type at the time the unit was made; they are how a
-- type learned by contact is the type as its owner built it.
CREATE TABLE IF NOT EXISTS units (
    id            INTEGER PRIMARY KEY,
    owner         INTEGER NOT NULL,
    name          TEXT NOT NULL,
    type_name     TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    attack        INTEGER NOT NULL,
    health        INTEGER NOT NULL,
    energy        INTEGER NOT NULL,
    type_attack   INTEGER NOT NULL,
    type_health   INTEGER NOT NULL,
    type_energy   INTEGER NOT NULL,
    x             INTEGER NOT NULL,
    y             INTEGER NOT NULL,
    state         INTEGER NOT NULL,
    direction     INTEGER NOT NULL,
    destroyed     INTEGER NOT NULL,
    on_board      INTEGER NOT NULL,
    flag          INTEGER NOT NULL
);

-- one player's orders for the open turn. Present rows mean "not consumed
-- yet"; `clear_orders` deletes them.
CREATE TABLE IF NOT EXISTS orders (
    player_number INTEGER NOT NULL,
    id            INTEGER NOT NULL,
    owner         INTEGER,
    name          TEXT,
    type_name     TEXT,
    symbol        TEXT,
    attack        INTEGER,
    health        INTEGER,
    energy        INTEGER,
    type_attack   INTEGER,
    type_health   INTEGER,
    type_energy   INTEGER,
    x             INTEGER,
    y             INTEGER,
    state         INTEGER,
    direction     INTEGER,
    destroyed     INTEGER,
    on_board      INTEGER,
    flag          INTEGER NOT NULL,
    PRIMARY KEY (player_number, id)
);

-- the barrier record. `turn_no` NULL means "committed at some point but
-- not for a turn in particular", which is the state a marker written
-- before commits recorded a turn was in.
CREATE TABLE IF NOT EXISTS commits (
    player_number INTEGER PRIMARY KEY,
    turn_no       INTEGER
);

-- a session's uncommitted work. `commands` is JSON.
CREATE TABLE IF NOT EXISTS drafts (
    player_number INTEGER PRIMARY KEY,
    turn_no       INTEGER NOT NULL,
    commands      TEXT NOT NULL
);

-- refused orders. Written every turn, so the row set describes the turn
-- just resolved rather than accumulating stale refusals.
CREATE TABLE IF NOT EXISTS rejections (
    player_number INTEGER NOT NULL,
    turn_no       INTEGER NOT NULL,
    unit          TEXT,
    type_name     TEXT,
    x             INTEGER,
    y             INTEGER,
    reason        TEXT
);

-- who has seen what. Populated whenever `write_view(number, document)` is
-- called: each unit in the document becomes a sighting for that viewer.
-- Cleared and rewritten per resolution, the way the view file was.
CREATE TABLE IF NOT EXISTS sightings (
    viewer        INTEGER NOT NULL,
    seen_unit_id  INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    PRIMARY KEY (viewer, seen_unit_id)
);

-- the combat log: the whole of what each resolution did, which is what a
-- session entitled to the whole game reads. `payload` is JSON of the event
-- detail; the wording a person reads is the domain's, worked out from the
-- kind and the detail when it is read back, so it lives in one place and an
-- old row says whatever the domain says today.
CREATE TABLE IF NOT EXISTS turn_events (
    turn_no       INTEGER NOT NULL,
    seq           INTEGER NOT NULL,
    kind          TEXT NOT NULL,
    payload       TEXT NOT NULL,
    PRIMARY KEY (turn_no, seq)
);

-- where each player's flag is, published for every player to read whatever
-- their visibility. The square and the owner and nothing else: what unit
-- carries it, and what that unit is, reach a player through their own view.
-- `standing` is 0 once the carrier has been destroyed, and the square is then
-- NULL rather than the square it fell on.
CREATE TABLE IF NOT EXISTS flags (
    player_number INTEGER PRIMARY KEY,
    x             INTEGER,
    y             INTEGER,
    standing      INTEGER NOT NULL DEFAULT 1
);

-- the designs a seat has met. `sightings` lasts one turn, because where a
-- unit is now is not something a player may remember; what a type was built
-- with is, and this is where that is kept. No coordinates here, deliberately.
CREATE TABLE IF NOT EXISTS known_types (
    player_number INTEGER NOT NULL,
    owner         INTEGER NOT NULL,
    name          TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    attack        INTEGER NOT NULL,
    health        INTEGER NOT NULL,
    energy        INTEGER NOT NULL,
    first_seen    INTEGER,
    last_seen     INTEGER,
    PRIMARY KEY (player_number, owner, name)
);

-- what each seat was told about each turn: the part of the log above that
-- seat could see while it was happening. Decided at resolution because a
-- sighting lasts one turn - filtering the log at read time would answer with
-- today's visibility for a fight that happened a week ago.
CREATE TABLE IF NOT EXISTS player_events (
    player_number INTEGER NOT NULL,
    turn_no       INTEGER NOT NULL,
    seq           INTEGER NOT NULL,
    kind          TEXT NOT NULL,
    payload       TEXT NOT NULL,
    PRIMARY KEY (player_number, turn_no, seq)
);
