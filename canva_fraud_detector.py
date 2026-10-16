#!/usr/bin/env python3
"""
Canva Pro Fraud & Unauthorized Member Auditor for Design Hub
Scans Canva's live team roster using local Chrome session and compares against
the official subscriber database. Detects leaked invite links and unapproved members.
"""

import os
import re
import time
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import requests

from playwright.sync_api import sync_playwright
from subscription_manager import list_subscribers, get_canva_team_name

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

logger = logging.getLogger("CanvaFraudDetector")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

SESSION_FILE = Path(__file__).resolve().parent / "canva_session.json"
RENDER_SECRET_FILE = Path("/etc/secrets/canva_session.json")
if not SESSION_FILE.exists() and RENDER_SECRET_FILE.exists():
    SESSION_FILE = RENDER_SECRET_FILE

CANVA_SESSION_B64 = os.getenv("CANVA_SESSION_B64", "")
if not SESSION_FILE.exists() and CANVA_SESSION_B64:
    try:
        import base64
        SESSION_FILE.write_bytes(base64.b64decode(CANVA_SESSION_B64))
        logger.info("Restored canva_session.json from CANVA_SESSION_B64 environment variable.")
    except Exception as e:
        logger.error(f"Error restoring canva session: {e}")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")

IGNORE_FILE = Path(__file__).resolve().parent / "ignored_emails.json"

