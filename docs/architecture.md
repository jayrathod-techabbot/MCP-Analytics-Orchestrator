# Architecture Details

## Backend Layer Structure
1. **Routers** (HTTP layer only) → `backend/routers/`
2. **Services** (LLM orchestration) → `backend/services/openai_service.py`
3. **MCP Registry** (tool registration + schema export) → `backend/mcp/registry.py`
4. **MCP Executor** (tool dispatch + error wrapping) → `backend/mcp/executor.py`
5. **MCP Tools** (pure data operations) → `backend/mcp/tools/`
6. **Models** (Pydantic schemas) → `backend/models/schemas.py`
7. **Utils** (stateless helpers) → `backend/utils/`

## OpenAI Tool-Calling Loop (openai_service.py)
- System prompt instructs GPT-4o to call tools in order: load_csv → run_pandas_query → generate_chart → summarize_findings
- Max 10 iterations safeguard
- Collects charts, summary, insights from tool results
- Returns structured response: { answer, charts, summary, insights, tool_calls_made, tokens_used }

## MCP Tools
| Tool | Key Details |
|---|---|
| load_csv | Reads CSV/Excel, classifies columns (numeric/categorical/datetime) |
| run_pandas_query | Keyword blocklist safety, restricted builtins, max 100 rows output |
| generate_chart | Seaborn + Matplotlib, saves PNG with uuid, supports 6 chart types |
| summarize_findings | Secondary OpenAI call (non-tool), returns markdown summary + insights |
| python_sandbox | Docker SDK, network_disabled, read_only, mem_limit=256m, timeout=30s |

## Frontend Architecture
- Single-page app with two-panel layout: sidebar (upload + quick questions) + main chat
- State managed via custom `useAnalysis` hook (no Redux)
- Vite dev server proxies `/api` and `/charts` to backend
- Components: UploadPanel (dropzone + data table), ChatPanel (messages), ChartViewer (expand modal), SummaryCard (markdown + insights)

## Pydantic Schemas
- UploadResponse: file_id, filename, rows, columns, column_names, preview
- AnalyzeRequest: file_id, question, conversation_history
- AnalyzeResponse: answer, charts, summary, insights, tool_calls_made, tokens_used
- ConversationMessage: role (user|assistant), content
- ErrorResponse: error, detail
