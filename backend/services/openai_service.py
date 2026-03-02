import json

from openai import OpenAI

from backend.config import settings
from backend.mcp.executor import execute_tool
from backend.mcp.registry import get_openai_tools
from backend.models.schemas import ConversationMessage
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

MAX_TOOL_ITERATIONS = 10

SYSTEM_PROMPT = """You are an expert data analyst assistant. You help users analyze their data by using the available tools.

## Instructions:
1. When a user asks about their data, ALWAYS call `load_csv` first if you haven't already inspected the file in this conversation.
2. Use `run_pandas_query` to perform data computations. Write pandas code that assigns the result to a variable named `result`.
3. Generate charts with `generate_chart` whenever a visual representation would help explain the data.
4. After gathering enough data from queries and charts, call `summarize_findings` to produce a narrative summary with actionable insights.
5. If a user needs complex custom analysis, use `python_sandbox` to execute arbitrary Python code.

## Rules:
- Always base your answers on actual data results from tools — never guess or make up numbers.
- When generating charts, choose the most appropriate chart type for the data.
- Provide clear, business-friendly explanations alongside technical results.
- If a tool returns an error, explain the issue to the user and suggest alternatives."""


def run_analysis(
    file_path: str,
    question: str,
    conversation_history: list[ConversationMessage],
) -> dict:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    tools = get_openai_tools()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in conversation_history:
        messages.append({"role": msg.role, "content": msg.content})

    user_content = f"File path: {file_path}\n\nQuestion: {question}"
    messages.append({"role": "user", "content": user_content})

    tool_calls_made: list[str] = []
    charts: list[str] = []
    summary: str | None = None
    insights: list[str] = []
    total_tokens = 0

    for iteration in range(MAX_TOOL_ITERATIONS):
        logger.info("Tool-calling loop iteration %d", iteration + 1)

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        if response.usage:
            total_tokens += response.usage.total_tokens

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" or choice.message.tool_calls:
            assistant_message = {
                "role": "assistant",
                "content": choice.message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ],
            }
            messages.append(assistant_message)

            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                logger.info("Calling tool: %s", fn_name)
                tool_calls_made.append(fn_name)

                result_str = execute_tool(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                })

                try:
                    result_data = json.loads(result_str)

                    if fn_name == "generate_chart" and "chart_url" in result_data:
                        charts.append(result_data["chart_url"])

                    if fn_name == "summarize_findings":
                        if "summary" in result_data:
                            summary = result_data["summary"]
                        if "insights" in result_data:
                            insights = result_data["insights"]
                except json.JSONDecodeError:
                    pass

            continue

        answer = choice.message.content or "Analysis complete."
        logger.info(
            "Analysis finished after %d iterations, %d tool calls",
            iteration + 1,
            len(tool_calls_made),
        )
        return {
            "answer": answer,
            "charts": charts,
            "summary": summary,
            "insights": insights,
            "tool_calls_made": tool_calls_made,
            "tokens_used": total_tokens,
        }

    logger.warning("Hit max iterations (%d) in tool-calling loop", MAX_TOOL_ITERATIONS)
    last_content = messages[-1].get("content", "") if messages else ""
    return {
        "answer": last_content or "Analysis reached the maximum number of steps. Here are the results gathered so far.",
        "charts": charts,
        "summary": summary,
        "insights": insights,
        "tool_calls_made": tool_calls_made,
        "tokens_used": total_tokens,
    }
