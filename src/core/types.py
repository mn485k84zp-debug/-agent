from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage


@dataclass
class QueryRewriteResult:
    """Query 改写结果。"""

    original_query: str
    normalized_query: str
    rewritten_queries: list[str] = field(default_factory=list)


@dataclass
class RetrievedPassage:
    """统一的检索结果结构，便于后续融合排序与 Rerank。"""

    document: Document
    score: float
    source: Literal["vector", "bm25", "hybrid", "rerank"]


@dataclass
class ConversationTurn:
    """把一轮用户问题及其后续助手/工具消息打包，避免截断工具调用对。"""

    messages: list[BaseMessage]
    approx_tokens: int


class AgentState(TypedDict, total=False):
    """LangGraph 运行状态。"""

    user_input: str
    route: str
    route_reason: str

    # 主会话状态
    main_messages: list[BaseMessage]
    summary: str
    recent_turns: list[ConversationTurn]

    # 子 Agent 独立会话状态
    agent_sessions: dict[str, list[BaseMessage]]

    rag_subtask: str
    sql_subtask: str
    rag_answer: str
    sql_answer: str
    final_answer: str

    rag_documents: list[Document]
    tool_traces: list[str]
    last_error: str
