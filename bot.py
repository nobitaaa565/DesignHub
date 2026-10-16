#!/usr/bin/env python3
"""
Telegram Bot to Automate Facebook Page Publishing & Comment Auto-Replies (Design Hub)
Features:
- Direct Text & Photo Publishing to Facebook
- AI Post Drafting via Google Gemini 3.5 Flash
- AI Image Generation with Matching Captions
- 1-Tap Inline Button Previews & Approvals
- 24/7 Automated Comment Responder with Keyword Matching
- Instant Telegram Alerts for Every Handled Comment
- /comments Command for On-Demand Comment Scanning
"""

import os
import re
import sys
import json
import asyncio
import logging
import urllib.parse
from pathlib import Path
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from canva_worker import invite_canva_member, kick_canva_member, is_canva_authenticated
from facebook_funnel import handle_incoming_customer_message, send_payment_confirmed_to_customer, send_expiry_reminder_to_customer, send_subscription_ended_to_customer, notify_owner_user_joined_canva, load_replied_ids, save_replied_ids
from payment_verifier import analyze_payment_screenshot, extract_trx_from_text
from subscription_manager import (
    delete_subscriber,
    create_expiring_invite,
    extract_email_from_token,
    consume_expiring_invite,
    add_subscriber,
    mark_paid,
    kick_subscriber,
    extend_subscriber,
    get_subscriber,
    list_subscribers,
    get_db_stats,
    make_subscriber_keyboard,
    format_subscriber_card,
    get_subscribers_expiring_soon,
    clear_pending_telegram_msg,
    record_payment,
    get_all_payments,
    get_total_earnings,
    get_canva_team_name,
    set_canva_team_name,
    update_subscriber,
    update_payment,
    delete_payment,
    get_all_teams,
    add_team,
    delete_team
)
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Load configuration with absolute path resolution
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DATA_FILE = Path(__file__).resolve().parent / "replied_comments.json"

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Temporary in-memory storage for pending post drafts
PENDING_POSTS = {}


# ==================== AUTH & UTILS ====================

def check_auth(user_id: int) -> bool:
    """Security check to ensure only the authorized owner can use the bot."""
    if not ALLOWED_USER_ID:
        return True
    try:
        return str(user_id) == str(ALLOWED_USER_ID)
    except Exception:
        return False


def get_fb_page_info():
    """Fetch Facebook Page details to confirm live status."""
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}"
    params = {"fields": "id,name,link,fan_count", "access_token": FB_PAGE_ACCESS_TOKEN}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        logger.error(f"Error fetching page info: {e}")
    return None


def call_gemini(prompt: str, system_prompt: str = "") -> str:
    """Call Google Gemini 3.5 Flash for post drafting and copywriting."""
    if not GEMINI_API_KEY:
        return ""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
    full_prompt = f"{system_prompt}\n\nTask: {prompt}" if system_prompt else prompt
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            logger.error(f"Gemini API error ({res.status_code}): {res.text}")
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
    return ""


def generate_image_bytes(prompt: str) -> bytes:
    """Generate image using AI generation engine."""
    clean_prompt = urllib.parse.quote(prompt.strip())
    url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&nologo=true"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200 and len(res.content) > 1000:
            return res.content
    except Exception as e:
        logger.error(f"Image generation error: {e}")
    return b""


def publish_text_to_fb(message: str) -> dict:
    """Publish plain text post to Facebook Page feed."""
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload, timeout=20)
    return res.json()


def publish_photo_to_fb(image_bytes: bytes, caption: str = "") -> dict:
    """Publish photo post with caption to Facebook Page."""
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    files = {"source": ("image.jpg", image_bytes, "image/jpeg")}
    data = {"access_token": FB_PAGE_ACCESS_TOKEN}
    if caption:
        data["caption"] = caption
    res = requests.post(url, data=data, files=files, timeout=30)
    return res.json()


# ==================== AUTO-COMMENT RESPONDER ENGINE ====================

def load_replied_ids() -> set:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_replied_ids(ids: set):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(list(ids), f, indent=2)
    except Exception as e:
        logger.error(f"Error saving replied IDs: {e}")


# High-converting automatic greeting and package templates (Bengali & English)
GREETING_PACKAGE_BN = (
    "হ্যালো {name}! 👋 Design Hub-এ আপনাকে স্বাগতম।\n"
    "আপনার নিজস্ব পার্সোনাল জিমেইলেই (Gmail) পাচ্ছেন ১০০% অফিসিয়াল Canva Pro লাইসেন্স! কোনো পাসওয়ার্ডের প্রয়োজন নেই—সম্পূর্ণ নিরাপদ ও প্রাইভেট। 🔒✨\n\n"
    "🔥 আমাদের স্পেশাল প্যাকেজসমূহ:\n"
    "⭐ ১ মাস — মাত্র ২৫ টাকা\n"
    "⚡ ৩ মাস — মাত্র ৫০ টাকা (🔥 সর্বাধিক জনপ্রিয় • Access First, Pay Later)\n"
    "🚀 ৬ মাস — মাত্র ৯৯ টাকা (সেরা ভ্যালু)\n\n"
    "✨ যে যে সুবিধাগুলো পাবেন:\n"
    "• ১০০M+ প্রিমিয়াম ফটো, ভিডিও, অডিও ও গ্রাফিক্স\n"
    "• ১-ক্লিকে AI ব্যাকগ্রাউন্ড রিমুভার ও ম্যাজিক টুলস\n"
    "• ৩,০০০+ প্রিমিয়াম ফন্ট ও ব্র্যান্ড কিট অ্যাক্সেস\n"
    "• ২ মিনিটে ইনস্ট্যান্ট অ্যাক্টিভেশন গ্যারান্টি\n"
    "🛡️ আমাদের বিশেষ সুবিধা: \"আগে অ্যাক্সেস পেয়ে চেক করে নিন, তারপর নিশ্চিন্তে পেমেন্ট করুন!\"\n\n"
    "অনুগ্রহ করে আপনার পছন্দের প্যাকেজটি বাছাই করুন। অথবা ১, ২ বা ৩ লিখে জানিয়ে দিন:"
)

GREETING_PACKAGE_EN = (
    "Hello {name}! 👋 Welcome to Design Hub.\n\n"
    "Get official, full-featured Canva Pro access directly on your own personal email (100% Private, Secure & No password required)! 🔒✨\n\n"
    "🔥 Special Package Deals:\n"
    "⭐ 1 Month  — 25 TK\n"
    "⚡ 3 Months — 50 TK (🔥 Most Popular • Access First, Pay Later)\n"
    "🚀 6 Months — 99 TK (Best Value Deal)\n\n"
    "✨ What You Unlock:\n"
    "• 100M+ Premium Stock Photos, Videos, Audio & Graphics\n"
    "• 1-Click AI Magic Background Remover & Magic Eraser\n"
    "• 3,000+ Premium Fonts, Unlimited Folders & Brand Kit\n"
    "• Instant 2-Minute Activation Guarantee\n\n"
    "🛡️ Zero Risk Policy: Access First, Check Everything, Then Pay!\n\n"
    "👉 Please select your desired package or reply with 1, 2, or 3 in our Inbox! 🎨📩"
)

ORDER_DIRECT_BN = (
    "হ্যালো {name}! 😊 Design Hub-এ যোগাযোগ করার জন্য ধন্যবাদ।\n"
    "আপনার নিজস্ব জিমেইল অ্যাকাউন্টে অফিসিয়াল Canva Pro চালু করতে:\n"
    "🔥 আমাদের স্পেশাল প্যাকেজসমূহ:\n"
    "⭐ ১ মাস — মাত্র ২৫ টাকা\n"
    "⚡ ৩ মাস — মাত্র ৫০ টাকা (🔥 সর্বাধিক জনপ্রিয় • Access First, Pay Later)\n"
    "🚀 ৬ মাস — মাত্র ৯৯ টাকা (সেরা ভ্যালু)\n\n"
    "🛡️ সুবিধা: আগে অ্যাক্সেস নিন, চেক করুন, তারপর পেমেন্ট করুন!\n\n"
    "অনুগ্রহ করে আপনার পছন্দের প্যাকেজটি বাছাই করুন। অথবা ১, ২ বা ৩ লিখে জানিয়ে দিন:"
)

ORDER_DIRECT_EN = (
    "Hi {name}! 😊 Thank you for your interest in Design Hub.\n\n"
    "We provide official Canva Pro on your own personal email address (Access First, Pay Later)!\n"
    "⚡ Packages: 1 Mo (25 TK) | 3 Mo (50 TK) | 6 Mo (99 TK)\n\n"
    "🛡️ Benefit: Access First, Check Everything, Then Pay!\n\n"
    "👉 Please select your desired package or reply with 1, 2, or 3 in our Inbox!"
)

