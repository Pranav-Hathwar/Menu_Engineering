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
Open **http://localhost:5173** and sign in with the credentials above. The app issues a JWT token stored in memory; all subsequent API calls are authenticated automatically.

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

## Tests

```bash
# Backend
cd backend
venv\Scripts\activate
pytest

# Frontend type-check / build
cd frontend
npm run build
```

---

## Production Notes

Before deploying: add Alembic migrations, a production Dockerfile for backend and frontend, CI pipeline, managed secrets, HTTPS, rate limiting, and observability.
