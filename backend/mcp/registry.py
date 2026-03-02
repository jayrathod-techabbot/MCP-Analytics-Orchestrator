from dataclasses import dataclass
from typing import Callable

from backend.mcp.tools.generate_chart import (
    TOOL_SCHEMA as CHART_SCHEMA,
    generate_chart,
)
from backend.mcp.tools.load_csv import TOOL_SCHEMA as LOAD_CSV_SCHEMA, load_csv
from backend.mcp.tools.python_sandbox import (
    TOOL_SCHEMA as SANDBOX_SCHEMA,
    python_sandbox,
)
from backend.mcp.tools.run_pandas_query import (
    TOOL_SCHEMA as QUERY_SCHEMA,
    run_pandas_query,
)
from backend.mcp.tools.summarize_findings import (
    TOOL_SCHEMA as SUMMARY_SCHEMA,
    summarize_findings,
)
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ToolEntry:
    fn: Callable[..., str]
    schema: dict


_TOOLS: dict[str, ToolEntry] = {
    "load_csv": ToolEntry(fn=load_csv, schema=LOAD_CSV_SCHEMA),
    "run_pandas_query": ToolEntry(fn=run_pandas_query, schema=QUERY_SCHEMA),
    "generate_chart": ToolEntry(fn=generate_chart, schema=CHART_SCHEMA),
    "summarize_findings": ToolEntry(fn=summarize_findings, schema=SUMMARY_SCHEMA),
    "python_sandbox": ToolEntry(fn=python_sandbox, schema=SANDBOX_SCHEMA),
}


def get_openai_tools() -> list[dict]:
    return [entry.schema for entry in _TOOLS.values()]


def get_tool_function(name: str) -> Callable[..., str] | None:
    entry = _TOOLS.get(name)
    return entry.fn if entry else None


def list_tool_names() -> list[str]:
    return list(_TOOLS.keys())
