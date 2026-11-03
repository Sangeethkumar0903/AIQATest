"""Environment-backed test framework settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration shared by clients, fixtures, and tests."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    base_url: str = Field(default="http://testserver", validation_alias="BASE_URL")
    test_env: str = Field(default="local", validation_alias="TEST_ENV")
    request_timeout: float = Field(default=5.0, gt=0, validation_alias="REQUEST_TIMEOUT")
    max_latency_ms: float = Field(default=500.0, gt=0, validation_alias="MAX_LATENCY_MS")
    run_llm_evals: bool = Field(default=False, validation_alias="RUN_LLM_EVALS")
    run_ui_tests: bool = Field(default=False, validation_alias="RUN_UI_TESTS")
    ui_base_url: str = Field(default="http://127.0.0.1:8000", validation_alias="UI_BASE_URL")
    deepeval_model: str | None = Field(default=None, validation_alias="DEEPEVAL_MODEL")


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance for the current process."""

    return Settings()