def is_bengali(text: str) -> bool:
    """Check if the text contains Bengali script."""
    return any("\u0980" <= c <= "\u09ff" for c in text)


def determine_reply(message: str, user_name: str) -> str:
    msg = message.lower()
    order_keywords = ["inbox", "buy", "order", "lagbe", "setup", "চাই", "deben", "how to buy", "কিনব", "নেব", "অর্ডার"]
    bengali_keywords = ["কত", "টাকা", "দাম", "চাই", "প্যাকেজ", "অফার", "ক্যানভা", "কেমনে", "ভাই", "দিবেন"]

    has_order = any(k in msg for k in order_keywords)
    has_bengali = is_bengali(message) or any(k in msg for k in bengali_keywords)

    if has_order:
        return ORDER_DIRECT_BN.format(name=user_name) if has_bengali else ORDER_DIRECT_EN.format(name=user_name)
    else:
        # Default high-converting greeting & package message for all initial comments
        return GREETING_PACKAGE_BN.format(name=user_name) if has_bengali else GREETING_PACKAGE_EN.format(name=user_name)


def send_telegram_alert_sync(user_name: str, comment_text: str, reply_text: str, post_id: str):
    if not TELEGRAM_BOT_TOKEN or not ALLOWED_USER_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    text = (
        f"🔔 *New Facebook Comment Handled!*\n\n"
        f"👤 *User:* {user_name}\n"
        f"💬 *Comment:* \"{comment_text}\"\n"
        f"🤖 *Auto-Reply Sent:*\n_{reply_text}_\n\n"
        f"🔗 Post: https://facebook.com/{post_id}"
    )
    payload = {
        "chat_id": ALLOWED_USER_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")


def post_fb_comment_reply(comment_id: str, reply_text: str) -> bool:
    url = f"https://graph.facebook.com/v20.0/{comment_id}/comments"
    payload = {
        "message": reply_text,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    try:
        res = requests.post(url, data=payload, timeout=15)
        if res.status_code == 200 and "id" in res.json():
            logger.info(f"Replied to comment {comment_id}: {res.json().get('id')}")
            return True
        else:
            logger.error(f"Failed to reply to comment {comment_id}: {res.text}")
            return False
    except Exception as e:
        logger.error(f"Exception replying to comment {comment_id}: {e}")
        return False


def check_and_reply_comments() -> dict:
    """Scans all posts on the page and auto-replies to new comments."""
    replied_ids = load_replied_ids()
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    params = {
        "fields": "id,message,comments{id,from,message,created_time,comments{id,from}}",
        "access_token": FB_PAGE_ACCESS_TOKEN
    }

    stats = {"scanned_posts": 0, "replied_count": 0}

    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code != 200:
            logger.error(f"Error fetching feed: {res.text}")
            return stats

        posts = res.json().get("data", [])
        stats["scanned_posts"] = len(posts)

        for post in posts:
            post_id = post.get("id")
            comments = post.get("comments", {}).get("data", [])

            for c in comments:
                c_id = c.get("id")
                c_from = c.get("from", {})
                from_id = c_from.get("id")
                from_name = c_from.get("name", "Friend")
                c_msg = c.get("message", "")

                # Skip if already replied or if comment is from page itself
                if c_id in replied_ids or from_id == FB_PAGE_ID:
                    continue

                # Check if page already replied in nested comments
                nested = c.get("comments", {}).get("data", [])
                already_replied = any(n.get("from", {}).get("id") == FB_PAGE_ID for n in nested)
                if already_replied:
                    replied_ids.add(c_id)
                    save_replied_ids(replied_ids)
                    continue

                # Determine the readymade reply
                reply = determine_reply(c_msg, from_name)
                logger.info(f"Auto-replying to {from_name} on post {post_id}: '{c_msg}'")

                # Send reply to Facebook
                success = post_fb_comment_reply(c_id, reply)
                if success:
                    replied_ids.add(c_id)
                    save_replied_ids(replied_ids)
                    stats["replied_count"] += 1
                    send_telegram_alert_sync(from_name, c_msg, reply, post_id)

    except Exception as e:
        logger.error(f"Error checking comments: {e}")

    return stats


REPLIED_MSGS_FILE = Path(__file__).resolve().parent / "replied_messages.json"


def load_replied_msgs():
    if REPLIED_MSGS_FILE.exists():
        try:
            with open(REPLIED_MSGS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_replied_msgs(ids):
    try:
        with open(REPLIED_MSGS_FILE, "w") as f:
            json.dump(list(ids)[-1000:], f)
    except Exception:
        pass


CONV_STATES_FILE = Path(__file__).resolve().parent / "conversation_states.json"


def load_conv_states() -> dict:
    if CONV_STATES_FILE.exists():
        try:
            with open(CONV_STATES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_conv_states(states: dict):
    try:
        with open(CONV_STATES_FILE, "w") as f:
            json.dump(states, f)
    except Exception:
        pass


def send_fb_message(recipient_id: str, message_text: str, token: str, quick_replies=None) -> bool:
    """Send text message directly to a customer in Facebook Messenger inbox with optional quick reply buttons."""
    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={token}"
    msg_payload = {"text": message_text}
    if quick_replies:
        msg_payload["quick_replies"] = quick_replies

    payload = {
        "recipient": {"id": recipient_id},
        "message": msg_payload
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Error sending Messenger reply: {e}")
        return False


def check_and_reply_inbox(bot=None):
    """Scans Facebook Messenger inbox and delegates to the 8-step sales funnel."""
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    page_id = os.getenv("FB_PAGE_ID", "1312971105242105")
    if not token or not page_id:
        return

    replied = load_replied_ids()
    url = f"https://graph.facebook.com/v20.0/{page_id}/conversations?fields=messages{{message,from,created_time,attachments{{mime_type,image_data,file_url}}}}&access_token={token}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return
        data = r.json().get("data", [])
        for conv in data:
            messages = conv.get("messages", {}).get("data", [])
            if not messages:
                continue
            latest_msg = messages[0]
            msg_id = latest_msg.get("id")
            sender = latest_msg.get("from", {})
            sender_id = sender.get("id")
            sender_name = sender.get("name", "Customer")
            msg_text = latest_msg.get("message", "").strip()
            qr = latest_msg.get("quick_reply", {})
            qr_payload = qr.get("payload", "").strip() if isinstance(qr, dict) else ""
            pb = latest_msg.get("postback", {})
            pb_payload = pb.get("payload", "").strip() if isinstance(pb, dict) else ""
            if qr_payload:
                msg_text = f"{msg_text} {qr_payload}".strip() if msg_text else qr_payload
            if pb_payload:
                msg_text = f"{msg_text} {pb_payload}".strip() if msg_text else pb_payload

            attachments = latest_msg.get("attachments", {}).get("data", [])
            image_url = None
            for att in attachments:
                if att.get("image_data", {}).get("url"):
                    image_url = att["image_data"]["url"]
                    break
                elif "image" in att.get("mime_type", ""):
                    image_url = att.get("file_url") or att.get("image_data", {}).get("url")
                    break
                elif att.get("file_url") and any(ext in att.get("file_url", "").lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    image_url = att["file_url"]
                    break

            if not sender_id or sender_id == page_id or msg_id in replied or (not msg_text and not image_url):
                continue

            image_bytes = None
            if image_url:
                try:
                    img_resp = requests.get(image_url, timeout=15)
                    if img_resp.status_code == 200:
                        image_bytes = img_resp.content
                        logger.info(f"📸 Downloaded screenshot from Messenger ({len(image_bytes)} bytes)")
                except Exception as e:
                    logger.error(f"Error downloading attachment image: {e}")

            # Process through the 8-step conversational funnel
            handle_incoming_customer_message(
                sender_id=sender_id,
                sender_name=sender_name,
                msg_text=msg_text,
                msg_id=msg_id,
                page_token=token,
                bot_instance=bot,
                image_bytes=image_bytes
            )
            replied.add(msg_id)

        save_replied_ids(replied)
    except Exception as e:
        logger.error(f"Error in check_and_reply_inbox: {e}")


async def comment_monitor_loop(bot=None):
    """Background async worker that runs every 15 seconds for rapid inbox & comment replies."""
    global _bot_instance
    if bot:
        _bot_instance = bot
    logger.info("🚀 Background Inbox & Comment Auto-Responder active (15s rapid interval).")
    while True:
        try:
            await asyncio.to_thread(check_and_reply_inbox, _bot_instance)
            await asyncio.to_thread(check_and_reply_comments, _bot_instance)
        except asyncio.CancelledError:
            logger.info("Monitor loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in background loop: {e}")
        await asyncio.sleep(15)


async def expiry_reminder_loop(bot=None):
    """Background async worker that checks every 2 hours for subscribers expiring within 7 days and sends renewal reminders."""
    logger.info("⏰ Background Expiry Reminder Worker active (2-hour check cycle).")
    while True:
        try:
            token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
            if token:
                expiring = await asyncio.to_thread(get_subscribers_expiring_soon, 7)
                for sub in expiring:
                    fb_id = sub.get("fb_sender_id")
                    if fb_id:
                        await asyncio.to_thread(
                            send_expiry_reminder_to_customer,
                            fb_sender_id=fb_id,
                            sender_name=sub.get("name", "Customer"),
                            customer_id=sub.get("customer_id", 800),
                            email=sub.get("email"),
                            expires_at=sub.get("expires_at"),
                            page_token=token
                        )
                        await asyncio.sleep(2)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in expiry_reminder_loop: {e}")
        await asyncio.sleep(2 * 3600)


# ==================== TELEGRAM COMMANDS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    page_info = get_fb_page_info()
    page_name = page_info.get("name", "Facebook Page") if page_info else "Disconnected"
    ai_status = "🟢 Google Gemini 3.5 Flash Online" if GEMINI_API_KEY else "⚪ AI Key Inactive"

    msg = (
        f"👋 Welcome, {user.first_name}!\n\n"
        f"📱 *Design Hub Automation Center*\n"
        f"• Facebook: *{page_name}*\n"
        f"• AI Engine: *{ai_status}*\n"
        f"• Auto-Comments: *🟢 Active (60s loop)*\n\n"
        f"👥 *Subscriber Management:*\n"
        f"• `/add <email> [1m/3m/12m]` — Add subscriber & generate 1-tap card\n"
        f"• `/paid <email>` — Confirm bKash/Nagad payment received\n"
        f"• `/kick <email>` — Manually revoke & kick user access\n"
        f"• `/extend <email> [1m/3m/12m]` — Extend plan duration\n"
        f"• `/subs` — View active & pending subscribers\n"
        f"• `/check <email>` — Inspect subscriber status & actions\n\n"
        f"⚡ *Facebook Page Automation:*\n"
        f"• ✍️ `/ai <topic>` — Gemini viral post in Bangla or English\n"
        f"• 🎨 `/image <prompt>` — AI image with tailored caption\n"
        f"• 💬 `/comments` — Scan & auto-reply to Facebook comments\n"
        f"• 📷 *Send photo/text* — Preview with language selection\n"
        f"• 📊 `/status` — System health & subscriber stats\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    page_info = get_fb_page_info()
    fb_status = f"🟢 Connected ({page_info.get('name')})" if page_info else "🔴 Disconnected"
    ai_status = "🟢 Gemini 3.5 Flash (Active)" if GEMINI_API_KEY else "🔴 Inactive"
    replied_ids = load_replied_ids()

    stats = get_db_stats()
    earnings = get_total_earnings()
    team_name = get_canva_team_name()
    status_msg = (
        f"📊 *Design Hub — System Status*\n"
        f"────────────────────────\n"
        f"🎨 *Active Canva Team:* `{team_name}`\n"
        f"💰 *Total Revenue Earned:* `৳{earnings['total_bdt']:,.2f}` BDT ({earnings['total_count']} payments)\n"
        f"🌐 *Facebook Page:* {fb_status}\n"
        f"🆔 *Page ID:* `{FB_PAGE_ID}`\n"
        f"💬 *Comment Auto-Responder:* 🟢 Active (Every 60s)\n"
        f"📬 *Comments Handled:* `{len(replied_ids)}`\n"
        f"🤖 *AI Vision & Engine:* 🟢 Gemini 3.8 Flash\n"
        f"────────────────────────\n"
        f"👥 *Customer Overview:*\n"
        f"• 👥 *Total Customers:* `{stats['total']}`\n"
        f"• 🟢 *Active Paid Members:* `{stats['active_paid']}`\n"
        f"• 🟡 *Pending Payments:* `{stats['pending']}`\n"
        f"• 🔴 *Kicked / Revoked:* `{stats['kicked']}`\n"
        f"────────────────────────\n"
        f"💡 *Commands:* `/earnings` for ledger | `/team` for Canva team"
    )
    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def team_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return
    args = context.args
    if args:
        new_name = " ".join(args).strip()
        saved = set_canva_team_name(new_name)
        await update.message.reply_text(
            f"✅ *Canva Team Name Updated!*\n"
            f"────────────────────────\n"
            f"🎨 *Active Team:* `{saved}`\n"
            f"🌐 Synced to Web Dashboard & Messenger Funnel\n"
            f"🔗 [Open Canva Seat Roster](https://www.canva.com/settings/team-members)",
            parse_mode="Markdown"
        )
    else:
        curr = get_canva_team_name()
        await update.message.reply_text(
            f"🎨 *Design Hub — Active Canva Team*\n"
            f"────────────────────────\n"
            f"📌 *Current Team Name:* `{curr}`\n"
            f"🔗 [Manage Seats in Canva Settings](https://www.canva.com/settings/team-members)\n\n"
            f"✏️ *To change team name:*\n"
            f"`/team <New Team Name>`\n"
            f"Example: `/team Carmella Elan`",
            parse_mode="Markdown"
        )


async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return
    earnings = get_total_earnings()
    stats = get_db_stats()
    payments = get_all_payments(limit=5)
    
    rec_lines = []
    for p in payments:
        trx_str = f" (`{p['trx_id']}`)" if p['trx_id'] else ""
        rec_lines.append(f"• ৳{p['amount']:.2f} — #{p['customer_id']} ({p['package']}){trx_str}")
    rec_str = "\n".join(rec_lines) if rec_lines else "No transactions recorded yet."

    await update.message.reply_text(
        f"💰 *Design Hub — Revenue & Earnings*\n"
        f"────────────────────────\n"
        f"💵 *Total Earned:* `৳{earnings['total_bdt']:,.2f}` BDT\n"
        f"🧾 *Total Payments:* `{earnings['total_count']}` verified\n"
        f"👥 *Active Paid Users:* `{stats['active_paid']}`\n"
        f"🎨 *Canva Team:* `{get_canva_team_name()}`\n"
        f"────────────────────────\n"
        f"📜 *Recent Payments:*\n"
        f"{rec_str}\n\n"
        f"🌐 [Open Minimal Web Dashboard](https://designhub-1any.onrender.com)",
        parse_mode="Markdown"
    )


async def scan_comments_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    status_msg = await update.message.reply_text("🔍 *Scanning Facebook Page for new comments...*", parse_mode="Markdown")
    stats = await asyncio.to_thread(check_and_reply_comments)

    res_text = (
        f"✅ *Comment Scan Complete!*\n\n"
        f"• Posts Scanned: `{stats.get('scanned_posts', 0)}`\n"
        f"• New Comments Replied: `{stats.get('replied_count', 0)}`\n"
        f"• Next automated scan in ~60 seconds."
    )
    await status_msg.edit_text(res_text, parse_mode="Markdown")


async def ai_draft_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "💡 *Usage:* `/ai <topic>`\n*Example:* `/ai 5 reasons to upgrade to Canva Pro today for freelancers`",
            parse_mode="Markdown"
        )
        return

    topic = " ".join(context.args)
    status_msg = await update.message.reply_text("🤖 *Gemini is writing your Facebook post...*", parse_mode="Markdown")

    system_prompt = (
        "You are an expert social media manager for 'Design Hub', a Facebook page providing premium creative "
        "assets, Canva Pro access, graphic design tips, and design tool subscriptions to creators and businesses. "
        "Write a punchy, highly engaging Facebook post. Include a catchy hook, 2-3 value bullet points, "
        "a clear Call to Action (e.g. 'Send a message to get yours now!'), and 3-5 relevant hashtags."
    )
    generated_text = call_gemini(topic, system_prompt)

    if not generated_text:
        await status_msg.edit_text("❌ Failed to generate with Gemini. Please try again.")
        return

    PENDING_POSTS[user.id] = {"type": "text", "content": generated_text, "topic": topic}

    reply_markup = get_post_keyboard("text")

    preview = (
        f"🤖 *AI Generated Post:*\n"
        f"────────────────────────\n"
        f"{generated_text}\n"
        f"────────────────────────\n"
        f"Publish this to *Design Hub*?"
    )
    await status_msg.edit_text(preview, reply_markup=reply_markup)


async def image_gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "💡 *Usage:* `/image <description>`\n*Example:* `/image Modern Canva Pro promotional banner, purple gradient, 4k`",
            parse_mode="Markdown"
        )
        return

    prompt = " ".join(context.args)
    status_msg = await update.message.reply_text("🎨 *Generating AI image & caption...*", parse_mode="Markdown")

    caption_prompt = f"Write a 2-sentence engaging Facebook caption with 3 hashtags for a post showcasing: {prompt}"
    caption = call_gemini(caption_prompt) or "✨ Transform your workflow with Design Hub!\n\n#DesignHub #CreativeTools #GraphicDesign"

    img_bytes = generate_image_bytes(prompt)
    if not img_bytes:
        await status_msg.edit_text("❌ Failed to generate image. Please try a different prompt.")
        return

    PENDING_POSTS[user.id] = {
        "type": "photo",
        "image_bytes": img_bytes,
        "caption": caption,
        "prompt": prompt
    }

    keyboard = [
        [
            InlineKeyboardButton("🚀 Publish Photo to FB", callback_data="publish_confirm"),
            InlineKeyboardButton("🔄 Regenerate", callback_data="image_regen")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="publish_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await status_msg.delete()
    await update.message.reply_photo(
        photo=img_bytes,
        caption=f"📝 *Caption:*\n{caption}\n\nPublish to *Design Hub*?",
        reply_markup=reply_markup
    )


async def quick_post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: `/post Your message here`", parse_mode="Markdown")
        return

    text = " ".join(context.args)
    await update.message.reply_text("⏳ Publishing directly to Facebook...")

    res = publish_text_to_fb(text)
    if "id" in res:
        post_id = res["id"]
        await update.message.reply_text(
            f"🎉 *Successfully Published!*\n• Post ID: `{post_id}`\n• Page: https://facebook.com/{FB_PAGE_ID}",
            parse_mode="Markdown"
        )
    else:
        err_msg = res.get("error", {}).get("message", "Unknown error")
        await update.message.reply_text(f"❌ Failed to publish: {err_msg}")



# Ready-to-use high-converting caption templates for post publishing
CANVA_PRO_PROMO_BN = (
    "ডিজাইন নিয়ে আর কোনো লিমিটেশন নয়! 🎨🚀\n"
    "আপনার নিজস্ব পার্সোনাল জিমেইলেই (Gmail) পাচ্ছেন ১০০% অফিসিয়াল Canva Pro লাইসেন্স—সম্পূর্ণ নিরাপদ ও প্রাইভেট! 🔒✨\n\n"
    "💎 আমাদের স্পেশাল প্যাকেজসমূহ:\n"
    "⭐ ১ মাস — মাত্র ২৫ টাকা\n"
    "⚡ ৩ মাস — মাত্র ৫০ টাকা (🔥 সর্বাধিক জনপ্রিয় • Access First, Pay Later)\n"
    "🚀 ১২ মাস (১ বছর) — মাত্র ১৫০ টাকা (সেরা ভ্যালু)\n\n"
    "✨ যে যে সুবিধাগুলো পাবেন:\n"
    "✅ ১০০M+ প্রিমিয়াম ফটো, ভিডিও, টেমপ্লেট ও গ্রাফিক্স\n"
    "✅ ১-ক্লিকে AI ব্যাকগ্রাউন্ড রিমুভার ও ম্যাজিক স্টুডিও\n"
    "✅ ৩,০০০+ প্রিমিয়াম ফন্ট ও ফুল ব্র্যান্ড কিট অ্যাক্সেস\n"
    "✅ মাত্র ২ মিনিটে ইনস্ট্যান্ট ডেলিভারি গ্যারান্টি\n\n"
    "🛡️ আমাদের বিশেষ সুবিধা: \"আগে অ্যাক্সেস পেয়ে চেক করে নিন, তারপর নিশ্চিন্তে পেমেন্ট করুন!\" (Access First, Pay Later)\n\n"
    "👉 অফারটি নিতে এখনই কমেন্ট করুন অথবা আপনার জিমেইলটি আমাদের পেজের ইনবক্সে পাঠিয়ে দিন! 🎨📩\n\n"
    "#DesignHub #CanvaPro #CanvaProBangladesh #GraphicDesignBD #FreelancingBangladesh #CreativeTools #StudentOffer"
)

CANVA_PRO_PROMO_EN = (
    "Stop wasting hours on complex design tools. Upgrade your workflow with Canva Pro today! ⚡🎨\n\n"
    "Get 100% official Canva Pro directly on your personal email — safe, private, and zero passwords needed.\n\n"
    "🔥 Why Creators Love Canva Pro:\n"
    "• 100M+ Premium Stock Photos, Videos, Audio & Graphics\n"
    "• 1-Click AI Magic Background Remover & Magic Eraser\n"
    "• 3,000+ Premium Fonts, Custom Brand Kits & Resizing\n"
    "• Instant 2-Minute Activation Guarantee\n\n"
    "🏷️ Exclusive Rates:\n"
    "⭐ 1 Month  — 25 TK\n"
    "⚡ 3 Months — 50 TK (🔥 Most Popular • Access First, Pay Later)\n"
    "🚀 12 Months — 150 TK (Best Value Deal)\n\n"
    "🛡️ Zero Risk Policy: Access First, Check Everything, Then Pay!\n\n"
    "👉 Drop a message in our Page Inbox with your Gmail to get instant access right now! 📩✨\n\n"
    "#DesignHub #CanvaPro #DesignTools #ContentCreators #FreelancerLife #GraphicDesigners #DigitalTools"
)


def get_post_keyboard(post_type: str = "text") -> InlineKeyboardMarkup:
    if post_type == "photo":
        keyboard = [
            [
                InlineKeyboardButton("🚀 Publish Photo to FB", callback_data="publish_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="publish_cancel")
            ],
            [
                InlineKeyboardButton("🇧🇩 বাংলা ক্যাপশন (AI)", callback_data="caption_ai_bn"),
                InlineKeyboardButton("🇬🇧 English Caption (AI)", callback_data="caption_ai_en")
            ],
            [
                InlineKeyboardButton("💎 Canva Offer (বাংলা)", callback_data="caption_promo_bn"),
                InlineKeyboardButton("💎 Canva Offer (English)", callback_data="caption_promo_en")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("🚀 Publish to Facebook", callback_data="publish_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="publish_cancel")
            ],
            [
                InlineKeyboardButton("🇧🇩 বাংলায় লিখুন (AI)", callback_data="ai_lang_bn"),
                InlineKeyboardButton("🇬🇧 English Polish (AI)", callback_data="ai_polish")
            ],
            [
                InlineKeyboardButton("💎 Canva Offer (বাংলা)", callback_data="caption_promo_bn"),
                InlineKeyboardButton("💎 Canva Offer (English)", callback_data="caption_promo_en")
            ],
            [
                InlineKeyboardButton("🔄 Rewrite Angle", callback_data="ai_rewrite")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)



# ==================== SUBSCRIBER MANAGEMENT COMMANDS ====================


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    email = context.args[0] if context.args else "customer"
    minutes = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 10

    link_data = create_expiring_invite(email, minutes=minutes)
    join_url = f"https://designhub-1any.onrender.com/join/{link_data['token']}"

    msg = (
        f"⏳ *10-MINUTE CANVA PRO INVITE LINK*\n"
        f"────────────────────────\n"
        f"👤 *Customer:* `{email}`\n"
        f"⏱️ *Expires In:* `{minutes} Minutes` (Single-Use Only)\n"
        f"🔗 *Invite Link:*\n`{join_url}`\n"
        f"────────────────────────\n"
        f"💡 *Security Rule:* Once the customer clicks this link or {minutes} minutes pass, "
        f"it self-destructs and cannot be shared or reused!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def add_sub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "💡 *Usage:* `/add <email> [package] [name]`\n"
            "*Packages:* `1m` (25 TK), `3m` (50 TK), `6m` (99 TK), `12m` (150 TK)\n"
            "*Example:* `/add rahim@gmail.com 1m Rahim`",
            parse_mode="Markdown"
        )
        return

    email = context.args[0]
    pkg = context.args[1] if len(context.args) > 1 else "1m"
    name = " ".join(context.args[2:]) if len(context.args) > 2 else ""

    sub = add_subscriber(email, pkg, name)
    card_text = format_subscriber_card(sub)
    
    # Canva invite dispatch
    canva_note = ""
    if is_canva_authenticated():
        status_msg = await update.message.reply_text(f"⏳ *Dispatching Canva Pro invite to* `{email}`...", parse_mode="Markdown")
        canva_res = await asyncio.to_thread(invite_canva_member, email)
        if canva_res.get("status") == "success":
            canva_note = f"\n\n🎨 *Canva:* {canva_res.get('message', 'Invite dispatched!')}"
        else:
            canva_note = f"\n\n⚠️ *Canva:* {canva_res.get('message')}"
        await status_msg.delete()
    else:
        canva_note = "\n\n💡 *Canva Automation:* Session not saved yet. Run `python canva_login_helper.py` once on your Mac to enable 100% automatic invites."

    card_text += canva_note
    card_text += "\n\n⚠️ *Action:* Tap below once bKash/Nagad payment arrives:"
    keyboard = make_subscriber_keyboard(email, is_paid=False)

    await update.message.reply_text(card_text, reply_markup=keyboard, parse_mode="Markdown")


async def paid_sub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return
    if not context.args:
        await update.message.reply_text("💡 *Usage:* `/paid <email>`\n*Example:* `/paid rahim@gmail.com`", parse_mode="Markdown")
        return

    email = context.args[0]
    ok = mark_paid(email)
    if ok:
        sub = get_subscriber(email)
        card_text = format_subscriber_card(sub)
        card_text += "\n\n🎉 *Payment Confirmed!* Subscription is locked & active."
        keyboard = make_subscriber_keyboard(email, is_paid=True)
        await update.message.reply_text(card_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Subscriber with email `{email}` not found.", parse_mode="Markdown")


async def kick_sub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return
    if not context.args:
        await update.message.reply_text("💡 *Usage:* `/kick <email>`\n*Example:* `/kick rahim@gmail.com`", parse_mode="Markdown")
        return

    email = context.args[0]
    ok = kick_subscriber(email)
    canva_note = ""
    if is_canva_authenticated():
        canva_res = await asyncio.to_thread(kick_canva_member, email)
        canva_note = f"\n• Canva: {canva_res.get('message', 'Removed from team')}"

    if ok:
        sub = get_subscriber(email)
        cid = sub.get("customer_id", 800) if sub else 800
        name = sub.get("name") if sub else "Customer"
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        kick_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Canva Team to Remove Seat", url="https://www.canva.com/settings/team-members")],
            [InlineKeyboardButton("✅ Kick Confirmed", callback_data=f"kick_confirm:{email}")]
        ])
        await update.message.reply_text(
            f"🚨 *USER KICKED FROM DATABASE!*\n"
            f"────────────────────────\n"
            f"👤 Customer: {name} (ID: `#{cid}`)\n"
            f"📧 Email: `{email}`\n"
            f"🔴 Status: Kicked / Revoked in Database\n"
            f"────────────────────────\n"
            f"👉 ধাপ ১: নিচের লিংকে ক্লিক করে Canva টিম থেকে ব্যবহারকারীর সিট রিমুভ করুন।\n"
            f"👉 ধাপ ২: সিট রিমুভ শেষ হলে নিচে 'Kick Confirmed' বাটনে ট্যাপ করুন:",
            reply_markup=kick_kb,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ Subscriber `{email}` not found.", parse_mode="Markdown")


async def extend_sub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "💡 *Usage:* `/extend <email> [package]`\n"
            "*Packages:* `1m` (+30 days), `3m` (+90 days), `12m` (+365 days)\n"
            "*Example:* `/extend rahim@gmail.com 1m`",
            parse_mode="Markdown"
        )
        return

    email = context.args[0]
    pkg = context.args[1] if len(context.args) > 1 else "1m"
    res = extend_subscriber(email, pkg)
    if res:
        sub = get_subscriber(email)
        card_text = format_subscriber_card(sub)
        card_text += f"\n\n🎉 *Subscription Extended (+{res['added_package']})!*\nNew Expiry: `{res['new_expires_at']}`"
        keyboard = make_subscriber_keyboard(email, is_paid=True)
        await update.message.reply_text(card_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Subscriber `{email}` not found. Use `/add {email}` first.", parse_mode="Markdown")


async def list_subs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    subs = list_subscribers()
    stats = get_db_stats()
    if not subs:
        await update.message.reply_text("📋 *No subscribers in database.* Use `/add <email>` to add one.", parse_mode="Markdown")
        return

    lines = [
        f"📊 *Design Hub Subscribers*",
        f"• Total: `{stats['total']}` | 🟢 Paid: `{stats['active_paid']}` | 🟡 Pending: `{stats['pending']}` | 🔴 Kicked: `{stats['kicked']}`\n",
        f"📋 *Recent Subscriptions:*"
    ]
    for s in subs[:15]:
        p_icon = "🟢" if s["payment_status"] == "PAID" else ("🔴" if s["status"] == "kicked" else "🟡")
        name_str = f" ({s['name']})" if s.get("name") else ""
        cid_str = f"`#{s.get('customer_id', 800)}` "
        lines.append(f"{p_icon} {cid_str}`{s['email']}`{name_str} — *{s['package']}* (Exp: {s['expires_at'][:10]})")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def check_sub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return
    if not context.args:
        await update.message.reply_text("💡 *Usage:* `/check <email or customer_id>`\n*Examples:* `/check 800` or `/check rahim@gmail.com`", parse_mode="Markdown")
        return

    identifier = context.args[0]
    sub = get_subscriber(identifier)
    if not sub:
        await update.message.reply_text(f"❌ No subscriber found for `{identifier}`.", parse_mode="Markdown")
        return

    card_text = format_subscriber_card(sub)
    keyboard = make_subscriber_keyboard(sub["email"], is_paid=(sub.get("payment_status") == "PAID"))
    await update.message.reply_text(card_text, reply_markup=keyboard, parse_mode="Markdown")


async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    expiring = get_subscribers_expiring_soon(days=7)
    if not expiring:
        await update.message.reply_text("✅ *All active subscribers are up to date!* No subscriptions expiring in the next 7 days.", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text(f"⏳ Checking {len(expiring)} subscriber(s) expiring within 7 days...", parse_mode="Markdown")
    sent_count = 0
    for sub in expiring:
        fb_id = sub.get("fb_sender_id")
        if fb_id and token:
            ok = send_expiry_reminder_to_customer(
                fb_sender_id=fb_id,
                sender_name=sub.get("name", "Customer"),
                customer_id=sub.get("customer_id", 800),
                email=sub.get("email"),
                expires_at=sub.get("expires_at"),
                page_token=token
            )
            if ok:
                sent_count += 1

    await status_msg.edit_text(f"🚀 *Sent 7-day expiry reminders to {sent_count} customer(s) in Messenger!*", parse_mode="Markdown")


# ==================== MESSAGE HANDLERS ====================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    text = update.message.text

    # Check for TrxID in text
    trx_info = extract_trx_from_text(text)
    if trx_info.get("found"):
        trx_id = trx_info["trx_id"]
        prov = trx_info.get("provider", "bKash/Nagad")
        amt = trx_info.get("amount", "")
        amt_str = f"\n💵 *Amount:* {amt}" if amt else ""

        card = (
            f"🔢 *TRANSACTION ID DETECTED!*\n"
            f"────────────────────────\n"
            f"🏦 *Provider:* {prov}\n"
            f"🔢 *TrxID:* `{trx_id}`{amt_str}\n"
            f"────────────────────────\n"
            f"Select pending subscriber to confirm payment:"
        )
        pending_subs = [s for s in list_subscribers() if s.get("payment_status") == "PENDING" and s.get("status") == "active"]
        keyboard = []
        if pending_subs:
            for s in pending_subs[:3]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ Confirm for {s['email']}",
                        callback_data=f"trx_app:{trx_id}:{s['email']}"
                    )
                ])
        keyboard.append([InlineKeyboardButton("❌ Dismiss", callback_data="trx_reject")])
        await update.message.reply_text(card, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    PENDING_POSTS[user.id] = {"type": "text", "content": text}

    reply_markup = get_post_keyboard("text")

    preview = (
        f"📝 *Draft Preview:*\n"
        f"────────────────────────\n"
        f"{text}\n"
        f"────────────────────────\n"
        f"Publish this to *Design Hub*?"
    )
    await update.message.reply_text(preview, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_auth(user.id):
        return

    photo = update.message.photo[-1]
    caption = update.message.caption or ""

    status_msg = await update.message.reply_text("🔍 *Analyzing photo...*", parse_mode="Markdown")

    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    # 1. Vision Check: Is this a bKash/Nagad payment proof?
    proof = await asyncio.to_thread(analyze_payment_screenshot, bytes(image_bytes))
    if proof and proof.get("is_payment_proof"):
        trx_id = proof.get("trx_id") or "Not detected"
        amount = proof.get("amount") or "N/A"
        provider = proof.get("provider") or "bKash/Nagad"
        sender = proof.get("sender") or "N/A"
        time_str = proof.get("timestamp") or "N/A"

        card = (
            f"💳 *PAYMENT PROOF DETECTED! (AI Vision)*\n"
            f"────────────────────────\n"
            f"🏦 *Provider:* {provider}\n"
            f"🔢 *TrxID:* `{trx_id}`\n"
            f"💵 *Amount:* {amount}\n"
            f"📱 *Sender:* `{sender}`\n"
            f"📅 *Timestamp:* {time_str}\n"
            f"────────────────────────\n"
            f"Tap an action below to link & approve:"
        )

        pending_subs = [s for s in list_subscribers() if s.get("payment_status") == "PENDING" and s.get("status") == "active"]
        keyboard = []
        if pending_subs:
            for s in pending_subs[:3]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ Approve: {s['email']}",
                        callback_data=f"trx_app:{trx_id}:{s['email']}"
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton("❌ Reject / Fake", callback_data="trx_reject"),
            InlineKeyboardButton("📸 Publish to FB", callback_data="photo_publish_flow")
        ])

        PENDING_POSTS[user.id] = {
            "type": "photo",
            "image_bytes": bytes(image_bytes),
            "caption": caption,
            "detected_trx": trx_id
        }

        await status_msg.edit_text(card, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # Normal photo publishing flow
    await status_msg.delete()
    PENDING_POSTS[user.id] = {
        "type": "photo",
        "image_bytes": bytes(image_bytes),
        "caption": caption
    }

    reply_markup = get_post_keyboard("photo")
    await update.message.reply_text(
        f"📷 *Photo received!*\n"
        f"• Caption: {caption if caption else '_(No caption)_'}\n\n"
        f"Publish to *Design Hub*?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# ==================== INLINE BUTTON ACTIONS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not check_auth(user_id):
        await query.edit_message_text("⛔ Unauthorized action.")
        return

    data = query.data

    if data.startswith("trx_app:"):
        parts = data.split(":")
        trx_id = parts[1]
        email = parts[2]
        mark_paid(email, trx_id=trx_id)
        sub = get_subscriber(email)
        card_text = (
            f"🎉 *PAYMENT APPROVED & SUBSCRIBER ACTIVATED!*\n"
            f"────────────────────────\n"
            f"👤 *Email:* `{email}`\n"
            f"🔢 *TrxID:* `{trx_id}`\n"
            f"📦 *Package:* {sub.get('package', '1 Month')}\n"
            f"📅 *Valid Until:* `{sub.get('expires_at')}`\n"
            f"💰 *Status:* 🟢 PAID (Active)\n"
            f"────────────────────────"
        )
        await query.edit_message_text(card_text, reply_markup=make_subscriber_keyboard(email, is_paid=True), parse_mode="Markdown")
        return

    if data == "trx_reject":
        await query.edit_message_text("❌ Payment proof rejected / marked as unverified.", parse_mode="Markdown")
        return

    if data == "photo_publish_flow":
        draft = PENDING_POSTS.get(user_id)
        if draft and draft.get("type") == "photo":
            caption = draft.get("caption", "")
            await query.edit_message_text(
                f"📷 *Photo ready for publishing!*\n"
                f"• Caption: {caption if caption else '_(No caption)_'}\n\n"
                f"Publish to *Design Hub*?",
                reply_markup=get_post_keyboard("photo"),
                parse_mode="Markdown"
            )
        return

    if data.startswith("fb_pay_ok:"):
        parts = data.split(":")
        sender_id = parts[1]
        email = parts[2]
        mark_paid(email)
        clear_pending_telegram_msg(email)
        sub = get_subscriber(email)
        pkg_name = sub.get("package", "Canva Pro") if sub else "Canva Pro"
        
        # Send Step 6 & 7 confirmation to customer in Facebook Messenger
        token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
        if token:
            send_payment_confirmed_to_customer(sender_id, sub.get("name", "Customer"), pkg_name, token)

        cid = sub.get("customer_id", 800) if sub else 800
        card_text = (
            f"🎉 *PAYMENT VERIFIED & CONFIRMED TO CUSTOMER!*\n"
            f"────────────────────────\n"
            f"🆔 *Customer ID:* `#{cid}`\n"
            f"👤 *Email:* `{email}`\n"
            f"📦 *Package:* {pkg_name}\n"
            f"💰 *Status:* 🟢 PAID (Active)\n"
            f"💬 *Messenger Alert:* Dispatched to customer inbox!\n"
            f"────────────────────────"
        )
        await query.edit_message_text(card_text, reply_markup=make_subscriber_keyboard(email, is_paid=True), parse_mode="Markdown")
        return

    if data.startswith("sub_paid:"):
        email = data.split(":", 1)[1]
        mark_paid(email)
        clear_pending_telegram_msg(email)
        sub = get_subscriber(email)
        if sub:
            card_text = format_subscriber_card(sub) + "\n\n🎉 *Payment Confirmed!* Subscription locked & active."
            await query.edit_message_text(card_text, reply_markup=make_subscriber_keyboard(email, is_paid=True), parse_mode="Markdown")
        return

    if data.startswith("sub_kick:"):
        email = data.split(":", 1)[1]
        kick_subscriber(email)
        clear_pending_telegram_msg(email)
        sub = get_subscriber(email)
        cid = sub.get("customer_id", 800) if sub else 800
        name = sub.get("name") if sub else "Customer"
        card_text = (
            f"🚨 *USER KICKED FROM DATABASE!*\n"
            f"────────────────────────\n"
            f"👤 Customer: {name} (ID: `#{cid}`)\n"
            f"📧 Email: `{email}`\n"
            f"🔴 Status: Kicked & Access Revoked in Database\n"
            f"────────────────────────\n"
            f"👉 ধাপ ১: নিচের বাটনে ট্যাপ করে Canva টিম থেকে সিটটি রিমুভ করুন।\n"
            f"👉 ধাপ ২: সিট রিমুভ শেষ হলে 'Kick Confirmed' চাপুন (কাস্টমারকে মেসেজ পাঠানো হবে)।"
        )
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        kick_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Canva Team to Remove Seat", url="https://www.canva.com/settings/team-members")],
            [InlineKeyboardButton("✅ Kick Confirmed", callback_data=f"kick_confirm:{email}")]
        ])
        await query.edit_message_text(card_text, reply_markup=kick_kb, parse_mode="Markdown")
        return

    if data.startswith("kick_confirm:"):
        email = data.split(":", 1)[1]
        sub = get_subscriber(email)
        cid = sub.get("customer_id", 800) if sub else 800
        name = sub.get("name") if sub else "Customer"
        fb_id = sub.get("fb_sender_id") if sub else ""

        token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
        customer_notified = False
        if fb_id and token:
            customer_notified = send_subscription_ended_to_customer(fb_id, name, token)

        notice_str = "Dispatched to customer inbox! 💬" if customer_notified else "Customer notified."
        card_text = (
            f"🚨 *SEAT REMOVED & SUBSCRIPTION TERMINATED!*\n"
            f"────────────────────────\n"
            f"👤 Customer: {name} (ID: `#{cid}`)\n"
            f"📧 Email: `{email}`\n"
            f"🔴 Status: Kicked & Confirmed Removed\n"
            f"💬 Messenger Notice: {notice_str}\n"
            f"────────────────────────"
        )
        await query.edit_message_text(card_text, reply_markup=None, parse_mode="Markdown")
        return

    if data.startswith("sub_ext:"):
        parts = data.split(":")
        email = parts[1]
        pkg = parts[2] if len(parts) > 2 else "1m"
        res = extend_subscriber(email, pkg)
        if res:
            sub = get_subscriber(email)
            card_text = format_subscriber_card(sub) + f"\n\n🎉 *Extended (+{res['added_package']})!*\nNew Expiry: `{res['new_expires_at']}`"
            await query.edit_message_text(card_text, reply_markup=make_subscriber_keyboard(email, is_paid=True), parse_mode="Markdown")
        return

    if data == "publish_cancel":
        PENDING_POSTS.pop(user_id, None)
        try:
            await query.edit_message_text("🗑️ Post draft cancelled.")
        except Exception:
            await query.message.reply_text("🗑️ Post draft cancelled.")
        return

    if data == "ai_polish":
        draft = PENDING_POSTS.get(user_id)
        if not draft or draft.get("type") != "text":
            await query.edit_message_text("⚠️ No active draft found.")
            return

        await query.edit_message_text("✨ *Polishing with Gemini AI...*", parse_mode="Markdown")
        polished = call_gemini(
            draft["content"],
            "Enhance this Facebook post for Design Hub. Make it engaging, friendly, professional, and add relevant emojis and 3 hashtags."
        )
        if polished:
            draft["content"] = polished
            keyboard = [
                [
                    InlineKeyboardButton("🚀 Publish to Facebook", callback_data="publish_confirm"),
                    InlineKeyboardButton("🔄 Rewrite", callback_data="ai_polish")
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="publish_cancel")]
            ]
            preview = (
                f"✨ *Polished by Gemini:*\n"
                f"────────────────────────\n"
                f"{polished}\n"
                f"────────────────────────\n"
                f"Ready to publish to *Design Hub*?"
            )
            await query.edit_message_text(preview, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("⚠️ Could not polish with AI. Kept original text.")
        return

    if data == "ai_rewrite":
        draft = PENDING_POSTS.get(user_id)
        if not draft or "topic" not in draft:
            await query.edit_message_text("⚠️ No topic found to rewrite.")
            return

        await query.edit_message_text("🔄 *Gemini is rewriting a new angle...*", parse_mode="Markdown")
        new_text = call_gemini(
            f"Write a fresh, different angle for Facebook post about: {draft['topic']}",
            "You are a social media copywriter for Design Hub. Keep it concise, high-converting with emojis and hashtags."
        )
        if new_text:
            draft["content"] = new_text
            keyboard = [
                [
                    InlineKeyboardButton("🚀 Publish to Facebook", callback_data="publish_confirm"),
                    InlineKeyboardButton("🔄 Rewrite Again", callback_data="ai_rewrite")
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="publish_cancel")]
            ]
            await query.edit_message_text(
                f"🤖 *Fresh AI Draft:*\n────────────────────────\n{new_text}\n────────────────────────\nPublish to *Design Hub*?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return

    if data == "image_regen":
        draft = PENDING_POSTS.get(user_id)
        if not draft or "prompt" not in draft:
            await query.message.reply_text("⚠️ No image prompt found.")
            return

        prompt = draft["prompt"]
        status_msg = await query.message.reply_text("🎨 *Regenerating new image...*")
        img_bytes = generate_image_bytes(prompt)
        if img_bytes:
            draft["image_bytes"] = img_bytes
            keyboard = [
                [
                    InlineKeyboardButton("🚀 Publish Photo to FB", callback_data="publish_confirm"),
                    InlineKeyboardButton("🔄 Regenerate", callback_data="image_regen")
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="publish_cancel")]
            ]
            await status_msg.delete()
            await query.message.reply_photo(
                photo=img_bytes,
                caption=f"📝 *Caption:*\n{draft.get('caption', '')}\n\nPublish to *Design Hub*?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await status_msg.edit_text("❌ Failed to regenerate image.")
        return

    if data == "publish_confirm":
        draft = PENDING_POSTS.get(user_id)
        if not draft:
            await query.message.reply_text("⚠️ No pending draft found. Send a new message.")
            return

        try:
            await query.edit_message_text("⏳ Publishing to Facebook...")
        except Exception:
            pass

        try:
            if draft["type"] == "text":
                res = publish_text_to_fb(draft["content"])
            elif draft["type"] == "photo":
                res = publish_photo_to_fb(draft["image_bytes"], draft.get("caption", ""))
            else:
                res = {"error": {"message": "Unknown post type"}}

            if "id" in res:
                post_id = res["id"]
                PENDING_POSTS.pop(user_id, None)
                msg = (
                    f"🎉 *Live on Facebook!*\n\n"
                    f"• Post ID: `{post_id}`\n"
                    f"• View page: https://facebook.com/{FB_PAGE_ID}"
                )
                try:
                    await query.edit_message_text(msg, parse_mode="Markdown")
                except Exception:
                    await query.message.reply_text(msg, parse_mode="Markdown")
            else:
                err_msg = res.get("error", {}).get("message", "Unknown error")
                await query.message.reply_text(f"❌ Facebook API Error: {err_msg}")

        except Exception as e:
            logger.error(f"Error publishing: {e}")
            await query.message.reply_text(f"❌ Failed to publish: {str(e)}")



# ==================== RENDER / UPTIMEROBOT HEALTH SERVER ====================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        # On-Demand Session Renewal: Generates a brand-new token and redirects straight to Canva
        if self.path.startswith("/renew/"):
            token = self.path.split("/renew/")[1].split("?")[0].strip()
            email = extract_email_from_token(token)
            if email:
                new_invite = create_expiring_invite(email, minutes=30)
                new_token = new_invite["token"]
                self.send_response(302)
                self.send_header("Location", f"/join/{new_token}")
                self.end_headers()
                logger.info(f"🔄 Session renewed on-demand for {email} -> /join/{new_token}")
                return
            else:
                self.send_response(302)
                self.send_header("Location", "https://m.me/1312971105242105?text=newlink")
                self.end_headers()
                return

        # Self-Expiring Canva Invite Redirect (Session-Managed & Crawler-Safe)
        if self.path.startswith("/join/"):
            token = self.path.split("/join/")[1].split("?")[0].strip()
            user_agent = self.headers.get("User-Agent", "").lower()
            is_bot = any(b in user_agent for b in ["facebookexternalhit", "facebot", "meta-externalagent", "whatsapp", "slackbot", "twitterbot"])
            res = consume_expiring_invite(token, is_bot_prefetch=is_bot)
            if res.get("valid") and res.get("target_url"):
                email = res.get("email")
                if not is_bot and email:
                    notify_owner_user_joined_canva(email)

                self.send_response(302)
                self.send_header("Location", res["target_url"])
                self.end_headers()
                logger.info(f"✅ Expiring invite {token} accessed successfully for {email} (Bot: {is_bot}). Redirected to Canva.")
                return
            else:
                self.send_response(410)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                renew_href = f"/renew/{token}"
                messenger_href = "https://m.me/1312971105242105?text=newlink"
                html_resp = f'''<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Invitation Session Expired — Design Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Hind+Siliguri:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            background: radial-gradient(circle at 50% 20%, #17102e 0%, #090D16 100%); 
            color: #F8FAFC; 
            font-family: 'Hind Siliguri', 'Outfit', -apple-system, sans-serif; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            min-height: 100vh; 
            padding: 1.5rem; 
            text-align: center; 
        }}
        .card {{ 
            background: rgba(17, 24, 39, 0.85); 
            backdrop-filter: blur(20px); 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 24px; 
            padding: 2.75rem 2rem; 
            max-width: 460px; 
            width: 100%;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(125, 42, 232, 0.15); 
            animation: fadeIn 0.5s ease-out;
        }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .icon-wrap {{ 
            width: 72px; 
            height: 72px; 
            background: rgba(125, 42, 232, 0.15); 
            border: 1px solid rgba(125, 42, 232, 0.3); 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            margin: 0 auto 1.5rem; 
            font-size: 2.25rem; 
        }}
        h2 {{ font-size: 1.4rem; font-weight: 800; margin-bottom: 0.75rem; color: #FFFFFF; font-family: 'Outfit', sans-serif; }}
        .badge {{
            display: inline-block;
            background: rgba(245, 158, 11, 0.15);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.3);
            padding: 0.3rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}
        p {{ color: #94A3B8; font-size: 0.95rem; line-height: 1.6; margin-bottom: 2rem; }}
        .btn-group {{ display: flex; flex-direction: column; gap: 0.85rem; }}
        .btn-renew {{ 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 0.5rem;
            background: linear-gradient(135deg, #7D2AE8 0%, #00C4CC 100%); 
            color: white; 
            text-decoration: none; 
            padding: 0.9rem 1.5rem; 
            border-radius: 14px; 
            font-weight: 700; 
            font-size: 1rem; 
            box-shadow: 0 10px 25px rgba(125, 42, 232, 0.35); 
            transition: all 0.25s ease;
        }}
        .btn-renew:hover {{ transform: translateY(-2px); box-shadow: 0 15px 30px rgba(125, 42, 232, 0.5); }}
        .btn-msg {{ 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 0.5rem;
            background: rgba(255, 255, 255, 0.05); 
            border: 1px solid rgba(255, 255, 255, 0.12); 
            color: #E2E8F0; 
            text-decoration: none; 
            padding: 0.85rem 1.5rem; 
            border-radius: 14px; 
            font-weight: 600; 
            font-size: 0.95rem; 
            transition: background 0.2s ease;
        }}
        .btn-msg:hover {{ background: rgba(255, 255, 255, 0.1); color: #FFFFFF; }}
        .brand-footer {{ margin-top: 1.75rem; font-size: 0.8rem; color: #64748B; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon-wrap">⏳</div>
        <div class="badge">Session Expired • সেশন শেষ</div>
        <h2>Invitation Session Expired</h2>
        <p>এই Canva Pro ইনভাইটেশন লিংকটির ৩০ মিনিটের সেশন মেয়াদ শেষ হয়ে গেছে।<br><br>সরাসরি একটি নতুন লিংক তৈরি করে এখনই যুক্ত হতে নিচের বাটনে ট্যাপ করুন:</p>
        <div class="btn-group">
            <a href="{renew_href}" class="btn-renew">⚡ Generate Fresh Link & Join Now</a>
            <a href="{messenger_href}" class="btn-msg">💬 Open Messenger (মেসেঞ্জারে লিংক নিন)</a>
        </div>
        <div class="brand-footer">Design Hub • Official Canva Pro Edu Partner</div>
    </div>
</body>
</html>'''
                self.wfile.write(html_resp.encode("utf-8"))
                return

        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Design Hub Bot is Active & Running 24/7!\n")
            return

        parsed_url = urllib.parse.urlparse(self.path)
        path_only = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)
        team_filter = query_params.get("team", ["all"])[0].strip()

        if path_only == "/api/subscribers":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = {
                "stats": get_db_stats(team_filter),
                "subscribers": list_subscribers(team_filter=team_filter),
                "teams": get_all_teams(),
                "team_name": get_canva_team_name(),
                "active_team": team_filter if team_filter.lower() != "all" else get_canva_team_name(),
                "earnings": get_total_earnings(team_filter)
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path_only == "/api/payments":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = {
                "payments": get_all_payments(team_filter=team_filter),
                "earnings": get_total_earnings(team_filter),
                "teams": get_all_teams()
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path_only == "/api/teams":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = {
                "teams": get_all_teams(),
                "active_team": get_canva_team_name()
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # Serve Dashboard HTML for / and all other routes
        html_file = Path(__file__).resolve().parent / "dashboard.html"
        if html_file.exists():
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open(html_file, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Design Hub Bot is Active & Running 24/7!\n")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        payload = {}
        if post_data:
            try:
                payload = json.loads(post_data.decode("utf-8"))
            except Exception:
                pass

        res = {"status": "ok"}
        if self.path == "/api/invite/create":
            email = payload.get("email", "")
            minutes = int(payload.get("minutes", 10))
            link_info = create_expiring_invite(email, minutes=minutes)
            res = {
                "status": "ok",
                "link": f"https://designhub-1any.onrender.com/join/{link_info['token']}",
                "expires_at": link_info["expires_at"]
            }

        elif self.path == "/api/team/update":
            team_name = payload.get("team_name", "").strip()
            if team_name:
                saved = set_canva_team_name(team_name)
                res = {"status": "ok", "team_name": saved}
            else:
                res = {"status": "error", "message": "Team name cannot be empty"}

        elif self.path == "/api/subscriber/update":
            email = payload.get("email", "")
            fields = payload.get("fields", {})
            if email and fields:
                sub = update_subscriber(email, fields)
                res = {"status": "ok", "subscriber": sub}
            else:
                res = {"status": "error", "message": "Email and fields are required"}

        elif self.path == "/api/payment/update":
            pay_id = payload.get("id")
            fields = payload.get("fields", {})
            if pay_id is not None and fields:
                p = update_payment(pay_id, fields)
                res = {"status": "ok", "payment": p}
            else:
                res = {"status": "error", "message": "Payment ID and fields are required"}

        elif self.path == "/api/payment/delete":
            pay_id = payload.get("id")
            if pay_id is not None:
                delete_payment(pay_id)
                res = {"status": "ok"}
            else:
                res = {"status": "error", "message": "Payment ID is required"}

        elif self.path == "/api/team/add":
            team_name = payload.get("team_name", "").strip()
            if team_name:
                add_team(team_name)
                res = {"status": "ok", "teams": get_all_teams()}
            else:
                res = {"status": "error", "message": "Team name cannot be empty"}

        elif self.path == "/api/team/delete":
            team_name = payload.get("team_name", "").strip()
            if team_name:
                delete_team(team_name)
                res = {"status": "ok", "teams": get_all_teams()}
            else:
                res = {"status": "error", "message": "Team name cannot be empty"}

        elif self.path == "/api/payment/add":
            email = payload.get("email", "").strip()
            amount = payload.get("amount")
            provider = payload.get("provider", "bKash")
            trx_id = payload.get("trx_id", "")
            pkg = payload.get("package", "1m")
            notes = payload.get("notes", "Manual Entry")
            team_name = payload.get("team_name", None)
            if email:
                rec = record_payment(email, amount=amount, provider=provider, trx_id=trx_id, package=pkg, notes=notes, team_name=team_name)
                res = {"status": "ok", "payment": rec}
            else:
                res = {"status": "error", "message": "Email is required"}

        elif self.path == "/api/subscriber/add":
            email = payload.get("email", "")
            pkg = payload.get("package", "3m")
            name = payload.get("name", "")
            is_paid = payload.get("is_paid", False)
            trx_id = payload.get("trx_id", "")
            amount = payload.get("amount")
            provider = payload.get("provider", "bKash")
            team_name = payload.get("team_name", None)
            if email:
                add_subscriber(email, pkg, name, team_name=team_name)
                if is_paid:
                    mark_paid(email, trx_id=trx_id, amount=amount, provider=provider)

        elif self.path == "/api/subscriber/paid":
            email = payload.get("email", "")
            trx_id = payload.get("trx_id", "")
            amount = payload.get("amount")
            provider = payload.get("provider", "bKash")
            if email:
                mark_paid(email, trx_id=trx_id, amount=amount, provider=provider)

        elif self.path == "/api/subscriber/extend":
            email = payload.get("email", "")
            pkg = payload.get("package", "3m")
            if email:
                extend_subscriber(email, pkg)

        elif self.path == "/api/subscriber/kick":
            email = payload.get("email", "")
            if email:
                kick_subscriber(email)

        elif self.path == "/api/subscriber/delete":
            email = payload.get("email", "")
            if email:
                delete_subscriber(email)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Keep logs clean


def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"🌐 Health server listening on 0.0.0.0:{port} for Render/UptimeRobot pings.")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error starting health server: {e}")

# ==================== MAIN APPLICATION ====================

async def post_init(application):
    """Start background async tasks and register Telegram menu button commands."""
    commands = [
        BotCommand("status", "📊 System health & subscriber stats"),
        BotCommand("earnings", "💰 View total revenue & payment history"),
        BotCommand("team", "🎨 View & change active Canva Team"),
        BotCommand("subs", "👥 View active & pending subscribers"),
        BotCommand("add", "➕ Add subscriber: /add <email> [pkg]"),
        BotCommand("paid", "✅ Confirm payment: /paid <email>"),
        BotCommand("extend", "⌛ Extend plan: /extend <email> [pkg]"),
        BotCommand("kick", "🚨 Revoke access: /kick <email>"),
        BotCommand("check", "🔍 Inspect user: /check <email>"),
        BotCommand("remind", "⏰ Scan & send 7-day expiry reminders"),
        BotCommand("comments", "💬 Scan Facebook comments now"),
        BotCommand("ai", "✍️ Draft viral post: /ai <topic>"),
        BotCommand("start", "🏠 Main control menu"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ Telegram native Menu Button commands registered.")
    except Exception as e:
        logger.error(f"Error setting bot commands: {e}")

    asyncio.create_task(comment_monitor_loop(application.bot))
    asyncio.create_task(expiry_reminder_loop(application.bot))


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN is not set in .env")
        sys.exit(1)

    print("🤖 Starting Design Hub Telegram Bot with Gemini 3.5 Flash & Comment Auto-Responder...")
    # Start background web server for Render & UptimeRobot pings
    threading.Thread(target=start_health_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("link", link_command))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("ai", ai_draft_command))
    app.add_handler(CommandHandler("image", image_gen_command))
    app.add_handler(CommandHandler("post", quick_post_command))
    app.add_handler(CommandHandler("comments", scan_comments_command))
    app.add_handler(CommandHandler("checkcomments", scan_comments_command))
    app.add_handler(CommandHandler("add", add_sub_command))
    app.add_handler(CommandHandler("paid", paid_sub_command))
    app.add_handler(CommandHandler("kick", kick_sub_command))
    app.add_handler(CommandHandler("extend", extend_sub_command))
    app.add_handler(CommandHandler("subs", list_subs_command))
    app.add_handler(CommandHandler("subscribers", list_subs_command))
    app.add_handler(CommandHandler("check", check_sub_command))
    app.add_handler(CommandHandler("remind", remind_command))
    app.add_handler(CommandHandler("team", team_command))
    app.add_handler(CommandHandler("earnings", earnings_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))

    # Inline Callbacks
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Bot is polling for Telegram updates & monitoring comments! Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
