CREATE TABLE IF NOT EXISTS sessions (
    thread_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
    idempotency_key TEXT PRIMARY KEY,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metrics (
    name TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0
);
