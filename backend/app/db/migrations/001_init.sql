PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    revision INTEGER NOT NULL CHECK (revision >= 0),
    stage TEXT NOT NULL,
    state_json TEXT,
    created_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processed_messages (
    conversation_id TEXT NOT NULL,
    client_message_id TEXT NOT NULL,
    base_revision INTEGER NOT NULL,
    result_state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (conversation_id, client_message_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);

INSERT OR IGNORE INTO schema_migrations(version, applied_at)
VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));
