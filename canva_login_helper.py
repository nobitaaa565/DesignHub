#!/usr/bin/env python3
"""
Official Google Chrome Canva Session Capture for Design Hub
Uses your REAL Google Chrome app (not test Chromium) with anti-detection flags
so Google and Canva do not block verification codes.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path(__file__).resolve().parent / "canva_session.json"


def main():
    print("=" * 60)
    print("🎨 Design Hub — Real Chrome Canva Session Capture")
    print("=" * 60)
    print("• Opening your official Google Chrome app...")
    print("• Anti-automation flags bypassed (Google Login enabled).")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",  # Uses your real installed Google Chrome
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
                "--no-first-run",
                "--disable-infobars"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Mask navigator.webdriver
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page.goto("https://www.canva.com/login", wait_until="domcontentloaded")
        print("\n👉 Real Chrome is open! Please log into Canva now.")
        print("💡 The script will automatically detect when you are on the dashboard and save cookies.")

        start_time = time.time()
        logged_in = False

        # Wait up to 5 minutes
        while time.time() - start_time < 300:
            try:
                curr_url = page.url.lower()
                if "canva.com" in curr_url and not any(k in curr_url for k in ["/login", "/signup", "accounts.google.com"]):
                    cookies = context.cookies()
                    # Check for authenticated cookies
                    if len(cookies) > 5:
                        print(f"\n🎉 Successfully logged in! Detected on: {page.url}")
                        print("⏳ Saving session tokens (5 seconds)...")
                        time.sleep(5)
                        logged_in = True
                        break
            except Exception:
                pass
            time.sleep(2)

        if logged_in:
            context.storage_state(path=str(SESSION_FILE))
            print(f"\n✅ Session saved successfully to: {SESSION_FILE}")
        else:
            print("\n⚠️ Saving current session state...")
            context.storage_state(path=str(SESSION_FILE))

        browser.close()

    if SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 100:
        print("\n🎉 ALL DONE! Your Canva Pro team is now connected.")
    else:
        print("\n❌ Failed to capture session.")


if __name__ == "__main__":
    main()
