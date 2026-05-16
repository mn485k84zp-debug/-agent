from __future__ import annotations

import json
import uuid
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage

from src.core.config import get_settings
from src.core.message_utils import estimate_tokens
from src.graph.builder import build_application
from src.llm.factory import build_chat_model
from src.sql_agent.executor import SQLExecutor
from src.sql_agent.generator import SQLGenerator
from src.sql_agent.schema_index import SchemaIndexer
from src.web.models import SessionRuntime


class AgentRuntimeService:
    """面向 FastAPI 的运行时服务层。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.sessions: dict[str, SessionRuntime] = {}
        self.llm = None
        self.schema_indexer = None
        self.sql_generator = None
        self.sql_executor = None

    def bootstrap(self) -> None:
        if self.llm is None:
            self.llm = build_chat_model(self.settings)
            self.schema_indexer = SchemaIndexer(self.settings)
            self.sql_generator = SQLGenerator(self.llm)
            self.sql_executor = SQLExecutor(self.settings)

    def ensure_session(self, session_id: str | None) -> dict:
        if session_id and session_id in self.sessions:
            return self._session_summary(self.sessions[session_id])
        return self.create_session()

    def create_session(self) -> dict:
        session_id = uuid.uuid4().hex
        runtime = SessionRuntime(
            session_id=session_id,
            title="新会话",
            app=build_application(),
        )
        self.sessions[session_id] = runtime
        return self._session_summary(runtime)

    def list_sessions(self) -> list[dict]:
        records = sorted(self.sessions.values(), key=lambda item: item.updated_at, reverse=True)
        return [self._session_summary(item) for item in records]

    def delete_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def get_session_detail(self, session_id: str) -> dict:
        session = self._get_session(session_id)
        messages = []
        for message in session.app.state.get("main_messages", []):
            role = "assistant"
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            messages.append({"role": role, "content": str(message.content)})
        return {**self._session_summary(session), "messages": messages}

    def chat(self, session_id: str, message: str) -> dict:
        session = self._get_session(session_id)
        result = session.app.invoke({"user_input": message})
        session.updated_at = datetime.now().isoformat(timespec="seconds")
        session.last_route = result.get("route", "rag")
        session.last_route_reason = result.get("route_reason", "")

        rag_docs = result.get("rag_documents", []) or []
        session.rag_calls += 1
        session.rag_hits += min(len(rag_docs), self.settings.rerank_top_k)

        tool_traces = result.get("tool_traces", []) or []
        if tool_traces:
            session.tool_error_count += len(tool_traces)
        elif session.last_route in {"rag", "both"}:
            session.tool_success_count += 1

        if session.title == "新会话":
            session.title = self._build_title(message)

        return {
            "answer": result.get("final_answer", ""),
            "route": session.last_route,
            "route_reason": session.last_route_reason,
            "tool_traces": tool_traces,
        }

    def query_data(self, question: str, session_id: str | None = None) -> dict:
        self.bootstrap()
        schema_docs = self.schema_indexer.retrieve(question, top_k=self.settings.sql_schema_top_k)
        if not schema_docs:
            raise ValueError("没有检索到相关表结构，暂时无法生成 SQL。")

        schema_context = "\n\n".join(doc.page_content for doc in schema_docs)
        error_feedback = ""
        draft = None
        rows: list[dict] = []

        for _ in range(3):
            draft = self.sql_generator.generate(
                question=question,
                schema_context=schema_context,
                error_feedback=error_feedback,
            )
            try:
                rows = self.sql_executor.execute_read_only(draft.sql)
                break
            except Exception as exc:
                error_feedback = str(exc)
        else:
            raise ValueError(f"SQL 执行失败：{error_feedback}")

        context_messages = []
        if session_id and session_id in self.sessions:
            session_detail = self.get_session_detail(session_id)
            context_messages.append(
                HumanMessage(
                    content=(
                        "以下是会话中最近的上下文，请帮助补充业务解释：\n"
                        f"{json.dumps(session_detail['messages'][-6:], ensure_ascii=False)}"
                    )
                )
            )

        summary_prompt = f"""
你是电商数据分析专家，请将 SQL 查询结果解释成用户容易理解的中文。

用户问题：
{question}

生成 SQL：
{draft.sql if draft else ""}

