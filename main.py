"""
main.py — Glas MCP root entry point

Run with:
    python main.py
or:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
import os
import sys

# Make glas_mcp importable from the project root
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from glas_mcp.main import app  # noqa: F401  (re-exported for uvicorn)


def main():
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("DEV", "false").lower() == "true"
    uvicorn.run(
        "glas_mcp.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
