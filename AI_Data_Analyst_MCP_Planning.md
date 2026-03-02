# AI Data Analyst MCP Client — Implementation Planning

> **Stack:** FastAPI · React · OpenAI GPT-4o · MCP (In-Process) · Matplotlib/Seaborn · Docker Sandbox · UV

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Project Structure](#3-project-structure)
4. [Tech Stack & Justifications](#4-tech-stack--justifications)
5. [Backend Implementation Details](#5-backend-implementation-details)
   - 5.1 [FastAPI Application](#51-fastapi-application)
   - 5.2 [MCP Tool Registry](#52-mcp-tool-registry)
   - 5.3 [MCP Tools — Detailed Specs](#53-mcp-tools--detailed-specs)
   - 5.4 [OpenAI Tool-Calling Loop](#54-openai-tool-calling-loop)
   - 5.5 [Docker Sandbox](#55-docker-sandbox)
   - 5.6 [Configuration & Environment](#56-configuration--environment)
6. [Frontend Implementation Details](#6-frontend-implementation-details)
   - 6.1 [Component Tree](#61-component-tree)
   - 6.2 [API Contract](#62-api-contract)
   - 6.3 [State Management](#63-state-management)
7. [Data Flow — Step by Step](#7-data-flow--step-by-step)
8. [API Endpoints](#8-api-endpoints)
9. [Pydantic Schemas](#9-pydantic-schemas)
10. [Error Handling Strategy](#10-error-handling-strategy)
11. [Security Considerations](#11-security-considerations)
12. [File & Storage Management](#12-file--storage-management)
13. [Dependencies](#13-dependencies)
14. [Environment Variables](#14-environment-variables)
15. [Setup & Run Instructions](#15-setup--run-instructions)
16. [Folder-by-Folder Responsibilities](#16-folder-by-folder-responsibilities)
17. [Resume-Worthy Talking Points](#17-resume-worthy-talking-points)

---

## 1. Project Overview

An **AI-powered data analysis assistant** that allows users to upload a CSV file and ask natural language questions about their data. The backend uses **OpenAI's function/tool-calling API** to orchestrate a set of **MCP (Model Context Protocol) tools** that perform real data operations — querying, charting, summarizing — and returns structured results to a clean React UI.

### Core Capabilities

| Capability | Description |
|---|---|
| CSV Upload & Parsing | Upload any CSV; auto-detect schema, dtypes, nulls, shape |
| Natural Language Querying | Ask questions like "What is the average revenue by region?" |
| Chart Generation | Auto-generate bar, line, scatter, histogram, heatmap charts as PNG |
| AI Summary | GPT-4o writes a narrative business summary of findings |
| Business Insights | AI surfaces 3–5 actionable insights from the data |
| Python Sandbox | Execute arbitrary pandas/matplotlib code in isolated Docker container |

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (React)                          │
│   UploadPanel → ChatPanel → ChartViewer → SummaryCard           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP (REST)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              OpenAI Service (Tool-Calling Loop)         │   │
│   │                                                         │   │
│   │  User Message → GPT-4o → tool_calls[] → execute tools  │   │
│   │       ↑                                        │        │   │
│   │       └──────────── tool results ─────────────┘        │   │
│   └──────────────────────────┬──────────────────────────────┘   │
│                              │                                  │
│   ┌──────────────────────────▼──────────────────────────────┐   │
│   │                   MCP Tool Registry                     │   │
│   │                                                         │   │
│   │  load_csv | run_pandas_query | generate_chart           │   │
│   │  summarize_findings | python_sandbox                    │   │
│   └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                    python_sandbox calls                         │
│                              ▼                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │        Docker Container (python:3.12-slim)               │  │
│   │        No network | No volume mount | 30s timeout        │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │ reads/writes                     │ writes charts
         ▼                                  ▼
    /uploads/                          /outputs/charts/
```

---

## 3. Project Structure

```
ai-data-analyst/
│
├── backend/
│   ├── main.py                        # FastAPI app factory, CORS, routers
│   ├── config.py                      # pydantic-settings: env vars, paths
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analysis.py                # POST /api/analyze
│   │   └── files.py                   # POST /api/upload, GET /api/charts/{id}
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── registry.py                # Tool registry: name → function + schema
│   │   ├── executor.py                # Dispatches tool calls from OpenAI response
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── load_csv.py            # Tool: load_csv
│   │       ├── run_pandas_query.py    # Tool: run_pandas_query
│   │       ├── generate_chart.py      # Tool: generate_chart
│   │       ├── summarize_findings.py  # Tool: summarize_findings
│   │       └── python_sandbox.py      # Tool: python_sandbox (Docker)
│   ├── services/
│   │   └── openai_service.py          # Full tool-calling agentic loop
│   ├── models/
│   │   └── schemas.py                 # All Pydantic request/response models
│   └── utils/
│       ├── file_handler.py            # Temp file save, cleanup, path resolution
│       └── logger.py                  # Structured logging setup
│
├── frontend/
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js              # Axios instance + API calls
│   │   ├── components/
│   │   │   ├── UploadPanel.jsx        # Drag-and-drop CSV upload
│   │   │   ├── ChatPanel.jsx          # Conversation interface
│   │   │   ├── ChartViewer.jsx        # Renders returned PNG charts
│   │   │   ├── SummaryCard.jsx        # Markdown summary + insights list
│   │   │   └── LoadingSpinner.jsx     # Reusable loading state
│   │   ├── hooks/
│   │   │   └── useAnalysis.js         # Custom hook: upload + chat state
│   │   ├── App.jsx                    # Root layout
│   │   └── main.jsx                   # ReactDOM entry
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
│
├── sandbox/
│   └── Dockerfile                     # python:3.12-slim sandbox image
│
├── uploads/                           # Temp CSV storage (gitignored)
├── outputs/
│   └── charts/                        # Generated PNGs (served statically)
│
├── pyproject.toml                     # UV project config
├── .env.example                       # Template env file
├── .gitignore
└── docker-compose.yml                 # Runs backend + builds sandbox image
```

---

## 4. Tech Stack & Justifications

| Component | Choice | Why |
|---|---|---|
| Python env | **UV** | Fast, modern, replaces pip+venv |
| Backend framework | **FastAPI** | Async, auto OpenAPI docs, Pydantic-native |
| LLM | **OpenAI GPT-4o** | Best-in-class tool-calling reliability |
| MCP pattern | **In-process registry** | Simple, inspectable, no IPC overhead for local dev |
| Charts | **Matplotlib + Seaborn** | Widely used, deterministic PNG output, easy PNG serving |
| Sandbox | **Docker `python:3.12-slim`** | True OS-level isolation, no deps on host Python |
| Frontend | **React + Vite** | Fast HMR, modern JSX, good ecosystem |
| Styling | **TailwindCSS** | Utility-first, no CSS files to manage |
| HTTP client | **Axios** | Interceptors, easy multipart form support |

---

## 5. Backend Implementation Details

### 5.1 FastAPI Application

**`backend/main.py`**

- Creates `FastAPI` app with metadata (title, version, docs_url)
- Registers CORS middleware allowing `http://localhost:5173` (Vite dev server)
- Mounts `/outputs/charts` as a **static file directory** so chart PNGs are served directly
- Includes routers: `analysis.router`, `files.router`
- On startup: creates `uploads/` and `outputs/charts/` directories if missing

```python
# Startup event pattern
@app.on_event("startup")
async def startup_event():
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
```

---

### 5.2 MCP Tool Registry

**`backend/mcp/registry.py`**

The registry is the heart of the MCP pattern. It stores:
1. **The Python function** to call when the tool is invoked
2. **The OpenAI-compatible JSON schema** sent to GPT-4o so it knows what tools are available

```python
# Registry structure (conceptual)
TOOLS: dict[str, ToolEntry] = {
    "load_csv": ToolEntry(fn=load_csv, schema={...}),
    "run_pandas_query": ToolEntry(fn=run_pandas_query, schema={...}),
    ...
}

def get_openai_tools() -> list[dict]:
    """Returns list of tool schemas in OpenAI format."""
    ...

def execute_tool(name: str, arguments: dict) -> str:
    """Calls the registered function and returns JSON string result."""
    ...
```

Each tool schema follows OpenAI's function-calling format:
```json
{
  "type": "function",
  "function": {
    "name": "load_csv",
    "description": "...",
    "parameters": {
      "type": "object",
      "properties": { ... },
      "required": [...]
    }
  }
}
```

---

### 5.3 MCP Tools — Detailed Specs

#### `load_csv`
- **Input:** `file_path: str`
- **Process:**
  - Read with `pandas.read_csv()`
  - Collect: shape, column names, dtypes, null counts per column, `head(5)` as dict
  - Detect potential date columns, categorical columns, numeric columns
- **Output JSON:**
  ```json
  {
    "shape": [1000, 8],
    "columns": ["date", "revenue", "region"],
    "dtypes": {"revenue": "float64", "region": "object"},
    "null_counts": {"revenue": 0, "region": 2},
    "preview": [...],
    "numeric_columns": ["revenue", "quantity"],
    "categorical_columns": ["region", "product"]
  }
  ```
- **Error handling:** FileNotFoundError, pandas parse errors → return `{"error": "..."}` string

---

#### `run_pandas_query`
- **Input:** `file_path: str`, `query_code: str` (pandas expression, e.g. `df.groupby('region')['revenue'].sum()`)
- **Process:**
  - Load CSV into `df`
  - Execute `query_code` in a controlled `exec()` with `{"df": df}` as local namespace
  - Capture result variable named `result`
  - Convert result to JSON-serializable format (`.to_dict()`, `.tolist()`, scalar)
  - Limit output rows to 100 to prevent token overflow
- **Safety:** Blocked keywords list: `import`, `open`, `os`, `sys`, `subprocess`, `eval`, `exec`, `__`
- **Output JSON:**
  ```json
  {
    "result": [...],
    "row_count": 12,
    "columns": ["region", "revenue"]
  }
  ```

---

#### `generate_chart`
- **Input:**
  - `file_path: str`
  - `chart_type: str` — one of: `bar`, `line`, `scatter`, `histogram`, `heatmap`, `box`
  - `x_col: str`
  - `y_col: str | None` (optional for histogram)
  - `title: str | None`
  - `hue_col: str | None` (optional grouping column)
- **Process:**
  - Load CSV
  - Use Seaborn/Matplotlib to generate the appropriate chart
  - Apply consistent style: `seaborn-v0_8-whitegrid` theme, figure size `(10, 6)`
  - Save as PNG to `outputs/charts/{uuid4()}.png`
  - `plt.close()` after saving (prevent memory leaks)
- **Output JSON:**
  ```json
  {
    "chart_path": "outputs/charts/abc123.png",
    "chart_url": "/charts/abc123.png",
    "chart_type": "bar",
    "title": "Revenue by Region"
  }
  ```

---

#### `summarize_findings`
- **Input:**
  - `data_context: str` — JSON string of all tool results so far
  - `user_question: str`
- **Process:**
  - Make a **secondary OpenAI call** (non-tool-calling, just text) with a structured prompt
  - Prompt instructs GPT-4o to write:
    - A 2–3 paragraph data narrative
    - 3–5 bullet-point business insights with actionable recommendations
  - Return as markdown string
- **Output JSON:**
  ```json
  {
    "summary": "## Data Summary\n\nThe dataset contains...",
    "insights": [
      "Revenue is highest in Q3, suggesting seasonal demand...",
      "Region X underperforms by 23% — investigate pricing..."
    ]
  }
  ```

---

#### `python_sandbox`
- **Input:** `code: str`
- **Process:** See [Section 5.5](#55-docker-sandbox)
- **Output JSON:**
  ```json
  {
    "stdout": "...",
    "stderr": "",
    "exit_code": 0,
    "success": true
  }
  ```

---

### 5.4 OpenAI Tool-Calling Loop

**`backend/services/openai_service.py`**

This implements the **agentic loop** — the core intelligence of the system.

```
1. Build messages list: [system_prompt, ...conversation_history, user_message]
2. Call OpenAI with tools=get_openai_tools(), tool_choice="auto"
3. If response has tool_calls:
   a. Append assistant message with tool_calls
   b. For each tool_call:
      - Parse function name + JSON arguments
      - Execute via registry.execute_tool()
      - Append tool result message
   c. Loop back to step 2 (multi-turn tool execution)
4. If response is a plain text message (no tool_calls): DONE
5. Return final text + list of all tool results (charts, data, etc.)
```

**System Prompt** instructs GPT-4o to:
- Always call `load_csv` first if it hasn't been called yet
- Use `run_pandas_query` for numerical questions before summarizing
- Generate a chart whenever visual representation would help
- Always end with `summarize_findings` after gathering enough data
- Return responses in a structured format the frontend can parse

**Loop safeguard:** Max 10 iterations to prevent infinite loops.

---

### 5.5 Docker Sandbox

**`sandbox/Dockerfile`**

```dockerfile
FROM python:3.12-slim
RUN pip install pandas numpy matplotlib seaborn --no-cache-dir
WORKDIR /sandbox
# No CMD — container is run with code piped via stdin
```

**`backend/mcp/tools/python_sandbox.py`**

Uses the `docker` Python SDK:

```python
import docker
import json

def python_sandbox(code: str) -> dict:
    client = docker.from_env()
    
    # Wrap user code to capture result
    wrapped_code = f"""
import sys, json, io
import pandas as pd
import numpy as np

# User code
{code}
"""
    container = client.containers.run(
        image="data-analyst-sandbox:latest",
        command=["python", "-c", wrapped_code],
        network_disabled=True,          # No internet
        mem_limit="256m",               # Memory cap
        cpu_quota=50000,                # 50% of 1 CPU
        remove=True,                    # Auto-cleanup
        stdout=True,
        stderr=True,
        timeout=30,                     # 30s hard limit
    )
    ...
```

**Security constraints applied:**
- `network_disabled=True` — no network access
- `mem_limit="256m"` — memory cap
- `read_only=True` filesystem (no writes to host)
- `user="nobody"` — non-root execution
- `cpu_quota` — CPU throttle

---

### 5.6 Configuration & Environment

**`backend/config.py`** uses `pydantic-settings`:

```python
class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    UPLOAD_DIR: Path = Path("uploads")
    CHARTS_DIR: Path = Path("outputs/charts")
    MAX_FILE_SIZE_MB: int = 50
    SANDBOX_TIMEOUT_SECONDS: int = 30
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")
```

---

## 6. Frontend Implementation Details

### 6.1 Component Tree

```
App
├── Header (title, status badge)
├── UploadPanel
│   ├── Dropzone (react-dropzone)
│   ├── FileInfo (name, size, rows preview)
│   └── DataPreviewTable (first 5 rows)
├── ChatPanel
│   ├── MessageList
│   │   ├── UserMessage
│   │   └── AssistantMessage
│   │       ├── TextContent (markdown rendered)
│   │       ├── ChartViewer (if chart returned)
│   │       └── SummaryCard (if summary returned)
└── InputBar
    └── QuestionInput + SendButton
```

---

### 6.2 API Contract

**Upload:**
```
POST /api/upload
Content-Type: multipart/form-data
Body: file=<CSV>
Response: { "file_id": "uuid", "filename": "data.csv", "rows": 1000, "columns": 8 }
```

**Analyze:**
```
POST /api/analyze
Content-Type: application/json
Body: {
  "file_id": "uuid",
  "question": "What is the average revenue by region?",
  "conversation_history": [...]
}
Response: {
  "answer": "The average revenue by region is...",
  "charts": ["/charts/abc.png"],
  "summary": "## Summary\n...",
  "insights": ["Insight 1", "Insight 2"],
  "tool_calls_made": ["load_csv", "run_pandas_query", "generate_chart", "summarize_findings"]
}
```

---

### 6.3 State Management

Uses **React `useState` + custom hook `useAnalysis`** (no Redux needed for this scope):

```javascript
// hooks/useAnalysis.js
{
  fileId: null,
  filename: null,
  dataPreview: null,        // { rows, columns, head }
  messages: [],             // conversation history
  isLoading: false,
  charts: [],               // list of chart URLs from responses
  error: null
}
```

---

## 7. Data Flow — Step by Step

```
1. User drags CSV → UploadPanel
2. POST /api/upload → backend saves to uploads/{uuid}.csv
3. Backend reads pandas preview → returns schema + head(5) to frontend
4. Frontend shows DataPreviewTable + enables chat input

5. User types question → ChatPanel
6. POST /api/analyze { file_id, question, history }
7. FastAPI router → OpenAI service
8. OpenAI service: builds messages + sends to GPT-4o with all tool schemas
9. GPT-4o responds with tool_calls: ["load_csv"]
10. Executor calls load_csv(file_path) → returns schema JSON
11. Tool result appended → loop continues
12. GPT-4o calls run_pandas_query + generate_chart
13. Chart PNG saved to outputs/charts/
14. GPT-4o calls summarize_findings with all gathered context
15. GPT-4o produces final text response
16. FastAPI returns: answer + chart URLs + summary + insights
17. React renders: assistant message + <img> charts + SummaryCard
```

---

## 8. API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload CSV file |
| `POST` | `/api/analyze` | Run AI analysis on uploaded file |
| `GET` | `/api/files/{file_id}` | Get file metadata |
| `DELETE` | `/api/files/{file_id}` | Delete uploaded file + charts |
| `GET` | `/charts/{filename}` | Serve chart PNG (static) |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | FastAPI auto-generated Swagger UI |

---

## 9. Pydantic Schemas

```python
# models/schemas.py

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    preview: list[dict]

class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class AnalyzeRequest(BaseModel):
    file_id: str
    question: str
    conversation_history: list[ConversationMessage] = []

class AnalyzeResponse(BaseModel):
    answer: str
    charts: list[str] = []          # List of chart URLs
    summary: str | None = None      # Markdown string
    insights: list[str] = []        # Bullet point insights
    tool_calls_made: list[str] = [] # Audit trail
    tokens_used: int | None = None

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
```

---

## 10. Error Handling Strategy

| Scenario | Handling |
|---|---|
| CSV parse error | Return 400 with descriptive message |
| File not found (stale file_id) | Return 404 |
| OpenAI API error | Return 502 with "LLM service unavailable" |
| Tool execution error | Tool returns `{"error": "..."}` → GPT-4o handles gracefully |
| Sandbox timeout (>30s) | Kill container, return error in tool result |
| Pandas query unsafe | Keyword blocklist check → return error before exec |
| File too large (>50MB) | Return 413 with size limit message |

All errors follow the `ErrorResponse` schema for consistent frontend handling.

---

## 11. Security Considerations

| Risk | Mitigation |
|---|---|
| Arbitrary code in `run_pandas_query` | Keyword blocklist + only `df` in namespace |
| Arbitrary code in `python_sandbox` | Full Docker isolation, no network, no mounts |
| Path traversal in file_path | Validate all paths are within `uploads/` directory |
| Large file DoS | 50MB limit enforced at upload |
| API key exposure | Never returned to frontend; backend only |
| Sandbox escape | `network_disabled`, `read_only`, `user=nobody`, `mem_limit` |
| Stored file cleanup | DELETE endpoint + optional TTL-based cleanup task |

---

## 12. File & Storage Management

- Uploaded CSVs stored at `uploads/{uuid4()}.csv`
- Generated charts stored at `outputs/charts/{uuid4()}.png`
- Files are NOT automatically deleted (manual delete or TTL job optional)
- File ID = UUID, never exposes original filename in storage path
- Charts are served via FastAPI `StaticFiles` mount at `/charts/`

---

## 13. Dependencies

### Backend (`pyproject.toml`)
```toml
[project]
name = "ai-data-analyst"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "openai>=1.30.0",
    "pandas>=2.2.0",
    "matplotlib>=3.9.0",
    "seaborn>=0.13.0",
    "docker>=7.0.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "python-multipart>=0.0.9",
    "aiofiles>=23.2.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
    "ruff>=0.4.0",
]
```

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "axios": "^1.7.0",
    "react-dropzone": "^14.2.0",
    "react-markdown": "^9.0.0"
  },
  "devDependencies": {
    "vite": "^5.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

---

## 14. Environment Variables

**`.env.example`**
```env
# Required
OPENAI_API_KEY=sk-...

# Optional (defaults shown)
OPENAI_MODEL=gpt-4o
UPLOAD_DIR=uploads
CHARTS_DIR=outputs/charts
MAX_FILE_SIZE_MB=50
SANDBOX_TIMEOUT_SECONDS=30
LOG_LEVEL=INFO
```

---

## 15. Setup & Run Instructions

### Prerequisites
- Python 3.12+
- UV installed (`pip install uv`)
- Node.js 20+
- Docker Desktop running

### Backend
```bash
cd ai-data-analyst
uv sync
cp .env.example .env
# Edit .env → add OPENAI_API_KEY

# Build sandbox Docker image
docker build -t data-analyst-sandbox:latest ./sandbox

# Run backend
uv run uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

### Full stack (docker-compose — optional)
```bash
docker-compose up --build
```

---

## 16. Folder-by-Folder Responsibilities

| Folder/File | Owner Responsibility |
|---|---|
| `backend/main.py` | App factory, middleware, routing |
| `backend/config.py` | All configuration in one place |
| `backend/routers/` | HTTP layer only — no business logic |
| `backend/services/openai_service.py` | The agentic loop — LLM orchestration |
| `backend/mcp/registry.py` | Tool registration + OpenAI schema export |
| `backend/mcp/executor.py` | Tool dispatch + error wrapping |
| `backend/mcp/tools/` | Pure data operations — no HTTP, no LLM |
| `backend/models/schemas.py` | Single source of truth for data shapes |
| `backend/utils/` | Stateless helpers only |
| `frontend/src/api/` | All network calls, no UI logic |
| `frontend/src/hooks/` | Business logic for React state |
| `frontend/src/components/` | Pure UI — driven by props/hooks |
| `sandbox/Dockerfile` | Locked-down Python execution environment |

---

## 17. Resume-Worthy Talking Points

> **Designed and built a Generative AI-powered data analysis assistant** using OpenAI's GPT-4o tool-calling API to orchestrate a custom Model Context Protocol (MCP) tool registry. The system enables natural language querying of tabular data, automated chart generation via Matplotlib/Seaborn, and AI-generated business insight summaries. Implemented a security-hardened Python code execution sandbox using Docker containers with network isolation, memory limits, and read-only filesystems. Built with FastAPI (async), React + Vite, and UV package management, following clean architecture principles with clear separation between HTTP routing, LLM orchestration, and data tool layers.

**Key technical highlights to mention:**
- Implemented the OpenAI agentic tool-calling loop with multi-turn tool execution (not just single-shot)
- Designed an extensible MCP-style in-process tool registry decoupled from the LLM layer
- Docker-based sandboxed code execution with OS-level isolation
- Full async FastAPI backend with static file serving for generated charts
- Clean React component architecture with custom hooks for state management
