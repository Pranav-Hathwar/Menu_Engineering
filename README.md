# MenuMind Pro

MenuMind Pro is a full-stack restaurant menu-engineering application. It ingests messy sales exports, normalizes them into clean sales records, and turns them into dashboards, BCG-style menu classifications, raw data review, and rule-based recommendations.

## Stack

- **Frontend:** React, Vite, React Router, Tailwind CSS, Framer Motion, Recharts, Axios, Lucide icons
- **Backend:** FastAPI, SQLAlchemy, Pydantic Settings, Pandas, PyJWT, bcrypt
- **Database:** SQLite (local dev) or PostgreSQL (production)

---

## Running the App

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env         # then open .env and set values
uvicorn app.main:app --reload
```

The API runs at **http://localhost:8000**.  
The interactive API docs are at **http://localhost:8000/docs**.  
Health check: **http://localhost:8000/health**.

> **SQLite (default):** Set `DATABASE_URL=sqlite:///./menumind.db` in `.env` — no extra setup needed.  
> **PostgreSQL:** Run `docker compose up -d` inside `backend/`, then set `DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/menumind`.

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The app runs at **http://localhost:5173** and proxies all `/api` calls to the backend.

---

## Default Login (local dev only)

A development admin (`admin@restaurant.com`) ships with the bundled SQLite DB
for convenience. **It is for local use only — never expose it on a deployed
instance.** Create your own admin and delete the demo one before any real use.

Passwords must be at least 10 characters with an uppercase letter, a lowercase
letter, a number, and a symbol.

To create a fresh admin account:

```bash
# Windows PowerShell
$env:ADMIN_EMAIL="owner@example.com"
$env:ADMIN_PASSWORD="StrongPass!123"
python create_admin.py

# macOS / Linux
ADMIN_EMAIL="owner@example.com" ADMIN_PASSWORD="StrongPass!123" python create_admin.py
```

---

## How the App Works

### Login
Open **http://localhost:5173** and sign in with the credentials above. The app issues a JWT access token, stored in the browser's `localStorage`; all subsequent API calls attach it automatically. A `401` response clears the token and redirects to the login page.

### Upload Sales Data
Go to the **Upload** page. Drop a CSV, Excel, or JSON file exported from your POS system. The pipeline:

1. Detects headers automatically, even for messy or non-standard column names.
2. Infers which columns represent item name, quantity sold, revenue, cost, and date.
3. Parses dates accurately: detects day-first (DD/MM/YYYY) vs month-first
   columns automatically, reads ISO dates and Excel serial day numbers, and
   assigns any unreadable date the file's most common date (reported back as
   `dates_defaulted`).
4. Normalizes and saves every row as a structured sales record.

Accepted formats: `.csv`, `.xlsx`, `.xls`, `.json`. Identical re-uploads to the
same restaurant are rejected (sha256 content hash) to prevent double-counting.

### Dashboard
After uploading, the **Dashboard** shows:

- Total revenue, estimated gross profit, and units sold for the selected period.
- Week-over-week comparison cards (last 7 data days vs the prior 7).
- Daily revenue trend chart with a 7-day moving average.
- Weekday performance profile (average revenue per day of week).
- Top revenue drivers, category mix, and the four-quadrant menu matrix.
- A sortable daily breakdown table with CSV export.

### Recipes & Costs (ingredient-level COGS)
The **Recipes & Costs** page holds a per-restaurant ingredient price list and a
recipe (bill-of-materials) builder for each menu item. When an item has a
recipe, all analytics use its live recipe cost instead of the flat `unit_cost`
from the uploaded file — update one ingredient price and every affected item's
margin recalculates instantly. Recipe-costed items are badged in the Catalog.

### Email Auto-Ingestion (daily POS reports)
Point the POS's scheduled daily report at a dedicated inbox, then set
`INGEST_EMAIL`, `INGEST_EMAIL_PASSWORD` (an app password), and
`INGEST_ENABLED=true` in `backend/.env`. The backend polls the inbox every
`INGEST_POLL_MINUTES`, ingests CSV/Excel/JSON attachments through the normal
upload pipeline (so duplicate reports are rejected automatically), and shows
status + a "Check inbox now" button on the Upload page. Optionally restrict
accepted senders with `INGEST_ALLOWED_SENDERS`.

