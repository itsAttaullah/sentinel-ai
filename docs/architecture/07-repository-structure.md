# Repository Structure

**Document:** Architecture Proposal — Monorepo Layout  
**Status:** Target structure for implementation phases  
**Note:** Directories below are the **planned** layout. Phase 0 creates documentation only; code packages appear in later phases.

---

## 1. Proposed Monorepo Tree

```text
sentinel-ai/
├── README.md
├── ROADMAP.md
├── LICENSE                    # selected before public release
├── CONTRIBUTING.md            # later phase
├── CODE_OF_CONDUCT.md         # later phase
├── docker-compose.yml         # later phase
├── docs/
│   ├── architecture/          # vision, requirements, HLD, ...
│   ├── adr/                   # architecture decision records
│   ├── diagrams/              # mermaid sources
│   └── phases/                # per-phase scope notes
├── packages/
│   ├── schema/                # JSON Schema + shared types
│   ├── sdk-python/            # Python instrumentation SDK
│   ├── sdk-typescript/        # TS instrumentation SDK
│   ├── client-python/         # API client (CLI/server tools)
│   ├── conformance/           # adapter conformance vectors
│   └── adapters/
│       ├── custom/            # reference adapter patterns
│       ├── forgemind/         # future
│       ├── research-agent/    # future
│       ├── openai-agents/     # future
│       ├── langgraph/         # future
│       ├── crewai/            # future
│       └── pydantic-ai/       # future
├── apps/
│   ├── server/                # FastAPI control plane + ingest + workers
│   ├── web/                   # Web UI
│   └── cli/                   # Developer CLI
├── examples/
│   ├── hello-trace/           # minimal instrumentation sample
│   └── benchmark-smoke/       # tiny suite example
├── scripts/                   # dev helpers (no git automation required)
└── tests/
    ├── integration/
    └── e2e/
```

---

## 2. Package Ownership

| Path | Owner mindset | Public surface |
|---|---|---|
| `packages/schema` | Compatibility police | Schema versions, fixtures |
| `packages/sdk-*` | Agent developer UX | Tracer APIs |
| `packages/adapters/*` | Framework specialists | Adapter entrypoints |
| `apps/server` | Platform engineers | HTTP API, workers |
| `apps/web` | Product/UX | UI routes |
| `apps/cli` | DX / CI | Commands |
| `docs/*` | Principal architect + all contributors | Living design |

---

## 3. Dependency Direction

```text
adapters → sdk → schema
cli → client → schema
web → (HTTP) server
server → schema
server ✗→ adapters
server ✗→ web
```

---

## 4. Documentation Rules

1. Every phase updates `docs/phases/phase-XX.md` status.  
2. Architectural changes update `docs/architecture/` and add/amend ADRs.  
3. Diagrams live as Markdown with Mermaid (source of truth in-repo).  
4. README remains the entrypoint; avoid duplicating long design prose there.

---

## 5. What Exists After Phase 1

```text
sentinel-ai/
├── README.md
├── ROADMAP.md
├── packages/
│   └── schema/          # JSON Schema v1, fixtures, OpenAPI stub
└── docs/
    ├── architecture/    # proposal set + schema reference
    ├── adr/
    ├── diagrams/
    └── phases/
```

SDK, server, and UI packages appear in later phases.

---

## Related Documents

- [ROADMAP](../../ROADMAP.md)
- [ADR-0003 Modular Monolith](../adr/0003-modular-monolith.md)
