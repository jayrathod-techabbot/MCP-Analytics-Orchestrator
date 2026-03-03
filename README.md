# AI Data Analyst

An **AI-powered data analysis assistant** that allows users to upload CSV or Excel files and ask natural language questions about their data. The backend uses **OpenAI's function/tool-calling API** to orchestrate a set of **MCP (Model Context Protocol) tools** that perform real data operations — querying, charting, summarizing — and returns structured results to a clean React UI.

---

## Core Capabilities

| Capability | Description |
|---|---|
| CSV & Excel Upload | Upload CSV, XLSX, XLS files; auto-detect schema, dtypes, nulls, shape |
| Natural Language Querying | Ask questions like "What is the average revenue by region?" |
| Chart Generation | Auto-generate bar, line, scatter, histogram, heatmap, box charts as PNG |
| AI Summary | GPT-4o writes a narrative business summary of findings |
| Business Insights | AI surfaces 3–5 actionable insights from the data |
| Python Sandbox | Execute arbitrary pandas/matplotlib code in isolated Docker container |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (React)                          │
│   UploadPanel → ChatPanel → ChartViewer → SummaryCard           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP (REST)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │        LLM Service (Tool-Calling Loop)                    │  │
│   │  User Message → OpenAI/Groq → tool_calls[] → execute tools│  │
│   └──────────────────────────┬───────────────────────────────┘  │
│                              ▼                                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                  MCP Tool Registry                        │  │
│   │  load_csv | run_pandas_query | generate_chart             │  │
│   │  summarize_findings | python_sandbox                      │  │
│   └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                    python_sandbox calls                           │
│                              ▼                                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │        Docker Container (python:3.12-slim)                │  │
│   │        No network | No volume mount | 30s timeout         │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │ reads/writes                     │ writes charts
         ▼                                  ▼
    /uploads/                          /outputs/charts/
```

---

## Tech Stack

| Component | Choice |
|---|---|
| Python env | **UV** |
| Backend | **FastAPI** (async) |
| LLM | **OpenAI GPT-4o** or **Groq Llama 3** (tool-calling) |
| MCP pattern | **In-process registry** |
| Charts | **Matplotlib + Seaborn** |
| Sandbox | **Docker python:3.12-slim** |
| Frontend | **React 18 + Vite** |
| Styling | **TailwindCSS** |
| HTTP client | **Axios** |

---

## Project Structure

```
ai-data-analyst/
├── backend/
│   ├── main.py                        # FastAPI app, CORS, static files, lifespan
│   ├── config.py                      # pydantic-settings: env vars, paths
│   ├── routers/
│   │   ├── analysis.py                # POST /api/analyze
│   │   └── files.py                   # POST /api/upload, GET/DELETE /api/files/{id}
│   ├── mcp/
│   │   ├── registry.py                # Tool registry: name → function + schema
│   │   ├── executor.py                # Dispatches tool calls from OpenAI response
│   │   └── tools/
│   │       ├── load_csv.py            # Tool: load CSV/Excel, return schema info
│   │       ├── run_pandas_query.py    # Tool: execute pandas query with safety checks
│   │       ├── generate_chart.py      # Tool: generate charts via Seaborn/Matplotlib
│   │       ├── summarize_findings.py  # Tool: AI narrative summary + insights
│   │       └── python_sandbox.py      # Tool: Docker-isolated code execution
│   ├── services/
│   │   └── openai_service.py          # Multi-turn agentic tool-calling loop
│   ├── models/
│   │   └── schemas.py                 # All Pydantic request/response models
│   └── utils/
│       ├── file_handler.py            # File ID, path resolution, extension validation
│       └── logger.py                  # Structured logging
├── frontend/
│   ├── src/
│   │   ├── api/client.js              # Axios instance + API calls
│   │   ├── components/
│   │   │   ├── UploadPanel.jsx        # Drag-and-drop CSV/Excel upload + data preview
│   │   │   ├── ChatPanel.jsx          # Conversation interface with messages
│   │   │   ├── ChartViewer.jsx        # Chart thumbnails + click-to-expand modal
│   │   │   ├── SummaryCard.jsx        # Markdown summary + numbered insights
│   │   │   └── LoadingSpinner.jsx     # Animated loading indicator
│   │   ├── hooks/useAnalysis.js       # State management for upload + chat
│   │   ├── App.jsx                    # Root layout
│   │   └── main.jsx                   # ReactDOM entry
│   ├── index.html
│   ├── vite.config.js                 # Dev proxy to backend
│   ├── tailwind.config.js
│   └── package.json
├── sandbox/
│   └── Dockerfile                     # python:3.12-slim sandbox image
├── pyproject.toml                     # UV project config + dependencies
├── .env.example                       # Template env file
└── .gitignore
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload CSV/Excel file |
| `POST` | `/api/analyze` | Run AI analysis on uploaded file (supports `provider` parameter: "openai" or "groq") |
| `GET` | `/api/files/{file_id}` | Get file metadata |
| `DELETE` | `/api/files/{file_id}` | Delete uploaded file |
| `GET` | `/charts/{filename}` | Serve chart PNG (static) |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## MCP Tools

