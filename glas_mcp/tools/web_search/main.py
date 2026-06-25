from typing import Any, Dict
from ddgs import DDGS
from glas_mcp.tools.base import BaseTool


class WebSearchTool(BaseTool):
    """
    MCP tool that performs web searches using DuckDuckGo.
    """

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        query = arguments.get("query", "")
        num_results = int(arguments.get("num_results", 10))
        num_results = min(num_results, 250)

        if not query:
            return {"error": "query is required"}

        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=num_results))

            results = [
                {
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                }
                for r in raw
            ]
            return results
        except Exception as e:
            return {"error": str(e)}
