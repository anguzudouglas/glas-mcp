"""
main.py — Glas MCP root entry point

Single command starts the full stack:
    python main.py

In DEV mode (DEV=true), also starts the Vite frontend dev server.
In production, serves pre-built React from glas_mcp/static/.

Environment variables:
    PORT   Server port          (default: 8000)
    HOST   Bind address         (default: 0.0.0.0)
    DEV    Enable dev mode      (default: false)
    VITE_PORT  Vite dev port    (default: 5173)
"""
from __future__ import annotations

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

# Make glas_mcp importable from the project root
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from glas_mcp.main import app  # noqa: F401  (re-exported for uvicorn)


# ── Dev: start Vite alongside uvicorn ────────────────────────────────────────
def _start_vite():
    """Start Vite dev server in a subprocess (DEV mode only)."""
    frontend_dir = Path(__file__).parent / "frontend"
    if not frontend_dir.exists():
        print("[Glas MCP] No frontend/ directory found — skipping Vite.")
        return

    vite_port = int(os.environ.get("VITE_PORT", 5173))
    node_modules = frontend_dir / "node_modules"

    # Install deps if needed
    if not node_modules.exists():
        print("[Glas MCP] Installing frontend dependencies (npm install)…")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)

    print(f"[Glas MCP] Starting Vite dev server on http://localhost:{vite_port}")
    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(vite_port)],
        cwd=frontend_dir,
    )

    def _stop():
        proc.terminate()

    import atexit
    atexit.register(_stop)

    # Give Vite a moment to start
    time.sleep(1.5)


# ── Build frontend for production ─────────────────────────────────────────────
def _build_frontend_if_needed():
    """
    In production, build the React app if static/ is missing or stale.
    Skipped if glas_mcp/static/index.html already exists (Docker build handles it).
    """
    static_index = Path(__file__).parent / "glas_mcp" / "static" / "index.html"
    if static_index.exists():
        return  # Already built

    frontend_dir = Path(__file__).parent / "frontend"
    if not frontend_dir.exists():
        return  # No frontend directory

    print("[Glas MCP] Building frontend…")
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
    subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
    print("[Glas MCP] Frontend built → glas_mcp/static/")


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    port   = int(os.environ.get("PORT", 8000))
    host   = os.environ.get("HOST", "0.0.0.0")
    dev    = os.environ.get("DEV", "false").lower() == "true"

    if dev:
        # Start Vite in a background thread so uvicorn stays in the foreground
        t = threading.Thread(target=_start_vite, daemon=True)
        t.start()
        print(f"[Glas MCP] DEV mode — backend: http://localhost:{port}  frontend: http://localhost:5173")
    else:
        _build_frontend_if_needed()

    uvicorn.run(
        "glas_mcp.main:app",
        host=host,
        port=port,
        reload=dev,
        log_level="info",
    )


if __name__ == "__main__":
    main()
