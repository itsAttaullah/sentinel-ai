# Sentinel AI

**Observe. Measure. Benchmark. Improve.**

Sentinel AI is an open-source platform for evaluating, benchmarking, observing, and improving autonomous AI agents.

It is **not** an agent runtime. It is the measurement and observation layer that sits beside any agent framework—custom runtimes, ForgeMind, Research Agent, OpenAI Agents SDK, LangGraph, CrewAI, PydanticAI, and future frameworks via plugins.

---

## Why Sentinel AI Exists

Autonomous agents fail in ways that are hard to see: silent retries, expensive tool loops, planner regressions, memory strategy regressions, and model swaps that quietly raise latency and cost.

Teams need answers to questions such as:

- Why did an agent fail?
- Which model performs better?
- Which planner is more efficient?
- How many retries were needed?
- Which tools consume the most time?
- Which memory strategy performs best?
- What is the average latency?
- What is the execution cost?
- Which version of an agent regressed?

Sentinel AI turns agent execution into structured telemetry, reproducible benchmarks, comparable scores, and actionable diagnostics.

---

## What Sentinel AI Does

| Capability | Description |
|---|---|
| **Observe** | Capture traces, spans, tool calls, planner steps, memory ops, retries, and errors |
| **Measure** | Compute latency, cost, token usage, success rate, retry counts, and efficiency metrics |
| **Benchmark** | Run controlled suites across models, planners, tools, and agent versions |
| **Evaluate** | Score outcomes with rubrics, judges, and deterministic checks |
| **Visualize** | Explore timelines, flame-style traces, regressions, and leaderboards |
| **Compare** | Diff runs, versions, and configurations to find what changed |

---

## Non-Goals (v1)

- Building or hosting agents
- Replacing frameworks such as LangGraph or CrewAI
- Being a general LLM gateway (though adapters may record gateway traffic)
- Guaranteeing agent correctness without evaluation criteria defined by the user

---

## Documentation Map

| Document | Purpose |
|---|---|
| [packages/schema/](./packages/schema/) | JSON Schema contracts, fixtures, OpenAPI |
| [packages/sdk-python/](./packages/sdk-python/) | Python instrumentation SDK |
| [packages/adapters/](./packages/adapters/) | Framework adapters (plugin packages) |
| [apps/server/](./apps/server/) | Ingest API + Postgres control plane |
| [apps/cli/](./apps/cli/) | `sentinel` developer CLI |
| [apps/web/](./apps/web/) | Run exploration + benchmark leaderboard UI |
| [examples/hello-trace/](./examples/hello-trace/) | File-export quickstart |
| [examples/adapter-custom/](./examples/adapter-custom/) | Custom reference adapter example |
| [examples/benchmark-smoke/](./examples/benchmark-smoke/) | Benchmark matrix smoke walkthrough |
| [docs/adr/](./docs/adr/) | Architecture Decision Records |
| [docs/diagrams/](./docs/diagrams/) | Mermaid architecture diagrams |
| [docs/ops/](./docs/ops/) | Backup/restore and release process |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | How to contribute |
| [SECURITY.md](./SECURITY.md) | Vulnerability reporting |
| [CHANGELOG.md](./CHANGELOG.md) | Release notes |
| [LICENSE](./LICENSE) | Apache License 2.0 |

---

## Status

**Current capabilities (v1.0.0)**

- Schema: [`packages/schema`](./packages/schema/)
- Python SDK: [`packages/sdk-python`](./packages/sdk-python/)
- Adapters: [`packages/adapters`](./packages/adapters/) (custom reference + LangGraph)
- Server: [`apps/server`](./apps/server/) (ingest, metrics, evaluation, benchmarks, regression gates, redaction + scoped auth)
- CLI: [`apps/cli`](./apps/cli/) (`upload`, `compare`, `gate`, …)
- Web UI: [`apps/web`](./apps/web/)
- Examples: [`examples/hello-trace`](./examples/hello-trace/), [`examples/adapter-custom`](./examples/adapter-custom/), [`examples/benchmark-smoke`](./examples/benchmark-smoke/)

### Dev setup (virtualenv)

From the repository root (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".\packages\sdk-python[dev]"
pip install -e ".\apps\server[dev]"
pip install -e ".\apps\cli[dev]"
```

Web UI (separate Node toolchain):

```powershell
cd apps\web
npm install
npm run dev
```

Run tests:

```powershell
pytest .\packages\sdk-python\tests -q
pytest .\apps\server\tests -q
pytest .\apps\cli\tests -q
```

`.venv/` is gitignored — never commit the virtualenv.

### Quickstart (local stack)

```powershell
docker compose up --build
```

Upload a sample, then explore in the UI:

```powershell
sentinel init --project-id proj_demo
sentinel upload .\packages\schema\fixtures\valid\ingest-batch.hello.json
cd apps\web
npm install
npm run dev
```

Open http://localhost:5173 → project `proj_demo` → run `run_hello_001`.

---

## Suggested Contribution Workflow

See [CONTRIBUTING.md](./CONTRIBUTING.md). Release tagging: [docs/ops/release-process.md](./docs/ops/release-process.md).

---

## License

Licensed under the [Apache License 2.0](./LICENSE). See [ADR-0005](./docs/adr/0005-license-and-open-source-posture.md).
