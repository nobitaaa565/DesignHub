#!/usr/bin/env python3
from __future__ import annotations
"""
Design Hub - Dedicated Facebook Post Scheduler & 1-Hour Reminder Bot (Bot-2)
Telegram Bot: @designposterbot

Features:
- Single clean flow: eliminates duplicate confirmation messages and phantom schedules
- Auto-collapses & cleans wizard messages: deletes all intermediate questions and user inputs upon finalizing schedule
- Intelligent Bangla caption generator: properly understands 'you choose but in bangla' and crafts a high-converting Bengali caption
- Exact 1-Hour Advance Reminder with tap-to-copy prompt & caption
"""

import os
import sys
import time
import json
import re
import socket
import asyncio
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    MenuButtonCommands,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load environment
WORKSPACE_DIR = Path(__file__).resolve().parent
load_dotenv(WORKSPACE_DIR / ".env")

STUDIO_BOT_TOKEN = os.getenv("STUDIO_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID", "").strip()
SCHEDULES_FILE = WORKSPACE_DIR / "scheduled_posts.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("FacebookPostSchedulerBot")

# All 7 Master Design Archetypes
DESIGNS = [
    {
        "id": 1,
        "name": "Design 1: Clean & Bright Studio Character",
        "title": "Clean & Bright Studio Character",
        "image": "designs/design-1_reference/canva_pro_studio_promo_1080x1350.jpg",
        "desc": "Daylight studio, 3D Pixar student creator, dashed coupon with unique [ মাত্র ২৫ টাকা ] price badge.",
    },
    {
        "id": 2,
        "name": "Design 2: Atmospheric Dark Mode & Floating 3D Elements",
        "title": "Atmospheric Dark Mode & Floating 3D Elements",
        "image": "designs/design-2_reference/dynamic_horizontal_promo_1080x1350.jpg",
        "desc": "Cyber obsidian navy, neon rim lighting, floating 3D creative assets, frosted-glass bottom dock.",
    },
    {
        "id": 3,
        "name": "Design 3: Ultra-Premium Glassmorphism Pricing Tiles",
        "title": "Ultra-Premium Glassmorphism Pricing Tiles",
        "image": "designs/design-3_reference/reference.jpg",
        "desc": "Overhead dramatic spotlight, 3 floating frosted-glass cards with elevated center hero card.",
    },
    {
        "id": 4,
        "name": "Design 4: Poetic Conceptual Art & Physical Metaphor",
        "title": "Poetic Conceptual Art & Physical Metaphor",
        "image": "designs/design-4_reference/canva_conceptual_promo_1080x1350.jpg",
        "desc": "Physical wooden pencil transforming into a sweeping luminous ribbon of frosted colored glass.",
    },
    {
        "id": 5,
        "name": "Design 5: National & Observance Day Vector Art",
        "title": "National & Observance Day Vector Art",
        "image": "designs/design-5_reference/national_revolution_and_solidarity_day_celebration.jpg",
        "desc": "Patriotic vector art, national monument silhouettes, Bengali typography, zero commercial selling.",
    },
    {
        "id": 6,
        "name": "Design 6: Real Model & Floating 3D Feature Badges",
        "title": "Real Model & Floating 3D Feature Badges",
        "image": "designs/design-6_reference/canva_pro_mobile_promo_1080x1350.jpg",
        "desc": "Charismatic model holding smartphone with live UI, 4 orbiting 3D squircle tiles, neon aperture portal.",
    },
    {
        "id": 7,
        "name": "Design 7: Premium SaaS Split-Bento & Feature Stack Grid",
        "title": "Premium SaaS Split-Bento & Feature Stack Grid",
        "image": "designs/design-7_reference/canva_pro_bento_promo_1080x1350.jpg",
        "desc": "Split bento grid, rich gradient card, stark-white embossed [ মাত্র ৫০ টাকা ] ticket pill, 5 stacked feature cards.",
    },
    {
        "id": 8,
        "name": "Design 8: High-Impact Commercial Hardware & SaaS Showcase",
        "title": "High-Impact Commercial Hardware & SaaS Showcase",
        "image": "designs/design-8_reference/reference.jpg",
        "desc": "Bengali commercial product showcase, central hardware/device mockup on wooden counter, dashed coupon badge [ ফ্রি ট্রায়াল / অফার ], and hotline footer.",
    },
]

# Track wizard sessions and active message IDs to collapse
USER_SESSIONS: dict[int, dict] = {}
LOCK_SOCKET = None


def acquire_single_instance_lock(port: int = 49281) -> bool:
    global LOCK_SOCKET
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", port))
        s.listen(1)
        LOCK_SOCKET = s
        return True
    except socket.error:
        logger.warning(f"Bot-2 instance already running on port {port}. Exiting duplicate.")
        return False


def get_allowed_user_ids() -> set:
    raw = os.getenv("TELEGRAM_ALLOWED_USER_ID", "")
    ids = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


