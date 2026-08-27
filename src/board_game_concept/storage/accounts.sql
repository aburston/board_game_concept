-- The account store's schema: who plays, which seats they hold, and which
-- tokens are currently accepted.
--
-- This is the only state in the project that is not scoped to one game. A
-- person outlives every game they play in, so they cannot live inside one.
-- `games/_<gameno>/` is untouched by everything here.

PRAGMA foreign_keys = ON;

-- one row per person or program that plays. `username_key` is the form names
-- are compared by - case-folded - so that `Admin` cannot be registered
-- alongside `admin`; `username` keeps the case that was typed
CREATE TABLE IF NOT EXISTS accounts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL,
    username_key  TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    kind          TEXT NOT NULL,
    must_change   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

-- which account holds which seat of which game. The administrator and the
-- observer are NOT here: they are player 0 and 1000 of every game implicitly,
-- because they are roles a caller takes rather than seats a game holds.
--
-- PRIMARY KEY (gameno, number) makes a seat have one holder, which is what
-- stops two people ordering one army. There is deliberately NO unique
-- constraint on (gameno, account_id): one account may hold several seats in
-- one game, so that one person can play both sides to learn the game. That is
-- also why the seat stays in the request path - an account no longer
-- determines which number it is acting as.
CREATE TABLE IF NOT EXISTS memberships (
    gameno      TEXT NOT NULL,
    number      INTEGER NOT NULL,
    account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    claimed_at  TEXT NOT NULL,
    PRIMARY KEY (gameno, number)
);

CREATE INDEX IF NOT EXISTS memberships_by_account
    ON memberships (account_id);

-- one row per token that is currently accepted. A login token and a token
-- minted for a program are the same row: the second carries a label and a
-- distant expiry. One table, one verification path, two ways of carrying it.
--
-- Rows rather than a signed cookie, so that ending a session actually revokes
-- it - which matters more than usual here, because the observer password is
-- shared and "sign everyone out" is the only lever after it leaks.
CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT PRIMARY KEY,
    account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    label       TEXT,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_by_account
    ON sessions (account_id);
