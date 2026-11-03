"""Reusable HTTP client with timing and consistent failures."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import httpx

from core.exceptions import APIClientError

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TimedResponse:
    """An HTTP response paired with client-observed elapsed time."""

    response: httpx.Response
    elapsed_ms: float

    @property
    def status_code(self) -> int:
        return self.response.status_code

    def json(self) -> Any:
        return self.response.json()


class APIClient:
    """Small composable wrapper around an httpx-compatible client."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        headers: Mapping[str, str] | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=dict(headers or {}),
            trust_env=False,
        )
        if client is not None and headers:
            client.headers.update(headers)

    def __enter__(self) -> APIClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def get(self, path: str, **kwargs: Any) -> TimedResponse:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, *, json: Any = None, **kwargs: Any) -> TimedResponse:
        return self.request("POST", path, json=json, **kwargs)

    def request(self, method: str, path: str, **kwargs: Any) -> TimedResponse:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        started = perf_counter()
        try:
            response = self._client.request(method, url, timeout=self.timeout, **kwargs)
        except httpx.HTTPError as exc:
            elapsed_ms = (perf_counter() - started) * 1000
            raise APIClientError(
                f"{method.upper()} {url} failed after {elapsed_ms:.1f} ms: "
                f"{exc.__class__.__name__}: {exc}"
            ) from exc
        elapsed_ms = (perf_counter() - started) * 1000
        LOGGER.info(
            "http_request method=%s path=%s status=%s elapsed_ms=%.2f",
            method.upper(),
            path,
            response.status_code,
            elapsed_ms,
        )
        return TimedResponse(response=response, elapsed_ms=elapsed_ms)