### Monthly Reports & Data Retention
The **Monthly Report** page shows item-wise totals for any month with data —
or the running month (1st → today) at any time — with CSV export and print.
A reminder banner appears on the Dashboard at month end and again in the first
days of the new month. MenuMind keeps the **current and previous month** of
data; anything older is flagged on the Dashboard and deleted only after the
owner explicitly confirms.

### Insights & Price Simulator
The **Insights** page adds rule-based recommendations per item plus a
**price/margin what-if simulator**: pick an item, move its price up to ±20%,
choose how price-sensitive its demand is, and see the projected revenue and
profit impact before touching the real menu.

### Menu Classification (BCG Matrix)
The **Catalog** page classifies every menu item into one of four quadrants based on popularity (quantity sold) and profitability (net margin):

| Class       | High Profit | Low Profit |
|-------------|-------------|------------|
| **High Volume** | Stars      | Plowhorses |
| **Low Volume**  | Puzzles    | Dogs       |

- **Stars** — keep and promote.
- **Plowhorses** — high sellers but thin margins; find cost savings.
- **Puzzles** — high margin but underordered; market them more.
- **Dogs** — candidates for removal or repricing.

### Raw Data Viewer
The **Raw Data** page shows every imported sales record in a paginated table. You can filter by date range or item name, and inspect exactly what the upload pipeline parsed.

### Recommendations
The **Recommendations** page surfaces rule-based insights:

- Revenue concentration warnings (e.g., top 3 items drive 80%+ of revenue).
- Profit-driver identification.
- Trend signals (items growing or declining week-over-week).
- Margin watchlist items below a healthy threshold.
- Category mix observations.

---

## Environment Variables

All backend configuration lives in `backend/.env` (copy from `backend/.env.example`).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | SQLAlchemy URL. SQLite for dev, PostgreSQL for prod. |
| `SECRET_KEY` | ✅ | — | JWT signing secret. Use a long random value. |
| `ALGORITHM` | | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `60` | Access-token lifetime. |
| `APP_NAME` | | `MenuMind Pro` | App name shown in API metadata. |
| `DEBUG` | | `false` | Verbose logging when truthy. |
| `AUTO_CREATE_TABLES` | | `true` | Auto-create tables on startup (dev convenience). |
| `MAX_UPLOAD_BYTES` | | `10485760` | Max upload size (10 MB). |
| `LOGIN_MAX_ATTEMPTS` | | `5` | Failed logins before lockout. |
| `LOGIN_LOCKOUT_SECONDS` | | `300` | Lockout window in seconds. |
| `CORS_ORIGINS` | | `http://localhost:5173,http://localhost:3000` | Comma-separated allowed browser origins. **Add your production frontend URL before deploying.** |

The frontend needs no `.env`: in dev it proxies `/api` to `http://localhost:8000` (see `vite.config.js`); in the Docker image nginx proxies `/api` to the backend container.

---

## Docker (full stack)

From the `backend/` directory:

```bash
docker compose up --build
```

This starts PostgreSQL, the API (`http://localhost:8000`), and the built frontend behind nginx (`http://localhost:8080`). Set a real `SECRET_KEY` in `backend/docker-compose.yml` before any non-local use.

---

## Tests

```bash
# Backend (unit tests live in backend/tests/)
cd backend
venv\Scripts\activate
pytest

# Frontend production build
cd frontend
npm run build
```

Manual/smoke helpers (require a running server) live in `backend/scripts/`:

```bash
cd backend
python scripts/health_check.py     # ping the running API
python scripts/check_process.py    # run the upload pipeline in-process
```

---

## Production Notes

The app ships with rate-limited login, bcrypt password hashing, owner-scoped data,
env-driven CORS, a `/health` endpoint, duplicate-upload protection (content-hash
dedupe), batch-level delete, and split production bundles. With `DEBUG` off the
backend **refuses to start** unless `SECRET_KEY` is a strong (≥32-char) non-placeholder
value. Before a serious deployment, also add: Alembic migrations (replacing the runtime
schema guard), managed secrets, HTTPS/TLS termination, a CI pipeline, observability
(structured logs + metrics), and move the JWT off `localStorage` to an httpOnly cookie.
