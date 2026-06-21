"""
math_calculate/helpers/sandbox.py

Runs arbitrary Python math code inside an isolated subprocess with:
  - AST-based import allowlist (blocks os, sys, socket, subprocess, etc.)
  - stdout / stderr capture
  - hard timeout (SIGKILL after N seconds)
  - last-expression result capture (like a REPL)

Allowed top-level imports
─────────────────────────
  math, cmath, decimal, fractions, statistics, random,
  itertools, functools, operator, abc, typing,
  numpy (as np), scipy, sympy (+ common symbols pre-imported)
"""
from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
import time
from typing import Any, Dict

# Modules the executed code is allowed to import
ALLOWED_MODULES: frozenset[str] = frozenset([
    # stdlib math
    "math", "cmath", "decimal", "fractions", "statistics",
    "random", "itertools", "functools", "operator",
    "abc", "typing", "collections", "numbers",
    "string", "re", "pprint", "copy",
    # third-party math
    "numpy", "np", "scipy",
    "scipy.integrate", "scipy.optimize", "scipy.linalg",
    "scipy.stats", "scipy.fft", "scipy.special",
    "sympy",
    "sympy.core", "sympy.solvers", "sympy.calculus",
    "sympy.geometry", "sympy.matrices", "sympy.series",
    "sympy.simplify", "sympy.functions", "sympy.sets",
    "mpmath",
])

# Patterns that should never appear in trusted math code
_BLOCKED_NAMES: frozenset[str] = frozenset([
    "os", "sys", "subprocess", "socket", "shutil", "pathlib",
    "importlib", "builtins", "ctypes", "cffi", "gc",
    "open", "exec", "eval", "__import__",
    "compile", "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr", "hasattr",
])


# ── AST safety check ──────────────────────────────────────────────────────────

class _SafetyError(ValueError):
    pass


class _SafetyChecker(ast.NodeVisitor):
    """Walk the AST and raise _SafetyError on dangerous constructs."""

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root not in ALLOWED_MODULES:
                raise _SafetyError(
                    f"Import of '{alias.name}' is not allowed. "
                    f"Permitted: math, cmath, statistics, numpy, scipy, sympy."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root = (node.module or "").split(".")[0]
        if root not in ALLOWED_MODULES:
            raise _SafetyError(
                f"Import from '{node.module}' is not allowed. "
                f"Permitted: math, cmath, statistics, numpy, scipy, sympy."
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Block calls like __import__('os'), open('/etc/passwd')
        if isinstance(node.func, ast.Name):
            if node.func.id in _BLOCKED_NAMES:
                raise _SafetyError(f"Call to '{node.func.id}' is not allowed.")
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ("system", "popen", "exec", "eval", "run",
                                  "Popen", "check_output", "call", "spawn"):
                raise _SafetyError(
                    f"Method '{node.func.attr}' is not allowed."
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in ("__class__", "__bases__", "__subclasses__",
                         "__globals__", "__builtins__", "__code__",
                         "__func__", "__self__"):
            raise _SafetyError(
                f"Access to '{node.attr}' is not allowed."
            )
        self.generic_visit(node)


def check_safety(code: str) -> None:
    """
    Parse code and check for disallowed constructs.
    Raises _SafetyError with a descriptive message on violation.
    """
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise _SafetyError(f"Syntax error: {exc}") from exc
    _SafetyChecker().visit(tree)


# ── Subprocess runner ──────────────────────────────────────────────────────────

_PREAMBLE = textwrap.dedent("""\
    import math, cmath, decimal, fractions, statistics
    import itertools, functools, operator, collections, numbers
    import re, pprint, copy

    try:
        import numpy as np
    except ImportError:
        pass

    try:
        import scipy
        import scipy.integrate, scipy.optimize, scipy.linalg
        import scipy.stats, scipy.fft, scipy.special
    except ImportError:
        pass

    try:
        import sympy
        from sympy import *
        from sympy import init_printing
        init_printing(use_unicode=True)
    except ImportError:
        pass

    try:
        import mpmath
        mpmath.mp.dps = {precision}
    except ImportError:
        pass

""")

_RUNNER_TEMPLATE = textwrap.dedent("""\
    {preamble}
    import sys, traceback, ast, json

    _user_code = {code_repr}
    _result = None

    try:
        _tree = ast.parse(_user_code, mode="exec")
        # Capture last expression value
        if _tree.body and isinstance(_tree.body[-1], ast.Expr):
            _last = ast.Expression(body=_tree.body[-1].value)
            _tree.body = _tree.body[:-1]
            ast.fix_missing_locations(_last)
            exec(compile(_tree, "<math>", "exec"), globals())
            _result = eval(compile(_last, "<math>", "eval"), globals())
        else:
            exec(compile(_tree, "<math>", "exec"), globals())

        if _result is not None:
            print("\\n__RESULT__:", repr(_result))

    except Exception:
        print("__ERROR__:", traceback.format_exc(), file=sys.stderr)
""")


def run_code(
    code: str,
    timeout: int = 15,
    precision: int = 50,
) -> Dict[str, Any]:
    """
    Execute math code in an isolated subprocess.
    Returns a dict with keys: stdout, stderr, result, error, execution_time_ms, timed_out.
    """
    # Safety check first (fast, in-process)
    try:
        check_safety(code)
    except _SafetyError as exc:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "result": None,
            "error": f"Safety check failed: {exc}",
            "execution_time_ms": 0,
            "timed_out": False,
        }

    preamble = _PREAMBLE.format(precision=precision)
    runner   = _RUNNER_TEMPLATE.format(
        preamble=preamble,
        code_repr=repr(code),
    )

    t0 = time.perf_counter()
    timed_out = False

    try:
        proc = subprocess.run(
            [sys.executable, "-c", runner],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        returncode = proc.returncode

    except subprocess.TimeoutExpired:
        timed_out = True
        stdout = ""
        stderr = f"Execution timed out after {timeout}s."
        returncode = -1

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    # Extract __RESULT__ line from stdout if present
    result_value = None
    clean_stdout_lines = []
    for line in stdout.splitlines():
        if line.startswith("__RESULT__:"):
            result_value = line[len("__RESULT__:"):].strip()
        else:
            clean_stdout_lines.append(line)
    clean_stdout = "\n".join(clean_stdout_lines).strip()

    # Extract __ERROR__ from stderr
    error_text = ""
    if "__ERROR__:" in stderr:
        error_text = stderr.replace("__ERROR__:", "").strip()
    elif stderr:
        error_text = stderr

    success = returncode == 0 and not timed_out and not error_text

    return {
        "success":            success,
        "stdout":             clean_stdout,
        "result":             result_value,
        "error":              error_text,
        "execution_time_ms":  elapsed_ms,
        "timed_out":          timed_out,
    }
