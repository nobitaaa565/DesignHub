#!/usr/bin/env python3
"""
Design Hub — 8-Step Conversational Sales Funnel for Facebook Messenger & Comments
Handles:
1. Greeting
2. Package Selection (Buttons / Numbers 1, 2, 3)
3. Gmail Collection
4. Explicit Confirmation (Gmail + Package)
5. 10-Minute Expiring Link Delivery (Access First, Pay Later)
6. Payment Proof Handling (TrxID / Screenshot) & Telegram Approval
7. Extend Option Mention & Quick Replies
8. Restart / Extend Action Buttons
"""

import os
import re
import json
import logging
import asyncio
from pathlib import Path
import requests

from subscription_manager import add_subscriber, mark_paid, get_subscriber, create_expiring_invite
from payment_verifier import analyze_payment_screenshot, extract_trx_from_text

logger = logging.getLogger("FacebookFunnel")

STATES_FILE = Path(__file__).resolve().parent / "conversation_states.json"
REPLIED_FILE = Path(__file__).resolve().parent / "replied_messages.json"
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1312971105242105")
TELEGRAM_ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", "0"))

PACKAGES = {
    "1": {"key": "1m", "name": "১ মাস (২৫ টাকা)", "price": 25, "days": 30},
    "2": {"key": "3m", "name": "৩ মাস (৫০ টাকা)", "price": 50, "days": 90},
    "3": {"key": "12m", "name": "১ বছর (১৫০ টাকা)", "price": 150, "days": 365},
    "pkg_1m": {"key": "1m", "name": "১ মাস (২৫ টাকা)", "price": 25, "days": 30},
    "pkg_3m": {"key": "3m", "name": "৩ মাস (৫০ টাকা)", "price": 50, "days": 90},
    "pkg_12m": {"key": "12m", "name": "১ বছর (১৫০ টাকা)", "price": 150, "days": 365},
}


