import json
import uuid
from pathlib import Path

import pandas as pd

from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "export_to_excel",
        "description": (
            "Export the dataset (or a filtered/transformed subset of it) to an Excel file (.xlsx) "
            "and return a download URL. Optionally apply a pandas query expression to filter rows "
            "before exporting, and choose which columns to include. "
            "Use this when the user asks to download, save, or export data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the source CSV or Excel file.",
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the Excel sheet. Defaults to 'Data'.",
                },
                "filter_query": {
                    "type": "string",
                    "description": (
                        "Optional pandas query string to filter rows before exporting. "
                        "Example: \"revenue > 1000 and region == 'North'\". "
                        "Uses DataFrame.query() syntax."
                    ),
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional list of column names to include in the export. "
                        "If omitted, all columns are exported."
                    ),
                },
                "include_index": {
                    "type": "boolean",
                    "description": "Whether to include the DataFrame index as a column. Defaults to false.",
                },
            },
            "required": ["file_path"],
        },
    },
}


def export_to_excel(
    file_path: str,
    sheet_name: str = "Data",
    filter_query: str | None = None,
    columns: list[str] | None = None,
    include_index: bool = False,
) -> str:
    try:
        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"})

        ext = path.suffix.lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, engine="openpyxl")
        else:
            df = pd.read_csv(path)

        if filter_query:
            try:
                df = df.query(filter_query)
            except Exception as e:
                return json.dumps({"error": f"Invalid filter query: {str(e)}"})

        if columns:
            missing = [c for c in columns if c not in df.columns]
            if missing:
                return json.dumps({"error": f"Columns not found in dataset: {missing}"})
            df = df[columns]

        settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        export_id = str(uuid.uuid4())
        export_filename = f"{export_id}.xlsx"
        export_path = settings.EXPORTS_DIR / export_filename

        col_widths = {
            col: min(
                max(
                    len(str(col)),
                    df[col].astype(str).str.len().max() if len(df) > 0 else 0,
                ) + 4,
                50,
            )
            for col in df.columns
        }

        with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=include_index)

            worksheet = writer.sheets[sheet_name]
            for i, col in enumerate(df.columns):
                col_letter = worksheet.cell(row=1, column=i + (2 if include_index else 1)).column_letter
                worksheet.column_dimensions[col_letter].width = col_widths[col]

        download_url = f"/api/exports/{export_filename}"

        logger.info(
            "Exported %d rows x %d cols to %s",
            len(df),
            len(df.columns),
            export_path,
        )

        return json.dumps(
            {
                "export_path": str(export_path),
                "download_url": download_url,
                "filename": export_filename,
                "rows_exported": len(df),
                "columns_exported": df.columns.tolist(),
                "sheet_name": sheet_name,
            }
        )

    except Exception as e:
        logger.error("Export failed: %s", str(e))
        return json.dumps({"error": f"Export failed: {str(e)}"})
