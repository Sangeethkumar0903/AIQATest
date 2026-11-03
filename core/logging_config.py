"""Safe, concise logging configuration."""

from __future__ import annotations

import logging
import re
from typing import Any

_SENSITIVE = re.compile(r"(authorization|api[-_]?key|password|token)", re.IGNORECASE)


class SensitiveDataFilter(logging.Filter):
    """Redact obvious credential-shaped fields from structured log arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, dict):
            record.args = {
                key: "[REDACTED]" if _SENSITIVE.search(str(key)) else value
                for key, value in record.args.items()
            }
        return True


def configure_logging(level: int = logging.INFO) -> None:
    """Configure framework logging without recording request bodies or secrets."""

    handler = logging.StreamHandler()
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)


def safe_metadata(**values: Any) -> dict[str, Any]:
    """Return metadata with credential-named values redacted."""

    return {
        key: "[REDACTED]" if _SENSITIVE.search(key) else value for key, value in values.items()
    }
