# Skill: web_fetch

**Tool:** `web_fetch`  
**Version:** 1.0.0

## Purpose
Fetch any URL and receive clean Markdown content, links, and metadata — without a browser. Use after `web_search` to read the full content of a result, or directly when you know the target URL.

## Parameters Quick Reference

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `url` | string | **required** | `https://` added if missing |
| `mode` | string | `"auto"` | `auto`, `standard`, `js`, `cache` |
| `strategy` | string | `"auto"` | JS bypass strategy (see below) |
| `timeout` | integer | 30 | 5–120 seconds |
| `proxy` | string | `""` | `"http://user:pass@host:port"` |
| `include_links` | boolean | true | Set false to reduce response size |
| `include_raw_html` | boolean | false | Rarely needed |

## Mode Selection Guide

| Site Type | Recommended Mode |
|-----------|-----------------|
| Static site / documentation | `standard` |
| News site, blog | `auto` |
| React/Next.js SPA (returns shell) | `js` |
| Cloudflare-protected | `js` with `strategy: "cloudscraper"` |
| Site is down / blocked | `cache` |
| Unknown | `auto` (default, safe) |

## Strategy Selection (when mode = "js")

| Strategy | Best For |
|----------|----------|
| `smart_headers` | General Chrome fingerprint bypass |
| `session_warmup` | Sites that check referrer chain |
| `referer_bypass` | Sites that check Google referrer |
| `tls_ciphers` | TLS fingerprint checks |
| `http2` | HTTP/2 only servers |
| `cloudscraper` | Cloudflare IUAM challenges |
| `mobile_bypass` | Desktop-blocking sites |
| `embedded_json` | Next.js / Nuxt / Redux apps |
| `api_discovery` | SPAs with undocumented JSON APIs |
| `cache_fallback` | When live site is unreachable |

## Decision Tree

```
Know the URL?
  → mode: "auto" (let the tool decide)

Site is React/Vue/Angular (you see a loading spinner or blank page)?
  → mode: "js"

Getting 403/429?
  → mode: "js", strategy: "cloudscraper" or "referer_bypass"

Site is completely down?
  → mode: "cache"

Just need article text (no links)?
  → include_links: false

Scraping many pages in a loop?
  → timeout: 15, include_raw_html: false to keep responses small
```

## Output Fields

| Field | Description |
|-------|-------------|
| `success` | `true` / `false` |
| `url` | Original URL |
| `final_url` | URL after redirects |
| `title` | Page `<title>` |
| `description` | `<meta name="description">` |
| `markdown` | Full page content as Markdown |
| `links` | Array of `{text, href}` |
| `links_count` | Number of links |
| `status_code` | HTTP status |
| `strategy_used` | Which engine/strategy succeeded |
| `is_spa_shell` | True if the page is a JS shell with no real content |
| `cache_source` | Set when mode=cache: `google_cache`, `bing_cache`, `wayback_machine` |

## Quality Tips

- **Check `is_spa_shell`** — if `true` and mode was `auto`, re-call with `mode: "js"`.
- **Check `success: false`** — inspect `error` field and try a different strategy.
- **Large pages:** `markdown` is capped at 80 000 chars. For full content, paginate or use `api_discovery` to find the raw data endpoint.
- **Rate limits (429):** Add `timeout: 60` and retry after a delay; consider `proxy` if available.
- **`embedded_json` strategy** is best for Next.js sites — it extracts `__NEXT_DATA__` which often contains ALL page content pre-rendered.

## Common Mistake

Do **not** call `web_fetch` with `mode: "js"` for every URL — it is significantly slower than `standard`. Use `auto` mode and only escalate if `is_spa_shell` is true or status is 403/429/503.