def load_states() -> dict:
    if STATES_FILE.exists():
        try:
            with open(STATES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_states(states: dict):
    try:
        with open(STATES_FILE, "w", encoding="utf-8") as f:
            json.dump(states, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving states: {e}")


def load_replied_ids() -> set:
    if REPLIED_FILE.exists():
        try:
            with open(REPLIED_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_replied_ids(ids: set):
    try:
        with open(REPLIED_FILE, "w") as f:
            json.dump(list(ids)[-1000:], f)
    except Exception:
        pass


RESTART_BUTTON = {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}


def send_fb_message(recipient_id: str, text: str, page_token: str, quick_replies=None) -> bool:
    """Send message to customer with quick reply buttons, ALWAYS guaranteeing the Restart button is present."""
    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={page_token}"
    
    if quick_replies is None:
        buttons = [RESTART_BUTTON]
    else:
        buttons = list(quick_replies)
        has_restart = any(b.get("payload") == "ACTION_RESTART" for b in buttons)
        if not has_restart:
            buttons.append(RESTART_BUTTON)

    msg_payload = {
        "text": text,
        "quick_replies": buttons
    }

    payload = {
        "recipient": {"id": recipient_id},
        "message": msg_payload
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Error sending Messenger message: {e}")
        return False


def get_package_buttons():
    return [
        {"content_type": "text", "title": "1️⃣ ১ মাস (২৫৳)", "payload": "PKG_1M"},
        {"content_type": "text", "title": "2️⃣ ৩ মাস (৫০৳)", "payload": "PKG_3M"},
        {"content_type": "text", "title": "3️⃣ ১ বছর (১৫০৳)", "payload": "PKG_12M"},
        {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
    ]


def parse_package_choice(text: str):
    clean = text.lower().strip()
    if clean in ("1", "১", "1m", "pkg_1m") or "১ মাস" in clean or "1 month" in clean:
        return PACKAGES["1"]
    if clean in ("2", "২", "3m", "pkg_3m") or "৩ মাস" in clean or "3 month" in clean:
        return PACKAGES["2"]
    if clean in ("3", "৩", "12m", "pkg_12m", "1y") or "১ বছর" in clean or "1 year" in clean:
        return PACKAGES["3"]
    return None


def handle_incoming_customer_message(sender_id: str, sender_name: str, msg_text: str, msg_id: str, page_token: str, bot_instance=None):
    """Processes customer messages through the 8-step funnel."""
    states = load_states()
    state = states.get(sender_id, {})
    stage = state.get("stage", "greeting")

    clean_text = msg_text.strip().lower()

    # Global Triggers: Native 'Get Started' button, 'Restart', or Greetings ('Hi', 'Hello')
    start_keywords = (
        "get_started", "start", "restart", "রিস্টার্ট", "reset", "শুরু", "মেনু", "menu", "action_restart",
        "hi", "hello", "hey", "hlo", "hy", "hola", "সালাম", "assalamu alaikum", "slam", "kemon achen"
    )
    if clean_text in start_keywords or any(clean_text.startswith(k + " ") for k in ("hi", "hello", "hey")):
        states[sender_id] = {"stage": "awaiting_package", "sender_name": sender_name}
        save_states(states)
        text = (
            f"আসসালামু আলাইকুম {sender_name}! 🎨 Design Hub-এ আপনাকে স্বাগতম।\n\n"
            f"আমরা দিচ্ছি অফিসিয়াল Canva Pro এডুকেশন টিম অ্যাক্সেস (নিজের জিমেইলে এক্টিভ হবে)।\n\n"
            f"📦 আপনি কোন প্যাকেজটি নিতে চান?\n"
            f"১. ১ মাস — ২৫ টাকা\n"
            f"২. ৩ মাস — ৫০ টাকা\n"
            f"৩. ১ বছর — ১৫০ টাকা\n\n"
            f"নিচের বাটনে ট্যাপ করুন অথবা ১, ২ বা ৩ লিখে পাঠিয়ে দিন:"
        )
        send_fb_message(sender_id, text, page_token, quick_replies=get_package_buttons())
        return

    # Global Command: Extend
    if clean_text in ("extend", "মেয়াদ বাড়ান", "বাড়াতে চাই", "action_extend", "রিনিউ"):
        states[sender_id] = {"stage": "awaiting_package", "sender_name": sender_name, "is_extend": True}
        save_states(states)
        text = (
            f"⌛ {sender_name}, আপনার Canva Pro মেয়াদ বাড়াতে (Extend) কোন প্যাকেজটি নিতে চান?\n\n"
            f"১. ১ মাস (+৩০ দিন) — ২৫ টাকা\n"
            f"২. ৩ মাস (+৯০ দিন) — ৫০ টাকা\n"
            f"৩. ১ বছর (+৩৬৫ দিন) — ১৫০ টাকা\n\n"
            f"নিচের বাটনে ট্যাপ করুন অথবা ১, ২ বা ৩ লিখে দিন:"
        )
        send_fb_message(sender_id, text, page_token, quick_replies=get_package_buttons())
        return

    # Step 6 Check: Customer sent TrxID
    trx_info = extract_trx_from_text(msg_text)
    if trx_info.get("found"):
        trx_id = trx_info["trx_id"]
        amt = trx_info.get("amount") or "N/A"
        reply = (
            f"ধন্যবাদ {sender_name}! আপনার পেমেন্ট TrxID ({trx_id}) পেয়েছি।\n\n"
            f"আমাদের টিম আপনার পেমেন্ট ভেরিফাই করছে। ভেরিফিকেশন সফল হলে কনফার্মেশন মেসেজ পাবেন।"
        )
        quick_btns = [
            {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
            {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
        ]
        send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)

        # Notify Telegram Owner with 1-Tap Action
        if bot_instance and TELEGRAM_ALLOWED_USER_ID:
            email_info = state.get("email", "Unknown")
            pkg_info = state.get("package_name", "Canva Pro")
            alert = (
                f"💳 *NEW PAYMENT PROOF RECEIVED! (Messenger)*\n"
                f"────────────────────────\n"
                f"👤 Customer: {sender_name} (ID: `{sender_id}`)\n"
                f"📧 Email: `{email_info}`\n"
                f"📦 Package: {pkg_info}\n"
                f"🔢 TrxID: `{trx_id}`\n"
                f"💵 Amount: {amt}\n"
                f"────────────────────────"
            )
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve & Confirm to Customer", callback_data=f"fb_pay_ok:{sender_id}:{email_info}"),
                    InlineKeyboardButton("🚨 Kick User", callback_data=f"sub_kick:{email_info}")
                ]
            ]
            asyncio.run_coroutine_threadsafe(
                bot_instance.send_message(
                    chat_id=TELEGRAM_ALLOWED_USER_ID,
                    text=alert,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                ),
                asyncio.get_event_loop()
            )
        return

    # STEP 1 & 2: Greeting & Package Selection
    if stage in ("greeting", "awaiting_package"):
        pkg = parse_package_choice(msg_text)
        if pkg:
            # Package selected! Move to Step 3: Ask for Gmail
            states[sender_id] = {
                "stage": "awaiting_email",
                "package_key": pkg["key"],
                "package_name": pkg["name"],
                "package_price": pkg["price"],
                "sender_name": sender_name
            }
            save_states(states)

            reply = (
                f"✅ আপনি নির্বাচন করেছেন: **{pkg['name']}**\n\n"
                f"এখন আপনার যে জিমেইলে (Gmail) Canva Pro অ্যাক্সেস নিতে চান, "
                f"অনুগ্রহ করে সেই জিমেইল অ্যাড্রেসটি লিখে পাঠিয়ে দিন:"
            )
            quick_btns = [
                {"content_type": "text", "title": "🔄 Change Package", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
            return
        else:
            # First touch greeting & show packages
            states[sender_id] = {"stage": "awaiting_package", "sender_name": sender_name}
            save_states(states)
            reply = (
                f"আসসালামু আলাইকুম {sender_name}! 🎨 Design Hub-এ আপনাকে স্বাগতম।\n\n"
                f"আমরা দিচ্ছি অফিসিয়াল Canva Pro এডুকেশন টিম অ্যাক্সেস (নিজের পার্সোনাল জিমেইলে এক্টিভ হবে)।\n\n"
                f"📦 আপনি কোন প্যাকেজটি নিতে চান?\n"
                f"১. ১ মাস — ২৫ টাকা\n"
                f"২. ৩ মাস — ৫০ টাকা\n"
                f"৩. ১ বছর — ১৫০ টাকা\n\n"
                f"নিচের বাটনে চাপ দিন অথবা ১, ২ বা ৩ লিখে জানিয়ে দিন:"
            )
            send_fb_message(sender_id, reply, page_token, quick_replies=get_package_buttons())
            return

    # STEP 3 & 4: Ask for Gmail & Show Confirmation with Package & Email
    if stage == "awaiting_email":
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", msg_text)
        if email_match:
            email = email_match.group(0).lower()
            state["email"] = email
            state["stage"] = "awaiting_confirm"
            states[sender_id] = state
            save_states(states)

            pkg_name = state.get("package_name", "Canva Pro")

            reply = (
                f"অনুগ্রহ করে আপনার তথ্যটি নিশ্চিত করুন:\n\n"
                f"📦 প্যাকেজ: **{pkg_name}**\n"
                f"📧 জিমেইল: **{email}**\n\n"
                f"সবকিছু সঠিক থাকলে নিচের '✅ Confirm & Get Link' বাটনে চাপ দিন অথবা 'YES' / 'হ্যাঁ' লিখে কনফার্ম করুন:"
            )
            quick_btns = [
                {"content_type": "text", "title": "✅ Confirm & Get Link", "payload": f"CONFIRM_YES:{email}"},
                {"content_type": "text", "title": "🔄 Change / Restart", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
            return
        else:
            reply = "অনুগ্রহ করে একটি সঠিক জিমেইল (Gmail) অ্যাড্রেস লিখে পাঠান (যেমন: yourname@gmail.com):"
            quick_btns = [{"content_type": "text", "title": "🔄 Change Package", "payload": "ACTION_RESTART"}]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
            return

    # STEP 5: Customer Confirms -> Send 10-Minute Expiring Link + Request Payment
    if stage == "awaiting_confirm":
        positive_keywords = ["yes", "হ্যাঁ", "ha", "y", "confirm", "হাঁ", "thik ache", "ঠিক আছে", "হ্যা", "confirm_yes"]
        if any(k in clean_text for k in positive_keywords):
            confirmed_email = state.get("email")
            pkg_key = state.get("package_key", "1m")
            pkg_name = state.get("package_name", "১ মাস (২৫ টাকা)")
            pkg_price = state.get("package_price", 25)

            # 1. Enroll in database as PENDING payment
            add_subscriber(confirmed_email, pkg_key, sender_name)

            # 2. Generate 10-minute expiring invite link
            link_data = create_expiring_invite(confirmed_email, minutes=10)
            join_url = f"https://designhub-1any.onrender.com/join/{link_data['token']}"

            state["stage"] = "awaiting_payment"
            state["join_link"] = join_url
            states[sender_id] = state
            save_states(states)

            # 3. Deliver Link + Request Payment
            reply = (
                f"🎉 অভিনন্দন {sender_name}!\n\n"
                f"আপনার Canva Pro টিম জয়েন লিংক নিচে দেওয়া হলো:\n"
                f"🔗 {join_url}\n\n"
                f"⚠️ গুরুত্বপূর্ণ: এই লিংকটি আগামী ১০ মিনিটের জন্য সক্রিয় থাকবে। এখনই লিংকে ক্লিক করে আপনার টিমে যুক্ত হয়ে নিন।\n\n"
                f"💳 পেমেন্ট তথ্য:\n"
                f"• প্যাকেজ: {pkg_name}\n"
                f"• বিকাশ / নগদ (Personal): 01711-223344\n\n"
                f"টিমে জয়েন করার পর পেমেন্ট সম্পন্ন করে ট্রানজেকশন আইডি (TrxID) বা স্ক্রিনশট পাঠিয়ে দিন। ধন্যবাদ! 🎨"
            )
            quick_btns = [
                {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
                {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)

            # 4. Notify Telegram Owner with 1-Tap Control
            if bot_instance and TELEGRAM_ALLOWED_USER_ID:
                alert = (
                    f"⚡ *NEW CANVA PRO ACCESS DELIVERED!*\n"
                    f"────────────────────────\n"
                    f"👤 Customer: {sender_name}\n"
                    f"📧 Email: `{confirmed_email}`\n"
                    f"📦 Package: {pkg_name}\n"
                    f"🔗 10-Min Link: `{join_url}`\n"
                    f"⏳ Status: 🟡 PENDING PAYMENT\n"
                    f"────────────────────────\n"
                    f"⚠️ Customer has been given access. If they do not pay, tap Kick to revoke."
                )
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Mark Paid", callback_data=f"sub_paid:{confirmed_email}"),
                        InlineKeyboardButton("🚨 Kick User", callback_data=f"sub_kick:{confirmed_email}")
                    ]
                ]
                try:
                    asyncio.run_coroutine_threadsafe(
                        bot_instance.send_message(
                            chat_id=TELEGRAM_ALLOWED_USER_ID,
                            text=alert,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode="Markdown"
                        ),
                        asyncio.get_event_loop()
                    )
                except Exception as e:
                    logger.error(f"Error alerting Telegram: {e}")
            return


def send_payment_confirmed_to_customer(sender_id: str, sender_name: str, package_name: str, page_token: str):
    """Sends Step 6 & 7 confirmation + extend option to customer on Facebook Messenger."""
    text = (
        f"🎉 পেমেন্ট সফল হয়েছে!\n\n"
        f"ধন্যবাদ {sender_name}, আপনার {package_name} Canva Pro সাবস্ক্রিপশন নিশ্চিত করা হয়েছে।\n"
        f"আপনার অ্যাকাউন্টটি এখন সম্পূর্ণ ভেরিফায়েড ও অ্যাক্টিভ! 🎨\n\n"
        f"💡 বিশেষ সুবিধা: আপনার মেয়াদ শেষ হওয়ার আগে আপনি যেকোনো সময় মেয়াদ বাড়াতে (Extend) পারবেন।"
    )
    quick_btns = [
        {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
        {"content_type": "text", "title": "🔄 Main Menu", "payload": "ACTION_RESTART"}
    ]
    send_fb_message(sender_id, text, page_token, quick_replies=quick_btns)
