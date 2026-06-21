"""
glas_mcp/main.py — Glas MCP Server Entry Point

Exposes:
  GET  /sse       — MCP Server-Sent Events endpoint (MCP clients connect here)
  POST /messages  — MCP client-to-server messages
  GET  /api/v1/*  — Glas REST API (plug-and-play tool execution)
  GET  /          — Frontend documentation + playground
  GET  /health    — Quick health probe
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

_HERE       = os.path.dirname(os.path.abspath(__file__))
TOOLS_ROOT  = os.path.join(_HERE, "tools")
SKILLS_ROOT = os.path.join(_HERE, "skills")
FRONTEND    = os.path.join(_HERE, "frontend", "index.html")

# ── Shared mutable state ────────────────────────────────────────────────────
# Closures in the API router capture these objects by reference.
# The lifespan updates them in-place so closures always see current data.
from glas_mcp.engine.tools_loader import ToolsLoader
from glas_mcp.skills.base import SkillsLoader

_tools:  dict = {}                            # populated in lifespan
_sl = SkillsLoader(SKILLS_ROOT)               # instance created now; load_all() called in lifespan

# ── Build REST router NOW (before app starts) ───────────────────────────────
# Closures inside create_api_router reference _tools and _sl by identity.
# When lifespan calls _tools.update() and _sl.load_all(), all closures
# automatically see the populated data at request time.
from glas_mcp.API.service.serve import create_api_router
_api_router = create_api_router(_tools, _sl)

# ── MCP setup ──────────────────────────────────────────────────────────────
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
                name        = t.name,
                description = t.description.strip(),
                inputSchema = t.input_schema,
            )
            for t in _tools.values()
        ]

    @_mcp.call_tool()
    async def _mcp_call_tool(name: str, arguments: dict):
        import json
        tool = _tools.get(name)
        if not tool:
            return [mcp_types.TextContent(type="text", text=f"Error: no tool named '{name}'")]
        result = await tool.execute(arguments or {})
        return [mcp_types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]


# ── Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Populate tools dict in-place (closures already hold this dict reference)
    loaded = ToolsLoader(TOOLS_ROOT).load_all()
    _tools.update(loaded)

    # Populate skills loader in-place
    _sl.load_all()

    names = sorted(_tools.keys())
    skill_names = _sl.list_names()
    print(f"[Glas MCP] {len(names)} tools: {names}")
    print(f"[Glas MCP] {len(skill_names)} skills: {skill_names}")

    yield

    _tools.clear()


# ── FastAPI app ────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Glas MCP",
    description = "Modular MCP server — tools for web, math, charts, and documents.",
    version     = "1.0.0",
    lifespan    = lifespan,
    docs_url    = "/api/docs",
    redoc_url   = "/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST router before the app starts (routes registered at compile time)
app.include_router(_api_router, prefix="/api/v1")


# ── MCP SSE endpoints ──────────────────────────────────────────────────────
if _MCP_OK:
    @app.get("/sse", include_in_schema=False)
    async def sse_endpoint(request: Request):
        async with _sse.connect_sse(request.scope, request.receive, request.send) as streams:
            await _mcp.run(streams[0], streams[1], _mcp.create_initialization_options())

    @app.post("/messages", include_in_schema=False)
    async def messages_endpoint(request: Request):
        await _sse.handle_post_message(request.scope, request.receive, request.send)
else:
    @app.get("/sse",      include_in_schema=False)
    async def sse_unavailable():   return {"error": "mcp package not installed"}

    @app.post("/messages", include_in_schema=False)
    async def msgs_unavailable():  return {"error": "mcp package not installed"}


# ── REST API index ─────────────────────────────────────────────────────────
@app.get("/api/v1", include_in_schema=False)
async def api_root():
    return {
        "name":    "Glas MCP REST API",
        "version": "1.0.0",
        "docs":    "/api/docs",
        "endpoints": [
            "GET  /api/v1/health",
            "GET  /api/v1/schema",
            "GET  /api/v1/tools",
            "GET  /api/v1/tools/{name}",
            "POST /api/v1/tools/{name}",
            "GET  /api/v1/skills",
            "GET  /api/v1/skills/{name}",
            "POST /api/v1/skills",
            "PUT  /api/v1/skills/{name}",
            "DELETE /api/v1/skills/{name}",
            "GET  /api/v1/agent-context",
        ],
    }


# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "tools_loaded": len(_tools), "mcp_sse": _MCP_OK}


# ── Frontend ───────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def frontend():
    if os.path.exists(FRONTEND):
        return FileResponse(FRONTEND, media_type="text/html")
    return HTMLResponse(
        "<h1>Glas MCP</h1><p>See <a href='/api/docs'>/api/docs</a>.</p>"
    )
