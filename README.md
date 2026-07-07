<div align="center">

<img src="https://img.shields.io/badge/Glas_MCP-v1.0-5B6EF5?style=for-the-badge" />
<img src="https://img.shields.io/badge/License-MIT-10D9A0?style=for-the-badge" />
<img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" />

# Glas MCP

**Give your AI agent superpowers.**

Glas MCP is a modular [Model Context Protocol](https://modelcontextprotocol.io) server exposing **8 production-ready tools** over SSE and REST — web search, web fetch, math, charts, and document generation. Plug into any MCP client in 30 seconds.

[**Live Server**](https://glas-mcp.onrender.com) · [**Playground**](https://glas-mcp.onrender.com) · [**API Docs**](https://glas-mcp.onrender.com/api/docs) · [**Swagger UI**](https://glas-mcp.onrender.com/api/docs)

</div>

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Tools](#tools)
- [Providers](#providers)
- [API Reference](#api-reference)
- [MCP Integration](#mcp-integration)
- [Adding Tools](#adding-tools)
- [Adding Providers](#adding-providers)
- [Frontend Development](#frontend-development)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)

---

## Features

| Feature | Detail |
|---|---|
| **8 production tools** | web_search, web_fetch, math_eval, plot_chart, create_docx, create_xlsx, create_pptx, create_pdf |
| **Dual transport** | MCP over SSE (for AI agents) + REST JSON (for apps) |
| **Auto-discovery** | Drop a folder → tool auto-registers on restart. No wiring. |
| **4 AI providers** | Anthropic, Google Gemini, Groq, OpenRouter — loaded from YAML |
| **Multi-page frontend** | Home, Tools, Playground, Docs, API Reference |
| **Single command** | `python main.py` starts the full stack |
| **Docker ready** | Multi-stage build: Node (frontend) → Python (backend) |
| **GURS responses** | Every tool returns `{ ok, tool, result, error, meta }` |

---

## Quick Start

### Option A — Hosted (no setup)

The server is always live at **https://glas-mcp.onrender.com**. Open the playground and paste your API key.

### Option B — Run locally

```bash
# 1. Clone
git clone https://github.com/anguzudouglas/glas-mcp
cd glas-mcp

# 2. Install Python deps
pip install -r glas_mcp/requirements.txt

# 3. Start
python main.py
# → http://localhost:8000
```

### Option C — Dev mode (hot reload for both frontend and backend)

```bash
# Backend reloads on .py changes, Vite HMR for frontend
DEV=true python main.py
# Backend  → http://localhost:8000
# Frontend → http://localhost:5173
```

### Option D — Docker

```bash
docker build -t glas-mcp .
docker run -p 8000:8000 glas-mcp
```

---

## Project Structure

```
glas-mcp/
├── main.py                    # Root entry point — starts frontend + backend
├── Dockerfile                 # Multi-stage: Node build → Python serve
├── render.yaml                # Render deployment config
├── .gitignore
│
├── frontend/                  # React / Vite app (multi-page)
│   ├── package.json
│   ├── vite.config.js         # Builds to glas_mcp/static/
│   ├── index.html
│   └── src/
│       ├── App.jsx            # Router (BrowserRouter)
│       ├── index.css          # Design tokens + global styles
│       ├── components/
│       │   ├── Navbar.jsx
│       │   └── Footer.jsx
│       └── pages/
│           ├── Home.jsx       # Landing page
│           ├── Tools.jsx      # Tool catalog (live from API)
│           ├── Playground.jsx # Advanced chat (4 providers)
│           ├── Docs.jsx       # Full documentation
│           └── ApiRef.jsx     # API reference
│
└── glas_mcp/                  # Python package
    ├── main.py                # FastAPI app + MCP SSE + static serving
    ├── requirements.txt
    ├── engine/
    │   ├── tools_loader.py    # Auto-discovers tools/ subdirectories
    │   └── providers_loader.py# Auto-discovers providers/ subdirectories
    ├── factory/
    │   └── tool_factory.py    # Dynamically imports tool classes
    ├── API/
    │   └── service/
    │       └── serve.py       # REST API router
    ├── tools/                 # 8 built-in tools
    │   ├── web_search/
    │   │   ├── main.py
    │   │   └── tool.yaml
    │   ├── web_fetch/
    │   ├── math_eval/
    │   ├── plot_chart/
    │   ├── create_docx/
    │   ├── create_xlsx/
    │   ├── create_pptx/
    │   └── create_pdf/
    ├── providers/             # AI provider configs (auto-discovered)
    │   ├── Anthropic/
    │   │   └── provider.yaml
    │   ├── Google/
    │   │   └── provider.yaml
    │   ├── Groq/
    │   │   └── provider.yaml
    │   └── OpenRouter/
    │       └── provider.yaml
    ├── skills/                # Agent guidance markdowns
    └── static/                # Built React output (served by FastAPI)
```

---

## Tools

All tools are callable via `POST /api/v1/tools/{name}` with `{ "arguments": { ... } }`.

| Tool | Category | Description |
|---|---|---|
| `web_search` | Search | DuckDuckGo search, up to 250 results |
| `web_fetch` | Fetch | Scrape and parse any URL |
| `math_eval` | Math | Evaluate mathematical expressions safely |
| `plot_chart` | Charts | Generate charts as base64 PNG |
| `create_docx` | Documents | Generate Word documents |
| `create_xlsx` | Documents | Generate Excel spreadsheets |
| `create_pptx` | Documents | Generate PowerPoint presentations |
| `create_pdf` | Documents | Generate PDF files |

### Response schema (GURS)

Every tool returns the **Glas Unified Response Schema**:

```json
{
  "ok": true,
  "tool": "web_search",
  "result": { "results": [...] },
  "error": null,
  "meta": {
    "execution_time_ms": 312,
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid",
    "version": "1.0.0"
  }
}
```

### JavaScript example

```js
const BASE = "https://glas-mcp.onrender.com/api/v1";

async function callTool(name, args) {
  const res = await fetch(`${BASE}/tools/${name}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ arguments: args }),
  });
  const { ok, result, error } = await res.json();
  if (!ok) throw new Error(error.message);
  return result;
}

// Web search
const results = await callTool("web_search", { query: "AI news", num_results: 10 });

// Chart → base64 PNG
const chart = await callTool("plot_chart", {
  chart_type: "bar",
  data: { categories: ["Q1", "Q2", "Q3"], values: [[100, 145, 130]], labels: ["Revenue"] },
  title: "Quarterly Revenue",
  colors: ["#5B6EF5"],
});
document.querySelector("img").src = `data:image/png;base64,${chart.image_base64}`;
```

---

## Providers

Providers are auto-discovered from `glas_mcp/providers/`. Each folder contains a `provider.yaml`.

| Provider | Format | Tool Use | Key Prefix |
|---|---|---|---|
| **Anthropic** | `anthropic` | ✅ Full | `sk-ant-` |
| **Google Gemini** | `gemini` | ❌ | `AIza` |
| **Groq** | `openai` | ❌ | `gsk_` |
| **OpenRouter** | `openai` | ❌ | `sk-or-` |

> **Note:** Tool calling in the playground is only supported with Anthropic (Claude) because it's the only provider with native structured tool use in this implementation.

### Provider YAML schema

```yaml
name: anthropic              # Unique identifier (used in API URLs)
display_name: Anthropic      # UI label
logo: "◆"                   # Single character icon
color: "#CC785C"             # Brand colour (hex)
api_key_placeholder: "sk-ant-api03-…"
api_base_url: https://api.anthropic.com/v1/messages
auth_type: header            # header | bearer | query_param
auth_header: x-api-key
extra_headers:
  anthropic-version: "2023-06-01"
supports_tool_use: true
request_format: anthropic    # anthropic | openai | gemini
response_format: anthropic
models:
  - id: claude-sonnet-4-6
    label: Claude Sonnet 4.6
    context_window: 200000
    default: true
default_model: claude-sonnet-4-6
```

### Providers API

```bash
# List all providers
GET /api/v1/providers

# Get one provider
GET /api/v1/providers/anthropic
```

---

## API Reference

### Base URL

```
https://glas-mcp.onrender.com
```

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Server health + loaded tool/provider counts |
| `GET` | `/api/v1/tools` | List all tools with schemas |
| `GET` | `/api/v1/tools/{name}` | Get a single tool schema |
| `POST` | `/api/v1/tools/{name}` | Execute a tool |
| `GET` | `/api/v1/providers` | List all AI provider configs |
| `GET` | `/api/v1/providers/{name}` | Get one provider config |
| `GET` | `/api/v1/skills` | List skills |
| `GET` | `/api/v1/skills/{name}` | Get skill markdown |
| `POST` | `/api/v1/skills` | Create skill |
| `GET` | `/sse` | MCP SSE transport |
| `POST` | `/messages` | MCP messages |
| `GET` | `/api/docs` | Swagger UI |

Full interactive docs at [/api/docs](https://glas-mcp.onrender.com/api/docs).

---

## MCP Integration

### Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "glas": {
      "url": "https://glas-mcp.onrender.com/sse"
    }
  }
}
```

### Any MCP client

```
SSE endpoint:  GET  https://glas-mcp.onrender.com/sse
Messages:      POST https://glas-mcp.onrender.com/messages
```

Connected MCP clients auto-discover all 8 tools via `list_tools`.

---

## Adding Tools

Create a subdirectory in `glas_mcp/tools/` with two files:

### `tool.yaml`

```yaml
name: my_tool
description: What this tool does.
input_schema:
  type: object
  properties:
    query:
      type: string
      description: The input text.
    limit:
      type: integer
      description: Max results.
      default: 10
  required:
    - query
```

### `main.py`

```python
from glas_mcp.tools.base import BaseTool

class MyTool(BaseTool):
    async def execute(self, arguments: dict) -> dict:
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        # Your logic here
        return {"results": [], "query": query}
```

Restart the server — `ToolsLoader` picks it up automatically.

---

## Adding Providers

```bash
mkdir glas_mcp/providers/MyProvider
# Create provider.yaml with the schema shown above
# Restart — auto-loaded and served at /api/v1/providers/myprovider
```

The frontend loads providers from `/api/v1/providers` on startup — no rebuild needed.

---

## Frontend Development

```bash
cd frontend
npm install

# Dev server with HMR (proxies API to localhost:8000)
npm run dev

# Production build → glas_mcp/static/
npm run build
```

Or start everything with one command:

```bash
DEV=true python main.py
# Starts uvicorn (port 8000) + Vite (port 5173) together
```

### Pages

| Route | File | Description |
|---|---|---|
| `/` | `Home.jsx` | Landing page with stats, tools preview, quick start |
| `/tools` | `Tools.jsx` | Full tool catalog with live schemas from API |
| `/playground` | `Playground.jsx` | Advanced chat: 4 providers, tool toggles, session info |
| `/docs` | `Docs.jsx` | Full documentation with TOC sidebar |
| `/api` | `ApiRef.jsx` | Interactive API reference with curl examples |

---

## Deployment

### Render (one-click)

The `render.yaml` is pre-configured. Connect the GitHub repo in [Render](https://render.com) and deploy. Every push to `main` triggers a rebuild.

The Docker build:
1. **Stage 1 (Node 20):** installs frontend deps, runs `npm run build`, outputs to `glas_mcp/static/`
2. **Stage 2 (Python 3.11):** installs Python deps, copies backend + built frontend, starts `python main.py`

### Manual Docker

```bash
# Build
docker build -t glas-mcp .

# Run
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  glas-mcp

# Docker Compose
docker-compose up
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Bind address |
| `DEV` | `false` | Enable dev mode (starts Vite alongside uvicorn) |
| `VITE_PORT` | `5173` | Vite dev server port |
| `ANTHROPIC_API_KEY` | — | Optional server-side Anthropic key |
| `GOOGLE_API_KEY` | — | Optional server-side Google key |
| `GROQ_API_KEY` | — | Optional server-side Groq key |
| `OPENROUTER_API_KEY` | — | Optional server-side OpenRouter key |

> The playground uses keys entered by the user in the browser — they are stored in `localStorage` and never sent to our servers.

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-tool`
3. Add your tool or provider following the patterns above
4. Open a PR — describe what the tool does and any new deps

---

<div align="center">
Built by <a href="https://github.com/anguzudouglas">anguzudouglas</a> · MIT License · Hosted on <a href="https://render.com">Render</a>
</div>
