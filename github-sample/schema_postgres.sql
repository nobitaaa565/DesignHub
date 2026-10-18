-- ============================================================================
-- DesignHub Cloud PostgreSQL Database Schema
-- Master Copy for Render / Supabase / Neon Cloud Deployment
-- ============================================================================

-- 1. Subscriptions Table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT DEFAULT '',
    package TEXT NOT NULL,                  -- '1 Month', '3 Months', '6 Months', '12 Months'
    days INTEGER DEFAULT 30,               -- Duration in days (30, 90, 180, 365)
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    payment_status TEXT DEFAULT 'PENDING',  -- 'PAID', 'PENDING', 'REVOKED'
    status TEXT DEFAULT 'active',          -- 'active', 'kicked', 'expired', 'pending'
    notes TEXT DEFAULT '',
    trx_id TEXT DEFAULT '',
    customer_id INTEGER,                   -- Starts from #800
    fb_sender_id TEXT DEFAULT '',
    last_reminder_at TIMESTAMP,
    pending_telegram_msg_id INTEGER,
    team_name TEXT DEFAULT 'Carmella Elan'
);

CREATE INDEX IF NOT EXISTS idx_subs_email ON subscriptions (email);
CREATE INDEX IF NOT EXISTS idx_subs_team ON subscriptions (team_name);
CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions (status);
CREATE INDEX IF NOT EXISTS idx_subs_payment_status ON subscriptions (payment_status);

-- 2. Payments Table (Revenue & Transactions Ledger)
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    email TEXT NOT NULL,
    name TEXT DEFAULT '',
    package TEXT NOT NULL,                  -- '1 Month', '3 Months', '6 Months', '12 Months'
    amount DOUBLE PRECISION NOT NULL,       -- Strictly 25, 50, or 99 BDT
    currency TEXT DEFAULT 'BDT',
    provider TEXT DEFAULT 'bKash',          -- 'bKash', 'Nagad', 'Rocket', 'Bank Transfer', 'Other'
    trx_id TEXT DEFAULT '',
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT DEFAULT '',
    team_name TEXT DEFAULT 'Carmella Elan'
);

CREATE INDEX IF NOT EXISTS idx_payments_email ON payments (email);
CREATE INDEX IF NOT EXISTS idx_payments_paid_at ON payments (paid_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_team ON payments (team_name);

-- 3. Canva Teams Roster Table
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Application Settings Key-Value Table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- 5. Expiring Access Tokens Table
CREATE TABLE IF NOT EXISTS consumed_tokens (
    token TEXT PRIMARY KEY,
    email TEXT,
    consumed_at TEXT,
    access_count INTEGER DEFAULT 1
);

-- Default Seed Data
INSERT INTO teams (name) VALUES ('Carmella Elan') ON CONFLICT (name) DO NOTHING;
INSERT INTO teams (name) VALUES ('Pro Team 2') ON CONFLICT (name) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('canva_team_name', 'Carmella Elan') ON CONFLICT (key) DO NOTHING;
