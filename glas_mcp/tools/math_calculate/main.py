"""
glas_mcp/tools/math_calculate/main.py

MCP tool: math_calculate
Executes Python math code in an isolated subprocess and returns captured
stdout, the last expression value, errors, and execution time.

Allowed libraries: math, cmath, statistics, decimal, fractions, random,
itertools, functools, operator, numpy, scipy, sympy, mpmath.
All dangerous modules (os, sys, subprocess, socket, open…) are blocked
at the AST level before the subprocess is even launched.
"""
from __future__ import annotations

from typing import Any, Dict

from glas_mcp.tools.base import BaseTool
from glas_mcp.tools.math_calculate.helpers.sandbox import run_code


class MathCalculateTool(BaseTool):
    """
    MCP tool that safely executes Python math code and returns the results.
    """

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        # ── Input validation ────────────────────────────────────────────────
        if not isinstance(arguments, dict):
            return {"error": "Arguments must be a JSON object."}

        code: str = arguments.get("code", "")
        if not isinstance(code, str) or not code.strip():
            return {"error": "'code' is required and must be a non-empty string."}

        timeout: int  = max(1, min(int(arguments.get("timeout", 15)), 60))
        precision: int = max(1, min(int(arguments.get("precision", 50)), 1000))

        # ── Run in sandbox ──────────────────────────────────────────────────
        result = run_code(code, timeout=timeout, precision=precision)

        # ── Build response ──────────────────────────────────────────────────
        response: Dict[str, Any] = {
            "success":           result["success"],
            "execution_time_ms": result["execution_time_ms"],
        }

        if result.get("stdout"):
            response["output"] = result["stdout"]

        if result.get("result") is not None:
            response["result"] = result["result"]

        if not result["success"]:
            if result["timed_out"]:
                response["error"] = (
                    f"Execution timed out after {timeout}s. "
                    "Simplify the computation or increase timeout."
                )
            elif result.get("error"):
                response["error"] = result["error"]
            else:
                response["error"] = "Execution failed with unknown error."

        # Surface a helpful hint when neither output nor result is present
        if result["success"] and not response.get("output") and not response.get("result"):
            response["hint"] = (
                "No output captured. Use print() to display results, "
                "or ensure the last line is a bare expression."
            )

        return response
