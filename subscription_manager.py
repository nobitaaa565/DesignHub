import os
import time
#!/usr/bin/env python3
"""
Subscription Manager Module for Design Hub Bot
Handles:
- Subscriber Database (SQLite)
- /add, /paid, /kick, /extend, /subs, /check commands
- 1-Tap Inline Button actions (Confirm Paid, Manual Kick, Period Extension)
- Expiry and Payment Status Tracking
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

DB_FILE = Path(__file__).resolve().parent / "subscriptions.db"
logger = logging.getLogger("SubscriptionManager")

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None

RAW_DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if RAW_DATABASE_URL.startswith("postgres://"):
    RAW_DATABASE_URL = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1)

DATABASE_URL = RAW_DATABASE_URL if RAW_DATABASE_URL else None
IS_POSTGRES = bool(DATABASE_URL and psycopg2)

if IS_POSTGRES:
    logger.info("🐘 Using Cloud PostgreSQL database via DATABASE_URL.")
elif DATABASE_URL and not psycopg2:
    logger.warning("⚠️ DATABASE_URL is set but psycopg2 is not installed. Falling back to local SQLite.")
else:
    logger.info(f"💾 Using local SQLite database: {DB_FILE}")


class DBCursor:
    def __init__(self, raw_cursor, is_postgres=False):
        self.cursor = raw_cursor
        self.is_postgres = is_postgres
        self._lastrowid = None

    def execute(self, query, params=None):
        if self.is_postgres:
            sql = query.replace("?", "%s")
            
            # Auto-handle lastrowid for PostgreSQL on INSERT INTO payments
            if sql.strip().upper().startswith("INSERT INTO PAYMENTS") and "RETURNING" not in sql.upper():
                sql = sql.rstrip("; ") + " RETURNING id"
                if params is None:
                    self.cursor.execute(sql)
                else:
                    self.cursor.execute(sql, params)
                res = self.cursor.fetchone()
                self._lastrowid = res[0] if res else None
                return

            if params is None:
                return self.cursor.execute(sql)
            return self.cursor.execute(sql, params)
        else:
            if params is None:
                return self.cursor.execute(query)
            return self.cursor.execute(query, params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchmany(self, size):
        return self.cursor.fetchmany(size)

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def lastrowid(self):
        if self.is_postgres:
            return self._lastrowid
        return getattr(self.cursor, "lastrowid", None)


class DBConnection:
    def __init__(self, raw_conn, is_postgres=False):
        self.raw_conn = raw_conn
        self.is_postgres = is_postgres

    def cursor(self):
        return DBCursor(self.raw_conn.cursor(), self.is_postgres)

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        self.raw_conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db():
    global IS_POSTGRES, DATABASE_URL
    raw_url = os.environ.get("DATABASE_URL", "").strip()
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    if raw_url:
        DATABASE_URL = raw_url
        if psycopg2:
            IS_POSTGRES = True

    if IS_POSTGRES:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return DBConnection(conn, is_postgres=True)
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}. Falling back to SQLite.")
            conn = sqlite3.connect(DB_FILE)
            return DBConnection(conn, is_postgres=False)
    else:
        conn = sqlite3.connect(DB_FILE)
        return DBConnection(conn, is_postgres=False)


def init_db():
    with get_db() as conn:
        c = conn.cursor()
        if conn.is_postgres:
            c.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id SERIAL PRIMARY KEY,
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
                    team_name TEXT DEFAULT 'Carmella Elan'
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    customer_id INTEGER,
                    email TEXT NOT NULL,
                    name TEXT DEFAULT '',
                    package TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    currency TEXT DEFAULT 'BDT',
                    provider TEXT DEFAULT 'bKash',
                    trx_id TEXT DEFAULT '',
                    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT DEFAULT '',
                    team_name TEXT DEFAULT 'Carmella Elan'
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS consumed_tokens (
                    token TEXT PRIMARY KEY,
                    email TEXT,
                    consumed_at TEXT,
                    access_count INTEGER DEFAULT 1
                );
            """)
            c.execute("INSERT INTO teams (name) VALUES (?) ON CONFLICT (name) DO NOTHING", ('Carmella Elan',))
            c.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT (key) DO NOTHING", ('canva_team_name', 'Carmella Elan'))
            return

        c.execute("""
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
                notes TEXT DEFAULT ''
            )
        """)
        # Ensure all columns exist in subscriptions
        c.execute("PRAGMA table_info(subscriptions)")
        cols = [col[1] for col in c.fetchall()]
        if "name" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN name TEXT DEFAULT ''")
        if "days" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN days INTEGER DEFAULT 30")
        if "trx_id" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN trx_id TEXT DEFAULT ''")
        if "customer_id" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN customer_id INTEGER")
        if "fb_sender_id" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN fb_sender_id TEXT DEFAULT ''")
        if "last_reminder_at" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN last_reminder_at TIMESTAMP")
        if "pending_telegram_msg_id" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN pending_telegram_msg_id INTEGER")

        # Ensure team_name column in subscriptions
        c.execute("PRAGMA table_info(subscriptions)")
        sub_cols = [col[1] for col in c.fetchall()]
        if "team_name" not in sub_cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN team_name TEXT DEFAULT 'Carmella Elan'")
        c.execute("UPDATE subscriptions SET team_name = 'Carmella Elan' WHERE team_name IS NULL OR team_name = ''")

        # Payments table for revenue tracking & ledger
        c.execute("""
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
            )
        """)
        c.execute("PRAGMA table_info(payments)")
        pay_cols = [col[1] for col in c.fetchall()]
        if "team_name" not in pay_cols:
            c.execute("ALTER TABLE payments ADD COLUMN team_name TEXT DEFAULT 'Carmella Elan'")
        c.execute("UPDATE payments SET team_name = 'Carmella Elan' WHERE team_name IS NULL OR team_name = ''")

        # Teams table
        c.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("INSERT OR IGNORE INTO teams (name) VALUES ('Carmella Elan')")

        # Settings table for active team name and system config
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        c.execute("INSERT INTO settings (key, value) VALUES ('canva_team_name', 'Carmella Elan') ON CONFLICT (key) DO NOTHING")

        # Backfill any subscriber with missing or low customer_id (< 800)
        c.execute("SELECT id FROM subscriptions WHERE customer_id IS NULL OR customer_id < 800 ORDER BY id ASC")
        unassigned = c.fetchall()
        if unassigned:
            c.execute("SELECT MAX(customer_id) FROM subscriptions WHERE customer_id >= 800")
            max_row = c.fetchone()
            curr = 800 if (not max_row or max_row[0] is None) else (max_row[0] + 1)
            for (row_id,) in unassigned:
                c.execute("UPDATE subscriptions SET customer_id = ? WHERE id = ?", (curr, row_id))
                curr += 1

        # Backfill initial payment records for already PAID subscriptions if payments table is empty
        c.execute("SELECT COUNT(*) FROM payments")
        pay_count = c.fetchone()[0]
        if pay_count == 0:
            c.execute("SELECT email, name, package, customer_id, trx_id, added_at FROM subscriptions WHERE payment_status = 'PAID'")
            paid_subs = c.fetchall()
            for p_email, p_name, p_pkg, p_cid, p_trx, p_date in paid_subs:
                _, _, p_price = parse_package(p_pkg or "1m")
                c.execute("""
                    INSERT INTO payments (customer_id, email, name, package, amount, currency, provider, trx_id, paid_at, notes)
                    VALUES (?, ?, ?, ?, ?, 'BDT', 'bKash', ?, ?, 'Initial Enrollment')
                """, (p_cid or 800, p_email, p_name or "Subscriber", p_pkg or "1 Month", float(p_price), p_trx or "VERIFIED", p_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()


def resolve_email(identifier: str) -> str:
    """Helper that returns the subscriber email given an email or customer_id (e.g. 800, #800)."""
    raw = str(identifier).strip()
    clean = raw.lstrip("#").strip()
    if clean.isdigit():
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT email FROM subscriptions WHERE customer_id = ?", (int(clean),))
            row = c.fetchone()
            if row:
                return row[0]
    return raw.lower()


def get_customer_id_by_sender(sender_id: str = "", sender_name: str = "", email: str = "") -> int:
    """
    Returns the clean short customer_id (e.g. 800, 801, 802...) for a given sender or email.
    If not already in DB, assigns the next sequential customer_id starting from 800.
    """
    init_db()
    clean_email = email.lower().strip() if email else ""
    clean_sender = str(sender_id).strip() if sender_id else ""

    with get_db() as conn:
        c = conn.cursor()
        # 1. By email
        if clean_email:
            c.execute("SELECT customer_id FROM subscriptions WHERE email = ? AND customer_id >= 800", (clean_email,))
            row = c.fetchone()
            if row and row[0]:
                if clean_sender:
                    c.execute("UPDATE subscriptions SET fb_sender_id = ? WHERE email = ? AND (fb_sender_id IS NULL OR fb_sender_id = '')", (clean_sender, clean_email))
                    conn.commit()
                return row[0]

        # 2. By fb_sender_id
        if clean_sender:
            c.execute("SELECT customer_id FROM subscriptions WHERE fb_sender_id = ? AND customer_id >= 800", (clean_sender,))
            row = c.fetchone()
            if row and row[0]:
                return row[0]

        # 3. Next sequential ID starting at 800
        c.execute("SELECT MAX(customer_id) FROM subscriptions WHERE customer_id >= 800")
        max_row = c.fetchone()
        next_id = 800 if (not max_row or max_row[0] is None) else (max_row[0] + 1)

        if clean_email:
            c.execute("UPDATE subscriptions SET customer_id = ?, fb_sender_id = ? WHERE email = ?", (next_id, clean_sender, clean_email))
            conn.commit()

        return next_id


def parse_package(pkg: str):
    p = str(pkg).lower().strip()
    if any(k in p for k in ("12m", "1y", "1year", "12 month", "12 months", "1 year", "১২")):
        return "12 Months", 365, 150
    elif any(k in p for k in ("3m", "3mo", "3month", "3 months", "3 month", "৩")):
        return "3 Months", 90, 50
    return "1 Month", 30, 25


def get_all_teams() -> list:
    """Returns a list of all distinct Canva teams."""
    init_db()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM teams ORDER BY name ASC")
        db_teams = [r[0].strip() for r in c.fetchall() if r[0] and r[0].strip()]
        
        # Include any distinct team_name from subscriptions and payments
        c.execute("SELECT DISTINCT team_name FROM subscriptions WHERE team_name IS NOT NULL AND team_name != ''")
        for r in c.fetchall():
            t = r[0].strip()
            if t and t not in db_teams:
                db_teams.append(t)
                
        c.execute("SELECT DISTINCT team_name FROM payments WHERE team_name IS NOT NULL AND team_name != ''")
        for r in c.fetchall():
            t = r[0].strip()
            if t and t not in db_teams:
                db_teams.append(t)
                
        if not db_teams:
            db_teams = ["Carmella Elan"]
        return sorted(list(set(db_teams)))


def add_team(name: str) -> str:
    """Adds a new Canva Team name to the database."""
    init_db()
    clean_name = str(name).strip()
    if not clean_name:
        return "Carmella Elan"
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO teams (name) VALUES (?)", (clean_name,))
        conn.commit()
    return clean_name


def delete_team(name: str) -> bool:
    """Deletes a Canva Team name from the teams table."""
    init_db()
    clean_name = str(name).strip()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM teams WHERE name = ?", (clean_name,))
        conn.commit()
        return c.rowcount > 0


def add_subscriber(email: str, package: str = "1m", name: str = "", fb_sender_id: str = "", team_name: str = None) -> dict:
    init_db()
    pkg_name, days, price = parse_package(package)
    now = datetime.now()
    exp = now + timedelta(days=days)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    exp_str = exp.strftime("%Y-%m-%d %H:%M:%S")
    clean_email = email.lower().strip()
    clean_sender = str(fb_sender_id).strip() if fb_sender_id else ""
    assigned_team = (team_name or get_canva_team_name() or "Carmella Elan").strip()
    add_team(assigned_team)

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT customer_id, fb_sender_id, team_name FROM subscriptions WHERE email = ?", (clean_email,))
        existing = c.fetchone()
        if existing and existing[0]:
            assigned_id = existing[0]
            existing_sender = existing[1] or ""
            sender_to_save = clean_sender or existing_sender
            final_team = assigned_team if team_name else (existing[2] or assigned_team)
        else:
            c.execute("SELECT MAX(customer_id) FROM subscriptions WHERE customer_id >= 800")
            max_row = c.fetchone()
            assigned_id = 800 if (not max_row or max_row[0] is None) else (max_row[0] + 1)
            sender_to_save = clean_sender
            final_team = assigned_team

        c.execute("""
            INSERT INTO subscriptions (email, name, package, days, added_at, expires_at, payment_status, status, customer_id, fb_sender_id, team_name)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING', 'active', ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                package=excluded.package,
                days=excluded.days,
                added_at=excluded.added_at,
                expires_at=excluded.expires_at,
                payment_status='PENDING',
                status='active',
                customer_id=COALESCE(subscriptions.customer_id, excluded.customer_id),
                fb_sender_id=CASE WHEN excluded.fb_sender_id != '' THEN excluded.fb_sender_id ELSE subscriptions.fb_sender_id END,
                team_name=COALESCE(excluded.team_name, subscriptions.team_name)
        """, (clean_email, name.strip(), pkg_name, days, now_str, exp_str, assigned_id, sender_to_save, final_team))
        conn.commit()

    return {
        "customer_id": assigned_id,
        "email": clean_email,
        "name": name.strip(),
        "package": pkg_name,
        "days": days,
        "price": price,
        "expires_at": exp_str,
        "payment_status": "PENDING",
        "status": "active",
        "fb_sender_id": sender_to_save,
        "team_name": final_team
    }


def record_payment(
    identifier: str,
    amount: float = None,
    provider: str = "bKash",
    trx_id: str = "",
    package: str = None,
    notes: str = "",
    team_name: str = None
) -> dict:
    """Records a verified payment into the revenue ledger table."""
    init_db()
    clean_email = resolve_email(identifier)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT customer_id, name, package, trx_id, team_name FROM subscriptions WHERE email = ?", (clean_email,))
        row = c.fetchone()
        cid = 800
        name = "Customer"
        pkg_name = "1 Month"
        saved_trx = ""
        sub_team = "Carmella Elan"
        if row:
            cid = row[0] or 800
            name = row[1] or "Customer"
            pkg_name = row[2] or "1 Month"
            saved_trx = row[3] or ""
            sub_team = row[4] or "Carmella Elan"

        final_team = (team_name or sub_team or get_canva_team_name() or "Carmella Elan").strip()
        add_team(final_team)

        if package:
            pkg_name, _, resolved_price = parse_package(package)
        else:
            _, _, resolved_price = parse_package(pkg_name)

        final_amount = float(amount) if (amount is not None and float(amount) > 0) else float(resolved_price)
        final_trx = (trx_id or saved_trx or "VERIFIED").strip()
        final_provider = (provider or "bKash").strip()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""
            INSERT INTO payments (customer_id, email, name, package, amount, currency, provider, trx_id, paid_at, notes, team_name)
            VALUES (?, ?, ?, ?, ?, 'BDT', ?, ?, ?, ?, ?)
        """, (cid, clean_email, name, pkg_name, final_amount, final_provider, final_trx, now_str, notes, final_team))
        pay_id = c.lastrowid
        conn.commit()

        return {
            "id": pay_id,
            "customer_id": cid,
            "email": clean_email,
            "name": name,
            "package": pkg_name,
            "amount": final_amount,
            "provider": final_provider,
            "trx_id": final_trx,
            "paid_at": now_str,
            "notes": notes,
            "team_name": final_team
        }


def update_payment(payment_id: int, fields: dict) -> dict:
    """Updates an existing payment transaction in the ledger."""
    init_db()
    allowed_fields = [
        "amount", "provider", "trx_id", "package", 
        "team_name", "paid_at", "notes", "email", "name"
    ]
    updates = {}
    for k, v in fields.items():
        if k in allowed_fields and v is not None:
            if k == "amount":
                try:
                    updates[k] = float(v)
                except Exception:
                    pass
            else:
                updates[k] = v.strip() if isinstance(v, str) else v

    if not updates:
        return None

    if "team_name" in updates and updates["team_name"]:
        add_team(updates["team_name"])

    set_clauses = [f"{k} = ?" for k in updates.keys()]
    values = list(updates.values())
    values.append(int(payment_id))

    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"UPDATE payments SET {', '.join(set_clauses)} WHERE id = ?", tuple(values))
        conn.commit()
        
        c.execute("SELECT id, customer_id, email, name, package, amount, currency, provider, trx_id, paid_at, notes, team_name FROM payments WHERE id = ?", (int(payment_id),))
        r = c.fetchone()
        if r:
            return {
                "id": r[0],
                "customer_id": r[1] or 800,
                "email": r[2],
                "name": r[3] or "",
                "package": r[4],
                "amount": float(r[5]),
                "currency": r[6] or "BDT",
                "provider": r[7] or "bKash",
                "trx_id": r[8] or "",
                "paid_at": r[9],
                "notes": r[10] or "",
                "team_name": r[11] or "Carmella Elan"
            }
    return None


def delete_payment(payment_id: int) -> bool:
    """Deletes a payment record from the payments ledger."""
    init_db()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM payments WHERE id = ?", (int(payment_id),))
        conn.commit()
        return c.rowcount > 0


def get_all_payments(limit: int = 200, team_filter: str = None) -> list:
    """Fetches the recent payment transaction history ledger, optionally filtered by team."""
    init_db()
    with get_db() as conn:
        c = conn.cursor()
        query = """
            SELECT id, customer_id, email, name, package, amount, currency, provider, trx_id, paid_at, notes, COALESCE(team_name, 'Carmella Elan')
            FROM payments
        """
        params = []
        if team_filter and team_filter.lower() not in ("all", "all teams", ""):
            if "," in team_filter:
                teams = [t.strip() for t in team_filter.split(",") if t.strip()]
                placeholders = ",".join("?" for _ in teams)
                query += f" WHERE COALESCE(team_name, 'Carmella Elan') IN ({placeholders})"
                params.extend(teams)
            else:
                query += " WHERE COALESCE(team_name, 'Carmella Elan') = ?"
                params.append(team_filter.strip())

        query += " ORDER BY paid_at DESC, id DESC LIMIT ?"
        params.append(limit)

        c.execute(query, tuple(params))
        rows = c.fetchall()
        return [
            {
                "id": r[0],
                "customer_id": r[1] or 800,
                "email": r[2],
                "name": r[3] or "",
                "package": r[4],
                "amount": float(r[5]),
                "currency": r[6] or "BDT",
                "provider": r[7] or "bKash",
                "trx_id": r[8] or "",
                "paid_at": r[9],
                "notes": r[10] or "",
                "team_name": r[11] or "Carmella Elan"
            }
            for r in rows
        ]


def get_total_earnings(team_filter: str = None) -> dict:
    """Calculates total earnings in BDT and count of verified payments, optionally filtered by team."""
    init_db()
    with get_db() as conn:
        c = conn.cursor()
        query = "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM payments"
        params = []
        if team_filter and team_filter.lower() not in ("all", "all teams", ""):
            if "," in team_filter:
                teams = [t.strip() for t in team_filter.split(",") if t.strip()]
                placeholders = ",".join("?" for _ in teams)
                query += f" WHERE COALESCE(team_name, 'Carmella Elan') IN ({placeholders})"
                params.extend(teams)
            else:
                query += " WHERE COALESCE(team_name, 'Carmella Elan') = ?"
                params.append(team_filter.strip())

        c.execute(query, tuple(params))
        row = c.fetchone()
        total_bdt = float(row[0] or 0.0)
        total_tx = int(row[1] or 0)
        return {
            "total_bdt": round(total_bdt, 2),
            "total_count": total_tx
        }


def get_canva_team_name() -> str:
    """Retrieves the current Canva Team Name."""
    init_db()
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key = 'canva_team_name'")
            row = c.fetchone()
            if row and row[0]:
                return row[0].strip()
    except Exception as e:
        logger.error(f"Error fetching team name: {e}")
    return os.getenv("CANVA_TEAM_NAME", "Carmella Elan")


def set_canva_team_name(name: str) -> str:
    """Updates the active Canva Team Name persistently."""
    init_db()
    clean_name = name.strip() if name else "Carmella Elan"
    if not clean_name:
        clean_name = "Carmella Elan"
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO settings (key, value) VALUES ('canva_team_name', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (clean_name,))
            conn.commit()
    except Exception as e:
        logger.error(f"Error setting team name: {e}")
    return clean_name


def mark_paid(identifier: str, trx_id: str = "", amount: float = None, provider: str = "bKash") -> bool:
    init_db()
    clean_email = resolve_email(identifier)
    with get_db() as conn:
        c = conn.cursor()
        if trx_id:
            c.execute("""
                UPDATE subscriptions 
                SET payment_status = 'PAID', status = 'active', trx_id = ?
                WHERE email = ?
            """, (trx_id.strip(), clean_email))
        else:
            c.execute("""
                UPDATE subscriptions 
                SET payment_status = 'PAID', status = 'active' 
                WHERE email = ?
            """, (clean_email,))
        conn.commit()
        ok = c.rowcount > 0

    if ok:
        try:
            with get_db() as conn:
                c = conn.cursor()
                if trx_id and trx_id.strip():
                    c.execute("SELECT id FROM payments WHERE email = ? AND trx_id = ?", (clean_email, trx_id.strip()))
                    if not c.fetchone():
                        record_payment(clean_email, amount=amount, provider=provider, trx_id=trx_id)
                else:
                    five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("SELECT id FROM payments WHERE email = ? AND paid_at >= ?", (clean_email, five_mins_ago))
                    if not c.fetchone():
                        record_payment(clean_email, amount=amount, provider=provider, trx_id=trx_id)
        except Exception as e:
            logger.error(f"Error in auto-recording payment for {clean_email}: {e}")

    return ok


def kick_subscriber(identifier: str) -> bool:
    init_db()
    clean_email = resolve_email(identifier)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE subscriptions 
            SET status = 'kicked', payment_status = 'REVOKED' 
            WHERE email = ?
        """, (clean_email,))
        conn.commit()
        return c.rowcount > 0


def extend_subscriber(identifier: str, package: str = "1m") -> dict:
    init_db()
    pkg_name, days, price = parse_package(package)
    clean_email = resolve_email(identifier)
    now = datetime.now()

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT expires_at, package, customer_id FROM subscriptions WHERE email = ?", (clean_email,))
        row = c.fetchone()
        if not row:
            return None

        current_exp_str = row[0]
        cid = row[2] or 800
        try:
            current_exp = datetime.strptime(current_exp_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            current_exp = now

        base_date = current_exp if current_exp > now else now
        new_exp = base_date + timedelta(days=days)
        new_exp_str = new_exp.strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""
            UPDATE subscriptions 
            SET expires_at = ?, package = ?, days = days + ?, payment_status = 'PAID', status = 'active'
            WHERE email = ?
        """, (new_exp_str, pkg_name, days, clean_email))
        conn.commit()

    try:
        record_payment(clean_email, amount=float(price), package=package, notes=f"Plan Extension (+{pkg_name})")
    except Exception as e:
        logger.error(f"Error logging payment for extension: {e}")

    return {
        "customer_id": cid,
        "email": clean_email,
        "added_package": pkg_name,
        "added_days": days,
        "new_expires_at": new_exp_str
    }


def get_subscriber(identifier: str) -> dict:
    init_db()
    if not identifier:
        return None
    raw = str(identifier).strip()
    clean = raw.lstrip("#").strip()
    with get_db() as conn:
        c = conn.cursor()
        if clean.isdigit():
            c.execute("""
                SELECT email, name, package, days, added_at, expires_at, payment_status, status, customer_id, fb_sender_id, trx_id, COALESCE(team_name, 'Carmella Elan')
                FROM subscriptions WHERE customer_id = ?
            """, (int(clean),))
        else:
            c.execute("""
                SELECT email, name, package, days, added_at, expires_at, payment_status, status, customer_id, fb_sender_id, trx_id, COALESCE(team_name, 'Carmella Elan')
                FROM subscriptions WHERE email = ?
            """, (raw.lower(),))
        row = c.fetchone()
        if not row:
            return None
        return {
            "email": row[0],
            "name": row[1],
            "package": row[2],
            "days": row[3],
            "added_at": row[4],
            "expires_at": row[5],
            "payment_status": row[6],
            "status": row[7],
            "customer_id": row[8] or 800,
            "fb_sender_id": row[9] or "",
            "trx_id": row[10] or "",
            "team_name": row[11] or "Carmella Elan"
        }


def update_subscriber(identifier: str, fields: dict) -> dict:
    """
    Updates any editable attributes for a customer (name, email, package, expires_at, payment_status, status, trx_id, team_name, notes).
    """
    init_db()
    clean_email = resolve_email(identifier)
    allowed_fields = [
        "name", "email", "package", "expires_at", 
        "payment_status", "status", "trx_id", "team_name", "notes"
    ]
    updates = {}
    for k, v in fields.items():
        if k in allowed_fields and v is not None:
            updates[k] = v.strip() if isinstance(v, str) else v

    if not updates:
        return get_subscriber(clean_email)

    if "team_name" in updates and updates["team_name"]:
        add_team(updates["team_name"])

    new_email = updates.get("email", "").lower().strip()
    if new_email and new_email != clean_email:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM subscriptions WHERE email = ?", (new_email,))
            if c.fetchone():
                del updates["email"]
            else:
                updates["email"] = new_email

    set_clauses = [f"{k} = ?" for k in updates.keys()]
    values = list(updates.values())
    values.append(clean_email)

    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"UPDATE subscriptions SET {', '.join(set_clauses)} WHERE email = ?", tuple(values))
        conn.commit()

    target_email = updates.get("email", clean_email)
    return get_subscriber(target_email)


def list_subscribers(status_filter: str = None, team_filter: str = None) -> list:
    init_db()
    with get_db() as conn:
        c = conn.cursor()
        query = """
            SELECT email, name, package, expires_at, payment_status, status, customer_id, fb_sender_id, trx_id, COALESCE(team_name, 'Carmella Elan')
            FROM subscriptions
        """
        conditions = []
        params = []
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        if team_filter and team_filter.lower() not in ("all", "all teams", ""):
            if "," in team_filter:
                teams = [t.strip() for t in team_filter.split(",") if t.strip()]
                placeholders = ",".join("?" for _ in teams)
                conditions.append(f"COALESCE(team_name, 'Carmella Elan') IN ({placeholders})")
                params.extend(teams)
            else:
                conditions.append("COALESCE(team_name, 'Carmella Elan') = ?")
                params.append(team_filter.strip())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY customer_id DESC, id DESC LIMIT 100"

        c.execute(query, tuple(params))
        rows = c.fetchall()
        return [
            {
                "email": r[0],
                "name": r[1],
                "package": r[2],
                "expires_at": r[3],
                "payment_status": r[4],
                "status": r[5],
                "customer_id": r[6] or 800,
                "fb_sender_id": r[7] or "",
                "trx_id": r[8] or "",
                "team_name": r[9] or "Carmella Elan"
            }
            for r in rows
        ]


def get_db_stats(team_filter: str = None) -> dict:
    init_db()
    with get_db() as conn:
        c = conn.cursor()
        cond = ""
        params = []
        if team_filter and team_filter.lower() not in ("all", "all teams", ""):
            if "," in team_filter:
                teams = [t.strip() for t in team_filter.split(",") if t.strip()]
                placeholders = ",".join("?" for _ in teams)
                cond = f" AND COALESCE(team_name, 'Carmella Elan') IN ({placeholders})"
                params.extend(teams)
            else:
                cond = " AND COALESCE(team_name, 'Carmella Elan') = ?"
                params.append(team_filter.strip())

        c.execute(f"SELECT COUNT(*) FROM subscriptions WHERE 1=1 {cond}", tuple(params))
        total = c.fetchone()[0]

        c.execute(f"SELECT COUNT(*) FROM subscriptions WHERE payment_status = 'PAID' AND status = 'active' {cond}", tuple(params))
        active_paid = c.fetchone()[0]

        c.execute(f"SELECT COUNT(*) FROM subscriptions WHERE payment_status = 'PENDING' AND status = 'active' {cond}", tuple(params))
        pending = c.fetchone()[0]

        c.execute(f"SELECT COUNT(*) FROM subscriptions WHERE status = 'kicked' {cond}", tuple(params))
        kicked = c.fetchone()[0]

        earnings_info = get_total_earnings(team_filter=team_filter)

        return {
            "total": total,
            "active_paid": active_paid,
            "pending": pending,
            "kicked": kicked,
            "total_earnings": earnings_info["total_bdt"],
            "total_payments": earnings_info["total_count"],
            "canva_team_name": get_canva_team_name(),
            "all_teams": get_all_teams()
        }


def make_subscriber_keyboard(email: str, is_paid: bool = False) -> InlineKeyboardMarkup:
    """Creates 1-tap action buttons for subscriber cards."""
    clean_email = email.lower().strip()
    if is_paid:
        keyboard = [
            [
                InlineKeyboardButton("➕ Extend +1M", callback_data=f"sub_ext:{clean_email}:1m"),
                InlineKeyboardButton("➕ Extend +3M", callback_data=f"sub_ext:{clean_email}:3m")
            ],
            [
                InlineKeyboardButton("🚨 Kick User", callback_data=f"sub_kick:{clean_email}")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Paid", callback_data=f"sub_paid:{clean_email}"),
                InlineKeyboardButton("🚨 Kick User", callback_data=f"sub_kick:{clean_email}")
            ],
            [
                InlineKeyboardButton("➕ Extend +1M", callback_data=f"sub_ext:{clean_email}:1m"),
                InlineKeyboardButton("➕ Extend +3M", callback_data=f"sub_ext:{clean_email}:3m")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)


def format_subscriber_card(sub: dict) -> str:
    status_icon = "🟢 PAID" if sub.get("payment_status") == "PAID" else "🟡 PENDING (Unconfirmed)"
    if sub.get("status") == "kicked":
        status_icon = "🔴 KICKED / REVOKED"

    cid = sub.get("customer_id", 800)
    name_str = f" ({sub['name']})" if sub.get("name") else ""
    return (
        f"👤 *Subscriber Profile:* `#{cid}`\n"
        f"────────────────────────\n"
        f"🆔 *Customer ID:* `#{cid}`\n"
        f"📧 *Email:* `{sub['email']}`{name_str}\n"
        f"📦 *Package:* {sub['package']}\n"
        f"📅 *Expires:* `{sub['expires_at']}`\n"
        f"💰 *Payment:* {status_icon}\n"
        f"────────────────────────"
    )

if __name__ == "__main__":
    init_db()
    print("Subscription Manager initialized. Stats:", get_db_stats())

def delete_subscriber(email: str) -> bool:
    init_db()
    clean_email = email.lower().strip()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM subscriptions WHERE email = ?", (clean_email,))
        conn.commit()
        return c.rowcount > 0

def get_subscribers_expiring_soon(days: int = 7) -> list:
    """
    Finds active, paid subscribers expiring within `days` days 
    who haven't received a reminder in the last 7 days.
    """
    init_db()
    with get_db() as conn:
        c = conn.cursor()
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        exp_limit_str = (now_dt + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        reminder_limit_str = (now_dt - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            SELECT id, customer_id, fb_sender_id, name, email, package, expires_at, last_reminder_at
            FROM subscriptions
            WHERE status = 'active'
              AND payment_status = 'PAID'
              AND expires_at IS NOT NULL
              AND expires_at >= ?
              AND expires_at <= ?
              AND (
                  last_reminder_at IS NULL 
                  OR last_reminder_at < ?
              )
        """, (now_str, exp_limit_str, reminder_limit_str))
        rows = c.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "customer_id": r[1] or 800,
                "fb_sender_id": r[2] or "",
                "name": r[3] or "Customer",
                "email": r[4],
                "package": r[5],
                "expires_at": r[6],
                "last_reminder_at": r[7]
            })
        return result


