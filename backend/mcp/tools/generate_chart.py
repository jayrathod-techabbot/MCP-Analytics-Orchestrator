import json
import uuid
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from backend.config import settings
from backend.utils.logger import setup_logger

matplotlib.use("Agg")
logger = setup_logger(__name__)

VALID_CHART_TYPES = {"bar", "line", "scatter", "histogram", "heatmap", "box"}

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_chart",
        "description": (
            "Generate a chart from the dataset and save it as a PNG image. "
            "Supported chart types: bar, line, scatter, histogram, heatmap, box. "
            "Returns the URL path to the generated chart image."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the CSV or Excel file.",
                },
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "scatter", "histogram", "heatmap", "box"],
                    "description": "Type of chart to generate.",
                },
                "x_col": {
                    "type": "string",
                    "description": "Column name for the x-axis.",
                },
                "y_col": {
                    "type": "string",
                    "description": "Column name for the y-axis. Optional for histogram.",
                },
                "title": {
                    "type": "string",
                    "description": "Chart title. If not provided, a default will be generated.",
                },
                "hue_col": {
                    "type": "string",
                    "description": "Optional column for color grouping.",
                },
            },
            "required": ["file_path", "chart_type", "x_col"],
        },
    },
}


def generate_chart(
    file_path: str,
    chart_type: str,
    x_col: str,
    y_col: str | None = None,
    title: str | None = None,
    hue_col: str | None = None,
) -> str:
    try:
        if chart_type not in VALID_CHART_TYPES:
            return json.dumps({"error": f"Invalid chart type: {chart_type}. Must be one of {VALID_CHART_TYPES}"})

        path = Path(file_path)
        ext = path.suffix.lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, engine="openpyxl")
        else:
            df = pd.read_csv(path)

        if x_col not in df.columns:
            return json.dumps({"error": f"Column '{x_col}' not found in dataset."})
        if y_col and y_col not in df.columns:
            return json.dumps({"error": f"Column '{y_col}' not found in dataset."})
        if hue_col and hue_col not in df.columns:
            return json.dumps({"error": f"Column '{hue_col}' not found in dataset."})

        sns.set_theme(style="whitegrid")
        fig, ax = plt.subplots(figsize=(10, 6))

        hue_param = hue_col if hue_col else None

        if chart_type == "bar":
            sns.barplot(data=df, x=x_col, y=y_col, hue=hue_param, ax=ax)
        elif chart_type == "line":
            sns.lineplot(data=df, x=x_col, y=y_col, hue=hue_param, ax=ax)
        elif chart_type == "scatter":
            sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_param, ax=ax)
        elif chart_type == "histogram":
            sns.histplot(data=df, x=x_col, hue=hue_param, kde=True, ax=ax)
        elif chart_type == "heatmap":
            numeric_df = df.select_dtypes(include=["number"])
            corr = numeric_df.corr()
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
        elif chart_type == "box":
            sns.boxplot(data=df, x=x_col, y=y_col, hue=hue_param, ax=ax)

        chart_title = title or f"{chart_type.title()} Chart: {x_col}" + (f" vs {y_col}" if y_col else "")
        ax.set_title(chart_title, fontsize=14, fontweight="bold")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        chart_id = str(uuid.uuid4())
        chart_filename = f"{chart_id}.png"
        settings.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        chart_path = settings.CHARTS_DIR / chart_filename

        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        chart_url = f"/charts/{chart_filename}"

        logger.info("Generated %s chart: %s", chart_type, chart_url)
        return json.dumps({
            "chart_path": str(chart_path),
            "chart_url": chart_url,
            "chart_type": chart_type,
            "title": chart_title,
        })

    except Exception as e:
        logger.error("Chart generation error: %s", str(e))
        plt.close("all")
        return json.dumps({"error": f"Chart generation failed: {str(e)}"})