def save_allowed_user_ids(allowed_set: set):
    ids_str = ",".join(str(i) for i in sorted(allowed_set))
    env_path = WORKSPACE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("TELEGRAM_ALLOWED_USER_ID="):
                new_lines.append(f"TELEGRAM_ALLOWED_USER_ID={ids_str}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"\nTELEGRAM_ALLOWED_USER_ID={ids_str}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    os.environ["TELEGRAM_ALLOWED_USER_ID"] = ids_str


async def check_auth(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    allowed = get_allowed_user_ids()
    if not allowed:
        return True
    if user.id not in allowed:
        msg = (
            "⛔ *Unauthorized Access*\n\n"
            f"Your Telegram User ID is: `{user.id}`\n\n"
            "Please contact the administrator to whitelist your ID:\n"
            f"`/adduser {user.id}`"
        )
        if update.message:
            await update.message.reply_text(msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.answer(f"⛔ Unauthorized. Your ID: {user.id}", show_alert=True)
        return False
    return True


# =====================================================================
# PERSISTENT STORAGE
# =====================================================================

def load_schedules() -> list:
    if not SCHEDULES_FILE.exists():
        return []
    try:
        with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading schedules: {e}")
        return []


def save_schedules(schedules: list):
    try:
        with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
            json.dump(schedules, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving schedules: {e}")


# =====================================================================
# AI PROMPT & CAPTION ENHANCERS
# =====================================================================

def enhance_short_prompt(style_id: int, user_idea: str) -> str:
    """Shortly enhances rough prompt into a clean 4-line structured brief for Antigravity IDE."""
    design = next((d for d in DESIGNS if d["id"] == style_id), DESIGNS[0])

    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
            system_instruction = (
                f"You are the master design art director for Design Hub in Bangladesh. "
                f"Design Archetype: {design['name']} ({design['desc']}). "
                f"The user's rough idea is: '{user_idea}'. "
                f"Shortly enhance this into a concise 4-line prompt brief for Antigravity IDE. "
                f"Format strictly as:\n"
                f"• Style: Design {style_id} ({design['title']})\n"
                f"• Offer: [Package & Price, e.g. Canva Pro 25 TK / 50 TK]\n"
                f"• Key Visuals: [Hero subject, colors, and badge details]\n"
                f"• Highlight Perks: [3-4 flagship features, e.g. No Switch Team Hassle, 1TB Storage, Updated Designs, Magic Studio AI]\n"
                f"Keep it punchy, crisp, and clean. No extra conversational fluff."
            )
            res = requests.post(
                url,
                json={"contents": [{"parts": [{"text": system_instruction}]}]},
                timeout=8
            )
            if res.status_code == 200:
                text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
        except Exception as e:
            logger.warning(f"Gemini prompt enhancement fallback: {e}")

    # Tailored structured brief fallback with 5 Core Value Pillars
    lines = [
        f"• Style: Design {style_id} ({design['title']})",
        f"• Offer: {user_idea}",
        f"• 5 Core Pillars: 🔒 100% Private & Secure (others cannot see your designs) | ⚡ Zero Expire Hassle (no team expiry before due date) | 🔄 Extend Policy (keeps designs permanently safe) | 📂 1TB Cloud Storage | ✨ 100M+ Designs & Assets",
        f"• Key Visuals: 3D creative elements, high-contrast typography, and floating pricing badge",
        f"• Flagship Power: Canva Pro Official Access, Magic Studio AI, Instant Activation",
    ]
    return "\n".join(lines)


def generate_facebook_caption(style_id: int, rough_prompt: str, lang: str = "bangla") -> str:
    """Generates high-converting Bengali Facebook caption tailored specifically to the offer details."""
    design = next((d for d in DESIGNS if d["id"] == style_id), DESIGNS[0])

    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
            prompt = (
                f"Write a high-converting Facebook post caption strictly in natural, professional Bengali for Design Hub Bangladesh. "
                f"Offer & Features requested by user: '{rough_prompt}'. "
                f"Design Archetype: {design['title']}. "
                f"Ensure you highlight whatever features the user mentioned (e.g. no switch team hassle, 1TB cloud storage, updated designs, starting at 25 tk). "
                f"Include:\n"
                f"1. Attractive headline with emojis\n"
                f"2. Bulleted highlights of the offer\n"
                f"3. Core Canva Pro premium perks (Magic Studio AI, BG Remover, 100M+ assets)\n"
                f"4. Ordering CTA (inbox or comment)\n"
                f"5. #CanvaPro #DesignHub #CanvaProBangladesh #GraphicDesign\n"
                f"Return ONLY the caption text, ready to paste."
            )
            res = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=8
            )
            if res.status_code == 200:
                caption = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return caption
        except Exception as e:
            logger.warning(f"Gemini caption generation fallback: {e}")

    # High quality dynamic fallback in natural, double-checked Bengali
    perk_bullets = []
    lower_p = rough_prompt.lower()

    if "25" in lower_p:
        perk_bullets.append("✨ মাত্র ২৫ টাকা থেকেই শুরু Canva Pro স্পেশাল সাবস্ক্রিপশন!")
    elif "50" in lower_p:
        perk_bullets.append("✨ মাত্র ৫০ টাকায় পাচ্ছেন ৩ মাসের সেরা সাবস্ক্রিপশন অফার!")
    else:
        first_line = rough_prompt.splitlines()[0]
        perk_bullets.append(f"✨ বিশেষ অফার: {first_line}")

    # 5 Flagship Pillars (Double-Checked Bengali Spellings)
    perk_bullets.append("🔒 সম্পূর্ণ নিরাপদ ও প্রাইভেট — আপনার ডিজাইন অন্য কেউ দেখতে পারবে না, ১০০% সুরক্ষিত!")
    perk_bullets.append("⚡ নো টিম এক্সপায়ার হ্যাসেল — মেয়াদ শেষ হওয়ার আগে টিম বন্ধ হওয়ার কোনো সুযোগ নেই!")
    perk_bullets.append("🔄 সহজ এক্সটেন্ড পলিসি — যেকোনো সময় মেয়াদ বাড়িয়ে নিন, ডিজাইন থাকবে আজীবন সুরক্ষিত!")
    perk_bullets.append("📂 ১ TB বিশাল ক্লাউড স্টোরেজ — ফাইল, ব্র্যান্ড কিট ও হাই-রেস ছবি ব্যাকআপের নিশ্চয়তা!")
    perk_bullets.append("✨ ১০০M+ প্রিমিয়াম রিসোর্স — আনলিমিটেড ডিজাইন, টেমপ্লেট, ভিডিও, ফটো ও ফন্টস আনলকড!")

    perk_text = "\n".join(f"• {b}" for b in perk_bullets)

    return (
        f"🎨 আপনার ডিজাইনিংকে নিয়ে যান পেশাদার উচ্চতায় Canva Pro এর সাথে! 🚀\n\n"
        f"📌 কেন Design Hub থেকে Canva Pro নিবেন?\n"
        f"{perk_text}\n\n"
        f"💎 সাথে থাকছে আরও আকর্ষণীয় প্রিমিয়াম ফিচারসমূহ:\n"
        f"• Magic Studio AI ফুল পাওয়ার আনলকড\n"
        f"• ১-ক্লিকে Background Remover & Magic Eraser\n"
        f"• অফিসিয়াল ও ভেরিফায়েড অ্যাক্টিভেশন\n\n"
        f"📲 অফারটি সীমিত সময়ের জন্য! অর্ডার করতে এখনই আমাদের পেজে ইনবক্স করুন অথবা কমেন্ট করুন।\n\n"
        f"#CanvaPro #DesignHub #CanvaProBangladesh #GraphicDesign #DesignSecurity"
    )


# =====================================================================
# SMART DATE & TIME PARSER
# =====================================================================

def parse_target_datetime(text: str) -> tuple[datetime | None, str]:
    now = datetime.now()
    raw = text.strip()
    lower = raw.lower()

    m_in_m = re.search(r'\bin\s+(\d+)\s*(?:m|min|mins|minute|minutes)\b', lower)
    if m_in_m:
        mins = int(m_in_m.group(1))
        return (now + timedelta(minutes=mins), "")

    m_in_h = re.search(r'\bin\s+(\d+)\s*(?:h|hr|hrs|hour|hours)\b', lower)
    if m_in_h:
        hours = int(m_in_h.group(1))
        return (now + timedelta(hours=hours), "")

    m_in_d = re.search(r'\bin\s+(\d+)\s*(?:d|day|days)\b', lower)
    if m_in_d:
        days = int(m_in_d.group(1))
        return (now + timedelta(days=days), "")

    base_date = now.date()
    is_explicit_today = False

    if "tomorrow" in lower:
        base_date = now.date() + timedelta(days=1)
        lower = lower.replace("tomorrow", "").strip()
    elif "tonight" in lower:
        base_date = now.date()
        is_explicit_today = True
        lower = lower.replace("tonight", "").strip()
    elif "today" in lower:
        base_date = now.date()
        is_explicit_today = True
        lower = lower.replace("today", "").strip()

    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    for day_name, day_idx in weekdays.items():
        if day_name in lower:
            days_ahead = (day_idx - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            base_date = now.date() + timedelta(days=days_ahead)
            lower = lower.replace(day_name, "").strip()
            break

    m_time = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', lower)
    if m_time:
        hour = int(m_time.group(1))
        minute = int(m_time.group(2)) if m_time.group(2) else 0
        meridiem = m_time.group(3)

        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        elif not meridiem and hour < 8:
            hour += 12

        target = datetime.combine(base_date, datetime.min.time()).replace(hour=hour, minute=minute)
        if target <= now:
            if is_explicit_today:
                return (None, f"The time '{raw}' has already passed today! Please choose a future time.")
            else:
                target += timedelta(days=1)

        return (target, "")

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M"):
        try:
            target = datetime.strptime(raw, fmt)
            if target <= now:
                return (None, f"The date/time '{raw}' is in the past! Please choose a future time.")
            return (target, "")
        except Exception:
            continue

    return (None, f"Could not understand the time '{raw}'. Try 'today 9:30pm', 'tomorrow 8pm', or 'in 3 hours'.")


def format_countdown(target_ts: int) -> str:
    secs = target_ts - int(time.time())
    if secs <= 0:
        return "due now"
    mins = secs // 60
    hours = mins // 60
    days = hours // 24
    if days > 0:
        rem_hours = hours % 24
        return f"in {days}d {rem_hours}h"
    if hours > 0:
        rem_mins = mins % 60
        return f"in {hours}h {rem_mins}m"
    return f"in {mins}m"


# =====================================================================
# SEND DESIGNS GALLERY
# =====================================================================

async def send_all_designs(chat_id: int, context: ContextTypes.DEFAULT_TYPE, user_id: int | None = None):
    """Sends all 7 design reference master images with names and registers message IDs to collapse later."""
    header_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🎨 *Available Facebook Poster Designs for Design Hub:*\n"
            "──────────────────────────────\n"
            "Browse the 7 styles below and tap **Select Design** on your preferred archetype to start scheduling your post!"
        ),
        parse_mode="Markdown"
    )

    wizard_ids = [header_msg.message_id]
    if user_id:
        USER_SESSIONS[user_id] = {
            "step": "waiting_design_choice",
            "wizard_msg_ids": wizard_ids,
        }

    for d in DESIGNS:
        img_path = WORKSPACE_DIR / d["image"]
        caption = (
            f"🖼️ *{d['name']}*\n"
            f"_{d['desc']}_"
        )
        keyboard = [
            [
                InlineKeyboardButton(f"✨ Select {d['title']}", callback_data=f"select_design:{d['id']}")
            ]
        ]

        try:
            if img_path.exists():
                with open(img_path, "rb") as photo:
                    p_msg = await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=caption,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    wizard_ids.append(p_msg.message_id)
            else:
                p_msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                wizard_ids.append(p_msg.message_id)
        except Exception as e:
            logger.warning(f"Error sending design photo: {e}")

        await asyncio.sleep(0.2)

    if user_id and user_id in USER_SESSIONS:
        USER_SESSIONS[user_id]["wizard_msg_ids"] = wizard_ids


# =====================================================================
# KEYBOARDS & SUMMARY CARDS
# =====================================================================

def make_caption_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 You Choose (Bangla AI Caption)", callback_data="caption_ai_choose"),
        ],
        [
            InlineKeyboardButton("✏️ I will type my caption below", callback_data="caption_user_types"),
        ],
        [
            InlineKeyboardButton("❌ Cancel Schedule", callback_data="cancel_flow"),
        ]
    ])


