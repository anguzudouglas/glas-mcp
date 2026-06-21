# Glas MCP Architecture

A modular MCP (Model Context Protocol) server that exposes AI agent tools over HTTP using Server-Sent Events (SSE). Tools are self-contained modules — adding a new capability requires only a new directory with two files.

## Project Structure

```
glas_mcp/
├── main.py                    ← Entry point: FastAPI app + MCP SSE server
├── requirements.txt           ← Python dependencies
├── .env.example               ← Environment variable template
├── test_glas_mcp.py           ← Tool discovery + invocation integration test
├── tools/
│   ├── base.py                ← Abstract BaseTool class (tool contract)
│   └── web_search/
│       ├── main.py            ← WebSearchTool implementation
│       ├── tool.yaml          ← Tool contract: name, description, inputSchema
│       └── helpers/
│           └── search_utils.py
├── factory/
│   └── tool_factory.py        ← Dynamic tool instantiation via importlib
├── engine/
│   └── tools_loader.py        ← Tool discovery: scans tools/, returns Dict[name, BaseTool]
├── helpers/
│   └── logging_config.py      ← Root logger setup (INFO, stdout)
├── oauth_handlers/
│   └── google_oauth.py        ← Google OAuth2 flow (tokens, refresh)
├── API/
│   └── workspace_api.py       ← Google Workspace API client (Drive, Docs, Sheets, Slides)
└── docs/
    └── usage.md               ← Setup and tool invocation examples
```

## Component Descriptions

### `main.py`

Entry point for the Glas MCP server. Initialises the FastAPI app, creates an MCP `Server` instance, and mounts SSE transport at two endpoints:

- `GET /sse` — client opens a persistent SSE stream; the MCP server runs over this connection
- `POST /messages` — client sends JSON-RPC messages back to the server

On startup it calls `ToolsLoader.load_all()` to discover all tools, then registers `list_tools` and `call_tool` handlers with the MCP server. `call_tool` dispatches to `tool.execute(arguments)` and wraps the return value in a `TextContent` block.

### `tools/base.py`

Defines the abstract `BaseTool` class that every tool must subclass.

- `__init__(tool_dir)` — loads `tool.yaml` from the tool's own directory
- `name`, `description`, `input_schema` — properties read directly from YAML; no duplication in Python
- `execute(arguments)` — abstract async method each tool must implement

`tool.yaml` is the single source of truth for the tool's identity and JSON Schema input contract. Changing metadata only requires editing YAML — no Python changes needed.

### `tools/<tool_name>/tool.yaml`

Declares the tool contract consumed by both `BaseTool` (for metadata properties) and the MCP server (as the `inputSchema` passed to the client). Format:

```yaml
name: web_search
description: Searches the web for information using DuckDuckGo. Supports up to 250 results.
input_schema:
  type: object
  properties:
    query:
      type: string
      description: The search query.
    num_results:
      type: integer
      description: Number of results to return (max 250).
      default: 10
      maximum: 250
  required:
    - query
```

### `factory/tool_factory.py`

`ToolFactory.create_tool(tool_dir)` dynamically loads a tool using `importlib`:

1. Looks for `main.py` in `tool_dir`; returns `None` if missing (tool is silently skipped)
2. Uses `importlib.util.spec_from_file_location` to load the module
3. Introspects the module via `dir()` to find a class that is a `BaseTool` subclass
4. Instantiates and returns it with `tool_dir` as the argument

This means the factory never needs to know tool names in advance — all discovery is structural.

### `engine/tools_loader.py`

`ToolsLoader(tools_root)` orchestrates tool discovery:

1. `os.scandir(tools_root)` — iterates subdirectories (skips `__`-prefixed dirs like `__pycache__`)
2. Calls `ToolFactory.create_tool(entry.path)` for each directory
3. Indexes each successfully created tool by `tool.name`
4. Returns `Dict[str, BaseTool]` — the live registry used by `main.py`

### `helpers/logging_config.py`

`setup_logging()` configures the Python root logger: `INFO` level, timestamped format, stdout handler. Call once at startup before any other imports.

### `oauth_handlers/google_oauth.py`

Manages the full Google OAuth2 authorization code flow: builds the consent URL, exchanges the code for tokens, stores and refreshes access tokens. Used by `workspace_api.py` to authenticate API calls.

### `API/workspace_api.py`

Provides a Python client layer over the Google Workspace REST APIs (Drive, Docs, Sheets, Slides). Handles request construction, pagination, and error mapping so tool implementations stay clean.

## Data Flow

```
AI Agent (MCP client)
    │
    │  GET /sse  (open SSE stream)
    ▼
FastAPI + SseServerTransport
    │
    │  MCP initialize / list_tools / call_tool
    ▼
mcp.Server
    │
    │  list_tools()  →  returns Tool[] from loaded_tools registry
    │  call_tool()   →  loaded_tools[name].execute(arguments)
    ▼
BaseTool subclass (e.g. WebSearchTool)
    │
    │  returns result dict / string
    ▼
TextContent  →  SSE stream  →  AI Agent
```

## Adding a New Tool

1. Create `tools/<your_tool>/`
2. Add `tool.yaml` — fill in `name`, `description`, `input_schema`
3. Add `main.py` — subclass `BaseTool`, implement `async def execute(self, arguments)`
4. Restart the server — `ToolsLoader` discovers and registers it automatically

No changes to `main.py`, `tool_factory.py`, or `tools_loader.py` are needed.

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Purpose |
|---|---|
| `GOOGLE_CLIENT_ID` | Google OAuth2 app client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 app client secret |
| `GOOGLE_REDIRECT_URI` | OAuth2 callback URL (default: `http://localhost:8000/oauth2callback`) |
| `WEB_SEARCH_API_KEY` | Optional — reserved for future paid search API integration |
| `PORT` | Server port (default: `8000`) |

## Dependencies

| Package | Purpose |
|---|---|
| `mcp[server]` | MCP SDK — Server, SSE transport, Tool/TextContent types |
| `fastapi` + `uvicorn` | HTTP server hosting the SSE endpoints |
| `duckduckgo_search` | Web search (no API key required) |
| `google-api-python-client` | Google Workspace REST APIs |
| `google-auth-oauthlib` | Google OAuth2 flow |
| `weasyprint` | HTML → PDF generation |
| `python-docx` | DOCX generation |
| `openpyxl` | XLSX generation |
| `python-pptx` | PPTX generation |
| `beautifulsoup4` + `httpx` | Web scraping / HTML parsing |
| `PyYAML` | `tool.yaml` parsing |
| `python-dotenv` | `.env` file loading |
