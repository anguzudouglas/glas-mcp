# Changelog

All notable changes to Glas MCP are documented here.  
Format: [Semantic Versioning](https://semver.org). Date format: YYYY-MM-DD.

---

## [1.0.0] — 2025-06-21

### Added — Core Infrastructure
- **FastAPI + MCP SSE server** (`glas_mcp/main.py`) — dual transport: MCP over SSE at `/sse` + `/messages`, REST API at `/api/v1/*`
- **ToolsLoader** — auto-discovers tools from `tools/` subdirectories at startup; no registry changes needed when adding tools
- **ToolFactory** — importlib-based dynamic loader; finds BaseTool subclasses via introspection
- **BaseTool** abstract class — YAML-driven tool contract (name, description, input_schema)
- **SkillsLoader** — auto-discovers skills from `skills/` subdirectories; hot-reload on every API request

### Added — REST API (`/api/v1`)
- `GET /health` — server health check
- `GET /schema` — Glas Unified Response Schema (GURS) documentation
- `GET /tools` — list all tools with full JSON Schema
- `GET /tools/{name}` — single tool schema
- `POST /tools/{name}` — execute any tool with arguments
- `GET /skills` — list all skills with `agent_hint` summary
- `GET /skills/{name}` — get skill full markdown content
- `POST /skills` — create a new skill (writes to disk)
- `PUT /skills/{name}` — update existing skill content
- `DELETE /skills/{name}` — remove skill (deletes directory)
- `GET /agent-context` — formatted system-prompt block for LLM injection

### Added — Tools (8 total)
- **`web_search`** — DuckDuckGo search via `ddgs`, up to 250 results, region/time filtering
- **`web_fetch`** — URL → Markdown with 10 JS bypass strategies (smart_headers, session_warmup, referer_bypass, tls_ciphers, http2, cloudscraper, mobile_bypass, embedded_json, api_discovery) + 4 cache fallbacks (Google, Bing, AMP, Wayback Machine); full redirect chain tracking
- **`math_calculate`** — Python math code sandbox (subprocess isolated, AST safety checker); supports numpy, scipy, sympy, mpmath; blocks os/sys/subprocess/socket/open
- **`plot_chart`** — matplotlib chart generator (12 types: line, bar, barh, scatter, pie, histogram, box, area, heatmap, step, stem, errorbar); full color/style/annotation control; returns base64 PNG or SVG
- **`document_create_pdf`** — HTML → PDF via WeasyPrint; full CSS3 print layout, page size, margins, headers/footers, Google Fonts
- **`document_create_docx`** — HTML → Word .docx via htmldocx + python-docx; heading styles, tables, lists
- **`document_create_xlsx`** — structured data → Excel .xlsx via openpyxl; multiple sheets, formulas, freeze panes, column widths
- **`document_create_pptx`** — slide definitions → PowerPoint .pptx via python-pptx; 5 layouts (title, content, two_column, image, blank), speaker notes, theme colors

### Added — Skills (8 total)
- `web_search_skill` — query construction rules, operator syntax, decision tree
- `web_fetch_skill` — mode/strategy selection guide, SPA detection, quality tips
- `math_calculate_skill` — code patterns for numpy/scipy/sympy, timeout guidelines
- `plot_chart_skill` — chart type selection, data structure guide, color palettes, annotation examples
- `pdf_creation_skill` — WeasyPrint HTML template, CSS feature matrix, quality rules
- `docx_creation_skill` — supported HTML elements, Word conversion patterns
- `xlsx_creation_skill` — sheet definition structure, formula examples, multi-sheet guide
- `pptx_creation_skill` — layout types, slide data structure, bullet formatting rules

### Added — Frontend
- **Docs + Playground** (`glas_mcp/frontend/index.html`) — single-page HTML/CSS/JS
  - Tool reference cards with expandable schemas
  - API endpoint documentation with live curl examples
  - Skills management panel (view, enable/disable, add, delete)
  - Live playground: chat with AI using own API key (OpenRouter, Groq, Gemini)
  - Full agentic loop: LLM → tool call → Glas MCP → result → LLM

### Added — Documentation
- `docs/about.md` — project overview, owner, architecture diagram, roadmap
- `docs/tool_creation_guide.md` — step-by-step guide with real `currency_convert` example
- `docs/usage_api.md` — REST API reference with Python, JS, and cURL examples
- `docs/changelog.md` — this file
- `ARCHITECTURE.md` — full system architecture reference
- `replit.md` — project README and developer conventions

### Added — Docker
- `Dockerfile` — multi-stage build, non-root user, health check
- `docker-compose.yml` — single-service compose with volume mounts and env file
- `.dockerignore` — excludes `__pycache__`, `.git`, `node_modules`, test files

### Infrastructure
- CORS middleware enabled (all origins — configure for production)
- Unified Response Schema enforced across all REST endpoints
- `uvicorn` with configurable host/port via `HOST`/`PORT` env vars
- `DEV=true` enables hot reload

---

## [Unreleased]

### Planned
- Google Workspace tools (Drive, Docs, Sheets, Slides) via OAuth2
- Authentication middleware (API key header, JWT)
- Tool call result streaming via SSE
- Prometheus `/metrics` endpoint
- Rate limiting per tool per client IP
- Tool versioning (pin tool version in requests)
- Web UI skill editor (no-code skill creation)

---

## Contributors

| Name | Role |
|------|------|
| Anguzudouglas | Creator, lead developer |

To contribute: see `docs/tool_creation_guide.md` and open a PR at [github.com/anguzudouglas/glas_mcp](https://github.com/anguzudouglas/glas_mcp).
