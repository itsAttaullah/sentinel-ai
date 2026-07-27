# Release process

Maintainers cut releases from `main` after CI is green.

## Versioning

- Server / public API line: SemVer (`apps/server` `version`)
- Python packages (`sentinel-ai`, adapters, CLI): SemVer; bump when public APIs change
- Trace wire format: `schema_version` in `packages/schema` (independent, additive when possible)

## Checklist

1. Update `CHANGELOG.md` (Added / Changed / Fixed)
2. Bump package versions if needed (`pyproject.toml`, `__version__`, web `package.json` if UI ships)
3. Ensure tests pass:

```powershell
pytest .\apps\server\tests -q
pytest .\apps\cli\tests -q
pytest .\packages\sdk-python\tests -q
```

4. Tag annotated release:

```powershell
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

5. Create a GitHub Release from the tag; paste the changelog section
6. Optional: publish Python packages to PyPI when the distribution pipeline is ready

## Hotfix tags

Use `v1.0.1` style patches. Cherry-pick onto a release branch only if `main` has moved too far.

## Do not

- Force-push tags that others may have consumed
- Ship with `SENTINEL_AUTH_MODE=local` documented as a production default
