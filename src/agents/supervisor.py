from __future__ import annotations

from typing import Literal

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class SupervisorDecision(BaseModel):
    """Supervisor 的结构化决策。"""

    route: Literal["rag", "sql", "both"] = Field(description="路由结果")
    reason: str = Field(description="路由原因")
    rag_subtask: str = Field(default="", description="需要交给 RAG Agent 的任务")
    sql_subtask: str = Field(default="", description="需要交给 SQL Agent 的任务")


class SupervisorAgent:
    """主控 Agent，负责意图识别和任务拆解。"""

    def __init__(self, llm) -> None:
        self.llm = llm
        self.structured_llm = llm.with_structured_output(SupervisorDecision)

    def decide(self, user_input: str, context_messages: list[BaseMessage]) -> SupervisorDecision:
        history = "\n".join(f"{msg.type}: {msg.content}" for msg in context_messages[-8:])
        prompt = f"""
你是一个电商客服与数据分析系统的 Supervisor。

请判断用户问题应该路由到：
- rag: 适合知识问答、政策解释、客服回复、流程说明
- sql: 适合结构化数据查询、销量统计、GMV、订单分析
- both: 同时包含知识问答与数据分析

历史上下文：
{history or "（空）"}

当前问题：
{user_input}
"""
        return self.structured_llm.invoke(prompt)
