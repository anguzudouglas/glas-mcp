# Tool Creation Guide

A complete walkthrough for adding a new tool to Glas MCP — from empty directory to a working, tested, deployed tool with its own skill.

---

## Overview

Every Glas MCP tool lives in `glas_mcp/tools/<tool_name>/` and requires exactly two files:

```
glas_mcp/tools/my_tool/
├── main.py       ← BaseTool subclass with execute()
└── tool.yaml     ← name, description, input_schema (JSON Schema)
```

The `ToolsLoader` engine scans `tools/` at startup and auto-registers every valid subdirectory. You never touch `main.py` (the server) or any registry.

---

## Step 1 — Create the Directory

```bash
mkdir -p glas_mcp/tools/currency_convert
touch glas_mcp/tools/currency_convert/__init__.py
```

---

## Step 2 — Write `tool.yaml`

`tool.yaml` is the **single source of truth** for the tool's identity and input contract. The MCP tool listing, REST API schema, and frontend playground all read from this file.

```yaml
# glas_mcp/tools/currency_convert/tool.yaml

name: currency_convert
description: >
  Converts an amount from one currency to another using live exchange rates
  from the ECB (European Central Bank) public API. No API key required.
  Supports ~30 major currencies (USD, EUR, GBP, JPY, CHF, CAD, AUD, …).

input_schema:
  type: object
  properties:
    amount:
      type: number
      description: Amount to convert. Must be positive.
    from_currency:
      type: string
      description: Source currency ISO 4217 code (e.g. "USD", "EUR", "GBP").
    to_currency:
      type: string
      description: Target currency ISO 4217 code.
    precision:
      type: integer
      description: Decimal places in the result. Default 2.
      default: 2
  required:
    - amount
    - from_currency
    - to_currency
```

### `input_schema` Rules
- Must be a valid JSON Schema object with `type: object`.
- `properties` keys become the argument names passed to `execute()`.
- Mark required fields in `required`.
- Provide `description` for every property — this is what the LLM reads to understand how to call your tool.
- Use `default` for optional parameters.

---

## Step 3 — Write `main.py`

Your tool must subclass `BaseTool` and implement `async def execute(arguments)`.

```python
# glas_mcp/tools/currency_convert/main.py

from __future__ import annotations

from typing import Any, Dict

import httpx

from glas_mcp.tools.base import BaseTool


class CurrencyConvertTool(BaseTool):
    """
    Converts currency amounts using ECB exchange rate data.
    """

    # ECB publishes daily rates relative to EUR
    _ECB_URL = "https://api.frankfurter.app/latest"

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        # ── 1. Validate inputs ──────────────────────────────────────────────
        if not isinstance(arguments, dict):
            return {"error": "Arguments must be a JSON object."}

        amount = arguments.get("amount")
        from_c = str(arguments.get("from_currency", "")).upper().strip()
        to_c   = str(arguments.get("to_currency",   "")).upper().strip()
        prec   = max(0, min(int(arguments.get("precision", 2)), 10))

        if amount is None:
            return {"error": "'amount' is required."}
        if not from_c:
            return {"error": "'from_currency' is required (e.g. 'USD')."}
        if not to_c:
            return {"error": "'to_currency' is required (e.g. 'EUR')."}

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return {"error": f"'amount' must be a number, got: {amount!r}"}

        if amount <= 0:
            return {"error": "'amount' must be positive."}

        if from_c == to_c:
            return {
                "success":       True,
                "amount":        amount,
                "from_currency": from_c,
                "to_currency":   to_c,
                "converted":     round(amount, prec),
                "rate":          1.0,
                "note":          "Same currency — no conversion needed.",
            }

        # ── 2. Fetch exchange rates ─────────────────────────────────────────
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    self._ECB_URL,
                    params={"from": from_c, "to": to_c, "amount": amount},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return {
                    "error": (
                        f"Currency not supported: '{from_c}' or '{to_c}'. "
                        "Supported: USD, EUR, GBP, JPY, CHF, CAD, AUD, CNY, …"
                    )
                }
            return {"error": f"Exchange rate API error: {exc}"}
        except Exception as exc:
            return {"error": f"Network error fetching exchange rates: {exc}"}

        # ── 3. Extract and return result ────────────────────────────────────
        converted = data["rates"].get(to_c)
        if converted is None:
            return {"error": f"No rate returned for '{to_c}'."}

        rate = converted / amount

        return {
            "success":       True,
            "amount":        amount,
            "from_currency": from_c,
            "to_currency":   to_c,
            "converted":     round(converted, prec),
            "rate":          round(rate, 6),
            "date":          data.get("date", "unknown"),
            "source":        "ECB via api.frankfurter.app",
        }
```

