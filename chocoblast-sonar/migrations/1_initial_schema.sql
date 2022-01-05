CREATE TABLE IF NOT EXISTS statistics (
    user_id INTEGER NOT NULL UNIQUE,
    chocoblasted INTEGER NOT NULL DEFAULT 0
);

PRAGMA user_version=1;