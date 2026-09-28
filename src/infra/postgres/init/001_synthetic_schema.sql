CREATE TABLE IF NOT EXISTS synthetic_seed_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO synthetic_seed_metadata(key, value)
VALUES ('data_scope', 'synthetic_only_no_merchant_connection')
ON CONFLICT (key) DO NOTHING;
