"""
glas_mcp/tools/web_fetch/main.py

MCP tool: web_fetch
Fetches any URL — including JS-heavy SPAs and bot-protected sites — and
returns clean Markdown, extracted links, page metadata, and optionally raw HTML.

Modes:
  auto     — standard HTTP first; auto JS bypass fallback if needed (default)
  standard — plain HTTP only
  js       — jump straight to JS bypass strategies
  cache    — Google/Bing/AMP/Wayback cache only
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from glas_mcp.tools.base import BaseTool
from glas_mcp.tools.web_fetch.helpers.engines import (
    scrape_standard,
    scrape_js,
    available_strategies,
)
from glas_mcp.tools.web_fetch.helpers.cache_engine import fetch_best_cache
from glas_mcp.tools.web_fetch.helpers.engines import _parse_html

_VALID_MODES      = {"auto", "standard", "js", "cache"}
_VALID_STRATEGIES = set(available_strategies()) | {"auto"}


class WebFetchTool(BaseTool):
    """
    MCP tool that fetches any URL without a browser and returns clean Markdown.
    """

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        # ── Input validation ────────────────────────────────────────────────
        if not isinstance(arguments, dict):
            return {"error": "Arguments must be a JSON object."}

        url: str = str(arguments.get("url", "")).strip()
        if not url:
            return {"error": "'url' is required and must not be empty."}

        if not url.startswith("http"):
            url = f"https://{url}"

        mode: str     = str(arguments.get("mode", "auto")).strip().lower()
        strategy: str = str(arguments.get("strategy", "auto")).strip().lower()
        timeout: int  = int(arguments.get("timeout", 30))
        proxy: str    = str(arguments.get("proxy", "")).strip() or None
        include_links: bool     = bool(arguments.get("include_links", True))
        include_raw_html: bool  = bool(arguments.get("include_raw_html", False))

        if mode not in _VALID_MODES:
            return {
                "error": f"Invalid mode '{mode}'. Must be one of: {sorted(_VALID_MODES)}.",
            }

        if strategy not in _VALID_STRATEGIES:
            return {
                "error": (
                    f"Invalid strategy '{strategy}'. "
                    f"Must be one of: {sorted(_VALID_STRATEGIES)}."
                ),
            }

        timeout = max(5, min(timeout, 120))

        # ── Dispatch to correct engine ──────────────────────────────────────
        try:
            result = await self._fetch(url, mode, strategy, timeout, proxy)
        except Exception as exc:
            return {
                "error": f"Unexpected fetch error: {exc}",
                "url":   url,
                "success": False,
            }

        # ── Post-process: strip fields the caller doesn't want ──────────────
        if not include_links:
            result.pop("links", None)
            result.pop("links_count", None)

        if not include_raw_html:
            result.pop("raw_html", None)

        # Trim very large markdown to stay inside MCP message limits
        md = result.get("markdown", "")
        if len(md) > 80_000:
            result["markdown"] = md[:80_000] + "\n\n[…content truncated at 80 000 chars…]"
            result["markdown_truncated"] = True

        return result

    # ── Private dispatch ────────────────────────────────────────────────────

    async def _fetch(
        self,
        url: str,
        mode: str,
        strategy: str,
        timeout: int,
        proxy: str | None,
    ) -> Dict[str, Any]:

        loop = asyncio.get_event_loop()

        if mode == "standard":
            result = await loop.run_in_executor(
                None, scrape_standard, url, None, timeout, proxy, 3
            )
            result.setdefault("strategy_used", "standard")
            return result

        if mode == "js":
            result = await loop.run_in_executor(
                None, scrape_js, url, timeout, proxy, strategy
            )
            return result

        if mode == "cache":
            hit = await loop.run_in_executor(
                None, fetch_best_cache, url, timeout, proxy
            )
            if hit:
                base = _parse_html(url, hit["html"], 200, "cache")
                base["final_url"] = url
                base["strategy_used"] = "cache_fallback"
                base.update({
                    k: hit[k]
                    for k in ("cache_source", "cache_url", "cache_note")
                    if k in hit
                })
                return base
            return {
                "success":     False,
                "url":         url,
                "error":       "All cache sources failed (Google, Bing, AMP, Wayback).",
                "markdown":    "",
                "links":       [],
                "links_count": 0,
            }

        # ── mode == "auto" ──────────────────────────────────────────────────
        result = await loop.run_in_executor(
            None, scrape_standard, url, None, timeout, proxy, 3
        )

        # Decide whether to try JS bypass
        needs_js = (
            result is not None and (
                result.get("is_spa_shell")
                or result.get("status_code") in (403, 429, 503)
                or (not result.get("success") and result.get("recoverable", False))
            )
        )

        if needs_js:
            js_result = await loop.run_in_executor(
                None, scrape_js, url, timeout, proxy, strategy
            )
            # Only upgrade if JS got more content
            if js_result.get("success") and len(
                js_result.get("markdown", "")
            ) > len((result or {}).get("markdown", "")):
                js_result["fallback_triggered"] = True
                return js_result

        result.setdefault("strategy_used", "standard")
        return result