def mark_reminder_sent(email_or_id) -> bool:
    """Marks that an expiry reminder was sent to this customer."""
    init_db()
    clean_email = resolve_email(email_or_id)
    with get_db() as conn:
        c = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            UPDATE subscriptions 
            SET last_reminder_at = ?
            WHERE email = ?
        """, (now_str, clean_email))
        conn.commit()
        return c.rowcount > 0


def set_pending_telegram_msg(email_or_id, msg_id: int):
    """Stores the Telegram message ID of a pending notification for this subscriber."""
    init_db()
    clean_email = resolve_email(email_or_id)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE subscriptions SET pending_telegram_msg_id = ? WHERE email = ?", (int(msg_id) if msg_id else None, clean_email))
        conn.commit()


def get_pending_telegram_msg(email_or_id) -> int:
    """Retrieves the Telegram message ID of a pending notification for this subscriber."""
    init_db()
    clean_email = resolve_email(email_or_id)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT pending_telegram_msg_id FROM subscriptions WHERE email = ?", (clean_email,))
        row = c.fetchone()
        return row[0] if (row and row[0]) else 0


def clear_pending_telegram_msg(email_or_id):
    """Clears the stored Telegram message ID for this subscriber."""
    set_pending_telegram_msg(email_or_id, 0)



import secrets

import hmac
import hashlib
import base64
import secrets

CANVA_TEAM_INVITE_URL = "https://www.canva.com/brand/join?token=7VoLaeSmblzCAyFQZJ_nhg&brandingVariant=edu&referrer=team-invite"
INVITE_HMAC_SECRET = b"designhub_permanent_hmac_secret_key_v1_2026"


def init_consumed_tokens_table():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS consumed_tokens (
                token TEXT PRIMARY KEY,
                email TEXT,
                consumed_at TEXT,
                access_count INTEGER DEFAULT 1
            )
        """)
        c.execute("PRAGMA table_info(consumed_tokens)")
        cols = [col[1] for col in c.fetchall()]
        if "access_count" not in cols:
            c.execute("ALTER TABLE consumed_tokens ADD COLUMN access_count INTEGER DEFAULT 1")
        conn.commit()

