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


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
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
        # Ensure all columns exist
        c.execute("PRAGMA table_info(subscriptions)")
        cols = [col[1] for col in c.fetchall()]
        if "name" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN name TEXT DEFAULT ''")
        if "days" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN days INTEGER DEFAULT 30")
        if "trx_id" not in cols:
            c.execute("ALTER TABLE subscriptions ADD COLUMN trx_id TEXT DEFAULT ''")
        conn.commit()


def parse_package(pkg: str):
    p = pkg.lower().strip()
    if p in ("3m", "3mo", "3months", "3", "3 month"):
        return "3 Months", 90, 50
    elif p in ("12m", "1y", "1year", "12", "12 month", "1 year"):
        return "12 Months", 365, 150
    return "1 Month", 30, 25


def add_subscriber(email: str, package: str = "1m", name: str = "") -> dict:
    init_db()
    pkg_name, days, price = parse_package(package)
    now = datetime.now()
    exp = now + timedelta(days=days)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    exp_str = exp.strftime("%Y-%m-%d %H:%M:%S")
    clean_email = email.lower().strip()

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO subscriptions (email, name, package, days, added_at, expires_at, payment_status, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING', 'active')
            ON CONFLICT(email) DO UPDATE SET
                package=excluded.package,
                days=excluded.days,
                added_at=excluded.added_at,
                expires_at=excluded.expires_at,
                payment_status='PENDING',
                status='active'
        """, (clean_email, name.strip(), pkg_name, days, now_str, exp_str))
        conn.commit()

    return {
        "email": clean_email,
        "name": name.strip(),
        "package": pkg_name,
        "days": days,
        "price": price,
        "expires_at": exp_str,
        "payment_status": "PENDING",
        "status": "active"
    }


def mark_paid(email: str, trx_id: str = "") -> bool:
    init_db()
    clean_email = email.lower().strip()
    with sqlite3.connect(DB_FILE) as conn:
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
        return c.rowcount > 0


def kick_subscriber(email: str) -> bool:
    init_db()
    clean_email = email.lower().strip()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE subscriptions 
            SET status = 'kicked', payment_status = 'REVOKED' 
            WHERE email = ?
        """, (clean_email,))
        conn.commit()
        return c.rowcount > 0


def extend_subscriber(email: str, package: str = "1m") -> dict:
    init_db()
    pkg_name, days, price = parse_package(package)
    clean_email = email.lower().strip()
    now = datetime.now()

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT expires_at, package FROM subscriptions WHERE email = ?", (clean_email,))
        row = c.fetchone()
        if not row:
            return None

        current_exp_str = row[0]
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

    return {
        "email": clean_email,
        "added_package": pkg_name,
        "added_days": days,
        "new_expires_at": new_exp_str
    }


def get_subscriber(email: str) -> dict:
    init_db()
    clean_email = email.lower().strip()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT email, name, package, days, added_at, expires_at, payment_status, status 
            FROM subscriptions WHERE email = ?
        """, (clean_email,))
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
            "status": row[7]
        }


def list_subscribers(status_filter: str = None) -> list:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        if status_filter:
            c.execute("""
                SELECT email, name, package, expires_at, payment_status, status 
                FROM subscriptions WHERE status = ? ORDER BY id DESC LIMIT 50
            """, (status_filter,))
        else:
            c.execute("""
                SELECT email, name, package, expires_at, payment_status, status 
                FROM subscriptions ORDER BY id DESC LIMIT 50
            """)
        rows = c.fetchall()
        return [
            {
                "email": r[0],
                "name": r[1],
                "package": r[2],
                "expires_at": r[3],
                "payment_status": r[4],
                "status": r[5]
            }
            for r in rows
        ]


def get_db_stats() -> dict:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM subscriptions")
        total = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE payment_status = 'PAID' AND status = 'active'")
        active_paid = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE payment_status = 'PENDING' AND status = 'active'")
        pending = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'kicked'")
        kicked = c.fetchone()[0]

        return {
            "total": total,
            "active_paid": active_paid,
            "pending": pending,
            "kicked": kicked
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

    name_str = f" ({sub['name']})" if sub.get("name") else ""
    return (
        f"👤 *Subscriber Profile:*\n"
        f"────────────────────────\n"
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
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM subscriptions WHERE email = ?", (clean_email,))
        conn.commit()
        return c.rowcount > 0