查询结果：
{json.dumps(rows, ensure_ascii=False, indent=2)}
"""
        final = self.llm.invoke(context_messages + [HumanMessage(content=summary_prompt)])
        answer = final.content if isinstance(final.content, str) else str(final.content)

        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_sql = draft.sql if draft else ""
            session.last_rows = rows
            session.updated_at = datetime.now().isoformat(timespec="seconds")

        return {
            "question": question,
            "answer": answer,
            "sql": draft.sql if draft else "",
            "rows": rows,
            "columns": list(rows[0].keys()) if rows else [],
            "chart": self._build_chart_payload(rows),
            "schema_tables": [doc.metadata.get("table_name", "") for doc in schema_docs],
        }

    def get_status(self, session_id: str | None = None) -> dict:
        session = self.sessions.get(session_id) if session_id else None
        current_tokens = 0
        summary_length = 0
        recent_turn_count = 0

        if session:
            state = session.app.state
            summary_text = state.get("summary", "")
            summary_length = estimate_tokens(summary_text)
            current_tokens = summary_length + sum(
                estimate_tokens(str(message.content))
                for message in state.get("main_messages", [])
            )
            recent_turn_count = len(
                [message for message in state.get("main_messages", []) if isinstance(message, HumanMessage)]
            )

        total_sessions = len(self.sessions)
        total_tool_calls = sum(item.tool_success_count + item.tool_error_count for item in self.sessions.values())
        total_tool_success = sum(item.tool_success_count for item in self.sessions.values())
        total_rag_calls = sum(item.rag_calls for item in self.sessions.values())
        total_rag_hits = sum(item.rag_hits for item in self.sessions.values())

        return {
            "system": {
                "api_ready": True,
                "session_count": total_sessions,
                "knowledge_documents": len(list(self.settings.docs_dir.glob("*.md"))),
                "chroma_path": str(self.settings.chroma_dir),
                "sqlite_path": str(self.settings.sqlite_db_path),
            },
            "memory": {
                "current_tokens": current_tokens,
                "summary_tokens": summary_length,
                "recent_turn_count": recent_turn_count,
                "window_limit": self.settings.memory_max_recent_turns,
                "token_threshold": self.settings.memory_token_threshold,
            },
            "rag": {
                "approx_recall_rate": round((total_rag_hits / (total_rag_calls * self.settings.rerank_top_k)) * 100, 2)
                if total_rag_calls
                else 0.0,
                "total_calls": total_rag_calls,
                "last_route": session.last_route if session else "",
            },
            "tools": {
                "success_rate": round((total_tool_success / total_tool_calls) * 100, 2) if total_tool_calls else 100.0,
                "success_count": total_tool_success,
                "error_count": sum(item.tool_error_count for item in self.sessions.values()),
            },
            "agents": {
                "supervisor": "ready",
                "rag_agent": "ready",
                "sql_agent": "ready",
                "last_route_reason": session.last_route_reason if session else "",
            },
        }

    def should_hint_sql(self, message: str) -> bool:
        keywords = ["订单量", "gmv", "销售额", "客单价", "统计", "数据", "销量", "图表", "分析"]
        lowered = message.lower()
        return any(keyword in message or keyword in lowered for keyword in keywords)

    def _get_session(self, session_id: str) -> SessionRuntime:
        if session_id not in self.sessions:
            raise ValueError("会话不存在，请刷新页面后重试。")
        return self.sessions[session_id]

    def _session_summary(self, session: SessionRuntime) -> dict:
        return {
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "last_route": session.last_route,
        }

    def _build_title(self, message: str) -> str:
        clean = message.strip().replace("\n", " ")
        return clean[:18] + ("..." if len(clean) > 18 else "")

    def _build_chart_payload(self, rows: list[dict]) -> dict:
        if not rows:
            return {"x_field": "", "y_field": "", "series": []}

        sample = rows[0]
        keys = list(sample.keys())
        x_field = keys[0]
        y_field = ""
        for key in keys[1:]:
            if isinstance(sample[key], (int, float)):
                y_field = key
                break
        if not y_field:
            return {"x_field": "", "y_field": "", "series": []}

        return {
            "x_field": x_field,
            "y_field": y_field,
            "series": [{"name": y_field, "data": [row.get(y_field, 0) for row in rows]}],
            "categories": [str(row.get(x_field, "")) for row in rows],
        }
