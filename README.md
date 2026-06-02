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

## Default Login

| Field    | Value                   |
|----------|-------------------------|
| Email    | `admin@restaurant.com`  |
| Password | `Admin!123`             |

If you need to create a fresh admin account:

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
3. Normalizes and saves every row as a structured sales record.

Accepted formats: `.csv`, `.xlsx`, `.xls`, `.json`.

### Dashboard
After uploading, the **Dashboard** shows:

- Total revenue, profit, and order count for the selected period.
- Revenue and profit trend charts over time.
- Top-performing items by revenue and by profit margin.
- Category mix breakdown.

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
env-driven CORS, a `/health` endpoint, and split production bundles. Before a serious
deployment, also add: Alembic migrations (replacing the runtime schema guard), managed
secrets, HTTPS/TLS termination, a CI pipeline, and observability (structured logs +
metrics).
