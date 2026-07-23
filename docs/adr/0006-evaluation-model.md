# ADR-0006: Explicit Versioned Evaluation Model

- **Status:** Accepted
- **Date:** 2026-07-23

## Context

“Quality” without a declared method is not actionable. LLM judges drift; prompts change; CI needs stable gates.

## Decision

1. Every score references a **versioned evaluator** definition (deterministic, judge, or plugin).
2. Re-evaluation creates new score records; historical scores remain immutable.
3. CI gates should prefer **deterministic** evaluators; judges are opt-in and must record model + prompt version.
4. Suites bind tasks → evaluators → thresholds explicitly.

## Consequences

### Positive

- Reproducible comparisons
- Auditable regressions
- Safer CI usage

### Negative

- More ceremony than “auto quality score”
- Judge costs must be managed

### Follow-ups

- Human-in-the-loop review UI (later phase)
- Statistical significance helpers for benchmark diffs
