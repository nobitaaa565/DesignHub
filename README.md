# Design Hub — Autonomous Social Commerce & Dual-Bot Cloud System

Automate Facebook Page publishing, 24/7 customer comment responding, Canva Pro subscriber management, and personal work & task scheduling for **Design Hub** (`1312971105242105`) directly from your phone using Telegram and **Google Gemini 3.5 Flash**.

---

## 🤖 Dual Telegram Bot Architecture
1. **Bot-1 (`@designhub_poster_bot` / `bot.py`):**
   - 24/7 Facebook Comment Auto-Responder with Bengali/English rates.
   - Canva Pro automated subscriber activation, payments, and 1-tap member management.
   - AI viral post drafter and payment verification engine.
2. **Bot-2 (`@designposterbot` / `studio_bot.py`):**
   - **Dedicated Work & Task Scheduler:** Schedule client deliverables, page posts, and personal work.
   - **Proactive 1-Hour Advance Alarm:** Alerts you 60 minutes before your scheduled work with full task instructions and notes so you are prepared.
   - **Due-Time Chime:** Alarms when the deadline hits.
   - **1-Tap Quick Actions:** Mark Done, Snooze (+15m, +30m, +1h), or Cancel directly from inline buttons.
   - **Co-Hosted Cloud Daemon:** Automatically launched alongside Bot-1 in the cloud so both bots run 24/7 even when your local machine is off!

---

## 📁 Repository Structure
```
├── bot.py                        # Bot-1: Telegram Bot, Publisher, Comment Monitor & Cloud Host
├── studio_bot.py                 # Bot-2: Dedicated Work & Task Scheduler & 1-Hour Reminder Bot
├── reminders.json                # Persistent task & reminder store for Bot-2
├── Run_Studio_Bot.command        # 1-Click desktop launcher for Bot-2
├── subscription_manager.py       # SQLite Subscriber Database & 1-Tap Control Engine
├── canva_worker.py               # Headless Playwright Worker (Canva Invites & Kicks)
├── canva_login_helper.py         # 1-Time 30s session cookie capture
├── subscriptions.db              # Local SQLite Database
├── requirements.txt              # Production dependencies
└── .env.example                  # Environment template
```

---

## 🛠️ Telegram Commands

### 🔹 Bot-1: Business & Subscription Engine (`@designhub_poster_bot`)
| Command | Action |
|---|---|
| `/add <email> [pkg]` | Adds subscriber and sends 1-tap control card |
| `/paid <email>` | Confirms payment received |
| `/kick <email>` | Manually kicks and revokes user access |
| `/extend <email> [pkg]` | Extends subscriber duration |
| `/subs` | Displays active, pending & kicked subscribers |
| `/check <email>` | Pulls up specific subscriber card with action buttons |
| `/ai <topic>` | Drafts viral post with Bangla/English switcher |
| `/comments` | Triggers immediate Facebook comment scan |
| `/status` | Full system health, subscribers, and API status |

### 🔹 Bot-2: Work & Task Scheduler (`@designposterbot`)
| Command | Action |
|---|---|
| `/start` or `/help` | Opens task scheduler dashboard with active counts |
| `/remind <time> - <task>` | Schedules task with automatic 1-hour pre-alarm & due chime |
| `/tasks` or `/reminders` | Interactive list of scheduled tasks with Snooze & Done buttons |
| `/clear` | Cleans up completed / cancelled tasks from storage |
| `/adduser <id>` | Authorizes a team member Telegram User ID |
| `/listusers` | Lists authorized Telegram accounts |
| `/removeuser <id>` | Revokes an account |

---

## 🚀 24/7 Cloud Deployment on Render
1. Connect this repository to **Render.com** as a **Web Service**.
2. **Build Command:** `pip install -r requirements.txt && playwright install chromium`
3. **Start Command:** `python bot.py`
4. Add environment variables from `.env` in the Render dashboard (`TELEGRAM_BOT_TOKEN`, `STUDIO_BOT_TOKEN`, etc.).
5. When `bot.py` boots, it starts Bot-1 on port `10000` and automatically launches Bot-2 in the background as a co-hosted daemon. Both bots run 24/7 together!
6. Copy your Render URL (`https://your-service.onrender.com`) and paste it into **UptimeRobot** (5-minute interval) for 24/7 uninterrupted uptime.
