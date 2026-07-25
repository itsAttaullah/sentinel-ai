# Sentinel AI Web UI

React + Vite UI for exploring projects, runs, timelines, and metrics.

## Prerequisites

- Node.js 20+
- Sentinel API running on `http://localhost:8080` (`docker compose up` or local uvicorn)

## Setup

```powershell
cd apps\web
npm install
npm run dev
```

Open http://localhost:5173

The Vite dev server proxies `/v1` and `/healthz` to the API, so no CORS setup is required for local use.

## Optional API URL

Set `VITE_API_URL` if you are not using the Vite proxy (e.g. production build talking to a remote API):

```powershell
$env:VITE_API_URL = "http://localhost:8080"
npm run build
```

## Routes

| Path | View |
|---|---|
| `/` | Projects |
| `/projects/:projectId` | Runs list + project metrics |
| `/projects/:projectId/runs/:runId` | Run detail waterfall + metrics |

## Out of scope (this phase)

- Auth UI / RBAC
- Benchmark leaderboards
- Eval score editors
