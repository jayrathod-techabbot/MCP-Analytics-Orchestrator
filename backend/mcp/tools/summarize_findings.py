import json

from openai import OpenAI

from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "summarize_findings",
        "description": (
            "Generate an AI-powered narrative summary and actionable business insights "
            "from the data analysis results collected so far. Call this after gathering "
            "enough data from queries and charts to provide a comprehensive summary."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data_context": {
                    "type": "string",
                    "description": "JSON string containing all tool results gathered so far (query results, chart info, etc.).",
                },
                "user_question": {
                    "type": "string",
                    "description": "The original user question to focus the summary on.",
                },
            },
            "required": ["data_context", "user_question"],
        },
    },
}

SUMMARY_SYSTEM_PROMPT = """You are a senior data analyst writing a report for a business stakeholder.

Based on the data analysis results provided, write:
1. A clear 2-3 paragraph narrative summary of the key findings, referencing specific numbers and trends.
2. A list of 3-5 actionable business insights with specific recommendations.

Format the summary in markdown. Be specific with numbers — don't generalize.
Keep the tone professional but accessible."""


def summarize_findings(data_context: str, user_question: str) -> str:
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"User's question: {user_question}\n\n"
                        f"Data analysis results:\n{data_context}"
                    ),
                },
            ],
            temperature=0.4,
            max_tokens=1500,
        )

        content = response.choices[0].message.content or ""

        parts = content.split("## Insights", 1)
        summary_text = parts[0].strip()
        insights = []

        if len(parts) > 1:
            insight_lines = parts[1].strip().split("\n")
            for line in insight_lines:
                line = line.strip()
                if line and line[0] in "-*•":
                    insights.append(line.lstrip("-*• ").strip())
        else:
            lines = content.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line and line[0] in "-*•" and len(line) > 20:
                    insights.append(line.lstrip("-*• ").strip())

        if not insights:
            insights = ["See the summary above for detailed findings."]

        logger.info("Generated summary with %d insights", len(insights))
        return json.dumps({
            "summary": summary_text,
            "insights": insights[:5],
        })

    except Exception as e:
        logger.error("Summary generation error: %s", str(e))
        return json.dumps({"error": f"Summary generation failed: {str(e)}"})
