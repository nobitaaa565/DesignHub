#!/usr/bin/env python3
"""
Design Hub - Dedicated Studio Campaign Planner & Poster Bot
Telegram Bot: @designposterbot
Runs natively on macOS in the background to:
1. Showcase all 7 Design References at once (/designs)
2. Interactive Campaign Planning: takes rough idea -> refines into clean Short Prompt
3. Flexible Prompt Editing: user can refine and tweak the prompt as much as needed
4. Dual Reminder Alarm System: sounds alarms 2 hours & 1 hour before scheduled post
5. Generates 1-tap copyable prompts ready to paste directly into Antigravity IDE
"""

import os
import sys
import time
import json
import re
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

STUDIO_BOT_TOKEN = os.getenv("STUDIO_BOT_TOKEN") or "8948969587:AAFCqGJDH2qG_En5szzPAfqJ6jxl5pFpbow"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")
CAMPAIGNS_FILE = WORKSPACE_DIR / "scheduled_campaigns.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("StudioPlannerBot")

# All 7 Design Archetypes in folder sequence with master posters
DESIGNS = [
    {
        "id": 1,
        "name": "Design 1",
        "title": "Style 1: Clean & Bright Studio Character",
        "image": "designs/design-1_reference/canva_pro_studio_promo_1080x1350.jpg",
        "desc": "Daylight studio, 3D Pixar student creator, dashed coupon with unique [ মাত্র ২৫ টাকা ] price badge.",
    },
    {
        "id": 2,
        "name": "Design 2",
        "title": "Style 2: Atmospheric Dark Mode & Floating 3D Elements",
        "image": "designs/design-2_reference/dynamic_horizontal_promo_1080x1350.jpg",
        "desc": "Cyber obsidian navy, neon rim lighting, floating 3D creative assets, frosted-glass bottom dock.",
    },
    {
        "id": 3,
        "name": "Design 3",
        "title": "Style 3: Ultra-Premium Glassmorphism Pricing Tiles",
        "image": "designs/design-3_reference/reference.jpg",
        "desc": "Overhead dramatic spotlight, 3 floating frosted-glass cards with elevated center hero card.",
    },
    {
        "id": 4,
        "name": "Design 4",
        "title": "Style 4: Poetic Conceptual Art & Physical Metaphor",
        "image": "designs/design-4_reference/canva_conceptual_promo_1080x1350.jpg",
        "desc": "Physical wooden pencil transforming into a sweeping luminous ribbon of frosted colored glass.",
    },
    {
        "id": 5,
        "name": "Design 5",
        "title": "Style 5: National & Observance Day Vector Art",
        "image": "designs/design-5_reference/national_revolution_and_solidarity_day_celebration.jpg",
        "desc": "Patriotic vector art, national monument silhouettes, Bengali typography, zero commercial selling.",
    },
    {
        "id": 6,
        "name": "Design 6",
        "title": "Style 6: Real Model & Floating 3D Feature Badges",
        "image": "designs/design-6_reference/canva_pro_mobile_promo_1080x1350.jpg",
        "desc": "Charismatic model holding smartphone with live UI, 4 orbiting 3D squircle tiles, neon aperture portal.",
    },
    {
        "id": 7,
        "name": "Design 7",
        "title": "Style 7: Premium SaaS Split-Bento & Feature Stack Grid",
        "image": "designs/design-7_reference/canva_pro_bento_promo_1080x1350.jpg",
        "desc": "Split bento grid, rich gradient card, stark-white embossed [ মাত্র ৫০ টাকা ] ticket pill, 5 stacked feature cards.",
    },
]

