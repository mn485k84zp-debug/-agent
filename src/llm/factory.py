from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import dashscope
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI
from openai import OpenAI

from src.core.config import Settings

logger = logging.getLogger(__name__)


def ensure_api_key(settings: Settings) -> None:
    if not settings.dashscope_api_key.strip():
        raise ValueError(
            "缺少 DASHSCOPE_API_KEY，请先复制 .env.example 为 .env 并填写百炼密钥。"
        )


def ensure_pure_string(value: Any) -> str:
    """把 embedding 输入强制清洗为纯字符串，避免 list/dict 直传到底层接口。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return " ".join(ensure_pure_string(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key}:{ensure_pure_string(val)}" for key, val in value.items())
    return str(value).strip()


class DashScopeOpenAIEmbeddings(Embeddings):
    """使用 DashScope OpenAI 兼容接口实现的 Embedding 适配器。"""

    def __init__(self, settings: Settings) -> None:
        ensure_api_key(settings)
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        cleaned = [ensure_pure_string(text) for text in texts]
        if any(not isinstance(item, str) for item in cleaned):
            raise TypeError("Embedding 输入必须被清洗为纯字符串。")

        response = self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=cleaned,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        cleaned = ensure_pure_string(text)
        if not isinstance(cleaned, str):
            raise TypeError("Embedding 查询必须是纯字符串。")
        response = self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=cleaned,
        )
        return response.data[0].embedding


class DashScopeReranker:
    """调用百炼官方重排序接口，对候选文档做二次精排。"""

    def __init__(self, settings: Settings) -> None:
        ensure_api_key(settings)
        self.settings = settings
        dashscope.api_key = settings.dashscope_api_key

    def rerank(self, query: str, documents: list[str], top_n: int = 5) -> list[dict[str, Any]]:
        if not documents:
            return []

        response = dashscope.TextReRank.call(
            model=self.settings.rerank_model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents)),
            return_documents=True,
        )

        if getattr(response, "status_code", None) not in (None, 200):
            raise RuntimeError(f"Rerank 调用失败: {response}")

        output = getattr(response, "output", {}) or {}
        results = output.get("results", [])
        logger.info("Rerank returned %s results", len(results))
        return results


def build_chat_model(settings: Settings) -> ChatOpenAI:
    """构建聊天模型。

    这里使用 OpenAI 兼容方式接入 DashScope，可以和 LangChain/LangGraph 自然集成。
    """

    ensure_api_key(settings)
    return ChatOpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )


def build_embeddings(settings: Settings) -> DashScopeOpenAIEmbeddings:
    return DashScopeOpenAIEmbeddings(settings)


def build_reranker(settings: Settings) -> DashScopeReranker:
    return DashScopeReranker(settings)
