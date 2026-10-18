-- ============================================================================
-- DesignHub Local SQLite Database Schema
-- Master Copy for Local Development & SQLite Fallback
-- ============================================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT DEFAULT '',
    package TEXT NOT NULL,
    days INTEGER DEFAULT 30,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    payment_status TEXT DEFAULT 'PENDING',
    status TEXT DEFAULT 'active',
    notes TEXT DEFAULT '',
    trx_id TEXT DEFAULT '',
    customer_id INTEGER,
    fb_sender_id TEXT DEFAULT '',
    last_reminder_at TIMESTAMP,
    pending_telegram_msg_id INTEGER,
    team_name TEXT DEFAULT 'Carmella Elan',
    reference_name TEXT DEFAULT 'Page Lead'
);

CREATE INDEX IF NOT EXISTS idx_subs_email ON subscriptions (email);
CREATE INDEX IF NOT EXISTS idx_subs_team ON subscriptions (team_name);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    email TEXT NOT NULL,
    name TEXT DEFAULT '',
    package TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'BDT',
    provider TEXT DEFAULT 'bKash',
    trx_id TEXT DEFAULT '',
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT DEFAULT '',
    team_name TEXT DEFAULT 'Carmella Elan'
);

CREATE INDEX IF NOT EXISTS idx_payments_email ON payments (email);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS consumed_tokens (
    token TEXT PRIMARY KEY,
    email TEXT,
    consumed_at TEXT,
    access_count INTEGER DEFAULT 1
);

INSERT OR IGNORE INTO teams (name) VALUES ('Carmella Elan');
INSERT OR IGNORE INTO teams (name) VALUES ('Pro Team 2');
INSERT OR IGNORE INTO settings (key, value) VALUES ('canva_team_name', 'Carmella Elan');
