import json

from backend.mcp.registry import get_tool_function
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


def execute_tool(name: str, arguments: dict) -> str:
    fn = get_tool_function(name)
    if fn is None:
        logger.warning("Unknown tool requested: %s", name)
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        logger.info("Executing tool: %s with args: %s", name, list(arguments.keys()))
        result = fn(**arguments)
        return result
    except TypeError as e:
        logger.error("Tool %s argument error: %s", name, str(e))
        return json.dumps({"error": f"Invalid arguments for tool '{name}': {str(e)}"})
    except Exception as e:
        logger.error("Tool %s execution error: %s", name, str(e))
        return json.dumps({"error": f"Tool '{name}' failed: {str(e)}"})
