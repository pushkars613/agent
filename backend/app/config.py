from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central JARVIS configuration.

    JARVIS is local-first:
    - No AI API keys
    - Ollama runs locally
    - Workspace is explicitly configured
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ============================================================
    # LOCAL AI
    # ============================================================

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    # ============================================================
    # WORKSPACE
    # ============================================================

    jarvis_workspace: str = "/Users/pushkar/jarvis"

    # ============================================================
    # AGENT
    # ============================================================

    max_iterations: int = 8
    request_timeout_seconds: int = 120

    # ============================================================
    # MEMORY
    # ============================================================

    sqlite_path: str = "./jarvis_memory.db"

    # ============================================================
    # PERMISSIONS
    # ============================================================

    auto_approve_safe: bool = True

    @property
    def workspace_path(self) -> Path:
        """
        Return the absolute JARVIS workspace.

        This directory is the root that JARVIS tools are allowed
        to access.
        """

        path = Path(self.jarvis_workspace).expanduser().resolve()

        path.mkdir(parents=True, exist_ok=True)

        return path


settings = Settings()