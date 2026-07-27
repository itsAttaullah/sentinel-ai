# Security Policy

## Supported versions

Security fixes are applied on the latest `main` release line (`1.x`).

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Email the maintainers via the contact listed on the GitHub repository profile, or open a **private** security advisory on GitHub if enabled.

Include:

- Affected component (`apps/server`, SDK, adapter, CLI, web)
- Sentinel / package version
- Reproduction steps
- Impact assessment (data exposure, auth bypass, DoS, etc.)

We aim to acknowledge reports within 7 days.

## Hardening defaults

- Prefer `SENTINEL_AUTH_MODE=api_key` outside local development
- Use scoped keys via `SENTINEL_API_KEY_SCOPES` (`ingest` / `read` / `write` / `admin`)
- Keep `SENTINEL_REDACTION_MODE=default` or `strict` in shared environments
- Restrict network access to the API and Postgres