def make_preset_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🕒 In 2 Hours", callback_data="set_time:in 2 hours"),
            InlineKeyboardButton("🕒 In 3 Hours", callback_data="set_time:in 3 hours"),
        ],
        [
            InlineKeyboardButton("🌙 Tonight 8:00 PM", callback_data="set_time:today 8pm"),
            InlineKeyboardButton("🌙 Tonight 10:00 PM", callback_data="set_time:today 10pm"),
        ],
        [
            InlineKeyboardButton("☀️ Tomorrow 10:00 AM", callback_data="set_time:tomorrow 10am"),
            InlineKeyboardButton("🌆 Tomorrow 8:00 PM", callback_data="set_time:tomorrow 8pm"),
        ],
        [
            InlineKeyboardButton("✍️ Type Custom Time", callback_data="prompt_custom_time"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_flow"),
        ]
    ])


def make_total_info_card(schedule: dict) -> str:
    target_dt = datetime.fromtimestamp(schedule["target_ts"])
    remind_1h_dt = datetime.fromtimestamp(schedule["remind_1h_ts"])
    countdown = format_countdown(schedule["target_ts"])

    return (
        f"🎉 *FACEBOOK POST SCHEDULED & ALARM SET!*\n"
        f"──────────────────────────────\n"
        f"🎨 *Design Archetype:* {schedule['design_name']}\n"
        f"🗓️ *Scheduled Post Time:* `{target_dt.strftime('%A, %d %b %Y — %I:%M %p')}` ({countdown})\n"
        f"⏰ *1-Hour Advance Reminder:* `{remind_1h_dt.strftime('%I:%M %p')}`\n\n"
        f"📋 *Enhanced Prompt (for Antigravity):*\n"
        f"```text\n{schedule['enhanced_prompt']}\n```\n\n"
        f"📝 *Facebook Post Caption:*\n"
        f"```text\n{schedule['caption']}\n```\n"
        f"──────────────────────────────\n"
        f"🔔 *Automated 1-Hour Reminder:*\n"
        f"At **{remind_1h_dt.strftime('%I:%M %p')}** (exact 1 hour before), I will send you this complete information to remind you to generate the poster in Antigravity and publish to Facebook!"
    )


