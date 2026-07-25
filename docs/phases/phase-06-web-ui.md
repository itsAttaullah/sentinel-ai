# Phase 6 — Web UI Foundations

| Field | Value |
|---|---|
| **Status** | Complete |
| **Branch** | `feat/web-ui` |
| **Depends on** | Phases 3–5 |

## Objectives

- Project and run list views  
- Run detail timeline / waterfall  
- Basic latency and cost panels  

## In Scope (delivered)

- `apps/web` Vite + React + TypeScript SPA
- Projects list, runs list (status/text filters), run detail
- Span waterfall timeline
- Metrics tiles + kind attribution bars + events list
- Vite proxy to API + CORS allowlist on server for local origins
- README / roadmap / phase docs updates

## Out of Scope

- Benchmark leaderboards (Phase 8)  
- Full RBAC admin UX  
- Production Docker image for the UI (local `npm run dev` is the Phase 6 path)

## Exit Criteria

- [x] Engineer can debug a failed run visually  
- [x] UI uses only public API contracts  

## Suggested Commit Message

```text
feat: add web UI for run exploration and timelines
```

## Suggested PR Title

`feat: web UI for run exploration and timelines`

## Manual Testing Checklist

- [ ] API up: `docker compose up` (or uvicorn)
- [ ] `cd apps\web && npm install && npm run dev`
- [ ] Open http://localhost:5173 — health chip shows API ok
- [ ] Open a project → runs list shows metrics summary
- [ ] Open a run → waterfall + cost/latency panels render
- [ ] Filter runs by status / text
