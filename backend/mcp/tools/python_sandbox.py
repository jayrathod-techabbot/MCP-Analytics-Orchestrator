import json

import docker
from docker.errors import ContainerError, ImageNotFound, APIError

from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

SANDBOX_IMAGE = "data-analyst-sandbox:latest"

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "python_sandbox",
        "description": (
            "Execute arbitrary Python code in a secure Docker sandbox. "
            "The sandbox has pandas, numpy, matplotlib, and seaborn pre-installed. "
            "Use this for complex data transformations or custom analysis that "
            "cannot be expressed as a simple pandas query. "
            "The code runs in an isolated container with no network access."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute in the sandbox.",
                }
            },
            "required": ["code"],
        },
    },
}


def python_sandbox(code: str) -> str:
    try:
        client = docker.from_env()

        wrapped_code = (
            "import sys, json, io\n"
            "import pandas as pd\n"
            "import numpy as np\n"
            "\n"
            f"{code}\n"
        )

        container_output = client.containers.run(
            image=SANDBOX_IMAGE,
            command=["python", "-c", wrapped_code],
            network_disabled=True,
            mem_limit="256m",
            cpu_quota=50000,
            remove=True,
            stdout=True,
            stderr=True,
            read_only=True,
            user="nobody",
            timeout=settings.SANDBOX_TIMEOUT_SECONDS,
        )

        stdout = container_output.decode("utf-8") if isinstance(container_output, bytes) else str(container_output)

        logger.info("Sandbox execution completed successfully")
        return json.dumps({
            "stdout": stdout,
            "stderr": "",
            "exit_code": 0,
            "success": True,
        })

    except ContainerError as e:
        stderr = e.stderr.decode("utf-8") if e.stderr else str(e)
        logger.warning("Sandbox container error: %s", stderr)
        return json.dumps({
            "stdout": "",
            "stderr": stderr,
            "exit_code": e.exit_status,
            "success": False,
        })

    except ImageNotFound:
        logger.error("Sandbox Docker image '%s' not found", SANDBOX_IMAGE)
        return json.dumps({
            "error": f"Docker image '{SANDBOX_IMAGE}' not found. Build it with: docker build -t {SANDBOX_IMAGE} ./sandbox",
        })

    except APIError as e:
        logger.error("Docker API error: %s", str(e))
        return json.dumps({"error": f"Docker error: {str(e)}"})

    except Exception as e:
        logger.error("Sandbox error: %s", str(e))
        return json.dumps({"error": f"Sandbox execution failed: {str(e)}"})
