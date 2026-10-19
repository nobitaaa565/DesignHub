#!/usr/bin/env python3
from __future__ import annotations
"""
Design Hub - Dedicated Work & Task Scheduler Bot (Bot-2)
Telegram Bot: @designposterbot
Runs natively on macOS and in 24/7 Cloud Background to:
1. Schedule personal work, client deliveries, design deadlines & errands
2. Automatically deliver a proactive 1-Hour Advance Alarm with complete task details
3. Deliver the Exact Due-Time Alarm when the scheduled time arrives
4. 1-Tap quick actions: Mark Done, Snooze (+15m, +30m, +1h), or Cancel
5. Persistent storage in reminders.json with instant restart resilience
"""

import os

import sys
import time
import json
import re
import socket
import asyncio
import logging
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
ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")
REMINDERS_FILE = WORKSPACE_DIR / "reminders.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("WorkSchedulerBot")

# Active user creation sessions
USER_SESSIONS = {}

# Single instance lock socket
LOCK_SOCKET = None


def acquire_single_instance_lock(port: int = 49281) -> bool:
    """Guarantees only one polling instance of Bot-2 runs to prevent Telegram conflict 409."""
    global LOCK_SOCKET
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", port))
        s.listen(1)
        LOCK_SOCKET = s
        return True
    except socket.error:
        logger.warning(f"Bot-2 instance already running on port {port}. Exiting duplicate process.")
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

def load_reminders() -> list:
    if not REMINDERS_FILE.exists():
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading reminders: {e}")
        return []


def save_reminders(reminders: list):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving reminders: {e}")


# =====================================================================
# SMART DATE & TIME PARSER
# =====================================================================

def parse_target_datetime(text: str) -> tuple[datetime | None, str]:
    """
    Parses flexible date/time strings.
    Returns (datetime_obj, error_message).
    """
    now = datetime.now()
    raw = text.strip()
    lower = raw.lower()

    # 1. Relative: 'in X mins / minutes'
    m_in_m = re.search(r'\bin\s+(\d+)\s*(?:m|min|mins|minute|minutes)\b', lower)
    if m_in_m:
        mins = int(m_in_m.group(1))
        return (now + timedelta(minutes=mins), "")

    # 2. Relative: 'in X hours'
    m_in_h = re.search(r'\bin\s+(\d+)\s*(?:h|hr|hrs|hour|hours)\b', lower)
    if m_in_h:
        hours = int(m_in_h.group(1))
        return (now + timedelta(hours=hours), "")

    # 3. Relative: 'in X days'
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

    # Weekday check
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

    # Time regex: '8pm', '8:30pm', '20:00', '8 am'
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
            # Assume PM if ambiguous small hour like 2, 3, 4, 5, 6
            hour += 12

        target = datetime.combine(base_date, datetime.min.time()).replace(hour=hour, minute=minute)
        
        # If target has already passed
        if target <= now:
            if is_explicit_today:
                return (None, f"The time '{raw}' has already passed today! Please specify a future time.")
            else:
                target += timedelta(days=1)

        return (target, "")

    # Try standard ISO / formats
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M"):
        try:
            target = datetime.strptime(raw, fmt)
            if target <= now:
                return (None, f"The specified date/time '{raw}' is in the past! Please choose a future time.")
            return (target, "")
        except Exception:
            continue

    return (None, f"Could not understand the time '{raw}'. Try formats like 'today 8pm', 'tomorrow 10am', or 'in 2 hours'.")


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
# REMINDER CREATION ENGINE
# =====================================================================

def create_task_record(user_id: int, chat_id: int, task_text: str, target_dt: datetime) -> dict:
    now_ts = int(time.time())
    target_ts = int(target_dt.timestamp())
    remind_1h_ts = target_ts - 3600

    # Short title: first line or first 60 chars
    title = task_text.strip().split("\n")[0][:60]

    # If scheduled less than 1 hour away, 1h alarm is already due/past, so skip 1h alarm
    remind_1h_sent = (remind_1h_ts <= now_ts)

    task_id = f"task_{int(time.time())}_{user_id % 1000}"
    record = {
        "id": task_id,
        "user_id": user_id,
        "chat_id": chat_id,
        "title": title,
        "details": task_text.strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "target_time_str": target_dt.strftime("%A, %d %b %Y - %I:%M %p"),
        "target_ts": target_ts,
        "remind_1h_ts": remind_1h_ts,
        "remind_1h_sent": remind_1h_sent,
        "due_sent": False,
        "status": "active",
    }

    reminders = load_reminders()
    reminders.append(record)
    save_reminders(reminders)
    return record


