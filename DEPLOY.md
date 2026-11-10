# Deploying the Shamba Ledger backend (Render)

The frontend (Cloudflare Pages) is static; this repo's `backend/` is a FastAPI
service that must run somewhere always-on. These are the exact settings used to
host it on Render (free tier works, with caveats noted below).

## Render service settings

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health` |

`requirements.txt` is a full, pinned export of the tested dependency set
(including `SQLAlchemy`, `alembic`, `psycopg` + `psycopg-binary`, and `pwdlib`
with Argon2), so installs are reproducible. The source of truth for abstract
requirements is `pyproject.toml`; if you change it, regenerate with
`pip freeze` minus dev tools (pytest/httpx/iniconfig/pluggy/Pygments/packaging).

## Environment variables (Render → Environment)

| Variable | Required | Notes |
|---|---|---|
| `ENVIRONMENT` | yes | set to `production` |
| `JWT_SECRET` | yes | **min 32 random chars** — the app refuses to boot otherwise. Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | yes | Postgres connection string from Render → New → PostgreSQL, e.g. `postgresql://user:pass@host/db` (the driver `psycopg` v3 is already installed). If omitted, the app falls back to a local SQLite file **which Render's ephemeral disk will wipe on every redeploy** — do not rely on it. |
| `FRONTEND_ORIGINS` | yes | comma-separated allowed CORS origins, e.g. `https://farm-management-system-eh7.pages.dev` (also accepts `FRONTEND_ORIGIN`) |
| `ACCESS_TOKEN_MINUTES` | no | token lifetime, default 720 |
| `LOGIN_RATE_LIMIT_ATTEMPTS` / `REGISTER_RATE_LIMIT_ATTEMPTS` / `AUTH_RATE_LIMIT_WINDOW_SECONDS` | no | per-IP+email auth rate limits (defaults 10 / 5 per 60 s) |

## After the first deploy

1. Open `https://<your-service>.onrender.com/health` — expect `{"status":"ok"}`.
   The health route is `/health`, **not** `/api/health`.
2. Create the tables (one time, and after every schema change):
   Render → your service → **Shell** → `alembic upgrade head`
   (or run it locally against the Render database, using the external DB URL).
3. Verify sign-up works through the live site at
   `https://farm-management-system-eh7.pages.dev` (incognito window).
4. Give the first admin via SQL — see `ADMIN_SETUP.md`.

## Frontend wiring

`VITE_API_URL` is baked in at **build** time, not read at runtime. In
Cloudflare Pages → Settings → Environment variables it must be
`https://<your-service>.onrender.com/api` (note the `/api` suffix), and a
**new deployment/retry** must be triggered after changing it. Then hard-refresh
the site (or purge the service worker cache / bump `CACHE` in `public/sw.js`).

## Troubleshooting

**`/health` returns Render's "Application loading" page forever**
The service never became healthy. In order of likelihood:
1. `ENVIRONMENT=production` without a valid 32+ char `JWT_SECRET` → the app
   raises at startup. Check Logs; set the secret; redeploy.
2. Start command not binding `$PORT` (e.g. hard-coded `--port 8000`) → set
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Root directory not set to `backend` → `app.main` not found.
4. First deploy still running `pip install` — give it a few minutes.

**Sign-up fails with "Server error" but `/health` is OK**
Tables don't exist yet → `alembic upgrade head` (see above). If you point
`DATABASE_URL` at a *new* database, everything is empty: create an account
from the site rather than reusing dev credentials.

**Live site can't reach the API / "Could not reach the server"**
CORS: `FRONTEND_ORIGINS` on the backend must include exactly
`https://farm-management-system-eh7.pages.dev` (no trailing slash). Also
confirm the site was redeployed *after* `VITE_API_URL` was set.

**First request after idle takes ~30–60 s**
Render free tier spins the service down; cold starts are normal. For real
usage, upgrade the instance or add an external uptime pinger (every ~10 min),
and move to managed Postgres (free plan is fine to start) to avoid data loss
from ephemeral disks.

**Rate limiting is per-process.** Behind multiple workers/replicas, enforce
limits at the edge (Cloudflare/nginx) or move to Redis-backed limits.