# =====================================================================
# COMMAND HANDLERS
# =====================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return

    schedules = load_schedules()
    active_count = len([s for s in schedules if s.get("status") == "active"])

    text = (
        "🚀 *Welcome to Design Hub Facebook Post Scheduler (Bot-2)!*\n"
        "──────────────────────────────\n"
        "Plan your Facebook promotional campaigns, refine master prompts, generate captions, and receive proactive 1-hour advance reminders before publishing.\n\n"
        "📋 *The 5-Step Scheduling Workflow:*\n"
        "1️⃣ **Choose Design Archetype:** Select from 7 master styles\n"
        "2️⃣ **Input Prompt Idea:** Give rough idea ➡️ bot shortly enhances it for Antigravity\n"
        "3️⃣ **Set Caption:** Type custom caption or tap `[🤖 You Choose]`\n"
        "4️⃣ **Schedule Time:** Set target post date & time\n"
        "5️⃣ **1-Hour Alarm:** Bot reminds you with full prompt & caption 60 mins before posting!\n\n"
        f"📊 *Active Scheduled Posts:* **{active_count}** pending"
    )

    keyboard = [
        [
            InlineKeyboardButton("📅 Schedule Facebook Post", callback_data="start_schedule_flow"),
        ],
        [
            InlineKeyboardButton(f"📋 View Active Schedules ({active_count})", callback_data="view_schedules"),
            InlineKeyboardButton("🖼️ View All Designs", callback_data="show_all_designs"),
        ],
        [
            InlineKeyboardButton("🧹 Clear Past Posts", callback_data="clear_past"),
            InlineKeyboardButton("💡 Help Guide", callback_data="help_guide"),
        ]
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    await send_all_designs(update.effective_chat.id, context, user_id=update.effective_user.id)


async def cmd_designs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    await send_all_designs(update.effective_chat.id, context, user_id=update.effective_user.id)


async def cmd_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    await show_active_schedules(update.effective_chat.id, context)


async def show_active_schedules(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    schedules = load_schedules()
    # Filter only valid active schedules
    active = [s for s in schedules if s.get("status") == "active" and s.get("caption")]
    active.sort(key=lambda x: x.get("target_ts", 0))

    if not active:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Schedule New Post", callback_data="start_schedule_flow")]
        ])
        await context.bot.send_message(
            chat_id=chat_id,
            text="📭 *No active scheduled posts right now.*\n\nTap below to schedule a Facebook post!",
            parse_mode="Markdown",
            reply_markup=kb
        )
        return

    for s in active:
        target_ts = s["target_ts"]
        countdown = format_countdown(target_ts)
        target_dt = datetime.fromtimestamp(target_ts)
        remind_1h_dt = datetime.fromtimestamp(s["remind_1h_ts"])

        alarm_status = "✅ Delivered" if s.get("remind_1h_sent") else f"⏳ Scheduled for `{remind_1h_dt.strftime('%I:%M %p')}`"

        card = (
            f"📌 *{s['design_name']}*\n"
            f"🗓️ *Post Time:* `{target_dt.strftime('%A, %d %b — %I:%M %p')}` ({countdown})\n"
            f"🔔 *1h Pre-Alarm:* {alarm_status}\n\n"
            f"📋 *Prompt Brief:*\n`{s['enhanced_prompt'][:140]}...`\n"
        )

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔍 View Full Details", callback_data=f"view_detail:{s['id']}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_camp:{s['id']}"),
            ],
            [
                InlineKeyboardButton("⏱️ +15m", callback_data=f"snooze_camp:{s['id']}:15"),
                InlineKeyboardButton("⏱️ +30m", callback_data=f"snooze_camp:{s['id']}:30"),
                InlineKeyboardButton("✅ Mark Posted", callback_data=f"done_camp:{s['id']}"),
            ]
        ])

        await context.bot.send_message(
            chat_id=chat_id,
            text=card,
            parse_mode="Markdown",
            reply_markup=kb
        )
        await asyncio.sleep(0.15)


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    schedules = load_schedules()
    kept = [s for s in schedules if s.get("status") == "active" and s.get("caption")]
    removed_count = len(schedules) - len(kept)
    save_schedules(kept)
    await update.message.reply_text(
        f"🧹 Cleaned up {removed_count} completed / cancelled posts from history.",
        parse_mode="Markdown"
    )


