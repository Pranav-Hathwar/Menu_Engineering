# 🍽️ MenuMind AI

MenuMind is a production-grade restaurant analytics SaaS platform that entirely removes the guesswork from menu design. By injecting raw CSV/Excel sales data into a deterministic mathematical engine, the platform classifies menu items securely into strict business-actionable paradigms (Stars, Plowhorses, Puzzles, and Dogs) based on the Boston Consulting Group matrix.

## 🚀 Key Features
- **Data Pipeline**: Seamlessly upload and normalize vast arrays of raw CSV/Excel transaction logs via Python Pandas.
- **Menu Engineering Classification**: A powerful backend categorizes items deterministically based on comparative absolute averages for popularity and profitability.
- **Actionable Recommendation Engine**: A rule-based insight generator prescribes precise pricing or operational strategies uniquely matched to specific matrix constraints.
- **Interactive BCG Matrix Visualization**: An enterprise-grade, fully responsive React interface scaling structural matrix insights effortlessly using soft psychology-backed tonal maps.

## 🛠️ Tech Stack
- **Frontend**: React (Vite), Tailwind CSS, Framer Motion, React Router, Axios
- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, Python (Pandas/NumPy)
- **Security**: OAuth2 with JWT password hashing (bcrypt)

## 📸 Screenshots
*(Coming Soon)*
- `[Screenshot: Main Analytics Dashboard]`
- `[Screenshot: Interactive 2x2 Menu Engineering Matrix]`
- `[Screenshot: Easy Drag-and-Drop Data Upload Portal]`

## ⚙️ Setup Instructions

### 1. Architecture Setup
Ensure PostgreSQL is active locally or provisioned via Docker. Create a database named `menumind`.

### 2. Backend Initialization
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```
Create a `.env` file mapping your Postgres URI securely:
`DATABASE_URL=postgresql://user:password@localhost:5432/menumind`
`SECRET_KEY=your_jwt_secret`

Run the engine:
```bash
uvicorn app.main:app --reload
```

### 3. Frontend Initialization
```bash
cd frontend
npm install
npm run dev
```

The unified platform executes securely at `http://localhost:5173`.
