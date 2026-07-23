"""CLI entry: `sentinel-server` or `python -m sentinel_server`."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run(
        "sentinel_server.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
    )


if __name__ == "__main__":
    main()