# User session state for interactive prompt building
USER_SESSIONS = {}


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
    """Verifies caller is authorized; if not, shows their user ID for easy onboarding."""
    user = update.effective_user
    if not user:
        return False
    allowed = get_allowed_user_ids()
    if not allowed:
        return True
    if user.id not in allowed:
        if update.message:
            msg = (
                "⛔ *Unauthorized Access*\n\n"
                f"Your Telegram User ID is: `{user.id}`\n\n"
                "Please send this ID to the admin to add you:\n"
                f"`/adduser {user.id}`"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.answer(f"⛔ Unauthorized. Your ID: {user.id}", show_alert=True)
        return False
    return True


async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to grant access to another Telegram account."""
    if not await check_auth(update):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "📌 *Usage:* `/adduser <telegram_user_id>`\n"
            "Example: `/adduser 123456789`",
            parse_mode="Markdown"
        )
        return
    new_id = int(args[0])
    allowed = get_allowed_user_ids()
    allowed.add(new_id)
    save_allowed_user_ids(allowed)
    await update.message.reply_text(
        f"✅ *Success!* User ID `{new_id}` has been granted access to @designposterbot.\n"
        "They can now message the bot directly!",
        parse_mode="Markdown"
    )


async def cmd_listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all authorized Telegram accounts."""
    if not await check_auth(update):
        return
    allowed = get_allowed_user_ids()
    text = "👥 *Authorized Telegram Accounts:*\n──────────────────────────────\n"
    for uid in sorted(allowed):
        text += f"• `{uid}`\n"
    text += "\n💡 Use `/adduser <id>` or `/removeuser <id>` to manage accounts."
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Removes an authorized account."""
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
        await update.message.reply_text(f"⚠️ User ID `{rem_id}` was not found in the allowed list.", parse_mode="Markdown")


# =====================================================================
# PERSISTENT CAMPAIGNS STORAGE
# =====================================================================

def load_campaigns() -> list:
    if not CAMPAIGNS_FILE.exists():
        return []
    try:
        with open(CAMPAIGNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading campaigns: {e}")
        return []


def save_campaigns(campaigns: list):
    try:
        with open(CAMPAIGNS_FILE, "w", encoding="utf-8") as f:
            json.dump(campaigns, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving campaigns: {e}")


# =====================================================================
# SHORT PROMPT REFINER (VIA GEMINI 3.8 FLASH)
# =====================================================================

def refine_short_prompt(style_id: int, user_idea: str) -> str:
    """Refines a rough user idea into a concise 4-line structured campaign brief."""
    d = next((item for item in DESIGNS if item["id"] == style_id), DESIGNS[0])
    
    if GEMINI_API_KEY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
        system_instruction = (
            f"You are a master social media ad planner for 'Design Hub' in Bangladesh. "
            f"The chosen design archetype is: {d['title']} ({d['desc']}). "
            f"Given the user's rough idea: '{user_idea}', summarize it into a clean, concise, 4-line Short Campaign Brief. "
            f"Format strictly as:\n"
            f"• Style: Design {style_id} ({d['name']})\n"
            f"• Offer: [Package & Price, e.g. Canva Pro 50 TK / 3 Months]\n"
            f"• Key Visuals: [Hero subject, colors, and unique price badge style]\n"
            f"• Highlight Perks: [3-4 flagship features, e.g. Magic Studio, BG Remover, 100M+ Assets]\n"
            f"Do NOT write long diffusion essays. Keep it punchy, structured, and easy for the user to edit."
        )
        try:
            res = requests.post(
                url,
                json={"contents": [{"parts": [{"text": system_instruction}]}]},
                timeout=15
            )
            if res.status_code == 200:
                text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
        except Exception as e:
            logger.warning(f"Could not call Gemini for brief refinement: {e}")

    # Fallback clean structured brief
    return (
        f"• Style: Design {style_id} ({d['title']})\n"
        f"• Offer: {user_idea}\n"
        f"• Key Visuals: Modern 3D elements with uniquely styled high-contrast price badge\n"
        f"• Highlight Perks: Canva Pro Official Access, Magic Studio AI, Instant Activation"
    )


# =====================================================================
# DATE & TIME PARSER
# =====================================================================

def parse_target_datetime(text: str) -> datetime:
    """Parses natural time strings like 'tomorrow 8pm', 'today 9:30pm', 'in 3 hours'."""
    now = datetime.now()
    text = text.strip().lower()

    # 'in X hours'
    m_in_h = re.search(r"in\s+(\d+)\s*h(?:our|ours)?", text)
    if m_in_h:
        hours = int(m_in_h.group(1))
        return now + timedelta(hours=hours)

    base_date = now.date()
    if "tomorrow" in text:
        base_date = now.date() + timedelta(days=1)
        text = text.replace("tomorrow", "").strip()
    elif "today" in text:
        text = text.replace("today", "").strip()

    # Time regex: '8pm', '8:30pm', '20:00', '8 am'
    m_time = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    if m_time:
        hour = int(m_time.group(1))
        minute = int(m_time.group(2)) if m_time.group(2) else 0
        meridiem = m_time.group(3)
        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        target = datetime.combine(base_date, datetime.min.time()).replace(hour=hour, minute=minute)
        if "today" not in text and target < now:
            target += timedelta(days=1)
        return target

    try:
        return datetime.fromisoformat(text)
    except Exception:
        # Default: in 3 hours
        return now + timedelta(hours=3)


# =====================================================================
# BOT COMMANDS & HANDLERS
# =====================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Studio Bot Welcome Menu."""
    if not await check_auth(update):
        await update.message.reply_text("⛔ Unauthorized. This bot is dedicated to Design Hub administration.")
        return

    text = (
        "🚀 *Welcome to Design Hub Campaign Planner Bot!*\n\n"
        "Plan your promotional posters, refine prompts, and schedule 2-hour & 1-hour alarms before posting.\n\n"
        "📌 *Quick Actions:*\n"
        "• `/designs` — Show all 7 design references at once\n"
        "• `/schedules` — View active campaign reminders\n"
        "• `/help` — How the workflow operates"
    )

    keyboard = [
        [
            InlineKeyboardButton("🖼️ Show All 7 Designs", callback_data="send_all_designs"),
        ],
        [
            InlineKeyboardButton("⏰ View Scheduled Reminders", callback_data="view_schedules"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cmd_designs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /designs command: immediately sends all 7 designs with minimalist captions."""
    if not await check_auth(update):
        return
    await send_all_designs(update.effective_chat.id, context)


async def send_all_designs(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Sends all 7 design references with clean, minimalist caption: simply Design Number."""
    for i, d in enumerate(DESIGNS):
        img_path = WORKSPACE_DIR / d["image"]
        caption = f"🎨 *Design {d['id']}*"

        keyboard = [
            [
                InlineKeyboardButton(f"📋 Plan Campaign in Style {d['id']}", callback_data=f"plan_style:{d['id']}"),
            ]
        ]

        if img_path.exists():
            with open(img_path, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
        await asyncio.sleep(0.3)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline keyboard interactions."""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if data == "send_all_designs":
        await send_all_designs(chat_id, context)

    elif data == "view_schedules":
        await show_scheduled_campaigns(chat_id, context)

    elif data.startswith("plan_style:"):
        style_id = int(data.split(":")[1])
        USER_SESSIONS[user_id] = {
            "step": "waiting_idea",
            "style_id": style_id,
        }
        await query.message.reply_text(
            f"🎯 *Design {style_id} Selected!*\n\n"
            f"✍️ *Send me your rough idea or package for this poster:*\n"
            f"_(e.g., 'Canva Pro 50 TK for 3 months with Magic Studio AI and student discount')_",
            parse_mode="Markdown",
        )

    elif data == "edit_prompt":
        session = USER_SESSIONS.get(user_id, {})
        session["step"] = "waiting_edit"
        USER_SESSIONS[user_id] = session
        await query.message.reply_text(
            "✏️ *Send your modifications or a new prompt text below:*",
            parse_mode="Markdown",
        )

    elif data == "confirm_schedule":
        session = USER_SESSIONS.get(user_id, {})
        if not session or "prompt" not in session:
            await query.message.reply_text("❌ No active prompt found. Please start with `/designs`.")
            return

        session["step"] = "waiting_time"
        USER_SESSIONS[user_id] = session

        # Quick time picker buttons
        keyboard = [
            [
                InlineKeyboardButton("🕒 In 3 Hours", callback_data="set_time:in 3 hours"),
                InlineKeyboardButton("🌙 Today 8:00 PM", callback_data="set_time:today 8pm"),
            ],
            [
                InlineKeyboardButton("☀️ Tomorrow 10:00 AM", callback_data="set_time:tomorrow 10am"),
                InlineKeyboardButton("🌆 Tomorrow 8:00 PM", callback_data="set_time:tomorrow 8pm"),
            ],
            [
                InlineKeyboardButton("✍️ Type Custom Time", callback_data="prompt_custom_time"),
            ]
        ]

        await query.message.reply_text(
            "⏰ *When do you plan to publish this post on Facebook?*\n\n"
            "Choose a quick preset or type any custom time (e.g. `today 9:30pm` or `tomorrow 11am`).\n"
            "🔔 *I will sound 2 reminder alarms before the post:* at **2 Hours** and **1 Hour** before!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("set_time:"):
        time_str = data.split(":", 1)[1]
        await finalize_schedule(chat_id, user_id, context, time_str)

    elif data == "prompt_custom_time":
        session = USER_SESSIONS.get(user_id, {})
        session["step"] = "waiting_time"
        USER_SESSIONS[user_id] = session
        await query.message.reply_text(
            "✍️ *Type your scheduled time below:*\n"
            "_(e.g. `tomorrow 8pm`, `today 10:30pm`, `in 4 hours`)_",
            parse_mode="Markdown",
        )

    elif data.startswith("cancel_camp:"):
        camp_id = data.split(":")[1]
        campaigns = load_campaigns()
        campaigns = [c for c in campaigns if c["id"] != camp_id]
        save_campaigns(campaigns)
        await query.message.reply_text("🗑️ *Scheduled campaign removed successfully.*", parse_mode="Markdown")


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text input during campaign planning and editing."""
    if not await check_auth(update):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    session = USER_SESSIONS.get(user_id)

    # 1. If user is in prompt creation / editing step
    if session and session.get("step") == "waiting_idea":
        style_id = session.get("style_id", 7)
        await update.message.reply_text("⏳ *Refining into a short, structured prompt brief...*", parse_mode="Markdown")
        
        short_prompt = refine_short_prompt(style_id, text)
        session["prompt"] = short_prompt
        session["step"] = "prompt_ready"
        USER_SESSIONS[user_id] = session

        await show_prompt_review(chat_id, context, style_id, short_prompt)
        return

    elif session and session.get("step") == "waiting_edit":
        style_id = session.get("style_id", 7)
        # Update prompt with user's exact modification
        session["prompt"] = text
        session["step"] = "prompt_ready"
        USER_SESSIONS[user_id] = session

        await update.message.reply_text("✅ *Prompt updated!*", parse_mode="Markdown")
        await show_prompt_review(chat_id, context, style_id, text)
        return

    elif session and session.get("step") == "waiting_time":
        await finalize_schedule(chat_id, user_id, context, text)
        return

    # 2. Natural language triggers
    lower = text.lower()
    if any(k in lower for k in ["show design", "show all design", "all design", "designs", "design"]):
        await send_all_designs(chat_id, context)
    elif "schedule" in lower or "reminder" in lower:
        await show_scheduled_campaigns(chat_id, context)
    else:
        await cmd_start(update, context)


async def show_prompt_review(chat_id: int, context: ContextTypes.DEFAULT_TYPE, style_id: int, short_prompt: str):
    """Displays the short prompt with Edit and Confirm buttons."""
    review_text = (
        f"📋 *Refined Short Prompt for Design {style_id}:*\n"
        f"──────────────────────────────\n"
        f"{short_prompt}\n"
        f"──────────────────────────────\n\n"
        f"💡 *You can modify this prompt as much as you need.* When satisfied, tap **Confirm & Schedule** to set your 2-hour & 1-hour alarms!"
    )

    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit / Modify Prompt", callback_data="edit_prompt"),
            InlineKeyboardButton("✅ Confirm & Schedule", callback_data="confirm_schedule"),
        ],
        [
            InlineKeyboardButton("🖼️ Back to Designs", callback_data="send_all_designs"),
        ]
    ]

    await context.bot.send_message(
        chat_id=chat_id,
        text=review_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def finalize_schedule(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE, time_str: str):
    """Calculates timestamps, saves to persistent storage, and confirms."""
    session = USER_SESSIONS.get(user_id, {})
    style_id = session.get("style_id", 7)
    short_prompt = session.get("prompt", "")

    target_dt = parse_target_datetime(time_str)
    now = datetime.now()

    if target_dt <= now:
        target_dt = now + timedelta(hours=3)

    target_ts = int(target_dt.timestamp())
    remind_2h_ts = target_ts - 7200
    remind_1h_ts = target_ts - 3600

    camp_id = f"camp_{int(time.time())}"
    campaign = {
        "id": camp_id,
        "user_id": user_id,
        "chat_id": chat_id,
        "style_id": style_id,
        "short_prompt": short_prompt,
        "target_time_str": target_dt.strftime("%Y-%m-%d %I:%M %p"),
        "target_ts": target_ts,
        "remind_2h_ts": remind_2h_ts,
        "remind_1h_ts": remind_1h_ts,
        "remind_2h_sent": False,
        "remind_1h_sent": False,
        "status": "active",
    }

    campaigns = load_campaigns()
    campaigns.append(campaign)
    save_campaigns(campaigns)

    # Clear user session
    USER_SESSIONS.pop(user_id, None)

    remind_2h_str = datetime.fromtimestamp(remind_2h_ts).strftime("%I:%M %p")
    remind_1h_str = datetime.fromtimestamp(remind_1h_ts).strftime("%I:%M %p")

    confirm_text = (
        f"🎉 *Campaign Scheduled & Alarms Set!*\n\n"
        f"🗓️ *Target Post Time:* `{target_dt.strftime('%A, %d %b %Y - %I:%M %p')}`\n\n"
        f"🔔 *Alarm Schedule:*\n"
        f"1️⃣ **Alarm 1 (2 Hours before):** at `{remind_2h_str}`\n"
        f"2️⃣ **Alarm 2 (1 Hour before):** at `{remind_1h_str}`\n\n"
        f"📋 *Saved Prompt Brief:*\n"
        f"```text\n{short_prompt}\n```\n"
        f"When the alarm sounds, simply tap the code block to copy the prompt and paste it into Antigravity!"
    )

    keyboard = [
        [
            InlineKeyboardButton("⏰ View All Schedules", callback_data="view_schedules"),
            InlineKeyboardButton("🖼️ Plan Another Design", callback_data="send_all_designs"),
        ]
    ]

    await context.bot.send_message(
        chat_id=chat_id,
        text=confirm_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_scheduled_campaigns(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Displays all active scheduled campaigns with cancel buttons."""
    campaigns = load_campaigns()
    active = [c for c in campaigns if c.get("status") == "active" and c.get("target_ts", 0) > time.time()]

    if not active:
        await context.bot.send_message(
            chat_id=chat_id,
            text="📭 *No active scheduled campaigns right now.*\n\nUse `/designs` to pick a style and plan a post!",
            parse_mode="Markdown",
        )
        return

    text = "⏰ *Active Scheduled Campaigns & Alarms:*\n──────────────────────────────\n"
    keyboard = []

    for c in active:
        text += (
            f"📌 *Design {c['style_id']} Promo*\n"
            f"• Target Time: `{c['target_time_str']}`\n"
            f"• 2h Alarm: `{'✅ Sent' if c.get('remind_2h_sent') else '⏳ Pending'}`\n"
            f"• 1h Alarm: `{'✅ Sent' if c.get('remind_1h_sent') else '⏳ Pending'}`\n"
            f"──────────────────────────────\n"
        )
        keyboard.append([InlineKeyboardButton(f"❌ Cancel {c['target_time_str']}", callback_data=f"cancel_camp:{c['id']}")])

    keyboard.append([InlineKeyboardButton("➕ Plan New Campaign", callback_data="send_all_designs")])

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =====================================================================
# BACKGROUND ALARM & REMINDER ENGINE
# =====================================================================

async def reminder_daemon_loop(application):
    """Continuously checks scheduled campaigns and delivers 2h and 1h proactive alarms."""
    logger.info("Reminder Daemon started.")
    while True:
        try:
            now_ts = int(time.time())
            campaigns = load_campaigns()
            updated = False

            for c in campaigns:
                if c.get("status") != "active":
                    continue

                chat_id = c.get("chat_id")
                style_id = c.get("style_id", 7)
                short_prompt = c.get("short_prompt", "")
                target_str = c.get("target_time_str", "")

                # 1. Check 2-Hour Reminder
                if not c.get("remind_2h_sent") and now_ts >= c.get("remind_2h_ts", 0):
                    c["remind_2h_sent"] = True
                    updated = True
                    alarm_msg = (
                        f"⏰ *[2-HOUR ALARM] Campaign Reminder!*\n\n"
                        f"Your scheduled Facebook post is in **2 hours** (`{target_str}`).\n\n"
                        f"📋 *Tap below to copy prompt for Antigravity:*\n"
                        f"```text\nDesign {style_id}: {short_prompt}\n```\n\n"
                        f"👉 Paste this prompt into Antigravity to synthesize your master poster and AI caption!"
                    )
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=alarm_msg, parse_mode="Markdown")
                        logger.info(f"Delivered 2-hour alarm for campaign {c['id']}")
                    except Exception as err:
                        logger.error(f"Failed to send 2h alarm: {err}")

                # 2. Check 1-Hour Reminder
                if not c.get("remind_1h_sent") and now_ts >= c.get("remind_1h_ts", 0):
                    c["remind_1h_sent"] = True
                    updated = True
                    alarm_msg = (
                        f"🚨 *[FINAL 1-HOUR ALARM] Post Coming Up Soon!*\n\n"
                        f"Your campaign is scheduled for **1 hour from now** (`{target_str}`).\n\n"
                        f"📋 *Tap below to copy prompt for Antigravity:*\n"
                        f"```text\nDesign {style_id}: {short_prompt}\n```\n\n"
                        f"👉 Generate the poster now in Antigravity so it's ready to post on time!"
                    )
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=alarm_msg, parse_mode="Markdown")
                        logger.info(f"Delivered 1-hour alarm for campaign {c['id']}")
                    except Exception as err:
                        logger.error(f"Failed to send 1h alarm: {err}")

                # 3. Post Time Arrival
                if now_ts >= c.get("target_ts", 0):
                    c["status"] = "completed"
                    updated = True
                    post_due_msg = (
                        f"🚀 *[POST TIME ARRIVED]* `{target_str}`\n\n"
                        f"Your campaign for **Design {style_id}** is scheduled for right now!\n"
                        f"If you've already generated the poster in Antigravity, publish it to Facebook Page now."
                    )
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=post_due_msg, parse_mode="Markdown")
                    except Exception:
                        pass

            if updated:
                save_campaigns(campaigns)

        except Exception as e:
            logger.error(f"Error in reminder loop: {e}", exc_info=True)

        await asyncio.sleep(20)


# =====================================================================
# MAIN ENTRYPOINT
# =====================================================================

async def post_init(application):
    """Sets bot menu commands and launches reminder loop."""
    commands = [
        BotCommand("designs", "Show all 7 design references"),
        BotCommand("schedules", "View active campaign reminders"),
        BotCommand("start", "Open campaign planner dashboard"),
    ]
    await application.bot.set_my_commands(commands)
    # Start background reminder daemon
    asyncio.create_task(reminder_daemon_loop(application))
    logger.info("Studio Bot commands registered & reminder daemon started.")


def main():
    if not STUDIO_BOT_TOKEN:
        print("❌ Error: STUDIO_BOT_TOKEN not set.")
        sys.exit(1)

    print(f"🚀 Starting Design Hub Campaign Planner Bot (@designposterbot)...")
    app = ApplicationBuilder().token(STUDIO_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("designs", cmd_designs))
    app.add_handler(CommandHandler("schedules", lambda u, c: show_scheduled_campaigns(u.effective_chat.id, c)))
    app.add_handler(CommandHandler("reminders", lambda u, c: show_scheduled_campaigns(u.effective_chat.id, c)))
    app.add_handler(CommandHandler("adduser", cmd_adduser))
    app.add_handler(CommandHandler("listusers", cmd_listusers))
    app.add_handler(CommandHandler("removeuser", cmd_removeuser))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    app.run_polling()


if __name__ == "__main__":
    main()
