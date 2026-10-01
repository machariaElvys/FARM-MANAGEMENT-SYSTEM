# Farm Record Management System

## Stack

- React + Vite frontend
- FastAPI backend
- SQLAlchemy 2
- PostgreSQL in deployment; SQLite as the zero-setup local default


### Backend

In the first terminal:

```bash
cd backend
source .venv/bin/activate  # if your virtual environment is in backend/.venv
python -m pip install -e .  # run once, or after dependencies change
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive API docs are at `http://127.0.0.1:8000/docs`. The default database is a local SQLite file. The API reads `DATABASE_URL`, `JWT_SECRET`, `ACCESS_TOKEN_MINUTES`, and `FRONTEND_ORIGIN` from the environment or `backend/.env`. If those variables are already set in your shell, keep using them. To use a project `.env` file, copy `.env.example` only if `backend/.env` does not already exist.

### Frontend

In a second Ubuntu terminal:

```bash
cd /mnt/c/Users/User/Documents/Codex/2026-10-01/th/outputs/farm-management-system/frontend
npm install  # run once, or after package.json changes
npm run dev -- --host 0.0.0.0
```

Open the Vite URL printed in the terminal. The frontend defaults to `http://127.0.0.1:8000/api`; set `VITE_API_URL` if the API is hosted elsewhere.

## First-slice scope

- Farmer account registration and bearer-token login
- Farm records for planting, inputs, labour, expenses, harvests, and sales
- Search, edit, and delete records belonging to the signed-in farmer
- Yearly report totals for expenses, sales, harvest quantity, and record categories

Report totals are calculated from farm records so the first version cannot show stale stored summaries. The `admin` role is present in the user model for the later administrator area; public registration always creates a farmer account.

## Next implemented step

Added offline-first behavior: cache the app shell, store records in IndexedDB, and sync queued create/update/delete operations when connectivity returns. The sync API should use idempotent operation IDs and define a conflict policy before multi-device use.

Replace `JWT_SECRET` before deployment. This starter is for development and has not been security-reviewed or deployed.
