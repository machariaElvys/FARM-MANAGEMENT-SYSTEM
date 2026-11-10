# Shamba Ledger — Farm Record Management System

A farm record system for small farms: planting, inputs, labour, expenses,
harvests, and sales in one ledger, with yearly reports (expenses, sales,
**profit**, harvest quantities, and a month-by-month profit breakdown),
CSV export, and offline-first sync for patchy rural connectivity.

## Stack

- React + Vite frontend (offline-first: IndexedDB cache + outbox sync)
- FastAPI backend
- SQLAlchemy 2 + Alembic migrations
- PostgreSQL in deployment; SQLite as the zero-setup local default

## Quick start (local development)

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then set a real JWT_SECRET in .env
alembic upgrade head   # create tables + seed categories
uvicorn app.main:app --reload
```

The API is at `http://127.0.0.1:8000`; interactive docs at `/docs`.
Settings come from the environment or `backend/.env`:
`ENVIRONMENT`, `DATABASE_URL`, `JWT_SECRET`, `ACCESS_TOKEN_MINUTES`,
`FRONTEND_ORIGIN`, `FRONTEND_ORIGINS`, and the auth rate-limit settings.

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

The frontend defaults to `http://127.0.0.1:8000/api`; set `VITE_API_URL`
at build time if the API is hosted elsewhere.

## Tests

```bash
cd backend
pytest
```

Tests cover auth, per-farmer ownership isolation, report math (profit and
monthly breakdown), CSV export, login rate limiting, admin guards, and
offline sync upsert/delete.

## Database migrations

```bash
cd backend
alembic upgrade head     # apply migrations
alembic current          # show current revision
alembic downgrade base   # roll back everything (destructive)
```

Local SQLite files (`*.db`) are git-ignored — never commit real data.

## Production checklist

- [ ] Set `ENVIRONMENT=production` and a random `JWT_SECRET` (32+ chars).
      The app **refuses to start** in production with the dev secret.
      Generate one: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- [ ] Set `DATABASE_URL` to PostgreSQL and run `alembic upgrade head`.
- [ ] Set `FRONTEND_ORIGIN` / `FRONTEND_ORIGINS` to your deployed frontend URL(s).
- [ ] Build the frontend with `VITE_API_URL` pointing at the deployed API.
- [ ] Grant the first admin via SQL (see `backend/ADMIN_SETUP.md`) — never
      through the public sign-up form.
- [ ] Note: auth rate limits are per-process. Behind multiple workers or
      replicas, enforce limits at the edge (Cloudflare/nginx) or use Redis.

## Features

- Farmer registration and bearer-token login (Argon2 password hashing)
- Farm records with search, edit, and delete — always scoped to the owner
- Yearly reports: expenses, sales, **profit (sales − expenses)**, harvest
  quantities by unit, category breakdown, and monthly profit
- CSV export of records (`GET /api/reports/export.csv?year=YYYY`, or all
  years when `year` is omitted)
- Offline-first: app shell cached by a service worker, records stored in
  IndexedDB, queued create/update/delete operations sync when connectivity
  returns (idempotent operation IDs; last-write-wins on conflicts)
- Admin area: account overview, paginated user search, suspend/reactivate
