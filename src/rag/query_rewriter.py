from __future__ import annotations

from pydantic import BaseModel, Field

from src.core.types import QueryRewriteResult


class RewritePayload(BaseModel):
    """Query 改写输出。"""

    normalized_query: str = Field(description="纠错与规范化后的核心查询")
    rewritten_queries: list[str] = Field(
        default_factory=list,
        description="用于检索扩展的同义改写或子查询列表",
    )


class QueryRewriter:
    """检索前置 Query 改写节点。"""

    def __init__(self, llm) -> None:
        self.llm = llm
        self.structured_llm = llm.with_structured_output(RewritePayload)

    def rewrite(self, query: str) -> QueryRewriteResult:
        prompt = f"""
你是企业级 RAG 系统中的 Query 改写器，需要帮助检索模块提升召回率。

请完成：
1. 修复错别字和口语化表达
2. 保留业务实体，例如 SKU、订单号、退款、物流、GMV 等术语
3. 生成 2 到 4 个能够提升召回率的同义改写或子问题
4. 不要发散，不要改掉用户真实意图

用户查询：
{query}
"""
        try:
            result = self.structured_llm.invoke(prompt)
            rewritten = [item for item in result.rewritten_queries if item and item != result.normalized_query]
            return QueryRewriteResult(
                original_query=query,
                normalized_query=result.normalized_query.strip(),
                rewritten_queries=rewritten,
            )
        except Exception:
            # 改写节点失败时，回退到原 Query，保证主流程可用。
            return QueryRewriteResult(
                original_query=query,
                normalized_query=query.strip(),
                rewritten_queries=[query.strip()],
            )
