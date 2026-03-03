import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from backend.config import settings
from backend.mcp.tools import run_pandas_query as rpq


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


@pytest.fixture(autouse=True)
def reset_pool_and_settings():
    original_ready = settings.PANDAS_QUERY_KERNEL_READY_TIMEOUT_SECONDS
    original_exec = settings.PANDAS_QUERY_EXEC_TIMEOUT_SECONDS
    original_cache_ttl = settings.PANDAS_QUERY_CACHE_TTL_SECONDS
    original_pool = settings.PANDAS_QUERY_POOL_MAX_KERNELS
    original_idle = settings.PANDAS_QUERY_IDLE_KERNEL_TTL_SECONDS

    rpq._reset_kernel_pool_for_tests()
    settings.PANDAS_QUERY_KERNEL_READY_TIMEOUT_SECONDS = 10
    settings.PANDAS_QUERY_EXEC_TIMEOUT_SECONDS = 20
    settings.PANDAS_QUERY_CACHE_TTL_SECONDS = 120
    settings.PANDAS_QUERY_POOL_MAX_KERNELS = 4
    settings.PANDAS_QUERY_IDLE_KERNEL_TTL_SECONDS = 300

    yield

    rpq._reset_kernel_pool_for_tests()
    settings.PANDAS_QUERY_KERNEL_READY_TIMEOUT_SECONDS = original_ready
    settings.PANDAS_QUERY_EXEC_TIMEOUT_SECONDS = original_exec
    settings.PANDAS_QUERY_CACHE_TTL_SECONDS = original_cache_ttl
    settings.PANDAS_QUERY_POOL_MAX_KERNELS = original_pool
    settings.PANDAS_QUERY_IDLE_KERNEL_TTL_SECONDS = original_idle


def test_safety_blocklist_unchanged(tmp_path: Path):
    file_path = tmp_path / "sample.csv"
    _write_csv(file_path, ["a", "1"])

    output = rpq.run_pandas_query(str(file_path), "result = eval('1+1')")
    payload = json.loads(output)

    assert payload["error"] == "Blocked keyword detected: 'eval('"


def test_missing_result_error_unchanged(tmp_path: Path):
    file_path = tmp_path / "sample.csv"
    _write_csv(file_path, ["a", "1", "2"])

    output = rpq.run_pandas_query(str(file_path), "x = df['a'].sum()")
    payload = json.loads(output)

    assert payload["error"] == "Query must assign output to a variable named `result`."


def test_dataframe_serialization_shape(tmp_path: Path):
    file_path = tmp_path / "sample.csv"
    _write_csv(file_path, ["a,b", "1,10", "2,20"])

    output = rpq.run_pandas_query(str(file_path), "result = df")
    payload = json.loads(output)

    assert payload["row_count"] == 2
    assert payload["columns"] == ["a", "b"]
    assert payload["result"][0]["a"] == 1


def test_cache_hit_reuses_loaded_dataframe(tmp_path: Path):
    file_id = "123e4567-e89b-12d3-a456-426614174000"
    file_path = tmp_path / f"{file_id}.csv"
    _write_csv(file_path, ["a", "1", "2"])

    out1 = rpq.run_pandas_query(str(file_path), "result = id(df)")
    out2 = rpq.run_pandas_query(str(file_path), "result = id(df)")

    p1 = json.loads(out1)
    p2 = json.loads(out2)

    assert p1["result"] == p2["result"]


def test_metadata_change_invalidates_cache(tmp_path: Path):
    file_id = "123e4567-e89b-12d3-a456-426614174001"
    file_path = tmp_path / f"{file_id}.csv"
    _write_csv(file_path, ["a", "1", "2"])

    out1 = rpq.run_pandas_query(str(file_path), "result = len(df)")
    assert json.loads(out1)["result"] == 2

    _write_csv(file_path, ["a", "1", "2", "3"])

    out2 = rpq.run_pandas_query(str(file_path), "result = len(df)")
    assert json.loads(out2)["result"] == 3


def test_pool_eviction_respects_max_kernels(tmp_path: Path):
    settings.PANDAS_QUERY_POOL_MAX_KERNELS = 1

    file1 = tmp_path / "123e4567-e89b-12d3-a456-426614174010.csv"
    file2 = tmp_path / "123e4567-e89b-12d3-a456-426614174011.csv"
    _write_csv(file1, ["a", "1"])
    _write_csv(file2, ["a", "2"])

    rpq.run_pandas_query(str(file1), "result = len(df)")
    rpq.run_pandas_query(str(file2), "result = len(df)")

    keys = list(rpq._KERNEL_POOL.runtimes.keys())
    assert len(keys) == 1
    assert keys[0].endswith("123e4567-e89b-12d3-a456-426614174011")


def test_concurrent_queries_different_files_isolated(tmp_path: Path):
    file1 = tmp_path / "123e4567-e89b-12d3-a456-426614174020.csv"
    file2 = tmp_path / "123e4567-e89b-12d3-a456-426614174021.csv"
    _write_csv(file1, ["a", "1", "2"])
    _write_csv(file2, ["a", "10", "20"])

    def run_query(path: Path, expr: str):
        out = rpq.run_pandas_query(str(path), expr)
        return json.loads(out)

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(run_query, file1, "result = int(df['a'].sum())")
        future2 = executor.submit(run_query, file2, "result = int(df['a'].sum())")

    p1 = future1.result()
    p2 = future2.result()

    assert p1["result"] == 3
    assert p2["result"] == 30


def test_concurrent_queries_same_file_no_interference(tmp_path: Path):
    file1 = tmp_path / "123e4567-e89b-12d3-a456-426614174030.csv"
    _write_csv(file1, ["a", "1", "2", "3"])

    queries = ["result = int(df['a'].sum())", "result = int(df['a'].mean())"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(rpq.run_pandas_query, str(file1), q) for q in queries]

    payloads = [json.loads(f.result()) for f in futures]
    assert all("error" not in payload for payload in payloads)
    values = sorted(p["result"] for p in payloads)

    assert values == [2, 6]