# User management commands
async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("📌 *Usage:* `/adduser <telegram_user_id>`", parse_mode="Markdown")
        return
    new_id = int(args[0])
    allowed = get_allowed_user_ids()
    allowed.add(new_id)
    save_allowed_user_ids(allowed)
    await update.message.reply_text(
        f"✅ *Success!* User ID `{new_id}` is now authorized on @designposterbot.",
        parse_mode="Markdown"
    )


async def cmd_listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    allowed = get_allowed_user_ids()
    text = "👥 *Authorized Accounts on @designposterbot:*\n──────────────────────────────\n"
    for uid in sorted(allowed):
        text += f"• `{uid}`\n"
    text += "\n💡 Use `/adduser <id>` or `/removeuser <id>` to manage accounts."
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("📌 *Usage:* `/removeuser <telegram_user_id>`", parse_mode="Markdown")
        return
    rem_id = int(args[0])
    allowed = get_allowed_user_ids()
    if rem_id in allowed:
        allowed.discard(rem_id)
        save_allowed_user_ids(allowed)
        await update.message.reply_text(f"🗑️ User ID `{rem_id}` has been removed.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ User ID `{rem_id}` not found.", parse_mode="Markdown")


# =====================================================================
# CALLBACK QUERY ROUTER
# =====================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if data == "start_schedule_flow" or data == "show_all_designs":
        await send_all_designs(chat_id, context, user_id=user_id)

    elif data == "view_schedules":
        await show_active_schedules(chat_id, context)

    elif data == "clear_past":
        schedules = load_schedules()
        kept = [s for s in schedules if s.get("status") == "active" and s.get("caption")]
        save_schedules(kept)
        await query.message.reply_text("🧹 Past completed and cancelled schedules cleared.", parse_mode="Markdown")

    elif data == "help_guide":
        help_text = (
            "💡 *Bot-2 Facebook Post Scheduler Guide:*\n\n"
            "1️⃣ Send `/schedule` to view all 7 design reference posters.\n"
            "2️⃣ Tap **Select Design** on your preferred style.\n"
            "3️⃣ Type your rough offer or prompt idea ➡️ the bot shortly enhances it.\n"
            "4️⃣ Type your Facebook caption or tap `[🤖 You Choose / AI Generate]`.\n"
            "5️⃣ Set your target post date & time.\n"
            "6️⃣ The bot collapses all wizard messages and displays a clean Total Info Card.\n"
            "7️⃣ **Exact 1 hour before post time**, the bot sends you an auto-message with the prompt & caption ready to paste into Antigravity and Facebook!"
        )
        await query.message.reply_text(help_text, parse_mode="Markdown")

    elif data.startswith("select_design:"):
        style_id = int(data.split(":")[1])
        design = next((d for d in DESIGNS if d["id"] == style_id), DESIGNS[0])

        existing_ids = USER_SESSIONS.get(user_id, {}).get("wizard_msg_ids", [])

        # Prompt message
        p_msg = await query.message.reply_text(
            f"🎯 *{design['name']} Selected!*\n\n"
            f"✍️ *Step 1 of 3: What is your rough prompt / idea for this poster?*\n"
            f"_(e.g. 'Canva Pro 25 tk, switch team hassle not present, 1tb storage, all updated design')_",
            parse_mode="Markdown"
        )

        existing_ids.append(p_msg.message_id)
        USER_SESSIONS[user_id] = {
            "step": "waiting_prompt",
            "style_id": style_id,
            "design_name": design["name"],
            "wizard_msg_ids": existing_ids,
        }

    elif data == "caption_ai_choose":
        session = USER_SESSIONS.get(user_id)
        if not session or session.get("step") not in ("waiting_caption_choice", "waiting_caption_text"):
            return

        style_id = session.get("style_id", 1)
        rough_prompt = session.get("rough_prompt", "Canva Pro Official Access")
        wizard_ids = session.get("wizard_msg_ids", [])

        wait_msg = await query.message.reply_text("⏳ *Crafting high-converting Facebook caption in Bengali...*", parse_mode="Markdown")
        wizard_ids.append(wait_msg.message_id)

        caption = generate_facebook_caption(style_id, rough_prompt, lang="bangla")
        session["caption"] = caption
        session["step"] = "waiting_time"

        time_msg = await query.message.reply_text(
            f"📝 *Generated Facebook Caption:*\n"
            f"──────────────────────────────\n"
            f"{caption}\n"
            f"──────────────────────────────\n\n"
            f"⏰ *Step 3 of 3: When do you want to publish this post on Facebook?*\n"
            f"Tap a preset below or type any custom time (e.g. `today 9:30pm`, `tomorrow 8pm`):",
            parse_mode="Markdown",
            reply_markup=make_preset_time_keyboard()
        )
        wizard_ids.append(time_msg.message_id)
        session["wizard_msg_ids"] = wizard_ids
        USER_SESSIONS[user_id] = session

    elif data == "caption_user_types":
        session = USER_SESSIONS.get(user_id)
        if not session:
            return
        session["step"] = "waiting_caption_text"
        m = await query.message.reply_text(
            "✍️ *Type your custom Facebook caption below:*",
            parse_mode="Markdown"
        )
        session.setdefault("wizard_msg_ids", []).append(m.message_id)
        USER_SESSIONS[user_id] = session

    elif data.startswith("set_time:"):
        time_str = data.split(":", 1)[1]
        # Remove keyboard from prompt message to prevent duplicate clicking
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await finalize_schedule_flow(chat_id, user_id, context, time_str)

    elif data == "prompt_custom_time":
        session = USER_SESSIONS.get(user_id)
        if not session:
            return
        session["step"] = "waiting_time"
        USER_SESSIONS[user_id] = session
        m = await query.message.reply_text(
            "✍️ *Type your scheduled time below:*\n"
            "_(e.g. `tomorrow 8pm`, `today 10:30pm`, `in 3 hours`, `friday 5pm`)_",
            parse_mode="Markdown"
        )
        session.setdefault("wizard_msg_ids", []).append(m.message_id)

    elif data == "cancel_flow":
        session = USER_SESSIONS.pop(user_id, None)
        if session:
            for mid in session.get("wizard_msg_ids", []):
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=mid)
                except Exception:
                    pass
        await query.message.reply_text("❌ Scheduling flow cancelled.")

    elif data.startswith("view_detail:"):
        camp_id = data.split(":")[1]
        schedules = load_schedules()
        match = next((s for s in schedules if s["id"] == camp_id), None)
        if match:
            card_text = make_total_info_card(match)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel This Schedule", callback_data=f"cancel_camp:{camp_id}")]
            ])
            await query.message.reply_text(card_text, parse_mode="Markdown", reply_markup=kb)

    elif data.startswith("done_camp:"):
        camp_id = data.split(":")[1]
        schedules = load_schedules()
        for s in schedules:
            if s["id"] == camp_id:
                s["status"] = "completed"
                break
        save_schedules(schedules)
        await query.message.reply_text("✅ *Awesome! Marked as published on Facebook.* 🎉", parse_mode="Markdown")

    elif data.startswith("cancel_camp:"):
        camp_id = data.split(":")[1]
        schedules = load_schedules()
        for s in schedules:
            if s["id"] == camp_id:
                s["status"] = "cancelled"
                break
        save_schedules(schedules)
        await query.message.reply_text("🗑️ *Scheduled campaign cancelled successfully.*", parse_mode="Markdown")

    elif data.startswith("snooze_camp:"):
        parts = data.split(":")
        camp_id = parts[1]
        mins = int(parts[2])
        schedules = load_schedules()
        for s in schedules:
            if s["id"] == camp_id:
                current_target = max(s.get("target_ts", int(time.time())), int(time.time()))
                new_target_ts = current_target + (mins * 60)
                new_target_dt = datetime.fromtimestamp(new_target_ts)
                s["target_ts"] = new_target_ts
                s["target_time_str"] = new_target_dt.strftime("%A, %d %b %Y — %I:%M %p")
                s["remind_1h_ts"] = new_target_ts - 3600
                s["remind_1h_sent"] = False
                s["post_due_sent"] = False
                s["status"] = "active"
                save_schedules(schedules)
                await query.message.reply_text(
                    f"⏱️ *Post snoozed for {mins} minutes!*\nNew post time: `{new_target_dt.strftime('%I:%M %p')}`",
                    parse_mode="Markdown"
                )
                break


