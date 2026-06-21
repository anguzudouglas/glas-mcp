from typing import List, Dict, Any


def format_results(raw: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Normalise raw DDGS result dicts into the standard Glas MCP result shape.
    """
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in raw
    ]
