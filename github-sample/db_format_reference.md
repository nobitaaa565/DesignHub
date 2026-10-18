# DesignHub Master Cloud Database & Application Format Reference

This folder contains the master copy of all application files and the exact database schema configured for Cloud (Render / PostgreSQL) and local operations.

---

## 1. Database Architecture

DesignHub uses a unified database layer defined in `subscription_manager.py`:
- **When `DATABASE_URL` is set** (Render Cloud PostgreSQL): Connects via `psycopg2-binary` to the cloud PostgreSQL database.
- **When `DATABASE_URL` is unset** (Local Machine): Falls back seamlessly to `subscriptions.db` (SQLite).

### Tables & Exact Formats

### Table: `subscriptions`
Stores student / customer Canva Pro subscriber accounts.

| Column | Type (PG) | Type (SQLite) | Default | Description |
|---|---|---|---|---|
| `id` | SERIAL PRIMARY KEY | INTEGER PRIMARY KEY AUTOINCREMENT | — | Unique internal ID |
| `email` | TEXT UNIQUE | TEXT UNIQUE | — | Primary user identifier (case-insensitive) |
| `name` | TEXT | TEXT | `''` | Full customer name |
| `package` | TEXT | TEXT | `'1 Month'` | Plan: `'1 Month'`, `'3 Months'`, `'6 Months'`, `'12 Months'` |
| `days` | INTEGER | INTEGER | `30` | Subscription duration in days (30, 90, 180, 365) |
| `added_at` | TIMESTAMP | TIMESTAMP | `CURRENT_TIMESTAMP` | Initial enrollment date |
| `expires_at` | TIMESTAMP | TIMESTAMP | Required | Subscription expiration datetime |
| `payment_status` | TEXT | TEXT | `'PENDING'` | Status: `'PAID'`, `'PENDING'`, `'REVOKED'` |
| `status` | TEXT | TEXT | `'active'` | Account status: `'active'`, `'kicked'`, `'expired'`, `'pending'` |
| `notes` | TEXT | TEXT | `''` | Admin notes |
| `trx_id` | TEXT | TEXT | `''` | bKash / Nagad Transaction ID |
| `customer_id` | INTEGER | INTEGER | `800+` | Human-readable customer ID (e.g. #801) |
| `fb_sender_id` | TEXT | TEXT | `''` | Messenger / Facebook Sender PSID |
| `last_reminder_at` | TIMESTAMP | TIMESTAMP | `NULL` | Timestamp of last renewal notice |
| `pending_telegram_msg_id` | INTEGER | INTEGER | `NULL` | Verification Telegram message ID |
| `team_name` | TEXT | TEXT | `'Carmella Elan'` | Canva Team roster assignment |

---

### Table: `payments`
Immutable ledger of all verified customer transactions.

| Column | Type (PG) | Type (SQLite) | Default | Description |
|---|---|---|---|---|
| `id` | SERIAL PRIMARY KEY | INTEGER PRIMARY KEY AUTOINCREMENT | — | Transaction ledger ID |
| `customer_id` | INTEGER | INTEGER | `NULL` | Customer #CID |
| `email` | TEXT | TEXT | Required | Customer email |
| `name` | TEXT | TEXT | `''` | Customer name |
| `package` | TEXT | TEXT | `'1 Month'` | Plan: `'1 Month'`, `'3 Months'`, `'6 Months'`, `'12 Months'` |
| `amount` | DOUBLE PRECISION | REAL | Required | **Payment amount in BDT: 25.00, 50.00, or 99.00** |
| `currency` | TEXT | TEXT | `'BDT'` | Currency |
| `provider` | TEXT | TEXT | `'bKash'` | Method: `'bKash'`, `'Nagad'`, `'Rocket'`, `'Bank Transfer'`, `'Other'` |
| `trx_id` | TEXT | TEXT | `''` | Verified Transaction ID |
| `paid_at` | TIMESTAMP | TIMESTAMP | `CURRENT_TIMESTAMP` | Transaction timestamp |
| `notes` | TEXT | TEXT | `''` | Payment reference or note |
| `team_name` | TEXT | TEXT | `'Carmella Elan'` | Team attributed to this payment |

---

### Table: `teams`
List of all Canva Team rosters.

| Column | Type | Default | Description |
|---|---|---|---|
| `id` | PRIMARY KEY | Auto | Team ID |
| `name` | TEXT UNIQUE | Required | Canva team name (e.g. `'Carmella Elan'`, `'Pro Team 2'`) |
| `created_at` | TIMESTAMP | `CURRENT_TIMESTAMP` | Creation time |

---

### Table: `settings`
Key-value store for application configuration.
- `'canva_team_name'`: Active Canva team name.

---

### Table: `consumed_tokens`
Tracks one-time expiring Canva invite tokens.
- `token`: String token (UUID / hex)
- `email`: Target recipient
- `consumed_at`: When the invite was accepted
- `access_count`: Number of accesses

---

## 2. Package Pricing Rules (Strict)

| Package | Duration | Price (BDT) |
|---|---|---|
| **1 Month** | 30 days | **৳25** |
| **3 Months** | 90 days | **৳50** |
| **6 Months** | 180 days | **৳99** |

---

## 3. Cloud Endpoints (`bot.py`)

- `GET /` — Serves the Admin Dashboard (`dashboard.html`)
- `GET /api/subscribers?team=...` — Returns `{ stats, subscribers, teams, team_name, active_team, earnings }`
- `GET /api/payments?team=...` — Returns `{ payments, earnings, teams }`
- `GET /api/teams` — Returns `{ teams, active_team }`
- `OPTIONS *` — Full CORS preflight handler (200 OK)
- `POST /api/subscriber/add` — Enrolls new subscriber with `amount`
- `POST /api/subscriber/paid` — Marks payment status as PAID
- `POST /api/subscriber/extend` — Extends subscription period
- `POST /api/subscriber/kick` — Sets status to kicked
- `POST /api/subscriber/delete` — Deletes subscriber record
- `POST /api/subscriber/update` — Updates fields
- `POST /api/payment/add` — Logs manual payment record
- `POST /api/payment/update` — Updates payment entry
- `POST /api/payment/delete` — Deletes payment entry
- `POST /api/team/add` — Registers new Canva team
- `POST /api/team/delete` — Removes Canva team
- `POST /api/team/update` — Sets active Canva team
