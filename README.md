# portfolio-backend

A small FastAPI service that auto-maintains the **projects** section of a
personal portfolio.

- **GitHub repos** are pulled via the GitHub API, enriched with AI-generated
  descriptions (Claude Haiku 4.5), and stored in Postgres (Supabase).
- **Manual projects** (freelance, group work, anything without a public repo)
  are added through a protected admin dashboard.
- The public portfolio fetches the unified list from one REST endpoint.

> Goal: adding a GitHub repo or filling the admin form is the **only** action
> needed to get a new project onto the live site. No HTML edits, no redeploys.

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI + Uvicorn |
| Database | Supabase (Postgres), via `supabase-py` |
| AI | Claude Haiku 4.5 — `claude-haiku-4-5-20251001` |
| GitHub | PyGithub (REST v3) |
| Hosting | Render (free web service) |
| Pinger | GitHub Actions cron (keeps the free dyno warm) |

## Project layout

```
portfolio-backend/
├── app/
│   ├── main.py          # FastAPI app, routes, CORS, auth dependency
│   ├── config.py        # Loads env vars (pydantic-settings)
│   ├── models.py        # Pydantic request/response models
│   ├── db.py            # Supabase client + all DB operations
│   ├── github_sync.py   # GitHub pull + sync orchestration
│   ├── claude_enrich.py # Claude prompt + enrichment
│   └── security.py      # X-API-Key validation
├── .github/workflows/ping.yml
├── schema.sql           # Run once in the Supabase SQL editor
├── .env.example
├── requirements.txt
└── render.yaml
```

## API

Base URL (prod): `https://<render-service>.onrender.com`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/health` | — | `{"status":"ok"}` |
| GET | `/projects` | — | optional `?featured=true` |
| GET | `/projects/{slug}` | — | single project |
| POST | `/projects` | `X-API-Key` | create a manual project |
| PUT | `/projects/{slug}` | `X-API-Key` | edit; sets `manual_override=true` |
| DELETE | `/projects/{slug}` | `X-API-Key` | delete |
| POST | `/sync-github` | `X-API-Key` | pull + enrich repos, returns a summary |

`/sync-github` returns: `{synced, enriched, skipped_override, cached, errors[]}`.

## Environment variables

Copy `.env.example` to `.env` and fill in:

| Var | Where to get it |
|---|---|
| `SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase → Project Settings → API (**service_role**, not anon) |
| `GITHUB_TOKEN` | GitHub → Developer settings → fine-grained token, **Public repos read-only** |
| `GITHUB_USERNAME` | your GitHub handle |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `BACKEND_API_KEY` | generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `CORS_ORIGIN` | your portfolio URL, e.g. `https://valeria.dev` |

`.env` is gitignored — never commit it.

## Run locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill it in
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- `GET /health` → `{"status":"ok"}`
- `GET /projects` → `[]` until you sync or add projects

Create a manual project (replace `<KEY>`):

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <KEY>" \
  -d '{"title":"Test","slug":"test","summary":"A test project."}'
```

Sync GitHub repos:

```bash
curl -X POST http://localhost:8000/sync-github -H "X-API-Key: <KEY>"
```

## Deploy (Render)

1. Push this repo to GitHub.
2. render.com → **New → Web Service** → connect this repo. Render reads `render.yaml`.
3. In **Environment**, add all 7 variables with production values
   (set `CORS_ORIGIN` to your real portfolio URL).
4. Deploy. Note the service URL, then:
   - update `<RENDER-SERVICE-NAME>` in `.github/workflows/ping.yml`
   - set `API_BASE` in the portfolio's `admin/admin.js` and the public projects fetch.

## How sync decides what to do

For each public, non-fork, non-archived repo:

1. If a row exists with `manual_override=true` → **skip** (your edits win).
2. If the README hash is unchanged → **cached**, no Claude call (saves money).
3. Otherwise → **enrich** with Claude and upsert (matched on `github_repo_name`).

Cost is Claude-only and tiny (Haiku, READMEs truncated to 12k chars). Everything
else runs on free tiers; the GitHub Actions pinger keeps the Render dyno warm and
the Supabase project active.

## Build phases

See the build spec for the full phased plan. Order: **Supabase → backend skeleton
→ GitHub sync → Claude enrichment → Render deploy → frontend fetch → admin
dashboard → pinger.** Don't skip a phase's verification step — the next one
depends on it.