init_consumed_tokens_table()


def create_expiring_invite(email: str, minutes: int = 30) -> dict:
    """
    Generates a cryptographically signed, stateless, self-expiring link with a full session window.
    Each call generates a brand-new unique token using a fresh nonce and timestamp.
    """
    expires_ts = int(time.time()) + (minutes * 60)
    nonce = secrets.token_hex(4)
    data = f"{email.lower().strip()}|{expires_ts}|{nonce}".encode("utf-8")
    sig = hmac.new(INVITE_HMAC_SECRET, data, hashlib.sha256).hexdigest()[:16]
    raw_payload = f"{email.lower().strip()}|{expires_ts}|{nonce}|{sig}"
    token = "dh_" + base64.urlsafe_b64encode(raw_payload.encode("utf-8")).decode("utf-8").rstrip("=")
    
    return {
        "token": token,
        "email": email,
        "expires_ts": expires_ts,
        "minutes": minutes
    }


def extract_email_from_token(token: str) -> str:
    """Safely extracts the registered email from an invitation token."""
    try:
        raw_b64 = token.replace("dh_", "", 1)
        pad = 4 - (len(raw_b64) % 4)
        if pad != 4:
            raw_b64 += "=" * pad
        decoded = base64.urlsafe_b64decode(raw_b64).decode("utf-8")
        parts = decoded.split("|")
        if len(parts) >= 1 and "@" in parts[0]:
            return parts[0].strip().lower()
    except Exception:
        pass
    return ""


