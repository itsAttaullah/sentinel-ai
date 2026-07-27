# Sentinel AI — Framework Adapters

Official adapters map agent frameworks into the **canonical Sentinel trace schema** via the Python SDK.

Per [ADR-0007](../../docs/adr/0007-framework-adapters-as-plugins.md):

- Adapters live under `packages/adapters/*` as **separate packages**
- Core SDK and server **never** depend on framework packages
- Official quality bar = the **conformance suite**

## Packages

| Package | Purpose |
|---|---|
| [`base`](./base/) | Plugin protocol, metadata, discovery helpers |
| [`custom`](./custom/) | Reference adapter for hand-rolled agents |
| [`langgraph`](./langgraph/) | LangGraph / LangChain callback adapter (optional deps) |
| [`conformance`](./conformance/) | Shared conformance checks for official adapters |

## Install (editable)

```powershell
pip install -e ".\packages\sdk-python"
pip install -e ".\packages\adapters\base"
pip install -e ".\packages\adapters\custom"
pip install -e ".\packages\adapters\conformance"
pip install -e ".\packages\adapters\langgraph"
```

With LangGraph callback subclass support:

```powershell
pip install -e ".\packages\adapters\langgraph[langchain]"
```

## Boundary

Adapters **instrument** — they do not execute agents or replace frameworks.