### `execute()` Contract

| Rule | Detail |
|------|--------|
| Signature | `async def execute(self, arguments: Dict[str, Any]) -> Any` |
| Input | Always validate `arguments` — it comes from an LLM and may be malformed |
| Output | Return a JSON-serialisable `dict` or primitive |
| Errors | Return `{"error": "description"}` — do NOT raise exceptions |
| Side effects | Allowed (write files, call APIs) but document them in `tool.yaml` |

---

## Step 4 — Add Helpers (Optional)

For tools with complex logic, put helper functions in a `helpers/` subdirectory:

```
glas_mcp/tools/currency_convert/
├── __init__.py
├── main.py
├── tool.yaml
└── helpers/
    ├── __init__.py
    └── formatter.py   ← e.g. currency symbol lookup, number formatting
```

Import them with a relative-style absolute import:
```python
from glas_mcp.tools.currency_convert.helpers.formatter import format_currency
```

---

## Step 5 — Write a Skill

Add a skill so the LLM uses your tool effectively:

```bash
mkdir -p glas_mcp/skills/currency_convert_skill
```

**`skill.yaml`:**
```yaml
name: currency_convert_skill
tool: currency_convert
version: "1.0.0"
description: Guide the agent to perform accurate currency conversions with proper input validation
tags: [currency, finance, conversion, exchange rate]
```

**`skill.md`:**
```markdown
# Skill: currency_convert

**Tool:** `currency_convert`

## When to Use
- User asks "how much is X USD in EUR?"
- Financial calculations involving multiple currencies
- Price comparisons across countries

## Rules
1. Always confirm the direction: FROM → TO.
2. Use ISO 4217 codes (USD not "dollar", EUR not "euro").
3. For historical rates, note that this tool returns the LATEST rate only.
4. Round precision to 2 for display, higher for calculations.

## Example Call
\`\`\`json
{
  "amount": 1000,
  "from_currency": "USD",
  "to_currency": "JPY",
  "precision": 0
}
\`\`\`
```

---

## Step 6 — Write a Test

```python
# test_currency_convert.py
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(__file__))

from glas_mcp.engine.tools_loader import ToolsLoader

async def main():
    tools_root = os.path.join("glas_mcp", "tools")
    tools = ToolsLoader(tools_root).load_all()
    tool = tools["currency_convert"]

    # Happy path
    r = await tool.execute({"amount": 100, "from_currency": "USD", "to_currency": "EUR"})
    assert r["success"], f"Expected success, got: {r}"
    print(f"100 USD = {r['converted']} EUR (rate: {r['rate']})")

    # Same currency
    r = await tool.execute({"amount": 50, "from_currency": "GBP", "to_currency": "GBP"})
    assert r["converted"] == 50.0

    # Error case
    r = await tool.execute({"amount": -5, "from_currency": "USD", "to_currency": "EUR"})
    assert "error" in r
    print("All tests passed.")

asyncio.run(main())
```

Run with:
```bash
python test_currency_convert.py
```

---

## Step 7 — Verify Auto-Discovery

Start the server and confirm the tool appears:

```bash
python main.py &
curl http://localhost:8000/api/v1/tools | python -m json.tool | grep currency
```

Execute via REST:
```bash
curl -X POST http://localhost:8000/api/v1/tools/currency_convert \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"amount": 100, "from_currency": "USD", "to_currency": "EUR"}}'
```

---

## Checklist

- [ ] `tool.yaml` — `name`, `description`, `input_schema` with `required` fields
- [ ] `main.py` — `BaseTool` subclass, `execute()` validates all inputs
- [ ] `execute()` returns `{"error": "..."}` on failure — never raises
- [ ] `__init__.py` in tool dir (can be empty)
- [ ] Test file passes all cases including error paths
- [ ] Skill added in `glas_mcp/skills/<tool>_skill/`
- [ ] Tool appears in `GET /api/v1/tools`

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `BaseTool` subclass is inside a function / `if __name__` block | Move it to module top level — `ToolFactory` finds it via `dir(module)` introspection |
| `tool.yaml` missing `required` array | Tools called without required args will silently receive `None` |
| `execute()` raises an exception | Wrap in try/except and return `{"error": str(exc)}` |
| Using `import os` inside the tool | Fine for normal tools; blocked only in `math_calculate`'s sandbox |
| Hardcoding a port or file path | Use `os.environ.get()` or `self.tool_dir` relative paths |
