from __future__ import annotations

import json

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.core.config import Settings
from src.sql_agent.executor import SQLExecutor
from src.sql_agent.generator import SQLGenerator
from src.sql_agent.schema_index import SchemaIndexer


class AnalyticsSQLAgent:
    """负责结构化数据查询与统计分析。"""

    def __init__(self, llm, settings: Settings) -> None:
        self.llm = llm
        self.settings = settings
        self.schema_indexer = SchemaIndexer(settings)
        self.sql_generator = SQLGenerator(llm)
        self.sql_executor = SQLExecutor(settings)

    def run(
        self,
        query: str,
        shared_context_messages: list[BaseMessage],
        session_messages: list[BaseMessage],
    ) -> tuple[str, list[BaseMessage]]:
        schema_docs = self.schema_indexer.retrieve(query, top_k=self.settings.sql_schema_top_k)
        if not schema_docs:
            answer = "SQL 子代理没有检索到相关表结构，无法安全生成查询。"
            new_session = session_messages + [HumanMessage(content=query), AIMessage(content=answer)]
            return answer, new_session

        schema_context = "\n\n".join(doc.page_content for doc in schema_docs)

        error_feedback = ""
        rows = []
        draft = None
        for _ in range(3):
            draft = self.sql_generator.generate(
                question=query,
                schema_context=schema_context,
                error_feedback=error_feedback,
            )
            try:
                rows = self.sql_executor.execute_read_only(draft.sql)
                break
            except Exception as exc:
                error_feedback = str(exc)
        else:
            answer = f"SQL 子代理未能成功执行查询，最后一次错误：{error_feedback}"
            new_session = session_messages + [HumanMessage(content=query), AIMessage(content=answer)]
            return answer, new_session

        summary_prompt = f"""
你是数据分析 Agent，请根据 SQL 执行结果输出中文业务结论。

用户问题：
{query}

已使用 SQL：
{draft.sql if draft else "（无）"}

相关 Schema：
{schema_context}

查询结果：
{json.dumps(rows, ensure_ascii=False, indent=2)}
"""
        final = self.llm.invoke(
            [
                SystemMessage(content="请输出简洁、业务化、可读的中文分析结论。"),
                *shared_context_messages,
                HumanMessage(content=summary_prompt),
            ]
        )
        answer = final.content if isinstance(final.content, str) else str(final.content)
        new_session = session_messages + [HumanMessage(content=query), AIMessage(content=answer)]
        return answer, new_session
