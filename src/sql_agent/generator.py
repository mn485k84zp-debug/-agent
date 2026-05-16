from __future__ import annotations

from pydantic import BaseModel, Field


class SQLDraft(BaseModel):
    """SQL 生成结果。"""

    sql: str = Field(description="最终 SQL，只能是只读查询")
    rationale: str = Field(description="生成 SQL 的依据")


class SQLGenerator:
    """根据相关 Schema 生成 SQL。"""

    def __init__(self, llm) -> None:
        self.llm = llm
        self.structured_llm = llm.with_structured_output(SQLDraft)

    def generate(self, question: str, schema_context: str, error_feedback: str = "") -> SQLDraft:
        prompt = f"""
你是企业级 BI 系统中的 SQL 专家，请根据给定的表结构生成只读 SQL。

强约束：
1. 只允许使用提供的表结构，不要臆造表名和字段
2. 只生成 SELECT 或 WITH 查询
3. 如果需要统计，请显式写出聚合逻辑
4. 时间筛选优先使用 created_at
5. 如果上一次执行报错，请修正 SQL

用户问题：
{question}

可用 Schema：
{schema_context}

上一次执行反馈：
{error_feedback or "（无）"}
"""
        return self.structured_llm.invoke(prompt)
