import atexit
import hashlib
import json
import sys
import threading
import time
import uuid
from pathlib import Path

import jupyter_client
import pandas as pd

from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

BLOCKED_KEYWORDS = [
    "import ",
    "__",
    "open(",
    "os.",
    "sys.",
    "subprocess",
    "eval(",
    "exec(",
    "compile(",
    "globals(",
    "locals(",
    "getattr(",
    "setattr(",
    "delattr(",
    "breakpoint(",
    "shutil.",
    "pathlib.",
    "requests.",
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


class _KernelRuntime:
    def __init__(self, isolation_key: str):
        self.isolation_key = isolation_key
        self.lock = threading.Lock()
        self.km: jupyter_client.KernelManager | None = None
        self.kc = None
        self.ready = False
        self.last_used = time.monotonic()

        self.cached_file_path: str | None = None
        self.cached_mtime_ns: int | None = None
        self.cached_size: int | None = None
        self.cache_expires_at: float = 0.0
        self.df_var_name = "_cached_df"

    def start_if_needed(self) -> None:
        if self.ready and self.km is not None and self.kc is not None:
            return

        self.shutdown()

        km = jupyter_client.KernelManager(kernel_name="python3")
        km.kernel_cmd = [
            sys.executable,
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
        km.start_kernel()

        kc = km.client()
        kc.start_channels()
        kc.wait_for_ready(timeout=settings.PANDAS_QUERY_KERNEL_READY_TIMEOUT_SECONDS)

        self.km = km
        self.kc = kc
        self.ready = True

    def shutdown(self) -> None:
        if self.kc is not None:
            try:
                self.kc.stop_channels()
            except Exception:
                pass
        if self.km is not None:
            try:
                self.km.shutdown_kernel()
            except Exception:
                pass

        self.km = None
        self.kc = None
        self.ready = False
        self.cached_file_path = None
        self.cached_mtime_ns = None
        self.cached_size = None
        self.cache_expires_at = 0.0


class _KernelPool:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runtimes: dict[str, _KernelRuntime] = {}

    @property
    def runtimes(self) -> dict[str, _KernelRuntime]:
        return self._runtimes

    def _shutdown_runtime(self, runtime: _KernelRuntime) -> None:
        runtime.shutdown()
        runtime.lock.release()

    def _cleanup_idle_locked(self, now: float) -> list[_KernelRuntime]:
        idle_ttl = settings.PANDAS_QUERY_IDLE_KERNEL_TTL_SECONDS
        removed: list[_KernelRuntime] = []

        for key, runtime in list(self._runtimes.items()):
            if now - runtime.last_used < idle_ttl:
                continue
            if not runtime.lock.acquire(blocking=False):
                continue
            self._runtimes.pop(key, None)
            removed.append(runtime)
            logger.info("Evicting idle pandas kernel runtime for key=%s", key)

        return removed

    def _reserve_evictable_runtime_locked(self) -> _KernelRuntime | None:
        for _, runtime in sorted(
            self._runtimes.items(), key=lambda item: item[1].last_used
        ):
            if runtime.lock.acquire(blocking=False):
                self._runtimes.pop(runtime.isolation_key, None)
                logger.info(
                    "Evicting LRU pandas kernel runtime for key=%s",
                    runtime.isolation_key,
                )
                return runtime
        return None

    def acquire(self, isolation_key: str) -> _KernelRuntime:
        while True:
            to_shutdown: list[_KernelRuntime] = []
            reserved: _KernelRuntime | None = None
            created: _KernelRuntime | None = None

            with self._lock:
                now = time.monotonic()
                to_shutdown.extend(self._cleanup_idle_locked(now))

                existing = self._runtimes.get(isolation_key)
                if existing is not None:
                    existing.last_used = now
                    return existing

                if len(self._runtimes) < settings.PANDAS_QUERY_POOL_MAX_KERNELS:
                    created = _KernelRuntime(isolation_key=isolation_key)
                    self._runtimes[isolation_key] = created
                    created.last_used = now
                else:
                    reserved = self._reserve_evictable_runtime_locked()

            for runtime in to_shutdown:
                self._shutdown_runtime(runtime)

            if created is not None:
                return created

            if reserved is not None:
                self._shutdown_runtime(reserved)
                continue

            # Pool is full and all runtimes are busy. Wait briefly for a slot.
            time.sleep(0.01)

    def shutdown_all(self) -> None:
        with self._lock:
            items = list(self._runtimes.values())
            self._runtimes.clear()

        for runtime in items:
            locked = runtime.lock.acquire(timeout=1)
            if not locked:
                continue
            self._shutdown_runtime(runtime)


def _derive_isolation_key(path: Path) -> str:
    stem = path.stem
    try:
        uuid.UUID(stem)
        return f"file_id:{stem}"
    except ValueError:
        hashed = hashlib.sha1(str(path).encode("utf-8")).hexdigest()
        return f"path_sha1:{hashed}"


def _read_expr(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xls"):
        return "pd.read_excel(file_path, engine='openpyxl')"
    return "pd.read_csv(file_path)"


def _execute_script(runtime: _KernelRuntime, script: str) -> tuple[str | None, str | None, str | None]:
    if runtime.kc is None:
        return (
            None,
            None,
            json.dumps(
                {
                    "error": (
                        "Kernel startup or query execution failed: "
                        "Kernel client unavailable"
                    )
                }
            ),
        )

    msg_id = runtime.kc.execute(script)
    stdout_chunks: list[str] = []
    error_traceback = None
    saw_idle = False

    while True:
        try:
            msg = runtime.kc.get_iopub_msg(
                timeout=settings.PANDAS_QUERY_EXEC_TIMEOUT_SECONDS
            )
        except Exception:
            logger.error("Timeout waiting for Jupyter kernel output")
            runtime.ready = False
            return (
                None,
                None,
                json.dumps({"error": "Query execution timed out waiting for output."}),
            )

        if msg["parent_header"].get("msg_id") != msg_id:
            continue

        msg_type = msg["header"]["msg_type"]
        if msg_type == "stream" and msg["content"]["name"] == "stdout":
            stdout_chunks.append(msg["content"]["text"])
            continue

        if msg_type == "error":
            error_traceback = "\\n".join(msg["content"]["traceback"])
            continue

        if msg_type == "status" and msg["content"]["execution_state"] == "idle":
            saw_idle = True
            break

    output_json_str = "".join(stdout_chunks).strip()
    if output_json_str:
        lines = [line.strip() for line in output_json_str.splitlines() if line.strip()]
        if lines:
            output_json_str = lines[-1]

    if not saw_idle and output_json_str == "" and error_traceback is None:
        return (
            None,
            None,
            json.dumps({"error": "Kernel finished execution without any output."}),
        )

    if output_json_str:
        try:
            json.loads(output_json_str)
            return output_json_str, None, None
        except json.JSONDecodeError:
            pass

    if error_traceback:
        return (
            None,
            f"Kernel execution error:\n{error_traceback}",
            None,
        )

    return None, None, json.dumps({"error": "No valid output gathered from kernel."})


def _load_df_if_needed(runtime: _KernelRuntime, path: Path, st_mtime_ns: int, st_size: int) -> str | None:
    now = time.monotonic()
    cache_ttl = settings.PANDAS_QUERY_CACHE_TTL_SECONDS

    cache_valid = (
        runtime.cached_file_path == str(path)
        and runtime.cached_mtime_ns == st_mtime_ns
        and runtime.cached_size == st_size
        and runtime.cache_expires_at > now
    )

    if cache_valid:
        logger.info("Pandas query cache hit for key=%s", runtime.isolation_key)
        runtime.cache_expires_at = now + cache_ttl
        return None

    logger.info("Pandas query cache miss for key=%s", runtime.isolation_key)
    script = f"""
import sys
import json
import pandas as pd

file_path = {repr(str(path))}
try:
    {runtime.df_var_name} = {_read_expr(path)}
except Exception as e:
    print(json.dumps({{"error": f"Failed to load file: {{str(e)}}"}}))
    sys.exit(0)

print(json.dumps({{"ok": True}}))
"""

    output_json, kernel_error, passthrough_error = _execute_script(runtime, script)
    if passthrough_error:
        return passthrough_error
    if kernel_error:
        return json.dumps({"error": kernel_error})

    try:
        payload = json.loads(output_json or "{}")
    except json.JSONDecodeError:
        return json.dumps({"error": "No valid output gathered from kernel."})

    if "error" in payload:
        return json.dumps(payload)

    runtime.cached_file_path = str(path)
    runtime.cached_mtime_ns = st_mtime_ns
    runtime.cached_size = st_size
    runtime.cache_expires_at = now + cache_ttl
    return None


def _execute_query(runtime: _KernelRuntime, query_code: str) -> str:
    query_script = f"""
import sys
import json
from backend.mcp.tools.run_pandas_query import _serialize_result

df = {runtime.df_var_name}

# User code execution
{query_code}

if 'result' not in locals():
    print(json.dumps({{"error": "Query must assign output to a variable named `result`."}}))
    sys.exit(0)

try:
    data, row_count, columns = _serialize_result(result)
    output = {{"result": data, "row_count": row_count}}
    if columns is not None:
        output["columns"] = columns
    print(json.dumps(output, default=str))
except Exception as e:
    print(json.dumps({{"error": f"Failed to serialize result: {{str(e)}}"}}))
"""

    output_json, kernel_error, passthrough_error = _execute_script(runtime, query_script)

    if passthrough_error:
        return passthrough_error
    if kernel_error:
        return json.dumps({"error": kernel_error})
    return output_json or json.dumps({"error": "No valid output gathered from kernel."})


_KERNEL_POOL = _KernelPool()
atexit.register(_KERNEL_POOL.shutdown_all)


def _reset_kernel_pool_for_tests() -> None:
    _KERNEL_POOL.shutdown_all()


def run_pandas_query(file_path: str, query_code: str) -> str:
    started = time.perf_counter()
    try:
        safety_error = _check_safety(query_code)
        if safety_error:
            return json.dumps({"error": safety_error})

        path = Path(file_path).resolve()
        isolation_key = _derive_isolation_key(path)
        runtime = _KERNEL_POOL.acquire(isolation_key)

        logger.info("Executing pandas query in Jupyter kernel: %s", query_code)
        logger.info("On file: %s", file_path)

        with runtime.lock:
            runtime.last_used = time.monotonic()

            runtime.start_if_needed()

            stat_result = path.stat()
            load_err = _load_df_if_needed(
                runtime,
                path,
                st_mtime_ns=stat_result.st_mtime_ns,
                st_size=stat_result.st_size,
            )
            if load_err:
                return load_err

            output = _execute_query(runtime, query_code)
            runtime.last_used = time.monotonic()
            logger.info(
                "Executed pandas query on %s successfully in kernel", file_path
            )
            return output

    except Exception as e:
        logger.error("Pandas kernel query error: %s", str(e))
        return json.dumps(
            {"error": f"Kernel startup or query execution failed: {str(e)}"}
        )
    finally:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info("run_pandas_query total_ms=%d", elapsed_ms)
