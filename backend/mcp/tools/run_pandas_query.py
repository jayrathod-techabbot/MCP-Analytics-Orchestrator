import json
from pathlib import Path

import pandas as pd

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

BLOCKED_KEYWORDS = [
    "import ", "__", "open(", "os.", "sys.", "subprocess",
    "eval(", "exec(", "compile(", "globals(", "locals(",
    "getattr(", "setattr(", "delattr(", "breakpoint(",
    "shutil.", "pathlib.", "requests.",
]

MAX_OUTPUT_ROWS = 100

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_pandas_query",
        "description": (
            "Execute a pandas query on the loaded dataset. The DataFrame is available as `df`. "
            "Assign your final result to a variable named `result`. "
            "Example: `result = df.groupby('region')['revenue'].mean()`. "
            "The result will be automatically serialized to JSON. "
            "Output is capped at 100 rows."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the CSV or Excel file.",
                },
                "query_code": {
                    "type": "string",
                    "description": (
                        "Pandas code to execute. Use `df` as the DataFrame variable. "
                        "Assign the final result to `result`."
                    ),
                },
            },
            "required": ["file_path", "query_code"],
        },
    },
}


def _check_safety(code: str) -> str | None:
    for keyword in BLOCKED_KEYWORDS:
        if keyword in code:
            return f"Blocked keyword detected: '{keyword.strip()}'"
    return None


def _serialize_result(result: object) -> tuple[object, int, list[str] | None]:
    if isinstance(result, pd.DataFrame):
        truncated = result.head(MAX_OUTPUT_ROWS)
        return (
            truncated.fillna("null").to_dict(orient="records"),
            len(result),
            result.columns.tolist(),
        )
    if isinstance(result, pd.Series):
        truncated = result.head(MAX_OUTPUT_ROWS)
        return truncated.fillna("null").to_dict(), len(result), None
    if isinstance(result, (int, float, str, bool)):
        return result, 1, None
    if isinstance(result, (list, tuple)):
        return list(result)[:MAX_OUTPUT_ROWS], len(result), None
    return str(result), 1, None


def run_pandas_query(file_path: str, query_code: str) -> str:
    try:
        safety_error = _check_safety(query_code)
        if safety_error:
            return json.dumps({"error": safety_error})

        path = Path(file_path)
        ext = path.suffix.lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, engine="openpyxl")
        else:
            df = pd.read_csv(path)

        local_ns = {"df": df, "pd": pd}
        exec(query_code, {"__builtins__": {}}, local_ns)

        if "result" not in local_ns:
            return json.dumps({"error": "Query must assign output to a variable named `result`."})

        data, row_count, columns = _serialize_result(local_ns["result"])

        output = {"result": data, "row_count": row_count}
        if columns is not None:
            output["columns"] = columns

        logger.info("Executed pandas query on %s: %d rows returned", file_path, row_count)
        return json.dumps(output, default=str)

    except Exception as e:
        logger.error("Pandas query error: %s", str(e))
        return json.dumps({"error": f"Query execution failed: {str(e)}"})