# =====================================================================
# UI VIEWS & KEYBOARDS
# =====================================================================

def make_start_keyboard(active_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ New Reminder / Task", callback_data="new_task"),
        ],
        [
            InlineKeyboardButton(f"📋 Active Tasks ({active_count})", callback_data="view_tasks"),
            InlineKeyboardButton("📜 History", callback_data="view_history"),
        ],
        [
            InlineKeyboardButton("❓ Help & Examples", callback_data="help_info"),
        ]
    ])


def make_preset_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🕒 In 30 Mins", callback_data="set_time:in 30 mins"),
            InlineKeyboardButton("🕒 In 1 Hour", callback_data="set_time:in 1 hour"),
        ],
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
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_session"),
        ]
    ])


def make_task_card_text(task: dict, title_prefix: str = "🎉 *Task Scheduled & Alarms Set!*") -> str:
    target_dt = datetime.fromtimestamp(task["target_ts"])
    remind_1h_dt = datetime.fromtimestamp(task["remind_1h_ts"])
    countdown = format_countdown(task["target_ts"])

    if task["remind_1h_sent"] and (task["target_ts"] - int(time.time()) < 3600):
        pre_alarm_info = "⚡ _Task is due in under 1 hour; alarm will chime at due time._"
    else:
        pre_alarm_info = f"⏰ **1-Hour Advance Alarm:** `{remind_1h_dt.strftime('%I:%M %p')}`\n   _(You will get full task details to prepare)_"

    return (
        f"{title_prefix}\n\n"
        f"📌 *Work Task:*\n"
        f"{task['details']}\n\n"
        f"🗓️ *Scheduled Due Time:*\n"
        f"`{target_dt.strftime('%A, %d %b %Y - %I:%M %p')}` ({countdown})\n\n"
        f"🔔 *Alarms Configured:*\n"
        f"1️⃣ {pre_alarm_info}\n"
        f"2️⃣ 🎯 **Exact Due Alarm:** `{target_dt.strftime('%I:%M %p')}`"
    )


# =====================================================================
# COMMAND HANDLERS
# =====================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return

    reminders = load_reminders()
    active = [r for r in reminders if r.get("status") == "active"]
    active_count = len(active)

    text = (
        "⏰ *Design Hub — Dedicated Work & Task Scheduler (Bot-2)*\n"
        "──────────────────────────────\n"
        "Never miss client deliverables, social media posts, or daily errands.\n\n"
        "🔔 *Dual-Alarm Alert System:*\n"
        "• ⏰ **1-Hour Advance Alarm:** Sounds 1 hour before scheduled time with your complete task details & notes.\n"
        "• 🎯 **Due Time Alarm:** Sounds when the exact deadline arrives.\n"
        "• ⏱️ **Instant Controls:** Snooze (+15m, +30m, +1h), Mark Done, or Reschedule anytime.\n\n"
        "📌 *Quick Commands:*\n"
        "• `/remind <time> - <task>` — Instant 1-line creation\n"
        "• `/tasks` — View active tasks & countdowns\n"
        "• `/clear` — Clear completed tasks\n"
        "──────────────────────────────\n"
        f"📊 *Active Tasks:* **{active_count}** pending"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=make_start_keyboard(active_count)
    )


