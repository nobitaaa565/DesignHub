# Design Hub — Autonomous Social Commerce & Subscription System

Automate Facebook Page publishing, 24/7 customer comment responding, Canva Pro subscriber management, and manual access control for **Design Hub** (`1312971105242105`) directly from your phone using Telegram and **Google Gemini 3.5 Flash**.

---

## 📁 Repository Structure
```
├── designs/
│   ├── design-1_reference/       # 3D Studio Character style & variations
│   ├── design-2_reference/       # Dark Mode 3D Isometric campaigns
│   ├── design-3_reference/       # Glassmorphism Pricing & Package badges
│   ├── design-4_reference/       # Conceptual Art & Creative Posters
│   └── design-5_reference/       # National & Observance Celebrations
├── bot.py                        # Unified Telegram Bot, Publisher & 24/7 Comment Monitor
├── subscription_manager.py       # SQLite Subscriber Database & 1-Tap Control Engine
├── canva_worker.py               # Headless Playwright Worker (Canva Invites & Kicks)
├── canva_login_helper.py         # 1-Time 30s session cookie capture
├── subscriptions.db              # Local SQLite Database
├── requirements.txt              # Production dependencies
└── .env.example                  # Environment template
```

---

## ⚡ Core Capabilities
- **🤖 Bilingual AI Post Drafter:** Interactive selection between high-converting **Bangla** (`[🇧🇩 বাংলা]`) and **English** (`[🇬🇧 English]`) captions before publishing.
- **💬 24/7 Comment Auto-Responder:** Background async loop scans Facebook posts every 60s, matches intent in Bangla/English, and replies with official Canva Pro rates.
- **👥 Subscriber & Access Engine:**
  - `/add <email> [1m/3m/12m]` — Adds customer and displays 1-tap action card.
  - `/paid <email>` — Confirms bKash/Nagad payment.
  - `/kick <email>` — Strictly manual kick (no auto-kicking without your tap).
  - `/extend <email> [1m/3m/12m]` — Extends subscriber period seamlessly.
  - `/subs` — Live overview of all active paid, pending, and kicked members.
- **🌐 24/7 Always-On Ready:** Built-in zero-dependency HTTP health server on port `10000` for Render deployment and UptimeRobot continuous keep-alive pings.

---

## 🛠️ Telegram Commands
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

---

## 🚀 24/7 Cloud Deployment on Render
1. Connect this repository to **Render.com** as a **Web Service**.
2. **Build Command:** `pip install -r requirements.txt && playwright install chromium`
3. **Start Command:** `python bot.py`
4. Add environment variables from `.env` in the Render dashboard.
5. Copy your Render URL (`https://your-service.onrender.com`) and paste it into **UptimeRobot** (5-minute interval) for 24/7 uninterrupted uptime!
