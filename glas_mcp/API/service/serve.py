"""
glas_mcp/API/service/serve.py

Comprehensive REST API router for Glas MCP.

All responses follow the Glas Unified Response Schema (GURS):
  {
    "ok":     true | false,
    "tool":   "tool_name" | null,
    "result": { ... } | null,
    "error":  { "code": str, "message": str, "details": any } | null,
    "meta":   { "execution_time_ms": int, "timestamp": str,
                "request_id": str, "version": str }
  }

Mount this router on your FastAPI app with:
    app.include_router(api_router, prefix="/api/v1")
"""
from __future__ import annotations

import os
import shutil
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

VERSION = "1.0.0"


# ── Pydantic models ────────────────────────────────────────────────────────────

class ToolExecuteRequest(BaseModel):
    arguments: Dict[str, Any] = {}

class SkillCreateRequest(BaseModel):
    name: str
    tool: str
    description: str
    version: str = "1.0.0"
    tags: list[str] = []
    content_md: str

class SkillUpdateRequest(BaseModel):
    description: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[list[str]] = None
    content_md: Optional[str] = None


# ── Response builder ───────────────────────────────────────────────────────────

def _meta(start: float, request_id: Optional[str] = None) -> Dict:
    return {
        "execution_time_ms": int((time.perf_counter() - start) * 1000),
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "request_id":        request_id or str(uuid.uuid4()),
        "version":           VERSION,
    }

def _ok(result: Any, *, tool: Optional[str] = None,
        start: float = 0, request_id: Optional[str] = None) -> Dict:
    return {
        "ok":     True,
        "tool":   tool,
        "result": result,
        "error":  None,
        "meta":   _meta(start, request_id),
    }

def _err(code: str, message: str, *,
         tool: Optional[str] = None, details: Any = None,
         status: int = 400, start: float = 0,
         request_id: Optional[str] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "ok":     False,
            "tool":   tool,
            "result": None,
            "error":  {"code": code, "message": message, "details": details},
            "meta":   _meta(start, request_id),
        },
    )


# ── Router factory ─────────────────────────────────────────────────────────────

