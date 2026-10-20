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
from payment_verifier import analyze_payment_screenshot, extract_trx_from_text, verify_payment_against_order, normalize_bd_phone

logger = logging.getLogger("FacebookFunnel")

STATES_FILE = Path(__file__).resolve().parent / "conversation_states.json"
REPLIED_FILE = Path(__file__).resolve().parent / "replied_messages.json"
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "1312971105242105")
def get_allowed_owner_ids() -> list:
    raw = os.getenv("TELEGRAM_ALLOWED_USER_ID", "0")
    ids = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids or [0]

TELEGRAM_ALLOWED_USER_ID = get_allowed_owner_ids()[0]

PACKAGES = {
    "1": {"key": "1m", "name": "১ মাস (২৫ টাকা)", "price": 25, "days": 30},
    "2": {"key": "3m", "name": "৩ মাস (৫০ টাকা)", "price": 50, "days": 90},
    "3": {"key": "6m", "name": "৬ মাস (৯৯ টাকা)", "price": 99, "days": 180},
    "pkg_1m": {"key": "1m", "name": "১ মাস (২৫ টাকা)", "price": 25, "days": 30},
    "pkg_3m": {"key": "3m", "name": "৩ মাস (৫০ টাকা)", "price": 50, "days": 90},
    "pkg_6m": {"key": "6m", "name": "৬ মাস (৯৯ টাকা)", "price": 99, "days": 180},
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


def to_unicode_bold(text: str) -> str:
    """Converts ASCII alphanumeric characters into Unicode Mathematical Bold characters
    so that text displays as actual bold in Facebook Messenger."""
    out = []
    for char in text:
        cp = ord(char)
        if 65 <= cp <= 90:    # A-Z
            out.append(chr(cp - 65 + 0x1d400))
        elif 97 <= cp <= 122: # a-z
            out.append(chr(cp - 97 + 0x1d41a))
        elif 48 <= cp <= 57:  # 0-9
            out.append(chr(cp - 48 + 0x1d7ce))
        else:
            out.append(char)
    return ''.join(out)


def format_messenger_text(text: str) -> str:
    """Transforms **bold text** into genuine Unicode bold and removes the asterisks,
    preventing raw '**' from showing up in Facebook Messenger."""
    if not text:
        return ""
    return re.sub(r'\*\*(.*?)\*\*', lambda m: to_unicode_bold(m.group(1)), str(text))


def send_fb_message(recipient_id: str, text: str, page_token: str, quick_replies=None) -> bool:
    """Send message to customer with quick reply buttons, ALWAYS guaranteeing the Restart button is present."""
    # Convert any **bold** markdown into actual Unicode bold glyphs
    formatted_text = format_messenger_text(text)
    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={page_token}"
    
    if quick_replies is None:
        buttons = [RESTART_BUTTON]
    else:
        buttons = list(quick_replies)
        has_restart = any(b.get("payload") == "ACTION_RESTART" for b in buttons)
        if not has_restart:
            buttons.append(RESTART_BUTTON)

    msg_payload = {
        "text": formatted_text,
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
        {"content_type": "text", "title": "3️⃣ ৬ মাস (৯৯৳)", "payload": "PKG_6M"},
        {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
    ]


def parse_package_choice(text: str):
    """Ultra-fast rule & regex package parser for button payloads and common colloquial text."""
    clean = text.lower().strip()
    if not clean:
        return None

    # Exact matches & payloads
    if clean in ("1", "১", "1m", "pkg_1m", "option 1", "package 1", "১ম") or "১ মাস" in clean or "1 month" in clean:
        return PACKAGES["1"]
    if clean in ("2", "২", "3m", "pkg_3m", "option 2", "package 2", "২য়") or "৩ মাস" in clean or "3 month" in clean:
        return PACKAGES["2"]
    if clean in ("3", "৩", "6m", "pkg_6m", "12m", "pkg_12m", "1y", "option 3", "package 3", "৩য়") or "৬ মাস" in clean or "6 month" in clean or "১ বছর" in clean or "1 year" in clean:
        return PACKAGES["3"]

    # Common Banglish/Bengali regex patterns (e.g. "2 no nite chai", "2 number ta", "50 taka", "৫০৳")
    if re.search(r"\b(1|১)\s*(no|num|number|st|ta|টা|টায়|নম্বর|নং)\b", clean) or re.search(r"\b(25|২৫)\s*(tk|taka|টাকা|৳)\b", clean):
        return PACKAGES["1"]
    if re.search(r"\b(2|২)\s*(no|num|number|nd|ta|টা|টায়|নম্বর|নং)\b", clean) or re.search(r"\b(50|৫০)\s*(tk|taka|টাকা|৳)\b", clean):
        return PACKAGES["2"]
    if re.search(r"\b(3|৩)\s*(no|num|number|rd|ta|টা|টায়|নম্বর|নং)\b", clean) or re.search(r"\b(99|৯৯)\s*(tk|taka|টাকা|৳)\b", clean):
        return PACKAGES["3"]

    return None


def gemini_analyze_customer_message(user_msg: str, sender_name: str = "Customer", current_stage: str = "greeting", current_pkg: str = None) -> dict:
    """Uses Gemini AI to understand complex Bengali, Banglish, English, or typos with human-like conciseness."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {}

    first_name = sender_name.strip().split()[0] if sender_name else "ভাই"

    prompt = (
        f"You are the friendly, smart Facebook Messenger chat assistant for 'Design Hub' (Bangladesh).\n\n"
        f"CORE BRAND & SERVICE FACTS:\n"
        f"- Brand Name: ALWAYS write 'Design Hub' in English. NEVER write 'ডিজাইন হাব' or 'ডিজাইন হাবে'.\n"
        f"- What we sell: Official Canva Pro on personal Gmail.\n"
        f"  • 1 Month: 25 TK\n"
        f"  • 3 Months: 50 TK (Most popular)\n"
        f"  • 6 Months: 99 TK\n"
        f"  • Note: We do NOT have a 1-year package, but plans can be renewed anytime easily.\n"
        f"- Top Features: 100% Private (no one else can see your designs), 1TB Cloud Storage, No team expiry hassle, All Magic AI & Brand Kits unlocked.\n"
        f"- How it works: We give join link first -> you verify Pro -> then pay via bKash/Nagad (01571425035, 01798361516).\n"
        f"- Other Services: We also do custom graphic/poster design.\n"
        f"- Contact / Hotline: 01571425035 (Call or WhatsApp).\n\n"
        f"CONVERSATIONAL STYLE & PERSONALITY RULES (CRITICAL):\n"
        f"1. BE SHORT & PUNCHY: Maximum 1 to 2 short sentences. Answer ONLY what the customer asked. Do NOT write long essays or walls of text.\n"
        f"2. NO REPETITIVE GREETINGS: Do NOT repeat 'আসসালামু আলাইকুম [Full Name] ভাই' in every message. Talk like a friendly human on chat.\n"
        f"3. SHOW EMOTION WITH EMOJIS: Add 1-2 expressive emojis that fit the mood (e.g. 😊, 🙌, 🔒, ✨, ⚡, 💡).\n"
        f"4. NO REDUNDANT PACKAGE LISTS IN TEXT: Do NOT append the list of packages in the message text (the buttons below already show them).\n"
        f"5. HUMAN / ADMIN HANDOVER: If the customer asks to speak with an admin, human, person, or agent, acknowledge immediately and warmly, give the hotline, and say an admin is connecting.\n\n"
        f"Context:\n"
        f"- Customer: {first_name}\n"
        f"- Funnel Stage: {current_stage}\n"
        f"- Package: {current_pkg or 'None'}\n"
        f"- Message: '{user_msg}'\n\n"
        f"Return STRICT JSON ONLY:\n"
        f"{{\n"
        f"  \"intent\": \"PACKAGE_SELECT\" | \"ASK_QUESTION\" | \"TALK_TO_HUMAN\" | \"GIVE_EMAIL\" | \"GENERAL_CHAT\",\n"
        f"  \"selected_package\": 1 | 2 | 3 | null,\n"
        f"  \"extracted_email\": \"valid email or null\",\n"
        f"  \"ai_reply\": \"1-2 short, punchy, emotive sentences in natural Bengali directly answering them.\"\n"
        f"}}"
    )

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
        res = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            },
            timeout=6
        )
        if res.status_code == 200:
            raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
    except Exception as e:
        logger.warning(f"Gemini customer NLU fallback: {e}")

    return {}

    prompt = (
        f"You are the intelligent, polite, and helpful Facebook Messenger Assistant for 'Design Hub' (Bangladesh).\n\n"
        f"ABOUT DESIGN HUB:\n"
        f"- We provide official Canva Pro Subscriptions and Professional Graphic Design Services.\n"
        f"- Canva Pro Subscriptions:\n"
        f"  • Package 1: 1 Month (25 TK)\n"
        f"  • Package 2: 3 Months (50 TK) [Most Popular]\n"
        f"  • Package 3: 6 Months (99 TK)\n"
        f"  • Security: 100% Private (others cannot view designs), 1TB Cloud Storage, No team expiry hassle, Easy extend policy.\n"
        f"  • Payment: bKash / Nagad Personal (01571425035, 01798361516). We provide join link first, customer checks access, then pays!\n"
        f"- Other Services: Professional Graphic Design, Logo Design, Social Media Posters, Brand Kits.\n"
        f"- Official Contact: Hotline 01571425035 (Call/WhatsApp) • Web: designhub.com.bd • Page: fb.com/DesignHub.\n\n"
        f"CONVERSATION CONTEXT:\n"
        f"- Customer Name: {sender_name}\n"
        f"- Current Funnel Stage: {current_stage}\n"
        f"- Selected Package (if any): {current_pkg or 'None yet'}\n"
        f"- Customer Message: '{user_msg}'\n\n"
        f"YOUR TASK:\n"
        f"Analyze the customer's message (which may be in Bengali, Banglish, English, slang, or typos).\n"
        f"Determine their intent:\n"
        f"1. 'PACKAGE_SELECT': Customer selected or wants to change their package (e.g. '2 no nite chai', '50 takar ta', 'change package to 1', 'na 3 month ta nibo').\n"
        f"2. 'GIVE_EMAIL': Customer provided an email address.\n"
        f"3. 'ASK_QUESTION': Customer asked a question about Canva Pro, payment, safety, features, devices, or how it works.\n"
        f"4. 'OFF_TOPIC_OR_GENERAL': Customer asked something unrelated to Canva Pro (e.g. custom graphic design, logo design, company phone/office, casual chit-chat 'kemon achen', or random questions).\n"
        f"5. 'GREETING': Hello / Hi / Salam.\n\n"
        f"RESPONSE GUIDELINES:\n"
        f"- Always reply in warm, natural, respectful Bengali (বাংলা).\n"
        f"- If intent is 'ASK_QUESTION': Answer their question directly, accurately, and reassuringly based on Design Hub policies. If stage is 'awaiting_email', gently append: 'আপনার অ্যাক্সেস সেটআপ করতে আপনার জিমেইলটি (Gmail) লিখে পাঠিয়ে দিন।'\n"
        f"- If intent is 'OFF_TOPIC_OR_GENERAL':\n"
        f"  • If about logo/graphic design: Politely explain that Design Hub does custom graphic/poster design, and ask what they need.\n"
        f"  • If about contact/phone/office: Share hotline 01571425035.\n"
        f"  • If casual greeting/chit-chat ('kemon achen', 'tumi ke'): Reply politely and ask how you can assist them with Canva Pro or design.\n"
        f"  • If completely irrelevant (weather, jokes, random): Politely explain you are the Design Hub assistant for Canva Pro and graphic design services, and ask how you can help them with their design needs.\n"
        f"- If stage is 'awaiting_email' and they haven't given email yet, always remind them politely at the end of your answer: 'আপনার অ্যাক্সেস সেটআপ করতে আপনার জিমেইলটি লিখে দিন।'\n\n"
        f"Return STRICT JSON ONLY:\n"
        f"{{\n"
        f"  \"intent\": \"PACKAGE_SELECT\" | \"GIVE_EMAIL\" | \"ASK_QUESTION\" | \"OFF_TOPIC_OR_GENERAL\" | \"GREETING\",\n"
        f"  \"selected_package\": 1 | 2 | 3 | null,\n"
        f"  \"extracted_email\": \"valid email or null\",\n"
        f"  \"ai_reply\": \"1-3 sentences in natural Bengali answering their question/chat and guiding the next step.\"\n"
        f"}}"
    )

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
        res = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            },
            timeout=6
        )
        if res.status_code == 200:
            raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
    except Exception as e:
        logger.warning(f"Gemini customer NLU fallback: {e}")

    return {}

    prompt = (
        f"You are the official customer assistant for 'Design Hub' on Facebook Messenger in Bangladesh.\n"
        f"We provide Canva Pro subscriptions on personal Gmail:\n"
        f"• Package 1: 1 Month (25 TK)\n"
        f"• Package 2: 3 Months (50 TK) [Most Popular]\n"
        f"• Package 3: 6 Months (99 TK)\n"
        f"• Security Guarantee: 100% Private (others cannot view designs), 1TB Cloud Storage, No team expiry hassle, Easy extend policy.\n"
        f"• Joining Process: Customer selects package -> provides Gmail -> receives join link & joins team -> verifies Pro -> pays via bKash/Nagad (01571425035, 01798361516).\n\n"
        f"Customer Name: {sender_name}\n"
        f"Current Funnel Stage: {current_stage}\n"
        f"Customer Message: '{user_msg}'\n\n"
        f"Analyze the customer's message (which may be in natural Bengali, Banglish, English, or typos).\n"
        f"Return STRICT JSON ONLY:\n"
        f"{{\n"
        f"  \"intent\": \"PACKAGE_SELECT\" | \"ASK_QUESTION\" | \"GIVE_EMAIL\" | \"GREETING\" | \"OTHER\",\n"
        f"  \"selected_package\": 1 | 2 | 3 | null,\n"
        f"  \"extracted_email\": \"valid email address or null\",\n"
        f"  \"ai_reply\": \"A concise, polite, helpful 1-2 sentence response strictly in natural Bengali directly answering their query and politely guiding them to choose a package (1, 2, or 3).\"\n"
        f"}}"
    )

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
        res = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            },
            timeout=5
        )
        if res.status_code == 200:
            raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
    except Exception as e:
        logger.warning(f"Gemini customer NLU fallback: {e}")

    return {}


def handle_incoming_customer_message(sender_id: str, sender_name: str, msg_text: str, msg_id: str, page_token: str, bot_instance=None, image_bytes: bytes = None):
    """Processes customer messages through the 8-step funnel."""
    states = load_states()
    state = states.get(sender_id, {})
    stage = state.get("stage", "greeting")

    clean_text = msg_text.strip().lower()

    # Global Command: Talk to Admin / Human Agent Handover
    is_admin_request = any(k in clean_text for k in [
        "admin", "এডমিন", "এডমিনের", "এডমিনকে", "person", "manush", "মানুষ", 
        "kotha bolte chai", "কথা বলতে চাই", "agent", "এজেন্ট", "call", "কল দিতে চাই"
    ])
    if is_admin_request:
        reply = (
            "অবশ্যই! একটু অপেক্ষা করুন, আমাদের একজন এডমিন এখনই আপনার সাথে যুক্ত হচ্ছেন। 🙋‍♂️\n\n"
            "জরুরি প্রয়োজনে সরাসরি কল বা হোয়াটসঅ্যাপ করতে পারেন আমাদের হটলাইনে: 01571425035 📞"
        )
        quick_btns = [{"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}]
        send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)

        # Notify Owner on Telegram
        alert = (
            f"🙋‍♂️ *HUMAN ASSISTANCE REQUESTED! (Messenger)*\n"
            f"────────────────────────\n"
            f"👤 Customer: {sender_name}\n"
            f"💬 Message: '{msg_text}'\n"
            f"────────────────────────\n"
            f"🔗 [Open Page Inbox](https://business.facebook.com/latest/inbox)"
        )
        send_telegram_alert(alert)
        return

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
                f"• বিকাশ / নগদ (Personal): 01571425035, 01798361516\n\n"
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
            f"৩. ৬ মাস — ৯৯ টাকা\n\n"
            f"অনুগ্রহ করে আপনার পছন্দের প্যাকেজটি বাছাই করুন। অথবা ১, ২ বা ৩ লিখে জানিয়ে দিন:"
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
            f"৩. ৬ মাস (+১৮০ দিন) — ৯৯ টাকা\n\n"
            f"অনুগ্রহ করে আপনার পছন্দের প্যাকেজটি বাছাই করুন। অথবা ১, ২ বা ৩ লিখে জানিয়ে দিন:"
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

        # Derive expected package price
        pkg_price = state.get("package_price")
        if not pkg_price and pkg_info:
            if "25" in str(pkg_info) or "১ মাস" in str(pkg_info):
                pkg_price = 25
            elif "50" in str(pkg_info) or "৩ মাস" in str(pkg_info):
                pkg_price = 50
            elif "99" in str(pkg_info) or "৬ মাস" in str(pkg_info):
                pkg_price = 99


        if proof.get("is_payment_proof"):
            provider = proof.get("provider", "Mobile Banking")
            trx_id = proof.get("trx_id") or "Found in Screenshot"
            amt = proof.get("amount") or "N/A"
            recip_raw = proof.get("recipient") or ""

            # Verify receiver phone number and amount
            verification = verify_payment_against_order(proof, expected_price=pkg_price)
            recip_phone = verification.get("clean_recipient") or recip_raw or "Not detected"

            state["trx_id"] = trx_id
            state["provider"] = provider
            state["amount"] = amt
            state["recipient"] = recip_phone
            state["proof_received"] = True
            states[sender_id] = state
            save_states(states)

            recip_badge = "✅" if verification["receiver_matched"] else "⚠️"
            amt_badge = "✅" if verification["amount_matched"] is True else ("⚠️" if verification["amount_matched"] is False else "")

            # Customer reply logic
            if not verification["receiver_matched"] and verification["clean_recipient"]:
                reply = (
                    f"⚠️ {sender_name}, আপনার স্ক্রিনশটে প্রাপক নম্বরটি ({recip_phone}) আমাদের অফিসিয়াল বিকাশ/নগদ নম্বরের (01571425035, 01798361516) সাথে মেলেনি।\n\n"
                    f"• TrxID: **{trx_id}**\n"
                    f"• পরিমাণ: **{amt}**\n\n"
                    f"আমাদের অ্যাডমিন এটি ম্যানুয়ালি চেক করছেন। আপনি যদি ভুল নম্বরে পাঠিয়ে থাকেন, অনুগ্রহ করে চেক করে জানান।"
                )
            elif verification["amount_matched"] is False:
                reply = (
                    f"ধন্যবাদ {sender_name}! আপনার {provider} পেমেন্ট স্ক্রিনশট পেয়েছি।\n\n"
                    f"• প্রাপক নম্বর: **{recip_phone}** {recip_badge}\n"
                    f"• TrxID: **{trx_id}**\n"
                    f"• পাঠানো পরিমাণ: **{amt}** ⚠️ (প্যাকেজ মূল্য: **{pkg_price}** টাকা)\n\n"
                    f"টাকার পরিমাণে গরমিল থাকায় আমাদের টিম এটি ম্যানুয়ালি পর্যালোচনা করছে।"
                )
            else:
                reply = (
                    f"ধন্যবাদ {sender_name}! আপনার {provider} পেমেন্ট স্ক্রিনশট পেয়েছি।\n\n"
                    f"• প্রাপক নম্বর: **{recip_phone}** {recip_badge}\n"
                    f"• TrxID: **{trx_id}**\n"
                    f"• পরিমাণ: **{amt}** {amt_badge}\n\n"
                    f"আমাদের টিম এটি ভেরিফাই করছে। ভেরিফিকেশন সফল হলেই কনফার্মেশন মেসেজ পাবেন। 🎨"
                )

            quick_btns = [
                {"content_type": "text", "title": "⌛ মেয়াদ বাড়ান (Extend)", "payload": "ACTION_EXTEND"},
                {"content_type": "text", "title": "🔄 Restart", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)

            cid = get_customer_id_by_sender(sender_id, sender_name, email_info)

            receiver_status = f"✅ MATCH (`{recip_phone}`)" if verification["receiver_matched"] else (f"🚨 MISMATCH (`{recip_phone}`)" if recip_phone != "Not detected" else "⚠️ Not Detected")
            amount_status = f"✅ MATCH (`{amt}`)" if verification["amount_matched"] is True else (f"⚠️ MISMATCH (Got `{amt}`, Expected `{pkg_price} TK`)" if verification["amount_matched"] is False else f"ℹ️ `{amt}`")
            auto_status = "🟢 *ALL DETAILS MATCH OFFICIAL DATA!*" if (verification["receiver_matched"] and verification["amount_matched"]) else "🟡 *Attention: Double-check details before approving.*"

            caption = (
                f"📸 *PAYMENT SCREENSHOT OCR & VERIFICATION (Messenger)*\n"
                f"────────────────────────\n"
                f"👤 Customer: {sender_name} (ID: `#{cid}`)\n"
                f"📧 Email: `{email_info}`\n"
                f"📦 Package: {pkg_info} ({pkg_price or 'N/A'} TK)\n"
                f"📱 Provider: {provider}\n"
                f"📞 Receiver: {receiver_status}\n"
                f"💵 Amount: {amount_status}\n"
                f"🔢 TrxID: `{trx_id}`\n"
                f"────────────────────────\n"
                f"{auto_status}"
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

    # STEP 1 & 2: Greeting & Package Selection (Powered by Hybrid Regex + Gemini AI)
    if stage in ("greeting", "awaiting_package"):
        # 1. Fast regex/button check
        pkg = parse_package_choice(msg_text)
        ai_analysis = {}

        if not pkg:
            # 2. Gemini AI Natural Language Understanding (Bengali / Banglish / English)
            ai_analysis = gemini_analyze_customer_message(msg_text, sender_name, stage)
            sel_pkg_num = ai_analysis.get("selected_package")
            if sel_pkg_num in (1, 2, 3, "1", "2", "3"):
                pkg = PACKAGES[str(sel_pkg_num)]

        if pkg:
            # Check if customer also included their email in the same message
            email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", msg_text)
            extracted_email = email_match.group(0).lower() if email_match else ai_analysis.get("extracted_email")

            if extracted_email and "@" in extracted_email:
                # Both package and email provided in one shot! Advance directly to confirmation!
                state["stage"] = "awaiting_confirm"
                state["package_key"] = pkg["key"]
                state["package_name"] = pkg["name"]
                state["package_price"] = pkg["price"]
                state["sender_name"] = sender_name
                state["email"] = extracted_email
                state["saved_email"] = extracted_email
                states[sender_id] = state
                save_states(states)

                reply = (
                    f"✅ প্যাকেজ: **{pkg['name']}**\n"
                    f"📧 জিমেইল: **{extracted_email}**\n\n"
                    f"সবকিছু সঠিক থাকলে নিচের '✅ Confirm & Get Link' বাটনে চাপ দিন :"
                )
                quick_btns = [
                    {"content_type": "text", "title": "✅ Confirm & Get Link", "payload": f"CONFIRM_YES:{extracted_email}"},
                    {"content_type": "text", "title": "🔄 Change / Restart", "payload": "ACTION_RESTART"}
                ]
                send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
                return

            # Move to Step 3: Ask for Gmail
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

        # Check if customer sent only email first
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", msg_text)
        if email_match:
            email = email_match.group(0).lower()
            state["email"] = email
            state["saved_email"] = email
            state["stage"] = "awaiting_package"
            states[sender_id] = state
            save_states(states)

            reply = (
                f"ধন্যবাদ {sender_name}! আপনার জিমেইল ({email}) পেয়েছি।\n\n"
                f"এখন অনুগ্রহ করে নিচের বাটন থেকে আপনার পছন্দের প্যাকেজটি বেছে নিন অথবা লিখে জানান:"
            )
            send_fb_message(sender_id, reply, page_token, quick_replies=get_package_buttons())
            return

        # If customer asked a question (related, unrelated, or general chat)
        if ai_analysis.get("ai_reply"):
            states[sender_id] = {"stage": "awaiting_package", "sender_name": sender_name}
            save_states(states)

            # Check if intent was human handover
            if ai_analysis.get("intent") == "TALK_TO_HUMAN":
                alert = (
                    f"🙋‍♂️ *HUMAN ASSISTANCE REQUESTED! (Messenger)*\n"
                    f"────────────────────────\n"
                    f"👤 Customer: {sender_name}\n"
                    f"💬 Message: '{msg_text}'\n"
                    f"────────────────────────\n"
                    f"🔗 [Open Page Inbox](https://business.facebook.com/latest/inbox)"
                )
                send_telegram_alert(alert)

            # Reply with crisp, personalized AI response + keep buttons (no text redundancy!)
            reply = ai_analysis["ai_reply"]
            send_fb_message(sender_id, reply, page_token, quick_replies=get_package_buttons())
            return

        # First touch greeting & show packages
        states[sender_id] = {"stage": "awaiting_package", "sender_name": sender_name}
        save_states(states)
        reply = (
            f"আসসালামু আলাইকুম {sender_name}! 🎨 Design Hub-এ আপনাকে স্বাগতম।\n\n"
            f"আমরা দিচ্ছি অফিসিয়াল Canva Pro এডুকেশন টিম অ্যাক্সেস (নিজের পার্সোনাল জিমেইলে এক্টিভ হবে)।\n\n"
            f"📦 আপনি কোন প্যাকেজটি নিতে চান?\n"
            f"১. ১ মাস — ২৫ টাকা\n"
            f"২. ৩ মাস — ৫০ টাকা\n"
            f"৩. ৬ মাস — ৯৯ টাকা\n\n"
            f"অনুগ্রহ করে আপনার পছন্দের প্যাকেজটি বাছাই করুন। অথবা ১, ২ বা ৩ লিখে জানিয়ে দিন:"
        )
        send_fb_message(sender_id, reply, page_token, quick_replies=get_package_buttons())
        return

    # STEP 3 & 4: Ask for Gmail & Show Confirmation with Package & Email (Intelligent Q&A Enabled)
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
                f"সবকিছু সঠিক থাকলে নিচের '✅ Confirm & Get Link' বাটনে চাপ দিন :"
            )
            quick_btns = [
                {"content_type": "text", "title": "✅ Confirm & Get Link", "payload": f"CONFIRM_YES:{email}"},
                {"content_type": "text", "title": "🔄 Change / Restart", "payload": "ACTION_RESTART"}
            ]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
            return
        else:
            # Customer sent a message without email (could be a question, package change, or off-topic query)
            cur_pkg_name = state.get("package_name")
            ai = gemini_analyze_customer_message(msg_text, sender_name, stage, cur_pkg_name)

            sel_pkg_num = ai.get("selected_package")
            direct_pkg = parse_package_choice(msg_text)

            # Only switch package if intent is genuinely PACKAGE_SELECT or user explicitly typed package name
            is_package_change = (
                direct_pkg is not None
                or (ai.get("intent") == "PACKAGE_SELECT" and sel_pkg_num in (1, 2, 3, "1", "2", "3"))
            )

            if is_package_change:
                new_pkg = direct_pkg or PACKAGES[str(sel_pkg_num)]
                state["package_key"] = new_pkg["key"]
                state["package_name"] = new_pkg["name"]
                state["package_price"] = new_pkg["price"]
                states[sender_id] = state
                save_states(states)

                reply = (
                    f"✅ প্যাকেজ পরিবর্তন করে **{new_pkg['name']}** করা হয়েছে।\n\n"
                    f"এখন আপনার যে জিমেইলে (Gmail) Canva Pro অ্যাক্সেস নিতে চান, অনুগ্রহ করে সেই জিমেইলটি লিখে পাঠিয়ে দিন:"
                )
                quick_btns = [{"content_type": "text", "title": "🔄 Change Package", "payload": "ACTION_RESTART"}]
                send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
                return

            # If customer asked any question (subscription related OR general / off-topic)
            if ai.get("ai_reply"):
                reply = ai["ai_reply"]
                quick_btns = [{"content_type": "text", "title": "🔄 Change Package", "payload": "ACTION_RESTART"}]
                send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
                return

            # Default fallback if AI was unavailable
            reply = "আপনার ক্যানভা প্রো সেটআপ করতে অনুগ্রহ করে আপনার একটি সঠিক জিমেইল (Gmail) অ্যাড্রেস লিখে পাঠান (যেমন: yourname@gmail.com):"
            quick_btns = [{"content_type": "text", "title": "🔄 Change Package", "payload": "ACTION_RESTART"}]
            send_fb_message(sender_id, reply, page_token, quick_replies=quick_btns)
            return

    # STEP 5: Customer Confirms -> Send 10-Minute Expiring Link + Request Payment
    if stage == "awaiting_confirm":
        positive_keywords = ["yes", "হ্যাঁ", "ha", "y", "confirm", "হাঁ", "thik ache", "ঠিক আছে", "হ্যা", "confirm_yes", "ok", "okay", "accha", "den", "link den", "sure", "হবে", "হ", "পাবো"]
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
                f"আপনার Canva Pro টিম জয়েন লিংক নিচে দেওয়া হলো:\n\n"
                f"🔗 {join_url}\n\n"
                f"⚠️ গুরুত্বপূর্ণ: এই লিংকটি আগামী ৩০ মিনিটের জন্য সক্রিয় থাকবে। এখনই লিংকে ক্লিক করে আপনার টিমে যুক্ত হয়ে নিন।\n\n"
                f"💳 পেমেন্ট তথ্য:\n"
                f"• প্যাকেজ: {pkg_name}\n"
                f"• বিকাশ / নগদ (Personal): 01571425035, 01798361516\n\n"
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
            f"ℹ️ {sender_name}, আপনার Canva Pro জয়েন লিংক:\n\n"
            f"🔗 {join_url}\n\n"
            f"💳 পেমেন্ট তথ্য:\n"
            f"• বিকাশ / নগদ (Personal): 01571425035, 01798361516\n\n"
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
