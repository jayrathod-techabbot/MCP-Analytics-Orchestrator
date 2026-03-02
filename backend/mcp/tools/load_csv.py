import json
from pathlib import Path

import pandas as pd

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "load_csv",
        "description": (
            "Load a CSV or Excel file and return its schema information including "
            "shape, column names, data types, null counts, and a preview of the first 5 rows. "
            "Call this tool first to understand the dataset before performing any analysis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the CSV or Excel file.",
                }
            },
            "required": ["file_path"],
        },
    },
}


def load_csv(file_path: str) -> str:
    try:
        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"})

        ext = path.suffix.lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, engine="openpyxl")
        else:
            df = pd.read_csv(path)

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()
        datetime_columns = []
        for col in df.columns:
            if df[col].dtype == "object":
                try:
                    pd.to_datetime(df[col].dropna().head(20))
                    datetime_columns.append(col)
                except (ValueError, TypeError):
                    pass

        preview = df.head(5).fillna("null").to_dict(orient="records")

        result = {
            "shape": list(df.shape),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": df.isnull().sum().to_dict(),
            "preview": preview,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "datetime_columns": datetime_columns,
        }

        logger.info("Loaded file %s: %d rows, %d columns", file_path, df.shape[0], df.shape[1])
        return json.dumps(result, default=str)

    except Exception as e:
        logger.error("Error loading file %s: %s", file_path, str(e))
        return json.dumps({"error": f"Failed to load file: {str(e)}"})
