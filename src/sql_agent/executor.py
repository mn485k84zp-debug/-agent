from __future__ import annotations

import sqlite3
from typing import Any

from src.core.config import Settings
from src.core.exceptions import DeterministicToolError


class SQLExecutor:
    """只读 SQL 执行器。"""

    FORBIDDEN_KEYWORDS = {
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "attach",
        "detach",
        "pragma",
        "create",
        "replace",
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def execute_read_only(self, sql: str) -> list[dict[str, Any]]:
        normalized = sql.strip().lower()
        if not (normalized.startswith("select") or normalized.startswith("with")):
            raise DeterministicToolError("只允许执行 SELECT 或 WITH 查询。")

        if any(keyword in normalized for keyword in self.FORBIDDEN_KEYWORDS):
            raise DeterministicToolError("检测到危险 SQL 关键字，已阻止执行。")

        with sqlite3.connect(self.settings.sqlite_db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql).fetchall()
            return [dict(row) for row in rows]
