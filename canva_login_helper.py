#!/usr/bin/env python3
"""
1-Time Canva Login Helper for Design Hub
Opens a visible Chrome window so you can log into your Canva admin account once.
Saves session cookies to 'canva_session.json' so the bot can run headlessly.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path(__file__).resolve().parent / "canva_session.json"


def main():
    print("=" * 60)
    print("🎨 Design Hub — Canva 1-Time Session Setup")
    print("=" * 60)
    print("1. A visible Chrome browser will open shortly.")
    print("2. Log into your Canva Admin / Team Account (Google, Email, etc.).")
    print("3. Once you are logged in and on the Canva dashboard, return here.")
    print("4. Press ENTER in this terminal to save your session.")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto("https://www.canva.com/login", wait_until="networkidle")

        print("\n👉 Browser is open! Please log into Canva now...")
        try:
            input("\nPress ENTER here AFTER you have successfully logged into Canva: ")
        except EOFError:
            print("Auto-waiting 30 seconds for login...")
            time.sleep(30)

        # Save session
        context.storage_state(path=str(SESSION_FILE))
        browser.close()

    if SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 100:
        print("\n🎉 SUCCESS! Canva session saved to: canva_session.json")
        print("Your bot can now invite and remove members headlessly without needing a password!")
    else:
        print("\n⚠️ Failed to save session. Please try running this script again.")


if __name__ == "__main__":
    main()
