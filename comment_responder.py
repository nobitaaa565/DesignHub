#!/usr/bin/env python3
"""
Design Hub Auto-Comment Responder
Monitors Facebook Page posts for customer comments, matches intent/keywords,
and automatically replies with pricing and order instructions.
Also sends real-time Telegram alerts to the page owner.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")

DATA_FILE = Path(__file__).resolve().parent / "replied_comments.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("CommentResponder")

# Load replied comments history
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

# Readymade response templates
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
        return GREETING_PACKAGE_BN.format(name=user_name) if has_bengali else GREETING_PACKAGE_EN.format(name=user_name)

def send_telegram_alert(user_name: str, comment_text: str, reply_text: str, post_id: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ALLOWED_USER_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    text = (
        f"🔔 *New Facebook Comment Handled!*\n\n"
        f"👤 *User:* {user_name}\n"
        f"💬 *Comment:* \"{comment_text}\"\n"
        f"🤖 *Auto-Reply:* \n_{reply_text}_\n\n"
        f"🔗 Post: https://facebook.com/{post_id}"
    )
    payload = {
        "chat_id": TELEGRAM_ALLOWED_USER_ID,
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

def check_and_reply_comments():
    replied_ids = load_replied_ids()
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    params = {
        "fields": "id,message,comments{id,from,message,created_time,comments{id,from}}",
        "access_token": FB_PAGE_ACCESS_TOKEN
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code != 200:
            logger.error(f"Error fetching feed: {res.text}")
            return

        posts = res.json().get("data", [])
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
                logger.info(f"Processing comment from {from_name}: '{c_msg}'")

                # Send reply to Facebook
                success = post_fb_comment_reply(c_id, reply)
                if success:
                    replied_ids.add(c_id)
                    save_replied_ids(replied_ids)
                    send_telegram_alert(from_name, c_msg, reply, post_id)

    except Exception as e:
        logger.error(f"Error checking comments: {e}")

if __name__ == "__main__":
    logger.info("Design Hub Comment Responder started...")
    print("🤖 Checking comments on Facebook Page Design Hub...")
    check_and_reply_comments()
    print("Done checking comments.")
