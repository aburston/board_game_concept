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
CREATE TABLE IF NOT EXISTS memberships (
    player_number INTEGER PRIMARY KEY
        CHECK (player_number BETWEEN 1 AND 999)
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

-- the authoritative board. `type_attack`/`type_health`/`type_energy` are
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
    on_board      INTEGER NOT NULL
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

-- the combat log. Written on every resolution, read by nothing yet. `payload`
-- is JSON of the event detail.
CREATE TABLE IF NOT EXISTS turn_events (
    turn_no       INTEGER NOT NULL,
    seq           INTEGER NOT NULL,
    kind          TEXT NOT NULL,
    payload       TEXT NOT NULL,
    PRIMARY KEY (turn_no, seq)
);
