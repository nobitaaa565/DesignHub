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

from subscription_manager import (
    add_subscriber,
    mark_paid,
    get_subscriber,
    create_expiring_invite,
    get_customer_id_by_sender,
    mark_reminder_sent,
    set_pending_telegram_msg,
    get_pending_telegram_msg,
    clear_pending_telegram_msg,
    get_canva_team_name
)
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



def delete_telegram_message(message_id: int) -> bool:
    """Deletes a Telegram message by message_id."""
    if not message_id:
        return False
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    owner_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")
    if not token or not owner_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/deleteMessage"
        r = requests.post(url, json={"chat_id": owner_id, "message_id": int(message_id)}, timeout=10)
        logger.info(f"Deleted Telegram message {message_id}: {r.status_code}")
        return r.status_code == 200 and r.json().get("ok", False)
    except Exception as e:
        logger.error(f"Error deleting Telegram message {message_id}: {e}")
        return False


def send_telegram_alert(text: str, reply_markup: dict = None, photo_bytes: bytes = None) -> int:
    """
    Direct, 100% thread-safe Telegram alert dispatcher using HTTP Bot API.
    Returns the created message_id (int) on success, or 0 on failure.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    owner_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")
    if not token or not owner_id:
        logger.warning("Telegram token or owner ID missing, cannot send alert.")
        return 0

    try:
        if photo_bytes:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            data = {"chat_id": owner_id, "caption": text, "parse_mode": "Markdown"}
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            files = {"photo": ("screenshot.jpg", photo_bytes, "image/jpeg")}
            r = requests.post(url, data=data, files=files, timeout=15)
            logger.info(f"Telegram photo alert response: {r.status_code}")
            if r.status_code == 200:
                res_data = r.json()
                return res_data.get("result", {}).get("message_id") or 1
            return 0
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": owner_id, "text": text, "parse_mode": "Markdown"}
            if reply_markup:
                payload["reply_markup"] = reply_markup
            r = requests.post(url, json=payload, timeout=15)
            logger.info(f"Telegram message alert response: {r.status_code}")
            if r.status_code == 200:
                res_data = r.json()
                return res_data.get("result", {}).get("message_id") or 1
            return 0
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")
        return 0


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


def handle_incoming_customer_message(sender_id: str, sender_name: str, msg_text: str, msg_id: str, page_token: str, bot_instance=None, image_bytes: bytes = None):
    """Processes customer messages through the 8-step funnel."""
    states = load_states()
    state = states.get(sender_id, {})
    stage = state.get("stage", "greeting")

    clean_text = msg_text.strip().lower()

    # Global Command: Request a Fresh New Link (Session management & on-demand brand-new generation)
    is_new_link_request = (
        "action_new_link" in clean_text
        or any(k in clean_text for k in [
            "new link", "newlink", "notun link", "নতুন লিংক", "link expired", 
            "link is expired", "link has expired", "expired link", "মেয়াদ শেষ", 
            "লিংক কাজ করছে না", "kaj kore na", "link den", "link pathan", 
            "send link", "give link", "link please", "expire", "expired", "আরেকটি লিংক"
        ])
        or clean_text in ("link", "লিংক", "নতুন লিংক চাই")
    )
    if is_new_link_request:
        customer_email = state.get("email") or state.get("saved_email")
        if not customer_email:
            from subscription_manager import list_subscribers
            sender_words = set(sender_name.lower().split())
            for s in list_subscribers():
                sub_name = (s.get("name") or "").lower()
                sub_words = set(sub_name.split())
                if sender_words.intersection(sub_words):
                    customer_email = s.get("email")
                    break

        if customer_email:
            # Always generate a brand-new unique token with a fresh 30-minute session
            link_data = create_expiring_invite(customer_email, minutes=30)
            join_url = f"https://designhub-1any.onrender.com/join/{link_data['token']}"
            state["join_link"] = join_url
            state["stage"] = "awaiting_payment"
            states[sender_id] = state
            save_states(states)

            reply = (
                f"✨ {sender_name}, আপনার জন্য একটি একদম নতুন জয়েন লিংক তৈরি করা হয়েছে:\n\n"
                f"🔗 {join_url}\n\n"
                f"⚠️ গুরুত্বপূর্ণ: এই নতুন লিংকটি আগামী ৩০ মিনিটের জন্য সক্রিয় থাকবে। এখনই লিংকে ক্লিক করে আপনার টিমে যুক্ত হয়ে নিন।\n\n"
                f"💳 পেমেন্ট তথ্য:\n"
                f"• বিকাশ / নগদ (Personal): 01711-223344\n\n"
                f"টিমে যুক্ত হয়ে পেমেন্ট সম্পন্ন করে TrxID বা স্ক্রিনশট পাঠিয়ে দিন। ধন্যবাদ! 🎨"
            )
            quick_btns = [
                {"content_type": "text", "title": "🔗 New Link", "payload": "ACTION_NEW_LINK"},
                {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
                {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
            logger.info(f"Generated fresh 30-min link for {sender_name} ({customer_email})")
            return
        else:
            reply = "আপনার কোনো জিমেইল পাওয়া যায়নি। দয়া করে আপনার যে জিমেইলে (Gmail) Canva Pro অ্যাক্সেস নিতে চান, সেটি লিখে পাঠান:"
            quick_btns = [{"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
            return

    # Global Triggers: Native 'Get Started' button, 'Restart', or Greetings ('Hi', 'Hello')
    is_restart_request = (
        "action_restart" in clean_text
        or "restart" in clean_text
        or "রিস্টার্ট" in clean_text
        or "get_started" in clean_text
        or clean_text in ("start", "reset", "শুরু", "মেনু", "menu", "hi", "hello", "hey", "hlo", "hy", "hola", "সালাম", "assalamu alaikum", "slam")
        or any(clean_text.startswith(k + " ") for k in ("hi", "hello", "hey", "start", "menu"))
    )
    if is_restart_request:
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

    # Step 6 Check: Customer sent Screenshot / Photo Attachment
    if image_bytes:
        logger.info(f"📸 Analyzing payment screenshot from {sender_name} ({len(image_bytes)} bytes)...")
        proof = analyze_payment_screenshot(image_bytes)
        email_info = state.get("email") or state.get("saved_email")
        pkg_info = state.get("package_name")
        if not email_info or not pkg_info:
            from subscription_manager import list_subscribers
            sender_words = set(sender_name.lower().split())
            for s in list_subscribers():
                sub_name = (s.get("name") or "").lower()
                sub_words = set(sub_name.split())
                if sender_words.intersection(sub_words):
                    if not email_info:
                        email_info = s.get("email")
                    if not pkg_info:
                        pkg_info = s.get("package")
                    break
        email_info = email_info or "Unknown"
        pkg_info = pkg_info or "Canva Pro" 

        if proof.get("is_payment_proof"):
            provider = proof.get("provider", "Mobile Banking")
            trx_id = proof.get("trx_id") or "Found in Screenshot"
            amt = proof.get("amount") or "N/A"

            state["trx_id"] = trx_id
            state["provider"] = provider
            state["amount"] = amt
            state["proof_received"] = True
            states[sender_id] = state
            save_states(states)

            reply = (
                f"ধন্যবাদ {sender_name}! আপনার {provider} পেমেন্ট স্ক্রিনশট পেয়েছি।\n\n"
                f"• TrxID: {trx_id}\n"
                f"• পরিমাণ: {amt}\n\n"
                f"আমাদের টিম এটি ভেরিফাই করছে। ভেরিফিকেশন সফল হলেই কনফার্মেশন মেসেজ পাবেন। 🎨"
            )
            quick_btns = [
                {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
                {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)

            cid = get_customer_id_by_sender(sender_id, sender_name, email_info)
            caption = (
                f"📸 *NEW PAYMENT SCREENSHOT VERIFIED VIA GEMINI! (Messenger)*\n"
                f"────────────────────────\n"
                f"👤 Customer: {sender_name} (ID: `#{cid}`)\n"
                f"📧 Email: `{email_info}`\n"
                f"📦 Package: {pkg_info}\n"
                f"📱 Provider: {provider}\n"
                f"🔢 TrxID: `{trx_id}`\n"
                f"💵 Amount: {amt}\n"
                f"────────────────────────"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Approve & Confirm to Customer", "callback_data": f"fb_pay_ok:{sender_id}:{email_info}"},
                        {"text": "🚨 Kick User", "callback_data": f"sub_kick:{email_info}"}
                    ],
                    [
                        {"text": "🔗 Open Canva Team to Remove Seat", "url": "https://www.canva.com/settings/team-members"}
                    ]
                ]
            }
            # Delete previous pending message (e.g. from joining Canva or delivery alert)
            prev_msg_id = get_pending_telegram_msg(email_info)
            if prev_msg_id:
                delete_telegram_message(prev_msg_id)
                clear_pending_telegram_msg(email_info)

            new_msg_id = send_telegram_alert(caption, reply_markup=keyboard, photo_bytes=image_bytes)
            if new_msg_id:
                set_pending_telegram_msg(email_info, new_msg_id)
            return
        else:
            reply = (
                f"ধন্যবাদ {sender_name}! আপনার পাঠানো স্ক্রিনশট পেয়েছি।\n\n"
                f"আমাদের অ্যাডমিন প্যানেলে এটি ম্যানুয়ালি ভেরিফিকেশনের জন্য পাঠানো হয়েছে। ভেরিফাই হলেই কনফার্মেশন পাবেন। 🎨"
            )
            quick_btns = [
                {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
                {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)

            cid = get_customer_id_by_sender(sender_id, sender_name, email_info)
            caption = (
                f"⚠️ *MANUAL PAYMENT SCREENSHOT RECEIVED (Messenger)*\n"
                f"────────────────────────\n"
                f"👤 Customer: {sender_name} (ID: `#{cid}`)\n"
                f"📧 Email: `{email_info}`\n"
                f"📦 Package: {pkg_info}\n"
                f"⚠️ OCR Status: TrxID not automatically detected. Please check image manually.\n"
                f"────────────────────────"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Approve & Confirm to Customer", "callback_data": f"fb_pay_ok:{sender_id}:{email_info}"},
                        {"text": "🚨 Kick User", "callback_data": f"sub_kick:{email_info}"}
                    ],
                    [
                        {"text": "🔗 Open Canva Team to Remove Seat", "url": "https://www.canva.com/settings/team-members"}
                    ]
                ]
            }
            # Delete previous pending message
            prev_msg_id = get_pending_telegram_msg(email_info)
            if prev_msg_id:
                delete_telegram_message(prev_msg_id)
                clear_pending_telegram_msg(email_info)

            new_msg_id = send_telegram_alert(caption, reply_markup=keyboard, photo_bytes=image_bytes)
            if new_msg_id:
                set_pending_telegram_msg(email_info, new_msg_id)
            return

    # Step 6 Check: Customer sent TrxID (Text)
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
        email_info = state.get("email") or state.get("saved_email") or "Unknown"
        pkg_info = state.get("package_name", "Canva Pro")
        cid = get_customer_id_by_sender(sender_id, sender_name, email_info)
        alert = (
            f"💳 *NEW PAYMENT PROOF RECEIVED! (Messenger)*\n"
            f"────────────────────────\n"
            f"👤 Customer: {sender_name} (ID: `#{cid}`)\n"
            f"📧 Email: `{email_info}`\n"
            f"📦 Package: {pkg_info}\n"
            f"🔢 TrxID: `{trx_id}`\n"
            f"💵 Amount: {amt}\n"
            f"────────────────────────"
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve & Confirm to Customer", "callback_data": f"fb_pay_ok:{sender_id}:{email_info}"},
                    {"text": "🚨 Kick User", "callback_data": f"sub_kick:{email_info}"}
                ],
                [
                    {"text": "🔗 Open Canva Team to Remove Seat", "url": "https://www.canva.com/settings/team-members"}
                ]
            ]
        }
        # Delete previous pending message
        prev_msg_id = get_pending_telegram_msg(email_info)
        if prev_msg_id:
            delete_telegram_message(prev_msg_id)
            clear_pending_telegram_msg(email_info)

        new_msg_id = send_telegram_alert(alert, reply_markup=keyboard)
        if new_msg_id:
            set_pending_telegram_msg(email_info, new_msg_id)
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
            state["saved_email"] = email
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
            sub = add_subscriber(confirmed_email, pkg_key, sender_name, fb_sender_id=sender_id)
            cid = sub.get("customer_id") or get_customer_id_by_sender(sender_id, sender_name, confirmed_email)

            # 2. Generate 30-minute expiring invite link (each time brand-new token)
            link_data = create_expiring_invite(confirmed_email, minutes=30)
            join_url = f"https://designhub-1any.onrender.com/join/{link_data['token']}"

            state["stage"] = "awaiting_payment"
            state["join_link"] = join_url
            state["customer_id"] = cid
            states[sender_id] = state
            save_states(states)

            # 3. Deliver Link + Request Payment
            reply = (
                f"🎉 অভিনন্দন {sender_name}!\n\n"
                f"আপনার Canva Pro টিম জয়েন লিংক নিচে দেওয়া হলো:\n"
                f"🔗 {join_url}\n\n"
                f"⚠️ গুরুত্বপূর্ণ: এই লিংকটি আগামী ৩০ মিনিটের জন্য সক্রিয় থাকবে। এখনই লিংকে ক্লিক করে আপনার টিমে যুক্ত হয়ে নিন।\n\n"
                f"💳 পেমেন্ট তথ্য:\n"
                f"• প্যাকেজ: {pkg_name}\n"
                f"• বিকাশ / নগদ (Personal): 01711-223344\n\n"
                f"টিমে জয়েন করার পর পেমেন্ট সম্পন্ন করে ট্রানজেকশন আইডি (TrxID) বা স্ক্রিনশট পাঠিয়ে দিন। ধন্যবাদ! 🎨"
            )
            quick_btns = [
                {"content_type": "text", "title": "🔗 New Link", "payload": "ACTION_NEW_LINK"},
                {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
                {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)

            # 4. Notify Telegram Owner with 1-Tap Control
            alert = (
                f"⚡ *NEW CANVA PRO ACCESS DELIVERED! (Messenger)*\n"
                f"────────────────────────\n"
                f"👤 Customer: {sender_name} (ID: `#{cid}`)\n"
                f"📧 Email: `{confirmed_email}`\n"
                f"📦 Package: {pkg_name}\n"
                f"⏳ Status: 🟡 PENDING PAYMENT\n"
                f"🔗 30-Min Link: `{join_url}`\n"
                f"────────────────────────"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Mark Paid", "callback_data": f"sub_paid:{confirmed_email}"},
                        {"text": "🚨 Kick User", "callback_data": f"sub_kick:{confirmed_email}"}
                    ]
                ]
            }
            new_msg_id = send_telegram_alert(alert, reply_markup=keyboard)
            if new_msg_id:
                set_pending_telegram_msg(confirmed_email, new_msg_id)
            return

    # Fallback for awaiting_payment stage: Don't stay silent on customer queries
    if stage == "awaiting_payment":
        customer_email = state.get("email") or state.get("saved_email")
        join_url = state.get("join_link")
        if not join_url and customer_email:
            link_data = create_expiring_invite(customer_email, minutes=30)
            join_url = f"https://designhub-1any.onrender.com/join/{link_data['token']}"
            state["join_link"] = join_url
            states[sender_id] = state
            save_states(states)

        reply = (
            f"ℹ️ {sender_name}, আপনার Canva Pro জয়েন লিংক:\n"
            f"🔗 {join_url}\n\n"
            f"💳 পেমেন্ট তথ্য:\n"
            f"• বিকাশ / নগদ (Personal): 01711-223344\n\n"
            f"টিমে জয়েন করা হয়ে গেলে পেমেন্টের TrxID বা স্ক্রিনশট পাঠিয়ে দিন।\n"
            f"নতুন লিংক প্রয়োজন হলে নিচের বাটনে ট্যাপ করুন:"
        )
        quick_btns = [
            {"content_type": "text", "title": "🔗 New Link", "payload": "ACTION_NEW_LINK"},
            {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
            {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
        ]
        send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
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



def send_expiry_reminder_to_customer(fb_sender_id: str, sender_name: str, customer_id: int, email: str, expires_at: str, page_token: str) -> bool:
    """Sends a 1-week renewal reminder to customer on Facebook Messenger with 1-tap Extend button."""
    if not fb_sender_id or not page_token:
        return False

    exp_date_str = expires_at[:10] if expires_at else "শীঘ্রই"
    text = (
        f"আসসালামু আলাইকুম {sender_name}! 🎨 Design Hub থেকে একটি গুরুত্বপূর্ণ রিমাইন্ডার:\n\n"
        f"আপনার Canva Pro সাবস্ক্রিপশনের মেয়াদ শেষ হতে আর মাত্র ৭ দিন বাকি আছে!\n"
        f"📅 মেয়াদের শেষ তারিখ: {exp_date_str}\n\n"
        f"আপনার ক্যানভা ডিজাইন যাতে কোনো বিরতি ছাড়া সচল থাকে, সেজন্য এখনই খুব সহজে মেয়াদ বাড়িয়ে (Extend) নিতে পারেন।\n\n"
        f"মেয়াদ বাড়াতে নিচের বাটনে ট্যাপ করুন:"
    )
    quick_btns = [
        {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
        {"content_type": "text", "title": "🔄 Main Menu", "payload": "ACTION_RESTART"}
    ]
    ok = send_fb_message(fb_sender_id, text, page_token, quick_replies=quick_btns)
    if ok:
        mark_reminder_sent(email)
        alert = (
            f"⏰ *EXPIRY REMINDER SENT TO CUSTOMER (Messenger)*\n"
            f"────────────────────────\n"
            f"👤 Customer: {sender_name} (ID: `#{customer_id}`)\n"
            f"📧 Email: `{email}`\n"
            f"📅 Expiry Date: `{exp_date_str}`\n"
            f"────────────────────────"
        )
        send_telegram_alert(alert)
    return ok



def notify_owner_user_joined_canva(email: str) -> bool:
    """
    Called when a customer accesses their /join/<token> link and enters Canva.
    Notifies the owner on Telegram and asks if they want to keep or kick this user.
    """
    if not email:
        return False
    sub = get_subscriber(email)
    if not sub:
        return False

    # If the user has already paid, no need to alert
    if sub.get("payment_status") == "PAID":
        return False

    # Check if a pending join alert has already been sent to avoid duplicate alerts on link reloads
    existing_msg = get_pending_telegram_msg(email)
    if existing_msg:
        return False

    cid = sub.get("customer_id", 800)
    name = sub.get("name") or "Customer"
    pkg = sub.get("package") or "Canva Pro"

    team = get_canva_team_name()
    text = (
        f"🎨 *CUSTOMER JOINED CANVA TEAM ({team})!*\n"
        f"────────────────────────\n"
        f"👤 Customer: {name} (ID: `#{cid}`)\n"
        f"📧 Email: `{email}`\n"
        f"📦 Package: {pkg}\n"
        f"🎨 Team: `{team}`\n"
        f"⏳ Status: 🟡 PENDING PAYMENT\n"
        f"────────────────────────\n"
        f"User has joined your Canva Team. Do you want to keep this user?"
    )
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Keep User (Confirm Paid)", "callback_data": f"sub_paid:{email}"},
                {"text": "🚨 Kick User", "callback_data": f"sub_kick:{email}"}
            ],
            [
                {"text": "🔗 Open Canva Team to Remove Seat", "url": "https://www.canva.com/settings/team-members"}
            ]
        ]
    }
    msg_id = send_telegram_alert(text, reply_markup=keyboard)
    if msg_id:
        set_pending_telegram_msg(email, msg_id)
        return True
    return False



def send_subscription_ended_to_customer(sender_id: str, sender_name: str, page_token: str) -> bool:
    """Sends subscription ended / access revoked notice to customer on Facebook Messenger."""
    if not sender_id or not page_token:
        return False
    text = (
        f"⚠️ আপনার সাবস্ক্রিপশন সমাপ্ত হয়েছে।\n\n"
        f"আসসালামু আলাইকুম {sender_name}!\n"
        f"আপনার Design Hub Canva Pro সাবস্ক্রিপশনটির মেয়াদ শেষ / বাতিল করা হয়েছে এবং টিম থেকে আপনার অ্যাক্সেস রিমুভ করা হয়েছে।\n\n"
        f"আপনি যদি পুনরায় সাবস্ক্রিপশন চালু করতে চান অথবা নতুন কোনো প্যাকেজ নিতে চান, তবে নিচের বাটনে চাপ দিন। ধন্যবাদ! 🎨"
    )
    quick_btns = [
        {"content_type": "text", "title": "🔄 Restart / New Plan", "payload": "ACTION_RESTART"},
        {"content_type": "text", "title": "💬 Support", "payload": "ACTION_RESTART"}
    ]
    return send_fb_message(sender_id, text, page_token, quick_replies=quick_btns)