# =====================================================================
# TEXT MESSAGE ROUTER
# =====================================================================

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    session = USER_SESSIONS.get(user_id)

    # 1. Step 1: User sends rough prompt idea
    if session and session.get("step") == "waiting_prompt":
        style_id = session.get("style_id", 1)
        session["rough_prompt"] = text
        wizard_ids = session.get("wizard_msg_ids", [])
        wizard_ids.append(update.message.message_id)

        wait_msg = await update.message.reply_text("⏳ *Shortly enhancing your prompt brief for Antigravity...*", parse_mode="Markdown")
        wizard_ids.append(wait_msg.message_id)

        enhanced = enhance_short_prompt(style_id, text)
        session["enhanced_prompt"] = enhanced
        session["step"] = "waiting_caption_choice"

        review_prompt = (
            f"✨ *Enhanced Prompt Brief (for Antigravity):*\n"
            f"──────────────────────────────\n"
            f"{enhanced}\n"
            f"──────────────────────────────\n\n"
            f"📝 *Step 2 of 3: Now, what caption would you like for this Facebook post?*\n\n"
            f"• Tap **[🤖 You Choose (Bangla AI Caption)]** to let me craft a high-converting caption, OR\n"
            f"• Type your own custom Facebook caption directly below!"
        )

        p_msg = await update.message.reply_text(
            review_prompt,
            parse_mode="Markdown",
            reply_markup=make_caption_choice_keyboard()
        )
        wizard_ids.append(p_msg.message_id)
        session["wizard_msg_ids"] = wizard_ids
        USER_SESSIONS[user_id] = session
        return

    # 2. Step 2: User typed caption text (or instructed AI in Bangla)
    elif session and session.get("step") in ("waiting_caption_choice", "waiting_caption_text"):
        wizard_ids = session.get("wizard_msg_ids", [])
        wizard_ids.append(update.message.message_id)

        lower_text = text.lower()
        is_ai_trigger = (
            any(k in lower_text for k in ["you choose", "ai choose", "choose", "auto", "generate", "ai"])
            or "bangla" in lower_text
            or "বাংলা" in text
        )

        style_id = session.get("style_id", 1)
        rough_prompt = session.get("rough_prompt", "Canva Pro Official Access")

        if is_ai_trigger:
            wait_m = await update.message.reply_text("⏳ *Generating high-converting Bengali caption for you...*", parse_mode="Markdown")
            wizard_ids.append(wait_m.message_id)
            caption = generate_facebook_caption(style_id, rough_prompt, lang="bangla")
        else:
            caption = text

        session["caption"] = caption
        session["step"] = "waiting_time"

        time_msg = await update.message.reply_text(
            f"✅ *Facebook Caption Saved:*\n"
            f"──────────────────────────────\n"
            f"{caption}\n"
            f"──────────────────────────────\n\n"
            f"⏰ *Step 3 of 3: When do you want to publish this post on Facebook?*\n"
            f"Choose a preset below or type any custom time (e.g. `today 9:30pm`, `tomorrow 8pm`, `in 3 hours`):",
            parse_mode="Markdown",
            reply_markup=make_preset_time_keyboard()
        )
        wizard_ids.append(time_msg.message_id)
        session["wizard_msg_ids"] = wizard_ids
        USER_SESSIONS[user_id] = session
        return

    # 3. Step 3: User typed scheduled time
    elif session and session.get("step") == "waiting_time":
        session.setdefault("wizard_msg_ids", []).append(update.message.message_id)
        await finalize_schedule_flow(chat_id, user_id, context, text)
        return

    # 4. Natural language triggers
    lower = text.lower()
    if any(k in lower for k in ["schedule facebook", "schedule post", "schedule", "post"]):
        await send_all_designs(chat_id, context, user_id=user_id)
        return
    elif any(k in lower for k in ["designs", "show design", "all design"]):
        await send_all_designs(chat_id, context, user_id=user_id)
        return
    elif any(k in lower for k in ["schedules", "reminders", "active post"]):
        await show_active_schedules(chat_id, context)
        return

    # Default
    await cmd_start(update, context)


