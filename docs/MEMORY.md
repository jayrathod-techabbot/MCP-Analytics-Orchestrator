# AI Data Analyst MCP Project — Memory

## Project Overview
- AI-powered data analyst: FastAPI backend + React frontend + OpenAI GPT-4o tool-calling
- Uses MCP (Model Context Protocol) pattern with in-process tool registry
- Supports CSV and Excel (.xlsx, .xls) file uploads
- See [architecture.md](./architecture.md) for detailed structure

## Key File Paths
- Backend entry: `backend/main.py`
- Config: `backend/config.py` (pydantic-settings, reads `.env`)
- Routers: `backend/routers/files.py`, `backend/routers/analysis.py`
- OpenAI agentic loop: `backend/services/openai_service.py` (max 10 tool iterations)
- MCP registry: `backend/mcp/registry.py`
- MCP executor: `backend/mcp/executor.py`
- MCP tools: `backend/mcp/tools/` — load_csv, run_pandas_query, generate_chart, summarize_findings, python_sandbox
- Schemas: `backend/models/schemas.py`
- Frontend app: `frontend/src/App.jsx`
- Components: `frontend/src/components/` — UploadPanel, ChatPanel, ChartViewer, SummaryCard, LoadingSpinner
- API client: `frontend/src/api/client.js`
- State hook: `frontend/src/hooks/useAnalysis.js`
- Sandbox Dockerfile: `sandbox/Dockerfile`

## Tech Stack
- Python 3.12+ with UV package manager
- FastAPI + Uvicorn (async)
- OpenAI SDK (tool-calling / function-calling)
- Pandas, Matplotlib, Seaborn, openpyxl
- Docker SDK for Python (sandbox)
- React 18, Vite 5, TailwindCSS 3, Axios, react-dropzone, react-markdown

## API Endpoints
- `POST /api/upload` — multipart file upload (CSV/Excel)
- `POST /api/analyze` — { file_id, question, conversation_history }
- `GET /api/files/{file_id}` — file metadata
- `DELETE /api/files/{file_id}` — delete file
- `GET /charts/{filename}` — static chart PNG
- `GET /health` — health check

## Patterns & Conventions
- All tools return JSON strings (even errors: `{"error": "..."}`)
- Tool registry uses dataclass `ToolEntry(fn, schema)` mapping
- Charts saved as `outputs/charts/{uuid4}.png`, served at `/charts/`
- Uploads saved as `uploads/{uuid4}.{ext}`
- Frontend uses Vite dev proxy to backend at localhost:8000
- Pandas query safety: keyword blocklist, restricted `__builtins__`
- Sandbox: Docker with network_disabled, read_only, mem_limit, user=nobody

## User Preferences
- Wants professional React components
- APIs should follow coding standards
- Supports Excel files alongside CSV
- Don't assume anything — read planning doc carefully
