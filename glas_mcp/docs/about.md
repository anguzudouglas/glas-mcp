# About Glas MCP

## Project

**Glas MCP** is an open-source, modular Model Context Protocol (MCP) server that gives AI agents production-ready tools for web interaction, mathematics, data visualization, and document generation — all served over HTTP via Server-Sent Events (SSE) and a clean REST API.

Any MCP-compatible AI client (Claude Desktop, custom agents, LangChain, AutoGen, etc.) can connect to `/sse` and immediately call any registered tool. No configuration required beyond pointing to the server URL.

## Owner

| | |
|---|---|
| **Author** | Anguzudouglas |
| **GitHub** | [github.com/anguzudouglas/glas_mcp](https://github.com/anguzudouglas/glas_mcp) |
| **Production** | [glas-mcp.onrender.com](https://glas-mcp.onrender.com) |
| **License** | MIT |

## What "Glas" Means

*Glas* (from Proto-Celtic *glastos*, meaning clear, bright, or transparent) — because the server exposes capabilities transparently: every tool is self-describing, every skill is readable, every response follows a single predictable schema.

## Tool Inventory

| Tool | Category | Description |
|------|----------|-------------|
| `web_search` | Web | DuckDuckGo search, up to 250 results |
| `web_fetch` | Web | Fetch any URL → clean Markdown. 10 JS bypass strategies + 4 cache fallbacks |
| `math_calculate` | Computation | Run Python math code (numpy, scipy, sympy) in a safe sandbox |
| `plot_chart` | Visualization | Generate charts (12 types) → base64 PNG/SVG via matplotlib |
| `document_create_pdf` | Documents | HTML → PDF via WeasyPrint (full CSS3 print support) |
| `document_create_docx` | Documents | HTML → Word .docx via python-docx |
| `document_create_xlsx` | Documents | Structured data → Excel .xlsx via openpyxl |
| `document_create_pptx` | Documents | Slide definitions → PowerPoint .pptx via python-pptx |

## Architecture

```
Client (Claude / custom agent)
        │
        │  SSE (MCP protocol)          REST (any HTTP client)
        ▼                               ▼
  GET /sse                     GET /api/v1/tools
  POST /messages               POST /api/v1/tools/{name}
        │                      GET /api/v1/skills
        └────────────┬──────────────────┘
                     ▼
             FastAPI Application
             glas_mcp/main.py
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    ToolsLoader            SkillsLoader
    (auto-discovers         (auto-discovers
     tools/ dirs)            skills/ dirs)
          │                     │
     ┌────┴────┐          ┌─────┴─────┐
     │ Tool    │          │ Skill     │
     │ Factory │          │ .md files │
     └────┬────┘          └───────────┘
          ▼
   BaseTool subclasses
   (execute() → result)
```

## Design Philosophy

1. **Zero-config tool discovery.** Drop a directory with `main.py` + `tool.yaml` into `tools/` — it's registered automatically on next startup.
2. **Single source of truth.** `tool.yaml` defines the name, description, and JSON Schema used by MCP, REST, and the frontend playground.
3. **Unified response schema.** Every REST API call returns `{ ok, tool, result, error, meta }` — predictable for any client.
4. **Skills as first-class citizens.** Skills are markdown guidance files that agents load to produce higher-quality tool outputs. Add a skill directory; it's immediately available via API and the playground.
5. **No lock-in.** MCP over SSE, REST over HTTP, or direct Python import — all three work.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| HTTP server | FastAPI + Uvicorn |
| MCP transport | `mcp[server]` SSE |
| Web tools | httpx, requests, cloudscraper, ddgs, html2text, BeautifulSoup4 |
| Math | numpy, scipy, sympy, mpmath |
| Charts | matplotlib, Pillow |
| Documents | WeasyPrint, python-docx, openpyxl, python-pptx |
| Config | PyYAML, python-dotenv |
| Container | Docker + docker-compose |
| Deployment | Render.com |

## Contributing

1. Fork [github.com/anguzudouglas/glas_mcp](https://github.com/anguzudouglas/glas_mcp)
2. Create a branch: `git checkout -b feat/my-tool`
3. Add your tool directory under `glas_mcp/tools/`
4. Add a skill under `glas_mcp/skills/`
5. Run tests: `python test_<your_tool>.py`
6. Submit a pull request

See `docs/tool_creation_guide.md` for the full step-by-step guide.

## Roadmap

- [ ] Google Workspace integration (Drive, Docs, Sheets, Slides)
- [ ] Authentication middleware (API key, OAuth)
- [ ] Tool call streaming (partial results via SSE)
- [ ] Web UI skill editor (create / edit skills without touching files)
- [ ] Tool versioning and rollback
- [ ] Prometheus metrics endpoint
- [ ] Rate limiting per tool per client