async def finalize_schedule_flow(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE, time_str: str):
    """
    Atomically finalizes schedule, deletes all wizard messages to collapse the chat,
    and sends a single Total Info Summary Card.
    """
    # 1. ATOMIC POP: Prevents duplicate execution on double-click or simultaneous input
    session = USER_SESSIONS.pop(user_id, None)
    if not session or not session.get("design_name") or session.get("step") not in ("waiting_time", "waiting_caption_choice", "waiting_caption_text"):
        logger.warning(f"Ignoring duplicate/stray finalize call for user {user_id}")
        return

    target_dt, err = parse_target_datetime(time_str)
    if err or not target_dt:
        # Re-insert session so user can retry entering time
        USER_SESSIONS[user_id] = session
        err_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ {err}\n\nPlease try again (e.g. `today 9pm`, `tomorrow 10am`, `in 2 hours`):"
        )
        session.setdefault("wizard_msg_ids", []).append(err_msg.message_id)
        return

    style_id = session.get("style_id", 1)
    design_name = session.get("design_name", f"Design {style_id}")
    rough_prompt = session.get("rough_prompt", "")
    enhanced_prompt = session.get("enhanced_prompt", "")
    caption = session.get("caption", "")

    now_ts = int(time.time())
    target_ts = int(target_dt.timestamp())
    remind_1h_ts = target_ts - 3600
    remind_1h_sent = (remind_1h_ts <= now_ts)

    camp_id = f"post_{int(time.time())}_{user_id % 1000}"
    schedule_record = {
        "id": camp_id,
        "user_id": user_id,
        "chat_id": chat_id,
        "style_id": style_id,
        "design_name": design_name,
        "rough_prompt": rough_prompt,
        "enhanced_prompt": enhanced_prompt,
        "caption": caption,
        "target_time_str": target_dt.strftime("%A, %d %b %Y — %I:%M %p"),
        "target_ts": target_ts,
        "remind_1h_str": datetime.fromtimestamp(remind_1h_ts).strftime("%A, %d %b %Y — %I:%M %p"),
        "remind_1h_ts": remind_1h_ts,
        "remind_1h_sent": remind_1h_sent,
        "post_due_sent": False,
        "status": "active",
        "created_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
    }

    # Save to persistent storage
    schedules = load_schedules()
    # Filter any accidental empty duplicates before adding
    schedules = [s for s in schedules if s.get("caption") or s.get("rough_prompt")]
    schedules.append(schedule_record)
    save_schedules(schedules)

    # 2. CLEAR ALL WIZARD MESSAGES (Collapse session into a clean chat)
    wizard_msg_ids = session.get("wizard_msg_ids", [])
    for mid in wizard_msg_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=mid)
        except Exception:
            pass

    # 3. SEND SINGLE CLEAN TOTAL INFO CARD
    card_text = make_total_info_card(schedule_record)
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 View All Schedules", callback_data="view_schedules"),
            InlineKeyboardButton("➕ Schedule Another Post", callback_data="start_schedule_flow"),
        ],
        [
            InlineKeyboardButton("❌ Cancel This Schedule", callback_data=f"cancel_camp:{camp_id}"),
        ]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=card_text,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =====================================================================
# BACKGROUND 1-HOUR ALARM DAEMON
# =====================================================================

