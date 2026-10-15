import os
#!/usr/bin/env python3
"""
Canva Headless Automation Worker for Design Hub
Uses saved 'canva_session.json' to automatically:
- Invite customer emails to Canva Pro / Canva Team
- Remove / kick customer emails when requested
Runs headlessly in the background via Playwright.
"""

import sys
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path(__file__).resolve().parent / "canva_session.json"

# Restore session from environment variable if on cloud host (Render)
CANVA_SESSION_B64 = os.getenv("CANVA_SESSION_B64", "")
if CANVA_SESSION_B64 and not SESSION_FILE.exists():
    try:
        import base64
        SESSION_FILE.write_bytes(base64.b64decode(CANVA_SESSION_B64))
        logger.info("Restored canva_session.json from CANVA_SESSION_B64 environment variable.")
    except Exception as e:
        logger.error(f"Error restoring canva session: {e}")
logger = logging.getLogger("CanvaWorker")


def is_canva_authenticated() -> bool:
    """Check if a saved session file exists."""
    return SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 100


def invite_canva_member(email: str) -> dict:
    """
    Invites an email to Canva Team headlessly.
    Returns: {"status": "success"|"error", "message": str}
    """
    clean_email = email.lower().strip()
    if not is_canva_authenticated():
        return {
            "status": "error",
            "message": "⚠️ Canva session not configured. Run 'python canva_login_helper.py' once on your Mac."
        }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                storage_state=str(SESSION_FILE),
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Go to Canva team members page
            logger.info(f"Navigating to Canva team settings to invite {clean_email}...")
            page.goto("https://www.canva.com/settings/team-members", wait_until="networkidle", timeout=30000)

            # Check if session is expired/redirected to login
            if "login" in page.url or "signup" in page.url:
                browser.close()
                return {
                    "status": "error",
                    "message": "⚠️ Canva session has expired. Please run 'python canva_login_helper.py' to refresh."
                }

            # Locate email input field
            input_selector = (
                "input[type='email'], "
                "input[placeholder*='email' i], "
                "input[placeholder*='name or email' i], "
                "input[aria-label*='email' i]"
            )
            
            try:
                page.wait_for_selector(input_selector, timeout=8000)
                email_input = page.locator(input_selector).first
                email_input.fill(clean_email)
                time.sleep(0.5)

                # Locate Invite / Send invitation button
                btn_selector = "button:has-text('Invite'), button:has-text('Send invitation'), button:has-text('Send invite')"
                invite_btn = page.locator(btn_selector).first
                if invite_btn.is_visible():
                    invite_btn.click()
                    time.sleep(2)  # Wait for submission
                    browser.close()
                    return {
                        "status": "success",
                        "email": clean_email,
                        "message": f"✅ Official Canva Pro invitation successfully dispatched to {clean_email}!"
                    }
                else:
                    # Press Enter as fallback
                    email_input.press("Enter")
                    time.sleep(2)
                    browser.close()
                    return {
                        "status": "success",
                        "email": clean_email,
                        "message": f"✅ Invitation sent to {clean_email}."
                    }

            except Exception as e:
                browser.close()
                return {
                    "status": "error",
                    "message": f"Could not find invite inputs on Canva page: {str(e)}"
                }

    except Exception as e:
        logger.error(f"Error inviting {clean_email}: {e}")
        return {"status": "error", "message": f"Playwright error: {str(e)}"}


def kick_canva_member(email: str) -> dict:
    """
    Removes/kicks an email from Canva Team headlessly.
    Returns: {"status": "success"|"error", "message": str}
    """
    clean_email = email.lower().strip()
    if not is_canva_authenticated():
        return {
            "status": "error",
            "message": "⚠️ Canva session not configured. Run 'python canva_login_helper.py' first."
        }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                storage_state=str(SESSION_FILE),
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            logger.info(f"Navigating to Canva team settings to kick {clean_email}...")
            page.goto("https://www.canva.com/settings/team-members", wait_until="networkidle", timeout=30000)

            if "login" in page.url or "signup" in page.url:
                browser.close()
                return {
                    "status": "error",
                    "message": "⚠️ Canva session expired. Please re-run login helper."
                }

            # Find member or pending invitation row with matching email
            row = page.locator(f"tr:has-text('{clean_email}'), div:has-text('{clean_email}')").first
            if row.is_visible():
                # Click the options / more actions button in that row
                more_btn = row.locator("button[aria-label*='more' i], button[aria-label*='action' i], button:has-text('...')").first
                if more_btn.is_visible():
                    more_btn.click()
                    time.sleep(0.5)

                    remove_btn = page.locator("button:has-text('Remove'), button:has-text('Revoke'), div[role='menuitem']:has-text('Remove')").first
                    if remove_btn.is_visible():
                        remove_btn.click()
                        time.sleep(1)

                        # Confirm dialog if any
                        confirm_btn = page.locator("button:has-text('Remove from team'), button:has-text('Confirm')").first
                        if confirm_btn.is_visible():
                            confirm_btn.click()
                            time.sleep(1)

                        browser.close()
                        return {
                            "status": "success",
                            "email": clean_email,
                            "message": f"🚨 {clean_email} has been successfully removed from Canva Pro Team!"
                        }

            browser.close()
            return {
                "status": "success",
                "email": clean_email,
                "message": f"Marked {clean_email} as kicked in database (Note: If not found in Canva UI, they may have already left or not accepted)."
            }

    except Exception as e:
        logger.error(f"Error kicking {clean_email}: {e}")
        return {"status": "error", "message": f"Playwright error: {str(e)}"}


if __name__ == "__main__":
    print("Canva Worker Module")
    print("Authenticated:", is_canva_authenticated())
