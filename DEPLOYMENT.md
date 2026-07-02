# Deployment Guide

This guide deploys Python Confidence Coach to:
- **Render** — MCP server + FastAPI backend + managed PostgreSQL
- **Vercel** — React frontend

---

## Prerequisites

- GitHub account with the repo pushed
- [Render](https://render.com) account (free tier works)
- [Vercel](https://vercel.com) account (free tier works)
- Groq API key (`gsk_…`) — free at [console.groq.com](https://console.groq.com)

---

## Step 1 — Generate a SECRET_KEY

Run locally:

```bash
make secret-key
```

Copy the output. You'll need it in Step 3.

---

## Step 2 — Deploy to Render (Blueprint)

1. Push your repo to GitHub.

2. In the Render dashboard: **New → Blueprint** → connect your GitHub repo.

3. Render reads `render.yaml` and creates three resources:
   - `coach-mcp` (Web Service)
   - `coach-backend` (Web Service)
   - `coach-db` (PostgreSQL database)

4. After creation, set the following **secret env vars** in each service's dashboard (Environment tab). Values marked `sync: false` in `render.yaml` are intentionally blank — Render will prompt you.

### coach-mcp — Environment

| Variable | Value |
|---|---|
| `GROQ_API_KEY` | `gsk_your-key` |

### coach-backend — Environment

| Variable | Value |
|---|---|
| `SECRET_KEY` | *(output of `make secret-key`)* |
| `GROQ_API_KEY` | `gsk_your-key` |
| `MCP_SERVER_URL` | `https://coach-mcp.onrender.com/mcp` |
| `CORS_ORIGINS` | `["https://your-app.vercel.app"]` *(fill in after Step 3)* |

> `DATABASE_URL` is auto-populated from `coach-db` — you don't set it manually.

---

## Step 3 — Run the database migration

After both services are live (green in Render dashboard):

1. Render dashboard → **coach-backend** → **Shell** tab
2. Run:

```bash
alembic upgrade head
```

This creates all five tables. Only needed once (or after new migrations).

---

## Step 4 — Deploy to Vercel (Frontend)

1. In the Vercel dashboard: **Add New → Project** → import your GitHub repo.

2. Set the **Root Directory** to `frontend`.

3. Vercel auto-detects Vite. Build settings should be:
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. No env vars needed — `vercel.json` rewrites `/api/*` to `https://coach-backend.onrender.com/api/*`.

5. After deploy, copy your Vercel URL (e.g. `https://python-confidence-coach.vercel.app`).

---

## Step 5 — Update CORS_ORIGINS

Back in the Render dashboard → **coach-backend** → Environment:

```
CORS_ORIGINS = ["https://python-confidence-coach.vercel.app"]
```

Trigger a manual redeploy of `coach-backend` after saving.

---

## Verifying the deployment

```bash
# Backend health check
curl https://coach-backend.onrender.com/health
# {"status":"ok","environment":"production","timestamp":"...","version":"0.1.0"}

# MCP server health check
curl https://coach-mcp.onrender.com/health
# {"status":"ok"}
```

Open your Vercel URL, register an account, and ask a Python question.

---

## Free tier notes

| Service | Free tier behaviour |
|---|---|
| Render Web Services | Spin down after 15 min of inactivity. First request after sleep takes ~30 s. Upgrade to Starter ($7/mo) for always-on. |
| Render PostgreSQL | Free DB expires after 90 days. Upgrade to avoid data loss. |
| Vercel | Always on; generous free limits. |

---

## Environment variable reference

### backend/.env (local dev)

```env
SECRET_KEY=<64-char hex>
DATABASE_URL=postgresql+asyncpg://coach:coach_secret@localhost:5432/confidence_coach
MCP_SERVER_URL=http://localhost:8001/mcp
GROQ_API_KEY=gsk_your-key
CORS_ORIGINS=["http://localhost:5173"]
ENVIRONMENT=development
```

### mcp-server/.env (local dev)

```env
GROQ_API_KEY=gsk_your-key
MCP_HOST=0.0.0.0
MCP_PORT=8001
```

---

## Full-stack Docker (optional local test)

To run everything in containers locally before deploying:

```bash
# Build and start all services
docker compose --profile full up --build

# Run migration (first time only)
docker exec coach_backend alembic upgrade head

# Open http://localhost:5173
```

---

## Updating the deployment

Push a new commit to `main`. Render and Vercel automatically redeploy on push.

If you add a new Alembic migration, run `alembic upgrade head` via the Render Shell after the new backend is live.
