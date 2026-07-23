# Phase 2 — Python SDK

| Field | Value |
|---|---|
| **Status** | Not started |
| **Branch (suggested)** | `feat/phase-2-python-sdk` |
| **Depends on** | Phase 1 |

## Objectives

- Implement Python tracer (run/span/event APIs)  
- Async buffered export (HTTP and/or file sink)  
- Context propagation for common async patterns  
- `examples/hello-trace` sample  

## Out of Scope

- Framework-specific adapters  
- Production metrics derivation  

## Exit Criteria

- [ ] Installable Python package  
- [ ] Emits schema-valid batches  
- [ ] Hello-trace docs path ≤ 10 minutes  

## Suggested Commit Message

```text
feat: add Python instrumentation SDK and hello-trace example
```

## Suggested PR Title

`feat: Phase 2 — Python SDK`