| Tool | Input | Output |
|---|---|---|
| `load_csv` | file_path | Schema: shape, columns, dtypes, nulls, preview, column classification |
| `run_pandas_query` | file_path, query_code | Query result (max 100 rows), row count, columns |
| `generate_chart` | file_path, chart_type, x_col, y_col?, title?, hue_col? | Chart URL, type, title |
| `summarize_findings` | data_context, user_question | Markdown summary + 3-5 insights |
| `python_sandbox` | code | stdout, stderr, exit_code, success |

---

## Setup & Run

### Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) installed
- Node.js 20+
- Docker Desktop (for sandbox — optional)

### 1. Backend

```bash
cd ai-data-analyst

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env → add your OPENAI_API_KEY (or GROQ_API_KEY for Groq)

# (Optional) Build sandbox Docker image
docker build -t data-analyst-sandbox:latest ./sandbox

# Run backend
uv run uvicorn backend.main:app --reload --port 8000
```

**Multi-Provider Setup:**
- **OpenAI**: Set `OPENAI_API_KEY` in `.env` (default provider)
- **Groq**: Set `GROQ_API_KEY` in `.env` and use `provider: "groq"` in API requests
- **LangSmith**: Set `LANGCHAIN_API_KEY` for optional tracing and monitoring

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

### 3. Use the app

1. Open http://localhost:5173
2. Drag-and-drop a CSV or Excel file
3. Ask natural language questions about your data
4. Get charts, summaries, and insights

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o` | OpenAI model to use |
| `GROQ_API_KEY` | No | — | Your Groq API key (alternative to OpenAI) |
| `GROQ_MODEL` | No | `llama3-70b-8192` | Groq model to use |
| `LANGCHAIN_API_KEY` | No | — | LangSmith API key for tracing |
| `LANGCHAIN_PROJECT` | No | `ai-data-analyst` | LangSmith project name |
| `LANGCHAIN_TRACING_V2` | No | `true` | Enable LangSmith tracing |
| `UPLOAD_DIR` | No | `uploads` | Directory for uploaded files |
| `CHARTS_DIR` | No | `outputs/charts` | Directory for generated charts |
| `MAX_FILE_SIZE_MB` | No | `50` | Maximum upload file size |
| `SANDBOX_TIMEOUT_SECONDS` | No | `30` | Docker sandbox timeout |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `LOG_FILE_PATH` | No | `logs/app.log` | Rotating log file path |
| `LOG_MAX_BYTES` | No | `10485760` | Max bytes per log file before rotation |
| `LOG_BACKUP_COUNT` | No | `3` | Number of rotated backup files to retain |

Backend logging writes to console and a rotating file. Rotation keeps one active log file plus up to 3 backups.

---

## Security

- **Pandas queries**: Keyword blocklist prevents `import`, `os`, `sys`, `exec`, `eval`, etc.
- **Docker sandbox**: `network_disabled`, `read_only` filesystem, `user=nobody`, memory/CPU limits
- **File uploads**: Extension validation, size limits, UUID-based storage paths
- **API key**: Never exposed to frontend
