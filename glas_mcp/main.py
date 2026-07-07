"""
glas_mcp/main.py — Glas MCP Server

Endpoints:
  GET  /sse            MCP SSE transport (AI agents connect here)
  POST /messages       MCP client → server messages
  GET  /api/v1/*       Glas REST API
  GET  /api/v1/providers          List all AI providers
  GET  /api/v1/providers/{name}   Get one provider config
  GET  /health         Health probe
  GET  /*              React frontend (SPA catch-all)
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

_HERE         = Path(__file__).parent
TOOLS_ROOT    = str(_HERE / "tools")
SKILLS_ROOT   = str(_HERE / "skills")
PROVIDERS_ROOT= str(_HERE / "providers")
STATIC_DIR    = str(_HERE / "static")          # built React output
STATIC_INDEX  = str(_HERE / "static" / "index.html")
LEGACY_HTML   = str(_HERE / "frontend" / "index.html")  # fallback

# ── Shared state (closures capture by reference) ────────────────────────────
from glas_mcp.engine.tools_loader     import ToolsLoader
from glas_mcp.engine.providers_loader import ProvidersLoader
from glas_mcp.skills.base             import SkillsLoader

_tools:     dict = {}
_providers: dict = {}
_sl = SkillsLoader(SKILLS_ROOT)

# ── Build routers before app starts ─────────────────────────────────────────
from glas_mcp.API.service.serve import create_api_router
_api_router = create_api_router(_tools, _sl)

# ── MCP setup ────────────────────────────────────────────────────────────────
try:
    from mcp.server import Server as McpServer
    from mcp.server.sse import SseServerTransport
    import mcp.types as mcp_types
    _MCP_OK = True
except ImportError:
    _MCP_OK = False

if _MCP_OK:
    _mcp = McpServer("glas-mcp")
    _sse = SseServerTransport("/messages")

    @_mcp.list_tools()
    async def _mcp_list_tools():
        return [
            mcp_types.Tool(
                name=t.name,
                description=t.description.strip(),
                inputSchema=t.input_schema,
            )
            for t in _tools.values()
        ]

    @_mcp.call_tool()
    async def _mcp_call_tool(name: str, arguments: dict):
        import json
        tool = _tools.get(name)
        if not tool:
            return [mcp_types.TextContent(type="text", text=f"Error: no tool '{name}'")]
        result = await tool.execute(arguments or {})
        return [mcp_types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load tools
    loaded = ToolsLoader(TOOLS_ROOT).load_all()
    _tools.update(loaded)

    # Load skills
    _sl.load_all()

    # Load providers
    prov_loaded = ProvidersLoader(PROVIDERS_ROOT).load_all()
    _providers.update(prov_loaded)

    print(f"[Glas MCP] {len(_tools)} tools:     {sorted(_tools.keys())}")
    print(f"[Glas MCP] {len(_sl.list_names())} skills:   {_sl.list_names()}")
    print(f"[Glas MCP] {len(_providers)} providers: {sorted(_providers.keys())}")

    yield

    _tools.clear()
    _providers.clear()


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Glas MCP",
    description="Modular MCP server — tools for web, math, charts, and documents.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API router
app.include_router(_api_router, prefix="/api/v1")


# ── Provider endpoints ────────────────────────────────────────────────────────
@app.get("/api/v1/providers", tags=["providers"], summary="List all AI providers")
async def list_providers():
    """Return all auto-discovered AI provider configurations."""
    safe = [{k: v for k, v in p.items() if not k.startswith("_")} for p in _providers.values()]
    return {"ok": True, "providers": safe, "count": len(safe)}


@app.get("/api/v1/providers/{name}", tags=["providers"], summary="Get a specific provider")
async def get_provider(name: str):
    p = _providers.get(name)
    if not p:
        return JSONResponse(status_code=404, content={"ok": False, "error": f"Provider '{name}' not found"})
    return {"ok": True, "provider": {k: v for k, v in p.items() if not k.startswith("_")}}


# ── MCP SSE endpoints ─────────────────────────────────────────────────────────
if _MCP_OK:
    @app.get("/sse", include_in_schema=False)
    async def sse_endpoint(request: Request):
        async with _sse.connect_sse(request.scope, request.receive, request.send) as streams:
            await _mcp.run(streams[0], streams[1], _mcp.create_initialization_options())

    @app.post("/messages", include_in_schema=False)
    async def messages_endpoint(request: Request):
        await _sse.handle_post_message(request.scope, request.receive, request.send)
else:
    @app.get("/sse", include_in_schema=False)
    async def sse_unavailable(): return {"error": "mcp package not installed"}

    @app.post("/messages", include_in_schema=False)
    async def msgs_unavailable(): return {"error": "mcp package not installed"}


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health():
    return {
        "status": "ok",
        "tools_loaded": len(_tools),
        "providers_loaded": len(_providers),
        "mcp_sse": _MCP_OK,
    }


@app.get("/api/v1", include_in_schema=False)
async def api_root():
    return {
        "name": "Glas MCP REST API", "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": [
            "GET  /api/v1/tools",
            "POST /api/v1/tools/{name}",
            "GET  /api/v1/skills",
            "GET  /api/v1/providers",
            "GET  /api/v1/providers/{name}",
            "GET  /health",
        ],
    }


# ── Frontend (SPA) ─────────────────────────────────────────────────────────────
# Serve built React app from glas_mcp/static/; fall back to legacy index.html.
# The catch-all must come LAST so API routes take priority.
_has_static = os.path.isdir(STATIC_DIR) and os.listdir(STATIC_DIR)

if _has_static:
    # Serve static assets (JS/CSS/images) at /assets/*
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets"), html=False), name="assets")

@app.get("/{full_path:path}", include_in_schema=False)
async def spa_catch_all(full_path: str):
    """Serve the React SPA for all non-API routes (client-side routing)."""
    if _has_static and os.path.exists(STATIC_INDEX):
        return FileResponse(STATIC_INDEX, media_type="text/html")
    if os.path.exists(LEGACY_HTML):
        return FileResponse(LEGACY_HTML, media_type="text/html")
    return HTMLResponse("<h1>Glas MCP</h1><p>See <a href='/api/docs'>/api/docs</a></p>")
