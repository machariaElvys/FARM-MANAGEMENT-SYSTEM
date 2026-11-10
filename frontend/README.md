# Shamba Ledger — Frontend

React 19 + Vite single-page app for Shamba Ledger (Farm Record Management System).
See the [root README](../README.md) for the full stack, backend setup, migrations,
and the production checklist.

## Commands

```bash
npm install        # install dependencies
npm run dev        # dev server (use -- --host 0.0.0.0 to expose on your LAN)
npm run build      # production build to dist/
npm run lint       # eslint
```

## Configuration

The frontend talks to the API at `http://127.0.0.1:8000/api` by default.
Set `VITE_API_URL` at **build time** to point at a deployed API, e.g.:

```bash
VITE_API_URL=https://your-api.example.com/api npm run build
```

Authentication uses a bearer token stored in localStorage (`shamba.access-token`).
Records are cached per-user in IndexedDB and mutations are queued in an outbox,
then synced to `POST /api/records/sync` when the connection returns. A service
worker (`public/sw.js`) caches the app shell for offline loads — bump the
`CACHE` version constant when shipping new assets.
