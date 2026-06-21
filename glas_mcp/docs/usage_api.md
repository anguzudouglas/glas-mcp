# Glas MCP — REST API Usage Guide

Base URL (production): `https://glas-mcp.onrender.com`  
Base URL (local): `http://localhost:8000`

All endpoints return the **Glas Unified Response Schema (GURS)**:

```json
{
  "ok":     true,
  "tool":   "tool_name",
  "result": { ... },
  "error":  null,
  "meta": {
    "execution_time_ms": 342,
    "timestamp": "2025-01-15T10:30:00Z",
    "request_id": "f3a8b2c1-...",
    "version": "1.0.0"
  }
}
```

---

## Endpoints

### `GET /api/v1/health`
Server health check.

```bash
curl https://glas-mcp.onrender.com/api/v1/health
```

```json
{
  "ok": true,
  "tool": null,
  "result": {
    "status": "ok",
    "tools_loaded": 8,
    "skills_loaded": 8
  }
}
```

---

### `GET /api/v1/tools`
List all registered tools.

```bash
curl https://glas-mcp.onrender.com/api/v1/tools
```

Returns an array of tool objects with `name`, `description`, and `input_schema`.

---

### `GET /api/v1/tools/{name}`
Get a single tool's full schema.

```bash
curl https://glas-mcp.onrender.com/api/v1/tools/web_search
```

---

### `POST /api/v1/tools/{name}`
**Execute a tool.**

```bash
curl -X POST https://glas-mcp.onrender.com/api/v1/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"query": "FastAPI SSE tutorial", "num_results": 5}}'
```

The `arguments` object maps directly to the tool's `input_schema` properties.

---

### `GET /api/v1/skills`
List all skills with their descriptions.

```bash
curl https://glas-mcp.onrender.com/api/v1/skills
```

---

### `GET /api/v1/skills/{name}`
Get a skill's full markdown content.

```bash
curl https://glas-mcp.onrender.com/api/v1/skills/web_search_skill
```

---

### `POST /api/v1/skills`
Create a new skill (writes to disk).

```bash
curl -X POST https://glas-mcp.onrender.com/api/v1/skills \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_custom_skill",
    "tool": "web_search",
    "description": "Custom search skill for legal research",
    "version": "1.0.0",
    "tags": ["search", "legal"],
    "content_md": "# My Custom Skill\n\nAlways add site:law.cornell.edu to legal queries."
  }'
```

---

### `PUT /api/v1/skills/{name}`
Update an existing skill's content.

```bash
curl -X PUT https://glas-mcp.onrender.com/api/v1/skills/my_custom_skill \
  -H "Content-Type: application/json" \
  -d '{"content_md": "# Updated Skill\n\nNew instructions here."}'
```

---

### `DELETE /api/v1/skills/{name}`
Remove a skill (deletes the directory from disk).

```bash
curl -X DELETE https://glas-mcp.onrender.com/api/v1/skills/my_custom_skill
```

---

### `GET /api/v1/agent-context`
Get a pre-formatted system-prompt block listing all tools and skills. Inject this into your agent's system prompt.

```bash
curl https://glas-mcp.onrender.com/api/v1/agent-context
```

---

## SDK Examples

### Python (httpx)

```python
import httpx, asyncio, base64

BASE = "https://glas-mcp.onrender.com/api/v1"

async def search(query: str):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/tools/web_search",
                         json={"arguments": {"query": query, "num_results": 10}})
        data = r.json()
        if data["ok"]:
            for result in data["result"]["results"]:
                print(result["title"], "—", result["href"])

async def fetch(url: str):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/tools/web_fetch",
                         json={"arguments": {"url": url, "mode": "auto"}})
        data = r.json()
        if data["ok"]:
            print(data["result"]["markdown"][:2000])

async def calculate(code: str):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/tools/math_calculate",
                         json={"arguments": {"code": code, "timeout": 15}})
        data = r.json()
        if data["ok"]:
            print("Output:", data["result"].get("output"))
            print("Result:", data["result"].get("result"))

async def chart(chart_type: str, chart_data: dict, **kwargs):
    args = {"chart_type": chart_type, "data": chart_data, **kwargs}
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/tools/plot_chart", json={"arguments": args})
        data = r.json()
        if data["ok"]:
            img_bytes = base64.b64decode(data["result"]["image_base64"])
            with open("chart.png", "wb") as f:
                f.write(img_bytes)
            print(f"Saved chart.png ({data['result']['image_size_bytes']} bytes)")

asyncio.run(search("MCP protocol tools"))
```

