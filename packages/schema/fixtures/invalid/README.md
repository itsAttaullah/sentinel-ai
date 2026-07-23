# Invalid fixtures

These payloads MUST **fail** validation against the listed schema for the documented reason.

| File | Schema | Expected failure |
|---|---|---|
| `run.missing-ended-at.json` | `run.schema.json` | Terminal `status` requires `ended_at` |
| `run.bad-schema-version.json` | `run.schema.json` | `schema_version` must be `1.0.0` |
| `span.llm-missing-payload.json` | `span.schema.json` | `kind=llm` requires `llm` object |
| `span.tool-missing-name.json` | `span.schema.json` | `tool.tool_name` required |
| `event.bad-type.json` | `event.schema.json` | `type` not in enum |
| `ingest-batch.empty.json` | `ingest-batch.schema.json` | At least one non-empty `runs`/`spans`/`events` |
