# Schema Versioning & Compatibility Policy

**Applies to:** `packages/schema` wire formats and OpenAPI contracts  
**Schema family:** `1.x` (current: `1.0.0`)

---

## 1. Identifiers

| Field | Where | Meaning |
|---|---|---|
| `schema_version` | Every Run, Span, Event, IngestBatch | Semver string of the **trace wire format** (e.g. `"1.0.0"`) |
| OpenAPI `info.version` | `openapi/openapi.yaml` | Version of the **HTTP API surface** (may move independently) |

Trace schema and HTTP API versions are **not** required to match.

---

## 2. Semver rules for `schema_version`

| Change type | Example | Version bump |
|---|---|---|
| **Major** | Rename/remove required field; change meaning of `kind` | `2.0.0` |
| **Minor** | Add optional field; add enum value that old clients can ignore | `1.1.0` |
| **Patch** | Docs-only clarification; tighter validation that rejects previously undocumented garbage | `1.0.1` |

### Compatibility commitments (1.x)

1. **Additive preferred.** New optional fields and new enum values are allowed in minor releases.
2. **Readers must ignore unknown fields** (forward compatibility).
3. **Writers must not omit required fields** defined for their declared `schema_version`.
4. **Breaking changes require a new major** and a migration note in this package.
5. Ingest **may** accept N-1 minor within the same major via an explicit compatibility shim (implemented in server phases)—not assumed in Phase 1.

---

## 3. Idempotency keys

Ingest is at-least-once. Upserts key on:

| Entity | Idempotency key |
|---|---|
| Run | `(project_id, run_id)` |
| Span | `(project_id, span_id)` |
| Event | `(project_id, event_id)` |

Re-sending the same IDs with updated fields is an upsert, not a duplicate row.

---

## 4. Status model

### Run `status`

`running` | `succeeded` | `failed` | `cancelled` | `timed_out`

### Span `status`

`ok` | `error` | `unset`

---

## 5. Timestamps

All timestamps are ISO-8601 / RFC 3339 strings in UTC, e.g. `2026-07-23T09:15:30.123Z`.

---

## 6. Extensibility

- `attributes` (object) holds open key/value extensions.
- `tags` (string array) holds low-cardinality labels for filtering.
- Kind-specific payloads (`llm`, `tool`, …) are optional objects; unknown kinds use `custom` + attributes.

---

## 7. Redaction

Schemas allow optional rich payloads (`input`, `output`, `messages`, etc.).  
Production systems SHOULD apply project redaction policies before durable storage (see NFR-SEC). Schemas do **not** encrypt data.

---

## 8. Deprecation process

1. Mark field `deprecated` in schema description and docs.
2. Keep accepting it for at least one minor release.
3. Remove only in a major version.

---

## 9. Fixture policy

- `fixtures/valid/**` MUST validate against the matching schema.
- `fixtures/invalid/**` MUST fail validation for the documented reason in the companion `*.md` or filename.
- Golden fixtures are part of the conformance surface for future SDKs and adapters.
