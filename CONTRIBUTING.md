# Contributing to Sentinel AI

Thanks for helping improve Sentinel AI.

## Ground rules

1. One focused change per PR (feature, fix, or docs).
2. Prefer tests for behavior changes.
3. Do not commit secrets, `.venv`, or local planning docs that are gitignored.
4. Keep the core SDK/server free of agent-framework dependencies (adapters live under `packages/adapters/`).

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".\packages\sdk-python[dev]"
pip install -e ".\apps\server[dev]"
pip install -e ".\apps\cli[dev]"
```

Web UI:

```powershell
cd apps\web
npm install
npm run dev
```

## Tests

```powershell
pytest .\packages\sdk-python\tests -q
pytest .\apps\server\tests -q
pytest .\apps\cli\tests -q
```

Adapter packages (when touched):

```powershell
pip install -e ".\packages\adapters\base" -e ".\packages\adapters\custom" -e ".\packages\adapters\langgraph" -e ".\packages\adapters\conformance"
pytest .\packages\adapters\conformance\tests .\packages\adapters\custom\tests .\packages\adapters\langgraph\tests -q
```

## Pull requests

- Clear title and summary of *why*
- Test plan checklist
- Link related issues when applicable

## License

By contributing, you agree that your contributions are licensed under the Apache License 2.0 (see `LICENSE`).
