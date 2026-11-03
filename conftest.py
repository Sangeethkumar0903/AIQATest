"""Shared pytest fixtures for all AIQATest suites."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

import pytest

from config.settings import Settings, get_settings
from core.api_client import APIClient
from core.logging_config import configure_logging
from evaluators.deterministic import DeterministicEvaluator
from sample_app.knowledge_base import as_mapping

ROOT = Path(__file__).parent


def pytest_configure() -> None:
    configure_logging()


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def application_url(settings: Settings) -> Iterator[str]:
    """Start the sample app locally, or use an explicitly configured external target."""

    if settings.base_url != "http://testserver":
        yield settings.base_url
        return

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "sample_app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Sample application exited with code {process.returncode}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    else:
        process.terminate()
        raise RuntimeError("Sample application did not start within 10 seconds")

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture()
def app_test_client(application_url: str, settings: Settings) -> Iterator[APIClient]:
    """Return the reusable httpx client connected to the application under test."""

    with APIClient(
        application_url,
        timeout=settings.request_timeout,
        headers={"User-Agent": "AIQATest/1.0"},
    ) as client:
        yield client


@pytest.fixture()
def api_client(app_test_client: APIClient) -> APIClient:
    return app_test_client


@pytest.fixture(scope="session")
def sample_knowledge_base() -> dict[str, str]:
    return as_mapping()


def _load_json(name: str) -> list[dict[str, Any]]:
    return json.loads((ROOT / "datasets" / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def golden_dataset() -> list[dict[str, Any]]:
    return _load_json("golden_questions.json")


@pytest.fixture(scope="session")
def security_dataset() -> list[dict[str, Any]]:
    return _load_json("security_cases.json")


@pytest.fixture(scope="session")
def deterministic_evaluator() -> DeterministicEvaluator:
    return DeterministicEvaluator()


@pytest.fixture()
def temporary_resource(tmp_path: Path) -> Path:
    resource = tmp_path / "aiqa-resource.json"
    resource.write_text('{"status": "temporary"}', encoding="utf-8")
    return resource


@pytest.fixture()
def request_timer() -> Any:
    @contextmanager
    def timer() -> Iterator[dict[str, float]]:
        measurement: dict[str, float] = {}
        started = perf_counter()
        try:
            yield measurement
        finally:
            measurement["elapsed_ms"] = (perf_counter() - started) * 1000

    return timer
