# Phase 7 — Evaluation Engine

| Field | Value |
|---|---|
| **Status** | Complete |
| **Branch** | `feat/evaluation` |
| **Depends on** | Phase 3 (+ metrics recommended) |

## Objectives

- Evaluator and suite registry  
- Deterministic evaluators  
- Optional LLM-as-judge with version pinning  
- Immutable score records  

## In Scope (delivered)

- Models: `Evaluator`, `Suite`, `EvalJob`, `Score`
- Deterministic checks: status, exact/regex, tool_called, retries, wall_ms, json type
- Judge evaluators with required `model` + `prompt_version` (`heuristic` / `stub` modes)
- APIs for evaluators, suites, evals, and run scores
- Re-eval creates new jobs/scores (no mutation)
- Docs: `docs/architecture/11-evaluation-model.md`
- Unit + API tests

## Out of Scope

- Full benchmark matrices (Phase 8)  
- Human review workflows  
- Remote hosted LLM judge HTTP provider (fields reserved; heuristic/stub for now)  

## Exit Criteria

- [x] Suite can score a run and return pass/fail  
- [x] Evaluator versions recorded on scores  
- [x] ADR-0006 respected  

## Suggested Commit Message

```text
feat: add versioned evaluation engine and scoring APIs
```

## Suggested PR Title

`feat: versioned evaluation engine and scoring APIs`

## Manual Testing Checklist

- [ ] `pytest .\apps\server\tests\test_eval_engine.py .\apps\server\tests\test_evaluation_api.py -q`
- [ ] Ingest hello batch
- [ ] Create evaluators + suite via API
- [ ] `POST /v1/projects/proj_demo/evals` → `passed` true/false
- [ ] Re-run eval → new job id; score count doubles
- [ ] Confirm duplicate evaluator version returns 400