### JavaScript (fetch)

```javascript
const BASE = "https://glas-mcp.onrender.com/api/v1";

async function callTool(name, args) {
  const res = await fetch(`${BASE}/tools/${name}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ arguments: args }),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error.message);
  return data.result;
}

// Web search
const results = await callTool("web_search", { query: "OpenAI function calling", num_results: 5 });
console.log(results.results.map(r => r.title));

// Generate a chart
const chart = await callTool("plot_chart", {
  chart_type: "bar",
  data: { categories: ["Q1","Q2","Q3","Q4"], values: [[100,145,130,175]], labels: ["Revenue"] },
  title: "Quarterly Revenue",
  colors: ["#003f5c"],
  style: "ggplot",
});
document.querySelector("img").src = `data:image/png;base64,${chart.image_base64}`;
```

### cURL — Full Tool Examples

**Web search:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"query": "Python asyncio tutorial 2024", "num_results": 5}}'
```

**Fetch a web page:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/web_fetch \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"url": "https://example.com", "mode": "auto", "include_links": false}}'
```

**Run math:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/math_calculate \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"code": "import numpy as np; np.linalg.det([[4,2],[1,3]])", "timeout": 10}}'
```

**Generate a chart:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/plot_chart \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "chart_type": "line",
      "data": {"x":[1,2,3,4,5], "y":[[10,14,13,17,20]], "labels":["Revenue"]},
      "title": "Monthly Revenue",
      "colors": ["#003f5c"],
      "style": "ggplot"
    }
  }' | python3 -c "import sys,json,base64; d=json.load(sys.stdin); open('chart.png','wb').write(base64.b64decode(d['result']['image_base64']))"
```

**Create a PDF:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/document_create_pdf \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"html_content": "<h1>Hello Glas MCP</h1><p>My first PDF.</p>", "filename": "hello.pdf"}}'
```

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `TOOL_NOT_FOUND` | 404 | No tool with that name |
| `TOOL_EXECUTION_ERROR` | 200/500 | Tool ran but returned an error |
| `INVALID_ARGUMENTS` | 400 | Request body failed validation |
| `SKILL_NOT_FOUND` | 404 | No skill with that name |
| `SKILL_EXISTS` | 409 | Skill already exists (use PUT) |
| `SKILL_WRITE_ERROR` | 500 | File system write failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## MCP SSE (for AI clients)

Connect any MCP-compatible client to the SSE endpoint:

```
GET https://glas-mcp.onrender.com/sse
POST https://glas-mcp.onrender.com/messages
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "glas": {
      "url": "https://glas-mcp.onrender.com/sse"
    }
  }
}
```

The server announces all 8 tools via `tools/list` automatically.

---

## Connecting to an Agent (OpenAI-compatible)

```python
import httpx, json

BASE = "http://localhost:8000/api/v1"

# 1. Fetch tools in OpenAI function format
async def get_openai_tools():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/tools")
        tools = r.json()["result"]["tools"]
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            }
        }
        for t in tools
    ]

# 2. Execute a tool call from the LLM
async def execute_tool_call(name: str, args: dict) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{BASE}/tools/{name}", json={"arguments": args})
        return json.dumps(r.json()["result"], ensure_ascii=False)
```
