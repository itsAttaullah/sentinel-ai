# System Context Diagram

C4 Level 1 — Sentinel AI in its environment.

```mermaid
C4Context
  title System Context — Sentinel AI

  Person(engineer, "Agent Engineer", "Builds and debugs agents")
  Person(eval, "Eval / QA Engineer", "Defines suites and gates")
  Person(platform, "Platform Engineer", "Self-hosts and operates Sentinel")

  System(sentinel, "Sentinel AI", "Observes, measures, benchmarks, evaluates agent executions")

  System_Ext(agents, "Agent Runtimes", "Custom, ForgeMind, LangGraph, CrewAI, OpenAI Agents SDK, PydanticAI, ...")
  System_Ext(llm, "LLM Providers", "OpenAI, Anthropic, local models, ...")
  System_Ext(ci, "CI Systems", "GitHub Actions, etc.")

  Rel(engineer, agents, "Develops / runs")
  Rel(agents, llm, "Calls models and tools")
  Rel(agents, sentinel, "Emits traces via SDK / adapters")
  Rel(engineer, sentinel, "Inspects timelines, metrics, diffs")
  Rel(eval, sentinel, "Configures evaluators and suites")
  Rel(platform, sentinel, "Deploys and monitors")
  Rel(ci, sentinel, "Uploads traces / checks gates")
```

## Narrative

Actors run agents **outside** Sentinel. Sentinel receives telemetry, stores it, derives metrics and scores, and presents results through UI, CLI, and API. Sentinel does not replace the agent runtime or the LLM provider.
