"""Framework-specific exceptions."""


class APIClientError(RuntimeError):
    """Raised when an HTTP request cannot be completed."""


class EvaluationError(RuntimeError):
    """Raised when an evaluator cannot produce a valid result."""