async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick 1-line creation: /remind tomorrow 8pm - Deliver Canva logo to client"""
    if not await check_auth(update):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    full_args = " ".join(context.args).strip() if context.args else ""

    if not full_args:
        # Start interactive flow
        USER_SESSIONS[user_id] = {"step": "waiting_task"}
        await update.message.reply_text(
            "📝 *Step 1 of 2: What work or task do you need to do?*\n\n"
            "_(e.g., 'Deliver Canva Pro template to client and verify bKash payment')_",
            parse_mode="Markdown"
        )
        return

    # Parse '<time> - <details>' or '<time> to <details>'
    time_part = ""
    task_part = ""
    if " - " in full_args:
        parts = full_args.split(" - ", 1)
        time_part = parts[0].strip()
        task_part = parts[1].strip()
    elif " : " in full_args:
        parts = full_args.split(" : ", 1)
        time_part = parts[0].strip()
        task_part = parts[1].strip()
    elif " to " in full_args:
        parts = full_args.split(" to ", 1)
        time_part = parts[0].strip()
        task_part = parts[1].strip()
    else:
        # Default prompt
        USER_SESSIONS[user_id] = {"step": "waiting_time", "task": full_args}
        await update.message.reply_text(
            f"📌 *Task:* {full_args}\n\n"
            f"⏰ *When is this task due / when should I remind you?*",
            parse_mode="Markdown",
            reply_markup=make_preset_time_keyboard()
        )
        return

    target_dt, err = parse_target_datetime(time_part)
    if err or not target_dt:
        await update.message.reply_text(
            f"⚠️ *Time Parsing Error:* {err}\n\n"
            f"*Example Usage:*\n"
            f"`/remind tomorrow 8pm - Deliver Canva files`\n"
            f"`/remind in 2 hours - Fix Facebook webhook`",
            parse_mode="Markdown"
        )
        return

    record = create_task_record(user_id, chat_id, task_part, target_dt)
    card_text = make_task_card_text(record)
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 View All Tasks", callback_data="view_tasks"),
            InlineKeyboardButton("➕ Add Another", callback_data="new_task"),
        ],
        [
            InlineKeyboardButton("❌ Cancel This Task", callback_data=f"task_cancel:{record['id']}"),
        ]
    ])
    await update.message.reply_text(card_text, parse_mode="Markdown", reply_markup=kb)


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    await show_tasks_list(update.effective_chat.id, context)


async def show_tasks_list(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    reminders = load_reminders()
    active = [r for r in reminders if r.get("status") == "active"]
    active.sort(key=lambda x: x.get("target_ts", 0))

    if not active:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Create First Task", callback_data="new_task")]
        ])
        await context.bot.send_message(
            chat_id=chat_id,
            text="📭 *No active scheduled tasks right now.*\n\nTap below to set a reminder!",
            parse_mode="Markdown",
            reply_markup=kb
        )
        return

    for t in active:
        target_ts = t["target_ts"]
        countdown = format_countdown(target_ts)
        target_dt = datetime.fromtimestamp(target_ts)
        remind_1h_dt = datetime.fromtimestamp(t["remind_1h_ts"])

        alarm_1h_status = "✅ Sent" if t.get("remind_1h_sent") else f"⏳ Scheduled for `{remind_1h_dt.strftime('%I:%M %p')}`"
        due_status = "🔔 Due Now!" if t.get("due_sent") else "⏳ Pending"

        text = (
            f"📌 *Task:* {t['details']}\n"
            f"🗓️ *Due:* `{target_dt.strftime('%A, %d %b - %I:%M %p')}` ({countdown})\n"
            f"• 1h Pre-Alarm: {alarm_1h_status}\n"
            f"• Due Alarm: {due_status}\n"
        )

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Mark Done", callback_data=f"task_done:{t['id']}"),
                InlineKeyboardButton("⏱️ +15m", callback_data=f"task_snooze:{t['id']}:15"),
                InlineKeyboardButton("⏱️ +30m", callback_data=f"task_snooze:{t['id']}:30"),
            ],
            [
                InlineKeyboardButton("⏱️ +1h", callback_data=f"task_snooze:{t['id']}:60"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"task_cancel:{t['id']}"),
            ]
        ])

        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=kb
        )
        await asyncio.sleep(0.15)


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    reminders = load_reminders()
    kept = [r for r in reminders if r.get("status") == "active"]
    removed_count = len(reminders) - len(kept)
    save_reminders(kept)
    await update.message.reply_text(
        f"🧹 Cleaned up {removed_count} completed / cancelled tasks from storage.",
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

    if data == "new_task":
        USER_SESSIONS[user_id] = {"step": "waiting_task"}
        await query.message.reply_text(
            "📝 *Step 1 of 2: What work or task do you need to do?*\n\n"
            "_(Type your task description, e.g. 'Post Facebook offer banner and reply to customer inquiries')_",
            parse_mode="Markdown"
        )

    elif data == "view_tasks":
        await show_tasks_list(chat_id, context)

    elif data == "view_history":
        reminders = load_reminders()
        inactive = [r for r in reminders if r.get("status") != "active"][-10:]
        if not inactive:
            await query.message.reply_text("📜 No past completed or cancelled tasks.")
            return
        text = "📜 *Recent Completed / Cancelled Tasks:*\n──────────────────────────────\n"
        for r in reversed(inactive):
            status_icon = "✅" if r.get("status") == "completed" else "❌"
            text += f"{status_icon} *{r['title']}*\n• Due: {r.get('target_time_str')}\n• Status: {r.get('status')}\n\n"
        await query.message.reply_text(text, parse_mode="Markdown")

    elif data == "help_info":
        help_text = (
            "💡 *How Bot-2 Scheduler Operates:*\n\n"
            "1️⃣ **Set Any Task:** Click **New Reminder** or use `/remind <time> - <task>`.\n"
            "2️⃣ **1-Hour Advance Alert:** 60 minutes before your scheduled deadline, the bot sends you an alarm containing your complete task instructions and copyable notes so you're ready.\n"
            "3️⃣ **Due-Time Chime:** When the exact time hits, the bot sounds the final chime.\n"
            "4️⃣ **Snooze / Complete:** Tap `[✅ Mark Done]` or snooze by 15m, 30m, or 1h at any time!"
        )
        await query.message.reply_text(help_text, parse_mode="Markdown")

    elif data == "cancel_session":
        USER_SESSIONS.pop(user_id, None)
        await query.message.reply_text("❌ Reminder creation cancelled.")

    elif data.startswith("set_time:"):
        time_str = data.split(":", 1)[1]
        session = USER_SESSIONS.get(user_id, {})
        task_text = session.get("task", "Scheduled Work")

        target_dt, err = parse_target_datetime(time_str)
        if err or not target_dt:
            await query.message.reply_text(f"⚠️ Error: {err}")
            return

        record = create_task_record(user_id, chat_id, task_text, target_dt)
        USER_SESSIONS.pop(user_id, None)

        card_text = make_task_card_text(record)
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 View All Tasks", callback_data="view_tasks"),
                InlineKeyboardButton("➕ Add Another", callback_data="new_task"),
            ],
            [
                InlineKeyboardButton("❌ Cancel This Task", callback_data=f"task_cancel:{record['id']}"),
            ]
        ])
        await query.message.reply_text(card_text, parse_mode="Markdown", reply_markup=kb)

    elif data == "prompt_custom_time":
        session = USER_SESSIONS.get(user_id, {})
        session["step"] = "waiting_time"
        USER_SESSIONS[user_id] = session
        await query.message.reply_text(
            "✍️ *Type your scheduled time below:*\n\n"
            "Examples:\n"
            "• `today 9:30pm`\n"
            "• `tomorrow 11:00 am`\n"
            "• `in 45 mins` or `in 3 hours`\n"
            "• `friday 5pm`",
            parse_mode="Markdown"
        )

    elif data.startswith("task_done:"):
        task_id = data.split(":")[1]
        reminders = load_reminders()
        found = False
        for r in reminders:
            if r.get("id") == task_id:
                r["status"] = "completed"
                found = True
                break
        if found:
            save_reminders(reminders)
            await query.message.reply_text("✅ *Task marked as COMPLETED! Great work.* 🎉", parse_mode="Markdown")

    elif data.startswith("task_cancel:"):
        task_id = data.split(":")[1]
        reminders = load_reminders()
        found = False
        for r in reminders:
            if r.get("id") == task_id:
                r["status"] = "cancelled"
                found = True
                break
        if found:
            save_reminders(reminders)
            await query.message.reply_text("🗑️ *Task has been cancelled.*", parse_mode="Markdown")

    elif data.startswith("task_snooze:"):
        parts = data.split(":")
        task_id = parts[1]
        mins = int(parts[2])

        reminders = load_reminders()
        found = False
        new_target_dt = None
        for r in reminders:
            if r.get("id") == task_id:
                current_target = max(r.get("target_ts", int(time.time())), int(time.time()))
                new_target_ts = current_target + (mins * 60)
                new_target_dt = datetime.fromtimestamp(new_target_ts)
                r["target_ts"] = new_target_ts
                r["target_time_str"] = new_target_dt.strftime("%A, %d %b %Y - %I:%M %p")
                r["due_sent"] = False
                r["status"] = "active"
                found = True
                break
        if found and new_target_dt:
            save_reminders(reminders)
            await query.message.reply_text(
                f"⏱️ *Task snoozed for {mins} minutes!*\n"
                f"Next alarm: `{new_target_dt.strftime('%I:%M %p')}`",
                parse_mode="Markdown"
            )


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

    # 1. Active Creation Flow: Step 1 (Task description received)
    if session and session.get("step") == "waiting_task":
        session["task"] = text
        session["step"] = "waiting_time"
        USER_SESSIONS[user_id] = session

        await update.message.reply_text(
            f"📌 *Task noted:* {text}\n\n"
            f"⏰ *Step 2 of 2: When is this task due / when should I remind you?*\n"
            f"Tap a preset below or type any custom time (e.g. `today 9pm`, `tomorrow 10am`, `in 2 hours`):",
            parse_mode="Markdown",
            reply_markup=make_preset_time_keyboard()
        )
        return

    # 2. Active Creation Flow: Step 2 (Time input received)
    elif session and session.get("step") == "waiting_time":
        task_text = session.get("task", "Scheduled Work")
        target_dt, err = parse_target_datetime(text)
        if err or not target_dt:
            await update.message.reply_text(
                f"⚠️ {err}\n\nPlease try typing a time like `today 8pm`, `tomorrow 10am`, or `in 30 mins`:"
            )
            return

        record = create_task_record(user_id, chat_id, task_text, target_dt)
        USER_SESSIONS.pop(user_id, None)

        card_text = make_task_card_text(record)
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 View All Tasks", callback_data="view_tasks"),
                InlineKeyboardButton("➕ Add Another", callback_data="new_task"),
            ],
            [
                InlineKeyboardButton("❌ Cancel This Task", callback_data=f"task_cancel:{record['id']}"),
            ]
        ])
        await update.message.reply_text(card_text, parse_mode="Markdown", reply_markup=kb)
        return

    # 3. Natural Language triggers
    lower = text.lower()
    if lower.startswith("remind me ") or lower.startswith("remind "):
        # Strip trigger word and route through cmd_remind parsing
        clean_text = re.sub(r'^remind\s+(?:me\s+)?', '', text, flags=re.IGNORECASE)
        context.args = clean_text.split()
        await cmd_remind(update, context)
        return

    if any(k in lower for k in ["tasks", "schedules", "reminders", "list task", "show task"]):
        await show_tasks_list(chat_id, context)
        return

    # Default: Show main menu
    await cmd_start(update, context)


# =====================================================================
# BACKGROUND SCHEDULER & ALARM DAEMON
# =====================================================================

async def reminder_daemon_loop(application):
    """Continuously monitors scheduled tasks and delivers 1-Hour advance alarms & Due alarms."""
    logger.info("Scheduler Daemon started.")
    while True:
        try:
            now_ts = int(time.time())
            reminders = load_reminders()
            updated = False

            for r in reminders:
                if r.get("status") != "active":
                    continue

                chat_id = r.get("chat_id")
                task_id = r.get("id")
                task_details = r.get("details", "Scheduled Task")
                target_str = r.get("target_time_str", "")
                target_ts = r.get("target_ts", 0)
                remind_1h_ts = r.get("remind_1h_ts", 0)

                # 1. Deliver 1-Hour Advance Alarm
                if not r.get("remind_1h_sent") and now_ts >= remind_1h_ts and target_ts > now_ts:
                    r["remind_1h_sent"] = True
                    updated = True
                    alarm_msg = (
                        f"⏰🚨 *[1-HOUR ADVANCE REMINDER]*\n"
                        f"──────────────────────────────\n"
                        f"Your scheduled work is due in **1 hour**!\n\n"
                        f"📌 *Task Details:*\n"
                        f"{task_details}\n\n"
                        f"🗓️ *Scheduled Due Time:* `{target_str}`\n"
                        f"──────────────────────────────\n"
                        f"💡 *Prepare your files, messages, or work now so you're ready on time!*"
                    )
                    kb = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Mark Done", callback_data=f"task_done:{task_id}"),
                            InlineKeyboardButton("⏱️ Snooze 15m", callback_data=f"task_snooze:{task_id}:15"),
                        ],
                        [
                            InlineKeyboardButton("⏱️ Snooze 30m", callback_data=f"task_snooze:{task_id}:30"),
                            InlineKeyboardButton("❌ Cancel", callback_data=f"task_cancel:{task_id}"),
                        ]
                    ])
                    try:
                        await application.bot.send_message(
                            chat_id=chat_id,
                            text=alarm_msg,
                            parse_mode="Markdown",
                            reply_markup=kb
                        )
                        logger.info(f"Delivered 1-hour alarm for task {task_id}")
                    except Exception as err:
                        logger.error(f"Failed to deliver 1h alarm for {task_id}: {err}")

                # 2. Deliver Exact Due Time Alarm
                if not r.get("due_sent") and now_ts >= target_ts:
                    r["due_sent"] = True
                    updated = True
                    due_msg = (
                        f"🔔🎯 *[DUE TIME ALARM - TIME TO WORK!]*\n"
                        f"──────────────────────────────\n"
                        f"It is now time to execute your scheduled work!\n\n"
                        f"📌 *Task Details:*\n"
                        f"{task_details}\n\n"
                        f"🗓️ *Due:* `{target_str}`\n"
                        f"──────────────────────────────"
                    )
                    kb = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Mark as Done", callback_data=f"task_done:{task_id}"),
                            InlineKeyboardButton("⏱️ Snooze 15m", callback_data=f"task_snooze:{task_id}:15"),
                        ],
                        [
                            InlineKeyboardButton("⏱️ Snooze 1 Hour", callback_data=f"task_snooze:{task_id}:60"),
                            InlineKeyboardButton("❌ Cancel", callback_data=f"task_cancel:{task_id}"),
                        ]
                    ])
                    try:
                        await application.bot.send_message(
                            chat_id=chat_id,
                            text=due_msg,
                            parse_mode="Markdown",
                            reply_markup=kb
                        )
                        logger.info(f"Delivered due-time alarm for task {task_id}")
                    except Exception as err:
                        logger.error(f"Failed to deliver due alarm for {task_id}: {err}")

            if updated:
                save_reminders(reminders)

        except Exception as e:
            logger.error(f"Error in scheduler daemon loop: {e}", exc_info=True)

        await asyncio.sleep(15)


# =====================================================================
# MAIN ENTRYPOINT
# =====================================================================

async def post_init(application):
    commands = [
        BotCommand("start", "Open task scheduler dashboard"),
        BotCommand("remind", "Set reminder: /remind <time> - <task>"),
        BotCommand("tasks", "View all active scheduled tasks"),
        BotCommand("clear", "Clear completed tasks"),
        BotCommand("help", "Scheduler help & usage guide"),
    ]
    await application.bot.set_my_commands(commands)
    asyncio.create_task(reminder_daemon_loop(application))
    logger.info("Bot-2 commands registered & scheduler daemon active.")


def main():
    if not acquire_single_instance_lock():
        sys.exit(0)

    if not STUDIO_BOT_TOKEN:
        print("❌ Error: STUDIO_BOT_TOKEN not set in environment.")
        sys.exit(1)

    print("🚀 Starting Design Hub Work & Task Scheduler Bot (@designposterbot)...")
    app = ApplicationBuilder().token(STUDIO_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("remind", cmd_remind))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(CommandHandler("reminders", cmd_tasks))
    app.add_handler(CommandHandler("schedules", cmd_tasks))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("adduser", cmd_adduser))
    app.add_handler(CommandHandler("listusers", cmd_listusers))
    app.add_handler(CommandHandler("removeuser", cmd_removeuser))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    app.run_polling()


if __name__ == "__main__":
    main()