def create_api_router(tools: Dict, skills_loader) -> APIRouter:
    """
    Build and return the /api/v1 router.

    Args:
        tools:         dict[name, BaseTool] from ToolsLoader.load_all()
        skills_loader: SkillsLoader instance (already loaded)
    """
    router = APIRouter(tags=["Glas MCP"])

    # ── /health ────────────────────────────────────────────────────────────────
    @router.get("/health", summary="Server health check")
    async def health():
        t0 = time.perf_counter()
        return _ok({
            "status":       "ok",
            "tools_loaded": len(tools),
            "skills_loaded": len(skills_loader.list_names()),
            "uptime_note":  "Use /tools and /skills for full listings",
        }, start=t0)

    # ── /schema ────────────────────────────────────────────────────────────────
    @router.get("/schema", summary="Glas Unified Response Schema (GURS) documentation")
    async def schema():
        t0 = time.perf_counter()
        return _ok({
            "description": "All Glas MCP API endpoints return this schema.",
            "schema": {
                "ok":     {"type": "boolean", "description": "true on success, false on error"},
                "tool":   {"type": "string|null", "description": "Tool name involved, or null"},
                "result": {"type": "object|null", "description": "Tool output on success"},
                "error": {
                    "type": "object|null",
                    "properties": {
                        "code":    "Machine-readable error identifier (e.g. TOOL_NOT_FOUND)",
                        "message": "Human-readable error description",
                        "details": "Extra context, stack trace, or validation errors",
                    },
                },
                "meta": {
                    "execution_time_ms": "Wall-clock time for this request",
                    "timestamp":         "ISO 8601 UTC timestamp",
                    "request_id":        "Unique request identifier (UUID)",
                    "version":           "API version string",
                },
            },
            "error_codes": {
                "TOOL_NOT_FOUND":       "No tool registered with that name",
                "TOOL_EXECUTION_ERROR": "Tool ran but returned an error in its output",
                "INVALID_ARGUMENTS":    "Request body failed validation",
                "SKILL_NOT_FOUND":      "No skill registered with that name",
                "SKILL_EXISTS":         "A skill with that name already exists (use PUT to update)",
                "SKILL_WRITE_ERROR":    "Could not write skill files to disk",
                "INTERNAL_ERROR":       "Unexpected server-side error",
            },
        }, start=t0)

    # ── /tools ─────────────────────────────────────────────────────────────────
    @router.get("/tools", summary="List all registered tools")
    async def list_tools():
        t0 = time.perf_counter()
        result = []
        for name, tool in sorted(tools.items()):
            result.append({
                "name":         tool.name,
                "description":  tool.description.strip()[:300],
                "input_schema": tool.input_schema,
            })
        return _ok({"count": len(result), "tools": result}, start=t0)

    @router.get("/tools/{name}", summary="Get a single tool's full schema")
    async def get_tool(name: str):
        t0 = time.perf_counter()
        tool = tools.get(name)
        if not tool:
            return _err("TOOL_NOT_FOUND", f"No tool named '{name}'",
                        tool=name, status=404, start=t0)
        return _ok({
            "name":         tool.name,
            "description":  tool.description.strip(),
            "input_schema": tool.input_schema,
        }, tool=name, start=t0)

    @router.post("/tools/{name}", summary="Execute a tool")
    async def execute_tool(name: str, body: ToolExecuteRequest, request: Request):
        t0 = time.perf_counter()
        rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))

        tool = tools.get(name)
        if not tool:
            return _err("TOOL_NOT_FOUND", f"No tool named '{name}'",
                        tool=name, status=404, start=t0, request_id=rid)
        try:
            result = await tool.execute(body.arguments)
        except Exception as exc:
            return _err("TOOL_EXECUTION_ERROR", str(exc),
                        tool=name, status=500, start=t0, request_id=rid)

        # If the tool itself signals an error in its result dict, reflect that
        if isinstance(result, dict) and result.get("error") and not result.get("success", True):
            return JSONResponse(
                status_code=200,   # tool ran — it just reported an error in its domain
                content={
                    "ok":     False,
                    "tool":   name,
                    "result": result,
                    "error": {
                        "code":    "TOOL_EXECUTION_ERROR",
                        "message": result.get("error", "Tool reported an error"),
                        "details": None,
                    },
                    "meta": _meta(t0, rid),
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "ok":     True,
                "tool":   name,
                "result": result,
                "error":  None,
                "meta":   _meta(t0, rid),
            },
        )

    # ── /skills ────────────────────────────────────────────────────────────────
    @router.get("/skills", summary="List all registered skills")
    async def list_skills():
        t0 = time.perf_counter()
        skills_loader.load_all()   # hot-reload from disk
        items = skills_loader.to_api_list()
        hint  = skills_loader.agent_hint()
        return _ok({
            "count":       len(items),
            "agent_hint":  hint,
            "skills":      items,
        }, start=t0)

    @router.get("/skills/{name}", summary="Get a skill's full content")
    async def get_skill(name: str):
        t0 = time.perf_counter()
        skills_loader.load_all()
        skill = skills_loader.get(name)
        if not skill:
            return _err("SKILL_NOT_FOUND", f"No skill named '{name}'",
                        status=404, start=t0)
        return _ok({
            "name":        skill.name,
            "tool":        skill.tool,
            "description": skill.description,
            "version":     skill.version,
            "tags":        skill.tags,
            "content_md":  skill.content_md,
        }, start=t0)

    @router.post("/skills", summary="Create a new skill (saved to disk)")
    async def create_skill(body: SkillCreateRequest):
        t0 = time.perf_counter()
        skills_loader.load_all()

        if skills_loader.get(body.name):
            return _err("SKILL_EXISTS",
                        f"Skill '{body.name}' already exists. Use PUT to update it.",
                        status=409, start=t0)

        skill_dir = os.path.join(skills_loader.skills_root, f"{body.name}_skill")
        # If dir already exists without proper files, reuse it
        os.makedirs(skill_dir, exist_ok=True)

        cfg = {
            "name":        body.name,
            "tool":        body.tool,
            "description": body.description,
            "version":     body.version,
            "tags":        body.tags,
        }
        try:
            with open(os.path.join(skill_dir, "skill.yaml"), "w") as f:
                yaml.dump(cfg, f, allow_unicode=True)
            with open(os.path.join(skill_dir, "skill.md"), "w", encoding="utf-8") as f:
                f.write(body.content_md)
        except Exception as exc:
            shutil.rmtree(skill_dir, ignore_errors=True)
            return _err("SKILL_WRITE_ERROR", str(exc), status=500, start=t0)

        skills_loader.load_all()
        return _ok({"name": body.name, "created": True}, start=t0)

    @router.put("/skills/{name}", summary="Update an existing skill's content")
    async def update_skill(name: str, body: SkillUpdateRequest):
        t0 = time.perf_counter()
        skills_loader.load_all()
        skill = skills_loader.get(name)
        if not skill:
            return _err("SKILL_NOT_FOUND", f"No skill named '{name}'",
                        status=404, start=t0)

        yaml_path = os.path.join(skill.skill_dir, "skill.yaml")
        md_path   = os.path.join(skill.skill_dir, "skill.md")

        try:
            with open(yaml_path) as f:
                cfg = yaml.safe_load(f) or {}
            if body.description is not None: cfg["description"] = body.description
            if body.version     is not None: cfg["version"]     = body.version
            if body.tags        is not None: cfg["tags"]        = body.tags
            with open(yaml_path, "w") as f:
                yaml.dump(cfg, f, allow_unicode=True)

            if body.content_md is not None:
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(body.content_md)
        except Exception as exc:
            return _err("SKILL_WRITE_ERROR", str(exc), status=500, start=t0)

        skills_loader.load_all()
        return _ok({"name": name, "updated": True}, start=t0)

    @router.delete("/skills/{name}", summary="Delete a skill (removes from disk)")
    async def delete_skill(name: str):
        t0 = time.perf_counter()
        skills_loader.load_all()
        skill = skills_loader.get(name)
        if not skill:
            return _err("SKILL_NOT_FOUND", f"No skill named '{name}'",
                        status=404, start=t0)
        try:
            shutil.rmtree(skill.skill_dir)
        except Exception as exc:
            return _err("SKILL_WRITE_ERROR", str(exc), status=500, start=t0)
        skills_loader.load_all()
        return _ok({"name": name, "deleted": True}, start=t0)

    # ── /agent-context ─────────────────────────────────────────────────────────
    @router.get("/agent-context", summary="Complete context block for an agent system prompt")
    async def agent_context():
        """
        Returns a pre-formatted system-prompt block listing all tools and skills.
        Inject this into any LLM system prompt to make it aware of Glas MCP.
        """
        t0 = time.perf_counter()
        skills_loader.load_all()

        tool_lines = [
            f"- {t.name}: {t.description.strip()[:150]}"
            for t in tools.values()
        ]
        skill_lines = [
            f"- {s.name} (for {s.tool}): {s.description}"
            for s in skills_loader._skills.values()
        ]

        block = (
            "You are connected to Glas MCP — a tool server providing the following capabilities:\n\n"
            "## Available Tools\n"
            + "\n".join(tool_lines)
            + "\n\n## Available Skills (usage guidance)\n"
            + ("\n".join(skill_lines) if skill_lines else "(none)")
            + "\n\nAlways consult the relevant skill before calling a tool for optimal output quality."
        )

        return _ok({
            "context_block": block,
            "tool_count":    len(tools),
            "skill_count":   len(skills_loader.list_names()),
        }, start=t0)

    return router
