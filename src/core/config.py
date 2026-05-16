from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。

    生产系统里不要把路径、模型名和阈值写死在代码里，而是统一放到配置层，
    这样便于不同环境之间做切换，也方便后续接入配置中心。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="DASHSCOPE_BASE_URL",
    )
    llm_model: str = Field(default="qwen-plus", alias="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-v3", alias="EMBEDDING_MODEL")
    rerank_model: str = Field(default="gte-rerank-v2", alias="RERANK_MODEL")

    docs_dir: Path = Field(default=Path("./data/docs"), alias="DOCS_DIR")
    chroma_dir: Path = Field(default=Path("./data/chroma"), alias="CHROMA_DIR")
    docs_index_path: Path = Field(default=Path("./data/docs_index.json"))
    sqlite_db_path: Path = Field(
        default=Path("./data/sqlite/ecommerce.db"),
        alias="SQLITE_DB_PATH",
    )

    memory_max_recent_turns: int = Field(default=5, alias="MEMORY_MAX_RECENT_TURNS")
    memory_token_threshold: int = Field(default=8000, alias="MEMORY_TOKEN_THRESHOLD")

    vector_top_k: int = Field(default=12, alias="VECTOR_TOP_K")
    bm25_top_k: int = Field(default=12, alias="BM25_TOP_K")
    rerank_top_k: int = Field(default=5, alias="RERANK_TOP_K")
    sql_schema_top_k: int = Field(default=4, alias="SQL_SCHEMA_TOP_K")

    tool_route_top_k: int = 3
    tool_max_self_heal_rounds: int = 3
    llm_temperature: float = 0.1

    def ensure_directories(self) -> None:
        """启动时确保本地所需目录存在。"""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
