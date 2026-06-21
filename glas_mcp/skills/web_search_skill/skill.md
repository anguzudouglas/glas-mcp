# Skill: web_search

**Tool:** `web_search`  
**Version:** 1.0.0

## Purpose
Use this skill whenever you need to find current information, research a topic, verify a fact, or discover URLs before fetching them with `web_fetch`.

## Parameters Quick Reference

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `query` | string | **required** | The search query |
| `num_results` | integer | 10 | 1–250 |
| `region` | string | `"wt-wt"` | e.g. `"us-en"`, `"gb-en"` |
| `safe_search` | string | `"moderate"` | `"off"`, `"moderate"`, `"strict"` |
| `time_filter` | string | `""` | `"d"` (day), `"w"` (week), `"m"` (month), `"y"` (year) |

## Query Construction Rules

1. **Be specific.** Prefer `"Python asyncio timeout best practices 2024"` over `"python async"`.
2. **Use quotes for exact phrases:** `"model context protocol" specification`.
3. **Use operators when helpful:** `site:github.com fastapi sse`, `filetype:pdf MCP protocol`.
4. **Strip filler words:** articles, prepositions, vague adjectives add noise.
5. **For recent events** always set `time_filter: "w"` or `"m"` to avoid stale results.
6. **For code/tech questions** include the version: `"numpy 2.0 broadcasting rules"`.
7. **For multi-part questions** issue separate focused queries rather than one compound query.

## Result Interpretation

Each result contains:
- `title` — page title
- `href` — full URL
- `body` — snippet (≤ 200 chars)

A snippet is NOT a substitute for the full page. If the snippet is insufficient, follow up with `web_fetch` on the most relevant URL.

## Decision Tree

```
Need current info?
  → web_search first, then web_fetch the best result

Need a specific document or page you already know?
  → Skip web_search, go straight to web_fetch

Need > 10 results?
  → Set num_results up to 250; scan titles/snippets before fetching

Results too old?
  → Add time_filter: "w" or "m"

Results from wrong country?
  → Set region: "us-en", "gb-en", etc.
```

## Output Example

```json
{
  "query": "FastAPI SSE streaming example",
  "total_results": 10,
  "results": [
    {
      "title": "Server-Sent Events with FastAPI",
      "href": "https://example.com/fastapi-sse",
      "body": "A complete guide to streaming responses using SSE in FastAPI..."
    }
  ]
}
```

## Common Mistakes to Avoid

- **Too broad:** `"machine learning"` → returns generic overviews
- **Too long:** `"what is the best way to do async programming in python with asyncio"` → trim to `"python asyncio best practices"`
- **Ignoring time_filter:** For news, prices, releases — always filter by recency
- **Single result assumption:** Always consider top 3–5 results before deciding which to fetch