async def reminder_daemon_loop(application):
    """Monitors scheduled campaigns and delivers the 1-Hour advance auto-message & Due alarms."""
    logger.info("Facebook Post Scheduler Daemon started.")
    while True:
        try:
            now_ts = int(time.time())
            schedules = load_schedules()
            updated = False

            for s in schedules:
                if s.get("status") != "active" or not s.get("caption"):
                    continue

                chat_id = s.get("chat_id")
                camp_id = s.get("id")
                design_name = s.get("design_name", "Design Poster")
                target_str = s.get("target_time_str", "")
                target_ts = s.get("target_ts", 0)
                remind_1h_ts = s.get("remind_1h_ts", 0)
                enhanced_prompt = s.get("enhanced_prompt", "")
                caption = s.get("caption", "")

                # 1. Deliver 1-Hour Advance Reminder Auto-Message
                if not s.get("remind_1h_sent") and now_ts >= remind_1h_ts and target_ts > now_ts:
                    s["remind_1h_sent"] = True
                    updated = True
                    alarm_msg = (
                        f"🚨⏰ *[1-HOUR REMINDER] TIME TO PREPARE YOUR FACEBOOK POST!*\n"
                        f"──────────────────────────────\n"
                        f"Your Facebook post is scheduled for **1 hour from now**:\n"
                        f"🗓️ *Scheduled Post Time:* `{target_str}`\n"
                        f"🎨 *Selected Style:* {design_name}\n\n"
                        f"📋 *Tap below to copy Prompt for Antigravity IDE:*\n"
                        f"```text\n{enhanced_prompt}\n```\n\n"
                        f"📝 *Tap below to copy Facebook Caption:*\n"
                        f"```text\n{caption}\n```\n"
                        f"──────────────────────────────\n"
                        f"⚡ *Action Required:*\n"
                        f"You have 1 hour until `{target_str}`. Paste the prompt into Antigravity IDE to generate the poster now, so you are ready to publish on time!"
                    )
                    kb = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Published to Facebook", callback_data=f"done_camp:{camp_id}"),
                            InlineKeyboardButton("⏱️ Snooze 15m", callback_data=f"snooze_camp:{camp_id}:15"),
                        ],
                        [
                            InlineKeyboardButton("⏱️ Snooze 30m", callback_data=f"snooze_camp:{camp_id}:30"),
                            InlineKeyboardButton("❌ Cancel Post", callback_data=f"cancel_camp:{camp_id}"),
                        ]
                    ])
                    try:
                        await application.bot.send_message(
                            chat_id=chat_id,
                            text=alarm_msg,
                            parse_mode="Markdown",
                            reply_markup=kb
                        )
                        logger.info(f"Delivered 1-hour alarm for post schedule {camp_id}")
                    except Exception as err:
                        logger.error(f"Failed to send 1h alarm for {camp_id}: {err}")

                # 2. Deliver Exact Post Time Chime
                if not s.get("post_due_sent") and now_ts >= target_ts:
                    s["post_due_sent"] = True
                    updated = True
                    due_msg = (
                        f"🔔🚀 *[POST TIME ARRIVED] PUBLISH TO FACEBOOK NOW!*\n"
                        f"──────────────────────────────\n"
                        f"It is now `{target_str}`!\n"
                        f"Your Facebook post for **{design_name}** is due right now.\n\n"
                        f"If you've already generated the poster in Antigravity, publish it with your saved caption to the Facebook Page!"
                    )
                    kb = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Published", callback_data=f"done_camp:{camp_id}"),
                            InlineKeyboardButton("⏱️ Snooze 15m", callback_data=f"snooze_camp:{camp_id}:15"),
                            InlineKeyboardButton("⏱️ Snooze 1h", callback_data=f"snooze_camp:{camp_id}:60"),
                        ]
                    ])
                    try:
                        await application.bot.send_message(
                            chat_id=chat_id,
                            text=due_msg,
                            parse_mode="Markdown",
                            reply_markup=kb
                        )
                        logger.info(f"Delivered post due chime for {camp_id}")
                    except Exception as err:
                        logger.error(f"Failed to send post due chime for {camp_id}: {err}")

            if updated:
                save_schedules(schedules)

        except Exception as e:
            logger.error(f"Error in scheduler daemon loop: {e}", exc_info=True)

        await asyncio.sleep(15)


# =====================================================================
# MAIN ENTRYPOINT
# =====================================================================

async def post_init(application):
    commands = [
        BotCommand("schedule", "📅 Schedule Facebook Post (Pick Design & Plan)"),
        BotCommand("designs", "🖼️ Show All 7 Design References"),
        BotCommand("schedules", "📋 View Active Scheduled Posts"),
        BotCommand("start", "🚀 Open Campaign Planner Dashboard"),
        BotCommand("clear", "🧹 Clear Completed Schedules"),
        BotCommand("help", "💡 Workflow Guide & Help"),
        BotCommand("listusers", "👥 View Authorized Users"),
        BotCommand("adduser", "➕ Authorize Team Member: /adduser <id>"),
    ]
    await application.bot.set_my_commands(commands)
    try:
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    except Exception as e:
        logger.warning(f"Could not set chat menu button: {e}")
    asyncio.create_task(reminder_daemon_loop(application))
    logger.info("Bot-2 commands & menu button registered, scheduler daemon active.")


def main():
    if not acquire_single_instance_lock():
        sys.exit(0)

    if not STUDIO_BOT_TOKEN:
        print("❌ Error: STUDIO_BOT_TOKEN not set in environment.")
        sys.exit(1)

    print("🚀 Starting Design Hub Facebook Post Scheduler Bot (@designposterbot)...")
    app = ApplicationBuilder().token(STUDIO_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    app.add_handler(CommandHandler("designs", cmd_designs))
    app.add_handler(CommandHandler("schedules", cmd_schedules))
    app.add_handler(CommandHandler("tasks", cmd_schedules))
    app.add_handler(CommandHandler("reminders", cmd_schedules))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("adduser", cmd_adduser))
    app.add_handler(CommandHandler("listusers", cmd_listusers))
    app.add_handler(CommandHandler("removeuser", cmd_removeuser))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    app.run_polling()


if __name__ == "__main__":
    main()
