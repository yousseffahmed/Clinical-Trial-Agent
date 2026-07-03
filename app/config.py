"""Application configuration and safe project-relative paths."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or ``.env``."""

    project_name: str = "Clinical Trial Protocol & Risk Assistant Agent"
    app_env: str = "development"
    log_level: str = "INFO"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"

    data_dir: Path = PROJECT_ROOT / "data"
    memory_db_path: Path = PROJECT_ROOT / "memory" / "memory.db"
    vector_store_dir: Path = PROJECT_ROOT / "vector_store"
    vector_index_name: str = "protocol_index.json"

    chunk_size: int = 900
    chunk_overlap: int = 120
    rag_top_k: int = 5
    rag_min_score: float = 0.18
    embedding_backend: str = "hash"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def vector_index_path(self) -> Path:
        return self.vector_store_dir / self.vector_index_name

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