def consume_expiring_invite(token: str, is_bot_prefetch: bool = False) -> dict:
    """
    Validates the cryptographic HMAC signature and manages the active onboarding session.
    Allows smooth multi-device / reload access within the session window (30 mins) while preventing viral redistribution.
    """
    init_consumed_tokens_table()
    now_ts = int(time.time())
    
    try:
        raw_b64 = token.replace("dh_", "", 1)
        pad = 4 - (len(raw_b64) % 4)
        if pad != 4:
            raw_b64 += "=" * pad
        decoded = base64.urlsafe_b64decode(raw_b64).decode("utf-8")
        parts = decoded.split("|")
        if len(parts) == 4:
            email, exp_str, nonce, sig = parts
            exp_ts = int(exp_str)
            
            # Verify HMAC signature
            expected_data = f"{email}|{exp_ts}|{nonce}".encode("utf-8")
            expected_sig = hmac.new(INVITE_HMAC_SECRET, expected_data, hashlib.sha256).hexdigest()[:16]
            if not hmac.compare_digest(sig, expected_sig):
                return {"valid": False, "reason": "invalid_signature", "email": email, "message": "Invalid link signature."}
            
            # Verify session expiry
            if now_ts > exp_ts:
                return {"valid": False, "reason": "expired", "email": email, "message": "This invitation session has expired."}
            
            # Session Management: Allow client reloads, app switching, and OAuth callbacks up to 20 accesses
            with get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT access_count FROM consumed_tokens WHERE token = ?", (token,))
                row = c.fetchone()
                if row:
                    count = row[0] or 1
                    if count >= 20:
                        return {"valid": False, "reason": "session_limit", "email": email, "message": "Invitation session access limit reached."}
                    if not is_bot_prefetch:
                        c.execute("UPDATE consumed_tokens SET access_count = access_count + 1 WHERE token = ?", (token,))
                        conn.commit()
                else:
                    if not is_bot_prefetch:
                        c.execute("""
                            INSERT INTO consumed_tokens (token, email, consumed_at, access_count) 
                            VALUES (?, ?, ?, 1)
                        """, (token, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
            
            return {
                "valid": True,
                "target_url": CANVA_TEAM_INVITE_URL,
                "email": email
            }
    except Exception as e:
        logger.error(f"Error parsing signed token: {e}")

    return {"valid": False, "reason": "invalid", "message": "Invalid invitation link."}
