from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.graph.builder import EcommerceAgentApplication


@dataclass
class SessionRuntime:
    """保存单个前端会话的运行态。"""

    session_id: str
    title: str
    app: EcommerceAgentApplication
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    last_route: str = "rag"
    last_route_reason: str = ""
    last_sql: str = ""
    last_rows: list[dict[str, Any]] = field(default_factory=list)
    rag_hits: int = 0
    rag_calls: int = 0
    tool_success_count: int = 0
    tool_error_count: int = 0