def load_ignored_emails() -> set:
    """Loads the user-managed ignore/whitelist from ignored_emails.json."""
    fallback = {"frankribery565@gmail.com", "tanvirsunny565@gmail.com"}
    if IGNORE_FILE.exists():
        try:
            with open(IGNORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {str(e).lower().strip() for e in data if e}
                elif isinstance(data, dict):
                    emails = data.get("ignored_emails", [])
                    return {str(e).lower().strip() for e in emails if e}
        except Exception as e:
            logger.error(f"Error reading {IGNORE_FILE}: {e}")
    return fallback


def scan_canva_members() -> dict:
    """
    Connects to Canva team settings via local Chrome or cloud Chromium with anti-detection flags
    and returns a clean list of all live member emails currently occupying seats.
    """
    if not SESSION_FILE.exists():
        return {
            "status": "error",
            "message": (
                "canva_session.json not found on this cloud server (Render).\n\n"
                "💡 How to run Canva Audit:\n"
                "1. Run directly from your Mac terminal (bypasses Cloudflare):\n"
                "   python3 canva_fraud_detector.py --telegram\n\n"
                "2. Or upload canva_session.json to Render Dashboard > Environment > Secret Files."
            )
        }

    logger.info("🔍 Launching browser in background mode to scan Canva team roster...")
    try:
        with sync_playwright() as p:
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
                "--no-first-run",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
            try:
                browser = p.chromium.launch(
                    channel="chrome",
                    headless=True,
                    args=launch_args
                )
            except Exception:
                browser = p.chromium.launch(
                    headless=True,
                    args=launch_args
                )
            context = browser.new_context(
                storage_state=str(SESSION_FILE),
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            page.goto("https://www.canva.com/settings/team-members", wait_until="domcontentloaded", timeout=35000)
            time.sleep(5)

            title = page.title()
            html = page.content()
            browser.close()

            if "Just a moment..." in title or "Cloudflare" in title:
                return {
                    "status": "error",
                    "message": (
                        "🛡️ Canva Cloudflare Challenge intercepted the cloud server.\n\n"
                        "Datacenter IPs on Render are challenged by Cloudflare Turnstile.\n"
                        "Run the audit from your Mac to bypass Cloudflare in 4 seconds:\n"
                        "👉 python3 canva_fraud_detector.py --telegram"
                    )
                }

            emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html)
            clean_emails = sorted(list(set(
                e.lower().strip() for e in emails 
                if not any(k in e for k in ["canva.com", "sentry", "example", ".png", ".jpg", ".webp", ".svg"])
            )))

            logger.info(f"✅ Found {len(clean_emails)} total member emails on Canva.")
            return {"status": "success", "members": clean_emails}

    except Exception as e:
        logger.error(f"Error scanning Canva members: {e}")
        return {"status": "error", "message": str(e)}


def audit_team_fraud() -> dict:
    """
    Compares live Canva members against the database of authorized active subscribers.
    Returns: dict with total_canva, total_db, authorized, fraud_emails, owner_emails.
    """
    scan_res = scan_canva_members()
    if scan_res.get("status") != "success":
        return scan_res

    canva_members = scan_res["members"]
    
    # Fetch registered subscribers from database
    db_subs = list_subscribers(team_filter="all")
    # Authorized are those with active status and not kicked
    authorized_db_emails = {
        s.get("email", "").lower().strip() 
        for s in db_subs 
        if s.get("status") == "active" and s.get("payment_status") != "KICKED"
    }

    ignored_emails = load_ignored_emails()
    fraud_emails = []
    verified_emails = []
    ignored_found = []

    for email in canva_members:
        if email in ignored_emails:
            ignored_found.append(email)
        elif email in authorized_db_emails:
            verified_emails.append(email)
        else:
            fraud_emails.append(email)

    team_name = get_canva_team_name() or "Canva Team"

    return {
        "status": "success",
        "team_name": team_name,
        "total_canva": len(canva_members),
        "total_authorized_db": len(authorized_db_emails),
        "verified_count": len(verified_emails),
        "fraud_count": len(fraud_emails),
        "ignored_count": len(ignored_found),
        "fraud_emails": fraud_emails,
        "verified_emails": verified_emails,
        "ignored_emails": ignored_found
    }


def format_fraud_telegram_message(audit: dict):
    """Formats the audit results into a beautiful Telegram Markdown card with 1-tap action buttons."""
    if audit.get("status") != "success":
        return f"⚠️ *Canva Scan Failed:*\n`{audit.get('message', 'Unknown error')}`", None

    team_name = audit["team_name"]
    total = audit["total_canva"]
    fraud = audit["fraud_emails"]
    verified = audit["verified_emails"]
    ignored = audit.get("ignored_emails", [])

    if not fraud:
        text = (
            f"✅ *CANVA TEAM AUDIT CLEAN! (NO FRAUD)*\n"
            f"────────────────────────\n"
            f"🎨 *Team Name:* `{team_name}`\n"
            f"👥 *Total Members in Canva:* `{total}`\n"
            f"🟢 *Verified Subscribers:* `{len(verified)}`\n"
            f"🛡️ *Whitelisted / Ignored:* `{len(ignored)}`\n"
            f"────────────────────────\n"
            f"🎉 *Zero fraud detected!* All {total} members in your Canva Team are either verified or whitelisted in your `ignored_emails.json` list."
        )
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔄 Scan Again", "callback_data": "audit_fraud"}],
                [{"text": "🔗 Open Canva Team", "url": "https://www.canva.com/settings/team-members"}]
            ]
        }
        return text, keyboard

    # Fraud detected!
    fraud_list_str = "\n".join([f"• `{e}`" for e in fraud])
    text = (
        f"🚨 *CANVA TEAM FRAUD / UNAUTHORIZED MEMBERS DETECTED!*\n"
        f"────────────────────────\n"
        f"🎨 *Team Name:* `{team_name}`\n"
        f"👥 *Total Seats Occupied in Canva:* `{total}`\n"
        f"🟢 *Legit Active Subscribers:* `{len(verified)}`\n"
        f"🛡️ *Whitelisted / Ignored:* `{len(ignored)}`\n"
        f"⚠️ *Unauthorized / Extra Members:* `{len(fraud)}`\n"
        f"────────────────────────\n"
        f"⚠️ *The following {len(fraud)} emails are inside your Canva Team but have NO active paid record in your database:*\n\n"
        f"{fraud_list_str}\n\n"
        f"────────────────────────\n"
        f"💡 *Action:* Remove them immediately below or directly in Canva Settings:"
    )

    inline_buttons = []
    # Add kick buttons for up to 5 fraud users
    for e in fraud[:5]:
        inline_buttons.append([{"text": f"🚨 Kick {e}", "callback_data": f"sub_kick:{e}"}])

    inline_buttons.append([{"text": "🔄 Scan Again", "callback_data": "audit_fraud"}])
    inline_buttons.append([{"text": "🔗 Open Canva Seat Settings", "url": "https://www.canva.com/settings/team-members"}])

    return text, {"inline_keyboard": inline_buttons}


def send_telegram_audit_report():
    """Runs the audit and delivers the result directly to the owner's Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ALLOWED_USER_ID:
        print("Telegram credentials missing in .env")
        return False

    print("Running Canva Team Fraud Audit...")
    audit = audit_team_fraud()
    text, markup = format_fraud_telegram_message(audit)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_ALLOWED_USER_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    if markup:
        payload["reply_markup"] = json.dumps(markup)

    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            print("✅ Fraud audit report sent directly to your Telegram!")
            return True
        else:
            print(f"Failed to send to Telegram: {r.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
    return False


if __name__ == "__main__":
    import sys
    if "--telegram" in sys.argv:
        send_telegram_audit_report()
    else:
        print("🔍 Running Canva Fraud Audit locally...")
        res = audit_team_fraud()
        print(json.dumps(res, indent=2))
        t, _ = format_fraud_telegram_message(res)
        print("\n=== Telegram Preview ===")
        print(t)
